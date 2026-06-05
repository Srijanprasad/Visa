from datetime import date

def evaluate_student(mode, data):
    common = data.get("common", {})
    student = data.get("student", {})

    passed_rules = []
    failed_rules = []

    if student.get("has_cas"):
        passed_rules.append("CAS_PRESENT")
    else:
        failed_rules.append("CAS_MISSING")

    if student.get("education_provider_is_licensed"):
        passed_rules.append("LICENSED_PROVIDER")
    else:
        failed_rules.append("PROVIDER_NOT_LICENSED")

    if common.get("english_requirement_met"):
        passed_rules.append("ENGLISH_REQUIREMENT_MET")
    else:
        failed_rules.append("ENGLISH_REQUIREMENT_NOT_MET")

    if student.get("meets_financial_requirement"):
        passed_rules.append("FINANCIAL_REQUIREMENT_MET")
    else:
        failed_rules.append("FINANCIAL_REQUIREMENT_NOT_MET")

    if student.get("funds_held_for_28_days"):
        passed_rules.append("FUNDS_HELD_28_DAYS")
    else:
        failed_rules.append("FUNDS_NOT_HELD_28_DAYS")

    if student.get("course_duration_months", 0) >= 6:
        passed_rules.append("COURSE_DURATION_SUFFICIENT")
    else:
        failed_rules.append("COURSE_DURATION_TOO_SHORT")

    eligible = len(failed_rules) == 0
    return {
        "eligible": eligible,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "summary": "Basic student visa eligibility evaluation.",
        "evaluation_date": date.today().isoformat()
    }
