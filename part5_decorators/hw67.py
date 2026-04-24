import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


def _make_func_name[**P, R_co](func: CallableWithMeta[P, R_co]) -> str:
    return f"{func.__module__}.{func.__name__}"


def _validate_circuit_breaker_args(critical_count: int, time_to_recover: int) -> None:
    errors: list[Exception] = []

    if not isinstance(critical_count, int) or critical_count <= 0:
        errors.append(ValueError(INVALID_CRITICAL_COUNT))

    if not isinstance(time_to_recover, int) or time_to_recover <= 0:
        errors.append(ValueError(INVALID_RECOVERY_TIME))

    if errors:
        raise ExceptionGroup(VALIDATIONS_FAILED, errors)


@dataclass
class CircuitBreaker:
    critical_count: int = 5
    time_to_recover: int = 30
    triggers_on: type[Exception] = Exception

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        exception_count: int = 0
        block_time: datetime | None = None
        func_name = _make_func_name(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            nonlocal exception_count, block_time

            self._check_if_blocked(block_time, func_name)
            block_time = None

            try:
                res: R_co = func(*args, **kwargs)
            except self.triggers_on as err:
                exception_count += 1
                if exception_count >= self.critical_count:
                    block_time = datetime.now(UTC)
                    raise BreakerError(func_name, block_time) from err
                raise

            exception_count = 0
            return res

        return wrapper

    def __post_init__(self) -> None:
        _validate_circuit_breaker_args(self.critical_count, self.time_to_recover)

    def _check_if_blocked(self, block_time: datetime | None, func_name: str) -> None:
        if not block_time:
            return

        time_to_unblock = block_time + timedelta(seconds=self.time_to_recover)
        if datetime.now(UTC) < time_to_unblock:
            raise BreakerError(func_name, block_time)


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
