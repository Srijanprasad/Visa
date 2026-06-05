from datetime import date

def evaluate(mode, data):
    common = data.get("common", {})
    skilled = data.get("skilled_worker", {})

    passed_rules = []
    failed_rules = []

    if skilled.get("job_offer_confirmed"):
        passed_rules.append("JOB_OFFER_CONFIRMED")
    else:
        failed_rules.append("JOB_OFFER_NOT_CONFIRMED")

    if skilled.get("employer_is_licensed_sponsor"):
        passed_rules.append("LICENSED_SPONSOR")
    else:
        failed_rules.append("EMPLOYER_NOT_LICENSED")

    if skilled.get("certificate_of_sponsorship_issued"):
        passed_rules.append("COS_ISSUED")
    else:
        failed_rules.append("COS_NOT_ISSUED")

    if skilled.get("meets_minimum_salary_threshold"):
        passed_rules.append("SALARY_THRESHOLD_MET")
    else:
        failed_rules.append("SALARY_THRESHOLD_NOT_MET")

    if common.get("english_requirement_met"):
        passed_rules.append("ENGLISH_REQUIREMENT_MET")
    else:
        failed_rules.append("ENGLISH_REQUIREMENT_NOT_MET")

    if skilled.get("job_is_eligible_occupation"):
        passed_rules.append("OCCUPATION_ELIGIBLE")
    else:
        failed_rules.append("OCCUPATION_NOT_ELIGIBLE")

    if skilled.get("salary_offered", 0) <= 0:
        failed_rules.append("SALARY_NOT_PROVIDED")

    eligible = len(failed_rules) == 0
    return {
        "eligible": eligible,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "summary": "Basic skilled worker visa eligibility evaluation.",
        "evaluation_date": date.today().isoformat()
    }
