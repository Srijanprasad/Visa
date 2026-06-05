def check_financial_requirement(data):
    nationality = data.get("nationality")
    time_spent = data.get("time_spent_in_uk_months", 0)
    exempt = nationality in {"Ireland", "Iceland", "Liechtenstein", "Norway", "Switzerland"}
    return {
        "required": not exempt,
        "exempt_nationality": exempt,
        "minimum_balance": 1270 if time_spent < 12 else 0,
        "notes": "Basic financial requirement stub."
    }


def calculate_required_funds(data):
    course_months = data.get("course_months", 0) or 0
    in_london = data.get("in_london")
    course_fee = data.get("course_fee", 0) or 0
    num_dependants = data.get("num_dependants", 0) or 0
    living_cost = 1265 if in_london else 1015
    total_required = course_fee + (living_cost * min(course_months, 9)) + (630 * num_dependants)
    return {
        "course_months": course_months,
        "in_london": bool(in_london),
        "course_fee": course_fee,
        "num_dependants": num_dependants,
        "living_cost_per_month": living_cost,
        "total_required": total_required
    }


def validate_financial_evidence(data):
    funds_amount = data.get("funds_amount", 0) or 0
    funds_held_since = data.get("funds_held_since")
    application_date = data.get("application_date")
    if funds_held_since and application_date:
        held_days = (application_date - funds_held_since).days if hasattr(application_date, "__sub__") else 0
    else:
        held_days = 0
    fail_reasons = []
    if funds_amount <= 0:
        fail_reasons.append("FUNDS_AMOUNT_MISSING")
    if held_days < 28:
        fail_reasons.append("FUNDS_NOT_HELD_28_DAYS")
    return {
        "funds_amount": funds_amount,
        "funds_held_days": held_days,
        "fail_reasons": fail_reasons,
        "valid": len(fail_reasons) == 0
    }
