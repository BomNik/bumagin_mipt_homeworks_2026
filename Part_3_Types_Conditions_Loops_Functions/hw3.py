#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"
DATE_PARTS_COUNT = 3
INCOME_COMMAND_PARTS = 3
COST_COMMAND_PARTS = 4
STATS_COMMAND_PARTS = 2
FIRST_MONTH = 1
LAST_MONTH = 12
MIN_DAY = 1
LONG_MONTH_DAYS = 31
SHORT_MONTH_DAYS = 30
LEAP_FEBRUARY_DAYS = 29
COMMON_FEBRUARY_DAYS = 28
FEBRUARY_MONTH = 2
LONG_MONTHS = (1, 3, 5, 7, 8, 10, 12)
SHORT_MONTHS = (4, 6, 9, 11)

Date = tuple[int, int, int]
IncomeRecord = tuple[float, str]
CostRecord = tuple[str, float, Date]
CategoryTotals = dict[str, float]
IncomeStats = tuple[float, float]
CostStats = tuple[float, float, CategoryTotals]


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    is_divisible_by_four = year % 4 == 0
    is_divisible_by_hundred = year % 100 == 0
    is_divisible_by_four_hundred = year % 400 == 0
    return (is_divisible_by_four and not is_divisible_by_hundred) or is_divisible_by_four_hundred


def parse_date_parts(maybe_dt: str) -> Date | None:
    date_parts = maybe_dt.split("-")
    if len(date_parts) != DATE_PARTS_COUNT:
        return None

    int_parts: list[int] = []
    for val in date_parts:
        if not val.isdigit():
            return None
        int_parts.append(int(val))

    return int_parts[0], int_parts[1], int_parts[2]


def days_in_month(month: int, year: int) -> int | None:
    if month in LONG_MONTHS:
        return LONG_MONTH_DAYS
    if month in SHORT_MONTHS:
        return SHORT_MONTH_DAYS
    if month == FEBRUARY_MONTH:
        if is_leap_year(year):
            return LEAP_FEBRUARY_DAYS
        return COMMON_FEBRUARY_DAYS
    return None


def extract_date(maybe_dt: str) -> Date | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: tuple формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parsed_date = parse_date_parts(maybe_dt)
    if parsed_date is None:
        return None

    day, month, year = parsed_date
    if month < FIRST_MONTH or month > LAST_MONTH:
        return None
    if day < MIN_DAY:
        return None
    max_days = days_in_month(month, year)
    if max_days is None or day > max_days:
        return None

    return parsed_date


def income_handler(amount: float, income_date: str) -> str:
    return f"{OP_SUCCESS_MSG} {amount=} {income_date=}"


def cost_handler(category_name: str, amount: float, cost_date: str) -> str:
    return f"{OP_SUCCESS_MSG} {category_name=} {amount=} {cost_date=}"


def handle_income(incomes: list[IncomeRecord], amount_str: str, income_date: str) -> str:
    amount: float | None = parse_amount(amount_str)
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    date: Date | None = extract_date(income_date)
    if date is None:
        return INCORRECT_DATE_MSG

    incomes.append((amount, income_date))
    return income_handler(amount, income_date)


def handle_cost(costs: list[CostRecord], category_name: str, amount_str: str, cost_date: str) -> str:
    if category_name.strip() == "":
        return UNKNOWN_COMMAND_MSG

    amount: float | None = parse_amount(amount_str)
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    date: Date | None = extract_date(cost_date)
    if date is None:
        return INCORRECT_DATE_MSG

    costs.append((category_name, amount, date))
    return cost_handler(category_name, amount, cost_date)


def date_key(date_tuple: Date) -> Date:
    """Преобразует дату в кортеж формата (год, месяц, день) для удобства сравнения."""
    day, month, year = date_tuple
    return year, month, day


def is_not_later(record_date: Date, border_date: Date) -> bool:
    return date_key(record_date) <= date_key(border_date)


def is_same_month(record_date: Date, border_date: Date) -> bool:
    _, record_month, record_year = record_date
    _, border_month, border_year = border_date
    return record_month == border_month and record_year == border_year


