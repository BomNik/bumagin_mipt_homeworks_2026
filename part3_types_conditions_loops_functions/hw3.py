#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS_COUNT = 3
DAY_LENGTH = 2
MONTH_LENGTH = 2
YEAR_LENGTH = 4
INCOME_ARGUMENTS_COUNT = 2
MIN_COST_ARGUMENTS_COUNT = 3
FIRST_MONTH = 1
LAST_MONTH = 12
FIRST_DAY = 1
FIRST_YEAR = 1
LONG_MONTH_DAYS = 31
SHORT_MONTH_DAYS = 30
COMMON_FEBRUARY_DAYS = 28
LEAP_FEBRUARY_DAYS = 29
FEBRUARY_MONTH = 2
LONG_MONTHS = (1, 3, 5, 7, 8, 10, 12)
SHORT_MONTHS = (4, 6, 9, 11)

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

Date = tuple[int, int, int]
CategoryTotals = dict[str, float]
IncomeStats = tuple[float, float]
CostStats = tuple[float, float, CategoryTotals]
ParsedTransaction = tuple[Date, float, str | None]
IncomeTransaction = tuple[Date, float]
CostTransaction = tuple[Date, float, str]
Transaction = dict[str, Any]

financial_transactions_storage: list[Transaction] = []


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


def has_valid_date_lengths(day_str: str, month_str: str, year_str: str) -> bool:
    actual_lengths = [len(day_str), len(month_str), len(year_str)]
    expected_lengths = [DAY_LENGTH, MONTH_LENGTH, YEAR_LENGTH]
    return actual_lengths == expected_lengths


def parse_date_parts(maybe_dt: str) -> Date | None:
    date_parts = maybe_dt.split("-")
    if len(date_parts) != DATE_PARTS_COUNT:
        return None

    day_str, month_str, year_str = date_parts
    is_valid = day_str.isdigit()
    is_valid = is_valid and month_str.isdigit()
    is_valid = is_valid and year_str.isdigit()
    is_valid = is_valid and has_valid_date_lengths(day_str, month_str, year_str)
    if not is_valid:
        return None

    return int(day_str), int(month_str), int(year_str)


def is_valid_date(date_tuple: Date) -> bool:
    day, month, year = date_tuple
    max_days = days_in_month(month, year)
    is_valid = year >= FIRST_YEAR
    is_valid = is_valid and FIRST_MONTH <= month <= LAST_MONTH
    is_valid = is_valid and day >= FIRST_DAY
    is_valid = is_valid and max_days is not None
    if not is_valid or max_days is None:
        return False
    return day <= max_days


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parsed_date = parse_date_parts(maybe_dt)
    if parsed_date is None:
        return None

    if not is_valid_date(parsed_date):
        return None
    return parsed_date


def append_invalid_transaction() -> None:
    financial_transactions_storage.append({})


def split_category_name(category_name: str) -> tuple[str, str] | None:
    normalized_category = category_name.strip()
    if normalized_category.count("::") != 1:
        return None

    common_category, target_category = normalized_category.split("::", maxsplit=1)
    if common_category == "" or target_category == "":
        return None
    return common_category, target_category


def is_existing_category(category_name: str) -> bool:
    category_parts = split_category_name(category_name)
    if category_parts is None:
        return False

    common_category, target_category = category_parts
    return common_category in EXPENSE_CATEGORIES and target_category in EXPENSE_CATEGORIES[common_category]


def build_income_transaction(amount: float, parsed_date: Date) -> Transaction:
    return {"amount": amount, "date": parsed_date}


def build_cost_transaction(category_name: str, amount: float, parsed_date: Date) -> Transaction:
    return {"category": category_name, "amount": amount, "date": parsed_date}


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        append_invalid_transaction()
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        append_invalid_transaction()
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(build_income_transaction(float(amount), parsed_date))
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if not is_existing_category(category_name):
        append_invalid_transaction()
        return NOT_EXISTS_CATEGORY

    if amount <= 0:
        append_invalid_transaction()
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        append_invalid_transaction()
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        build_cost_transaction(category_name.strip(), float(amount), parsed_date),
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(
        f"{common_category}::{target_category}"
        for common_category, target_categories in EXPENSE_CATEGORIES.items()
        for target_category in target_categories
    )


