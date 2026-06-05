from datetime import date

def evaluate(mode, data):
    common = data.get("common", {})
    graduate = data.get("graduate", {})

    passed_rules = []
    failed_rules = []

    if graduate.get("currently_in_uk"):
        passed_rules.append("CURRENTLY_IN_UK")
    else:
        failed_rules.append("CURRENTLY_OUTSIDE_UK")

    if graduate.get("course_completed"):
        passed_rules.append("COURSE_COMPLETED")
    else:
        failed_rules.append("COURSE_NOT_COMPLETED")

    if graduate.get("provider_reported_completion_to_home_office"):
        passed_rules.append("PROVIDER_REPORTED_COMPLETION")
    else:
        failed_rules.append("PROVIDER_NOT_REPORTED_COMPLETION")

    if graduate.get("student_visa_valid_on_application_date"):
        passed_rules.append("VISA_VALID_ON_APPLICATION_DATE")
    else:
        failed_rules.append("VISA_NOT_VALID_ON_APPLICATION_DATE")

    if common.get("english_requirement_met"):
        passed_rules.append("ENGLISH_REQUIREMENT_MET")
    else:
        failed_rules.append("ENGLISH_REQUIREMENT_NOT_MET")

    eligible = len(failed_rules) == 0
    return {
        "eligible": eligible,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "summary": "Basic graduate visa eligibility evaluation.",
        "evaluation_date": date.today().isoformat()
    }
