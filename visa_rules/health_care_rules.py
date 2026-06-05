from datetime import date

HEALTHCARE_SOC_CODES = {
    "2211", "2212", "2213", "2214", "2215", "2216", "2217", "2221",
    "2222", "2223", "2231", "2232", "2233", "2234", "2235", "2236"
}

def evaluate(mode, data):
    common = data.get("common", {})
    health = data.get("health_care", {})

    passed_rules = []
    failed_rules = []

    if health.get("job_offer_confirmed"):
        passed_rules.append("JOB_OFFER_CONFIRMED")
    else:
        failed_rules.append("JOB_OFFER_NOT_CONFIRMED")

    if health.get("employer_is_licensed_healthcare_sponsor"):
        passed_rules.append("LICENSED_HEALTHCARE_SPONSOR")
    else:
        failed_rules.append("EMPLOYER_NOT_LICENSED_HEALTHCARE_SPONSOR")

    if health.get("certificate_of_sponsorship_issued"):
        passed_rules.append("COS_ISSUED")
    else:
        failed_rules.append("COS_NOT_ISSUED")

    if health.get("job_is_eligible_healthcare_role") or health.get("soc_code") in HEALTHCARE_SOC_CODES:
        passed_rules.append("HEALTHCARE_ROLE_ELIGIBLE")
    else:
        failed_rules.append("HEALTHCARE_ROLE_NOT_ELIGIBLE")

    if health.get("professional_registration_required") and not health.get("professional_registration_provided"):
        failed_rules.append("REGISTRATION_REQUIRED_BUT_NOT_PROVIDED")
    else:
        passed_rules.append("PROFESSIONAL_REGISTRATION_OK")

    if common.get("english_requirement_met"):
        passed_rules.append("ENGLISH_REQUIREMENT_MET")
    else:
        failed_rules.append("ENGLISH_REQUIREMENT_NOT_MET")

    if health.get("salary_offered", 0) <= 0:
        failed_rules.append("SALARY_NOT_PROVIDED")

    eligible = len(failed_rules) == 0
    return {
        "eligible": eligible,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "summary": "Basic health and care visa eligibility evaluation.",
        "evaluation_date": date.today().isoformat()
    }