def date_key(date_tuple: Date) -> Date:
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


def get_transaction_data(transaction: Transaction) -> ParsedTransaction | None:
    transaction_date = extract_date_value(transaction.get("date"))
    transaction_amount = extract_amount_value(transaction.get("amount"))
    category_value = transaction.get("category")
    if transaction_date is None or transaction_amount is None:
        return None
    if category_value is None:
        return transaction_date, transaction_amount, None
    if not isinstance(category_value, str):
        return None
    return transaction_date, transaction_amount, category_value


def extract_date_value(raw_date: object) -> Date | None:
    if not isinstance(raw_date, tuple):
        return None
    if len(raw_date) != DATE_PARTS_COUNT:
        return None

    day, month, year = raw_date
    if not is_int_date(day, month, year):
        return None
    return day, month, year


def is_int_date(day: object, month: object, year: object) -> bool:
    return isinstance(day, int) and isinstance(month, int) and isinstance(year, int)


def extract_amount_value(raw_amount: object) -> float | None:
    if isinstance(raw_amount, bool):
        return None
    if not isinstance(raw_amount, int | float):
        return None
    return float(raw_amount)


def transactions_until(stats_date: Date) -> list[ParsedTransaction]:
    transactions: list[ParsedTransaction] = []
    for transaction in financial_transactions_storage:
        transaction_data = get_transaction_data(transaction)
        if transaction_data is None:
            continue
        if not is_not_later(transaction_data[0], stats_date):
            continue
        transactions.append(transaction_data)
    return transactions


def income_transactions_until(stats_date: Date) -> list[IncomeTransaction]:
    transactions: list[IncomeTransaction] = []
    for transaction_data in transactions_until(stats_date):
        transaction_date, transaction_amount, category_name = transaction_data
        if category_name is not None:
            continue
        transactions.append((transaction_date, transaction_amount))
    return transactions


def cost_transactions_until(stats_date: Date) -> list[CostTransaction]:
    transactions: list[CostTransaction] = []
    for transaction_data in transactions_until(stats_date):
        transaction_date, transaction_amount, category_name = transaction_data
        if category_name is None:
            continue
        transactions.append((transaction_date, transaction_amount, category_name))
    return transactions


def collect_income_stats(stats_date: Date) -> IncomeStats:
    total_income = float(0)
    month_income = float(0)

    for transaction_date, transaction_amount in income_transactions_until(stats_date):
        total_income += transaction_amount
        if is_same_month(transaction_date, stats_date):
            month_income += transaction_amount

    return total_income, month_income


def increase_category_total(categories: CategoryTotals, category_name: str, amount: float) -> None:
    _, target_category = category_name.split("::", maxsplit=1)
    categories[target_category] = categories.get(target_category, float(0)) + amount


def _collect_month_cost(cost_transaction: CostTransaction, stats_date: Date, categories: CategoryTotals) -> float:
    transaction_date, transaction_amount, category_name = cost_transaction
    if not is_same_month(transaction_date, stats_date):
        return float(0)

    increase_category_total(categories, category_name, transaction_amount)
    return transaction_amount


def collect_cost_stats(stats_date: Date) -> CostStats:
    total_cost = float(0)
    month_cost = float(0)
    categories: CategoryTotals = {}

    for cost_transaction in cost_transactions_until(stats_date):
        total_cost += cost_transaction[1]
        month_cost += _collect_month_cost(cost_transaction, stats_date, categories)

    return total_cost, month_cost, categories


def month_result(month_income: float, month_cost: float) -> tuple[str, float]:
    month_balance = month_income - month_cost
    if month_balance < 0:
        return "loss", -month_balance
    return "profit", month_balance


def month_summary_line(month_income: float, month_cost: float) -> str:
    result_name, result_amount = month_result(month_income, month_cost)
    return f"This month, the {result_name} amounted to {result_amount:.2f} rubles."


