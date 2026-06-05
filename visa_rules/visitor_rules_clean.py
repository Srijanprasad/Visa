from datetime import date

def evaluate(mode, data):
    common = data.get("common", {})
    visitor = data.get("visitor", {})

    passed_rules = []
    failed_rules = []

    if visitor.get("purpose_is_permitted_under_visitor_rules"):
        passed_rules.append("PURPOSE_PERMITTED")
    else:
        failed_rules.append("PURPOSE_NOT_PERMITTED")

    if visitor.get("stay_within_6_months_limit"):
        passed_rules.append("STAY_WITHIN_LIMIT")
    else:
        failed_rules.append("STAY_EXCEEDS_LIMIT")

    if visitor.get("accommodation_arranged"):
        passed_rules.append("ACCOMMODATION_ARRANGED")
    else:
        failed_rules.append("ACCOMMODATION_NOT_ARRANGED")

    if visitor.get("return_or_onward_travel_planned"):
        passed_rules.append("RETURN_TRAVEL_PLANNED")
    else:
        failed_rules.append("RETURN_TRAVEL_NOT_PLANNED")

    if visitor.get("intends_to_leave_uk_after_visit"):
        passed_rules.append("INTENDS_TO_LEAVE")
    else:
        failed_rules.append("INTENDS_TO_LEAVE_NOT_CONFIRMED")

    if visitor.get("sufficient_funds_for_stay"):
        passed_rules.append("FUNDS_SUFFICIENT_FOR_STAY")
    else:
        failed_rules.append("FUNDS_INSUFFICIENT_FOR_STAY")

    if common.get("english_requirement_met"):
        passed_rules.append("ENGLISH_REQUIREMENT_MET")

    eligible = len(failed_rules) == 0
    return {
        "eligible": eligible,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "summary": "Basic visitor visa eligibility evaluation.",
        "evaluation_date": date.today().isoformat()
    }
