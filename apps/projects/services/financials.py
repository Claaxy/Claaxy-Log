from datetime import datetime, time
from decimal import Decimal
from typing import Any

from django.utils import timezone


def parse_dashboard_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def get_date_range_bounds(from_date, to_date) -> tuple[datetime, datetime]:
    start = timezone.make_aware(datetime.combine(from_date, time.min))
    end = timezone.make_aware(datetime.combine(to_date, time.max))
    return start, end


def sum_financials_from_extracts(
    extracts: list[dict[str, Any] | None],
) -> dict[str, Any]:
    """Sum income and expenses across multiple voice-note extracts."""
    total_income = 0.0
    income_seen = False
    total_expense = 0.0

    for data in extracts:
        if not data:
            continue
        income = data.get('income')
        if income is not None:
            total_income += float(income)
            income_seen = True
        for item in data.get('expenses') or []:
            if not isinstance(item, dict):
                continue
            amount = item.get('amount')
            if amount is not None:
                total_expense += float(amount)

    profit = None
    if income_seen:
        profit = total_income - total_expense
    elif total_expense:
        profit = -total_expense

    return {
        'income': total_income if income_seen else None,
        'expense_total': total_expense,
        'profit': profit,
    }


def merge_voice_note_financials(
    extracts: list[dict[str, Any] | None],
) -> dict[str, Any] | None:
    """Merge per-note financial_extract values (chronological; later notes override)."""
    income = None
    expenses_by_label: dict[str, float] = {}

    for data in extracts:
        if not data:
            continue
        note_income = data.get('income')
        if note_income is not None:
            income = float(note_income)
        for item in data.get('expenses') or []:
            if not isinstance(item, dict):
                continue
            amount = item.get('amount')
            if amount is None:
                continue
            label = str(item.get('label', '')).strip() or 'Expense'
            expenses_by_label[label] = float(amount)

    if income is None and not expenses_by_label:
        return None

    expenses = [
        {'label': label, 'amount': amount}
        for label, amount in expenses_by_label.items()
    ]
    return normalize_financials({'income': income, 'expenses': expenses})


def normalize_financials(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return None

    income = data.get('income')
    if income is not None:
        income = float(income)

    expenses = []
    for item in data.get('expenses') or []:
        if not isinstance(item, dict):
            continue
        amount = item.get('amount')
        if amount is None:
            continue
        expenses.append({
            'label': str(item.get('label', '')).strip() or 'Expense',
            'amount': float(amount),
        })

    profit = get_profit({'income': income, 'expenses': expenses})
    return {
        'income': income,
        'expenses': expenses,
        'profit': profit,
    }


def get_profit(financials: dict[str, Any] | None) -> float | None:
    if not financials:
        return None

    income = financials.get('income')
    expenses = financials.get('expenses') or []
    total_expense = sum(
        float(item.get('amount', 0))
        for item in expenses
        if item.get('amount') is not None
    )

    if income is not None:
        return float(income) - total_expense

    profit = financials.get('profit')
    if profit is not None:
        return float(profit)
    return None


def clone_financials(financials: dict[str, Any] | None) -> dict[str, Any]:
    if not financials:
        return {'income': None, 'expenses': [], 'profit': None}
    return {
        'income': financials.get('income'),
        'expenses': [dict(item) for item in financials.get('expenses') or []],
        'profit': financials.get('profit'),
    }


def save_manual_financials(project, data: dict[str, Any]) -> None:
    normalized = normalize_financials(data)
    project.ai_financials = normalized
    project.financials_manually_edited = True
    project.save(update_fields=['ai_financials', 'financials_manually_edited', 'updated_at'])


def parse_amount(value) -> float | None:
    if value is None or value == '':
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    cleaned = str(value).strip().replace(',', '')
    if not cleaned:
        return None
    return float(cleaned)


def format_money(value: float | int | Decimal | None) -> str:
    if value is None:
        return '—'
    return f'{float(value):,.2f}'
