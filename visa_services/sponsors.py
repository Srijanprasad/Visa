def get_licensed_sponsor_names(limit=None):
    sponsors = [
        "DeepMind Technologies Ltd",
        "Google UK Ltd",
        "NHS England",
        "University of Oxford",
        "Amazon UK Services Ltd",
        "Revolut Ltd"
    ]
    return sponsors[:limit] if limit else sponsors


def is_licensed_employer(name: str) -> bool:
    return bool(name and name.strip() and name in get_licensed_sponsor_names())


def get_licensed_student_provider_names(limit=None):
    providers = [
        "University of Oxford",
        "University of Cambridge",
        "Imperial College London",
        "UCL (University College London)",
        "King's College London"
    ]
    return providers[:limit] if limit else providers


def is_licensed_student_provider(name: str) -> bool:
    return bool(name and name.strip() and name in get_licensed_student_provider_names())