def total_capital_line(income_stats: IncomeStats, cost_stats: CostStats) -> str:
    total_capital = income_stats[0] - cost_stats[0]
    return f"Total capital: {total_capital:.2f} rubles"


def build_detail_lines(categories: CategoryTotals) -> list[str]:
    return [
        f"{index}. {category_name}: {format_category_amount(categories[category_name])}"
        for index, category_name in enumerate(sorted(categories), start=1)
    ]


def build_stats_report(report_date: str, income_stats: IncomeStats, cost_stats: CostStats) -> str:
    month_income = income_stats[1]
    month_cost = cost_stats[1]
    report_lines = [
        f"Your statistics as of {report_date}:",
        total_capital_line(income_stats, cost_stats),
        month_summary_line(month_income, month_cost),
        f"Income: {month_income:.2f} rubles",
        f"Expenses: {month_cost:.2f} rubles",
        "",
        "Details (category: amount):",
    ]
    report_lines.extend(build_detail_lines(cost_stats[2]))
    return "\n".join(report_lines)


def stats_handler(report_date: str) -> str:
    stats_date = extract_date(report_date)
    if stats_date is None:
        return INCORRECT_DATE_MSG

    income_stats = collect_income_stats(stats_date)
    cost_stats = collect_cost_stats(stats_date)
    return build_stats_report(report_date, income_stats, cost_stats)


def is_valid_amount_body(normalized_amount: str) -> bool:
    if normalized_amount.count(".") > 1:
        return False
    if "." not in normalized_amount:
        return normalized_amount.isdigit()

    left_part, right_part = normalized_amount.split(".", maxsplit=1)
    return left_part.isdigit() and right_part.isdigit()


def parse_amount(raw_amount: str) -> float | None:
    stripped_amount = raw_amount.strip()
    if stripped_amount == "":
        return None

    sign = ""
    if stripped_amount[0] in "+-":
        sign = stripped_amount[0]
        stripped_amount = stripped_amount[1:]

    if stripped_amount == "":
        return None

    normalized_amount = stripped_amount.replace(",", ".")
    if not is_valid_amount_body(normalized_amount):
        return None

    return float(f"{sign}{normalized_amount}")


def process_income_command(arguments: list[str]) -> str:
    if len(arguments) != INCOME_ARGUMENTS_COUNT:
        return UNKNOWN_COMMAND_MSG

    amount_raw, income_date = arguments
    amount = parse_amount(amount_raw)
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    return income_handler(amount, income_date)


def is_categories_command(arguments: list[str]) -> bool:
    return len(arguments) == 1 and arguments[0] == "categories"


def parse_cost_arguments(arguments: list[str]) -> tuple[str, float, str] | None:
    if len(arguments) < MIN_COST_ARGUMENTS_COUNT:
        return None

    *category_parts, amount_raw, cost_date = arguments
    amount = parse_amount(amount_raw)
    if amount is None:
        return None
    return " ".join(category_parts), amount, cost_date


def process_cost_command(arguments: list[str]) -> str:
    if is_categories_command(arguments):
        return cost_categories_handler()

    parsed_arguments = parse_cost_arguments(arguments)
    if parsed_arguments is None:
        return UNKNOWN_COMMAND_MSG

    category_name, amount, cost_date = parsed_arguments
    result = cost_handler(category_name, amount, cost_date)
    if result != NOT_EXISTS_CATEGORY:
        return result
    return f"{result}\n{cost_categories_handler()}"


def process_stats_command(arguments: list[str]) -> str:
    if len(arguments) != 1:
        return UNKNOWN_COMMAND_MSG
    return stats_handler(arguments[0])


def process_command(raw_command: str) -> str:
    parts = raw_command.split()
    if not parts:
        return UNKNOWN_COMMAND_MSG

    command_name, *arguments = parts
    if command_name == "income":
        return process_income_command(arguments)
    if command_name == "cost":
        return process_cost_command(arguments)
    if command_name == "stats":
        return process_stats_command(arguments)
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    with open(0) as stdin:
        for raw_line in stdin:
            command = raw_line.strip()
            if command == "":
                break
            print(process_command(command))


if __name__ == "__main__":
    main()