def format_category_amount(amount: float) -> str:
    if amount.is_integer():
        return str(int(amount))

    return f"{amount:.10f}".rstrip("0").rstrip(".")


def collect_income_stats(incomes: list[IncomeRecord], stats_date: Date) -> IncomeStats:
    total_income: float = 0
    month_income: float = 0

    for amount, income_date_str in incomes:
        income_date = extract_date(income_date_str)
        if income_date is None or not is_not_later(income_date, stats_date):
            continue

        total_income += amount
        if is_same_month(income_date, stats_date):
            month_income += amount

    return total_income, month_income


def collect_cost_stats(costs: list[CostRecord], stats_date: Date) -> CostStats:
    total_cost: float = 0
    month_cost: float = 0
    categories: CategoryTotals = {}

    for cost in costs:
        if not is_not_later(cost[2], stats_date):
            continue

        total_cost += cost[1]
        if not is_same_month(cost[2], stats_date):
            continue

        month_cost += cost[1]
        if cost[0] not in categories:
            categories[cost[0]] = 0
        categories[cost[0]] += cost[1]

    return total_cost, month_cost, categories


def month_result(month_income: float, month_cost: float) -> tuple[str, float]:
    profit = month_income - month_cost
    result = "прибыль составила"
    if profit < 0:
        return "убыток составил", -profit
    return result, profit


def month_summary_line(month_income: float, month_cost: float) -> str:
    result, profit = month_result(month_income, month_cost)
    return f"В этом месяце {result} {profit:.2f} рублей"  # noqa: RUF001


def build_stats_report(date: str, income_stats: IncomeStats, cost_stats: CostStats) -> str:
    total_capital = income_stats[0] - cost_stats[0]
    lines = [
        f"Ваша статистика по состоянию на {date}:",
        f"Суммарный капитал: {total_capital:.2f} рублей",
        month_summary_line(income_stats[1], cost_stats[1]),
        f"Доходы: {income_stats[1]:.2f} рублей",
        f"Расходы: {cost_stats[1]:.2f} рублей",
        "",
        "Детализация (категория: сумма):",
    ]

    for idx, category_name in enumerate(sorted(cost_stats[2]), start=1):
        category_total = format_category_amount(cost_stats[2][category_name])
        lines.append(f"{idx}. {category_name}: {category_total}")

    return "\n".join(lines)


def show_stats(incomes: list[IncomeRecord], costs: list[CostRecord], date: str) -> str:
    stats_date = extract_date(date)
    if stats_date is None:
        return INCORRECT_DATE_MSG

    income_stats = collect_income_stats(incomes, stats_date)
    cost_stats = collect_cost_stats(costs, stats_date)
    return build_stats_report(date, income_stats, cost_stats)


def is_valid_amount_body(normalized: str) -> bool:
    if normalized.count(".") > 1:
        return False
    if "." not in normalized:
        return normalized.isdigit()

    left, right = normalized.split(".", 1)
    return left.isdigit() and right.isdigit()


def parse_amount(raw: str) -> float | None:
    stripped = raw.strip()
    if stripped == "":
        return None

    sign = ""
    if stripped[0] in "+-":
        sign = stripped[0]
        stripped = stripped[1:]

    if stripped == "":
        return None

    normalized = stripped.replace(",", ".")
    if not is_valid_amount_body(normalized):
        return None

    return float(sign + normalized)


def process_command(parts: list[str], incomes: list[IncomeRecord], costs: list[CostRecord]) -> str:
    if len(parts) == INCOME_COMMAND_PARTS and parts[0] == "income":
        return handle_income(incomes, parts[1], parts[2])
    if len(parts) == COST_COMMAND_PARTS and parts[0] == "cost":
        return handle_cost(costs, parts[1], parts[2], parts[3])
    if len(parts) == STATS_COMMAND_PARTS and parts[0] == "stats":
        return show_stats(incomes, costs, parts[1])
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    incomes: list[IncomeRecord] = []
    costs: list[CostRecord] = []

    with open(0) as stdin:
        for raw_line in stdin:
            raw = raw_line.strip()
            if raw == "":
                break

            print(process_command(raw.split(), incomes, costs))


if __name__ == "__main__":
    main()
