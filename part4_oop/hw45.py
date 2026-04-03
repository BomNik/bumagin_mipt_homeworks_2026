from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Self, TypeVar, cast

from part4_oop.interfaces import Cache, HasCache, Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class DictStorage(Storage[K, V]):
    _data: dict[K, V] = field(default_factory=dict, init=False)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def exists(self, key: K) -> bool:
        return key in self._data

    def remove(self, key: K) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


@dataclass
class FIFOPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key not in self._order:
            self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._order)


@dataclass
class LRUPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._order)


@dataclass
class LFUPolicy(Policy[K]):
    capacity: int = 5
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)
    _key_to_evict: K | None = field(default=None, init=False)

    def register_access(self, key: K) -> None:
        if key in self._key_counter:
            current_count = self._key_counter.get(key, 0)
            self._key_counter.update({key: current_count + 1})
            self._key_to_evict = None
            return

        if len(self._key_counter) >= self.capacity and self._key_counter:
            self._key_to_evict = min(self._key_counter, key=self._get_access_count)
        else:
            self._key_to_evict = None

        self._key_counter[key] = 1

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)
        if key == self._key_to_evict:
            self._key_to_evict = None

    def clear(self) -> None:
        self._key_counter.clear()
        self._key_to_evict = None

    @property
    def has_keys(self) -> bool:
        return bool(self._key_counter)

    def _get_access_count(self, key: K) -> int:
        return self._key_counter[key]

    def _eviction_candidate(self) -> K | None:
        if self._key_to_evict not in self._key_counter:
            self._key_to_evict = None
        return self._key_to_evict

    get_key_to_evict = _eviction_candidate


class MIPTCache(Cache[K, V]):
    def __init__(self, storage: Storage[K, V], policy: Policy[K]) -> None:
        self.storage = storage
        self.policy = policy

    def set(self, key: K, value: V) -> None:
        self.storage.set(key, value)
        self.policy.register_access(key)

        key_to_evict = self.policy.get_key_to_evict()
        if key_to_evict is not None:
            self.storage.remove(key_to_evict)
            self.policy.remove_key(key_to_evict)

    def get(self, key: K) -> V | None:
        if self.storage.exists(key):
            self.policy.register_access(key)
            return self.storage.get(key)
        return None

    def exists(self, key: K) -> bool:
        return self.storage.exists(key)

    def remove(self, key: K) -> None:
        self.storage.remove(key)
        self.policy.remove_key(key)

    def clear(self) -> None:
        self.storage.clear()
        self.policy.clear()


class CachedProperty[V]:
    def __init__(self, func: Callable[..., V]) -> None:
        self._func = func
        self._name = func.__name__

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def __get__(self, instance: HasCache[Any, V] | None, owner: type) -> V | Self:
        if instance is None:
            return self

        cache_key = self._construct_key(instance, owner)

        if instance.cache.exists(cache_key):
            return cast("V", instance.cache.get(cache_key))

        value = self._func(instance)
        instance.cache.set(cache_key, value)
        return value

    def _construct_key(self, instance: HasCache[Any, Any], owner: type) -> str:
        return f"cached_property:{owner.__name__}:{self._name}:{id(instance)}"
