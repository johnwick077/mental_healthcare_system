from collections import Counter

from evidence.models import ObservationPattern
from evidence.trend_analyzer import analyze_patient_trends


# ============================================================
# ALL OBSERVATION PARAMETERS
# ============================================================

OBSERVATION_FIELDS = [
    "mood",
    "behaviour",
    "sleep_quality",
    "appetite",
    "personal_hygiene",
    "communication",
    "participation",
]


# ============================================================
# FIELD DISPLAY NAMES
# ============================================================

FIELD_DISPLAY_NAMES = {
    "mood": "Mood",
    "behaviour": "Behaviour",
    "sleep_quality": "Sleep Quality",
    "appetite": "Appetite",
    "personal_hygiene": "Personal Hygiene",
    "communication": "Communication",
    "participation": "Participation",
}


# ============================================================
# GET ALL POSSIBLE CONDITIONS FROM MODEL CHOICES
# ============================================================

def get_possible_conditions(field):
    """
    Return every possible value defined for a DailyObservation field.
    """

    from observation.models import DailyObservation

    model_field = DailyObservation._meta.get_field(field)

    return [
        {
            "value": value,
            "label": label,
        }
        for value, label in model_field.choices
    ]


# ============================================================
# COUNT CONDITIONS
# ============================================================

def count_condition_occurrences(observations, field):
    """
    Count every possible condition for one observation field.
    """

    conditions = get_possible_conditions(field)

    values = [
        getattr(observation, field, None)
        for observation in observations
    ]

    counter = Counter(values)

    result = {}

    for condition in conditions:
        value = condition["value"]

        result[value] = {
            "label": condition["label"],
            "occurrences": counter.get(value, 0),
            "observed": counter.get(value, 0) > 0,
        }

    return result


# ============================================================
# ANALYZE ALL CONDITIONS
# ============================================================

def analyze_all_conditions(
    observations,
    minimum_occurrences=2,
):
    """
    Analyze every possible condition across all seven
    observation parameters.

    This does NOT assume that only 'poor sleep' or
    'withdrawn behaviour' are important.
    """

    if not observations:
        return {}

    total_observations = len(observations)

    analysis = {}

    for field in OBSERVATION_FIELDS:

        conditions = count_condition_occurrences(
            observations,
            field,
        )

        for value, condition in conditions.items():

            occurrences = condition["occurrences"]

            if total_observations:
                percentage = round(
                    (occurrences / total_observations) * 100,
                    2,
                )
            else:
                percentage = 0

            condition["percentage"] = percentage

            condition["repeated"] = (
                occurrences >= minimum_occurrences
            )

        analysis[field] = {
            "display_name": FIELD_DISPLAY_NAMES.get(
                field,
                field.replace("_", " ").title(),
            ),
            "total_observations": total_observations,
            "conditions": conditions,
        }

    return analysis


# ============================================================
# GET REPEATED CONDITIONS ONLY
# ============================================================

def get_repeated_conditions(
    condition_analysis,
    minimum_occurrences=2,
):
    """
    Return conditions that occurred repeatedly.
    """

    repeated = []

    for field, field_data in condition_analysis.items():

        for value, condition in field_data["conditions"].items():

            if condition["occurrences"] >= minimum_occurrences:

                repeated.append(
                    {
                        "field": field,
                        "field_name": field_data["display_name"],
                        "value": value,
                        "label": condition["label"],
                        "occurrences": condition["occurrences"],
                        "percentage": condition["percentage"],
                    }
                )

    return repeated


# ============================================================
# EXISTING RESEARCH PATTERN MATCHING
# ============================================================

def get_field_values(observations, field):
    values = []

    for observation in observations:

        value = getattr(
            observation,
            field,
            None,
        )

        if value is not None:
            values.append(value)

    return values


def count_matching_values(
    observations,
    field,
    expected_value,
):
    values = get_field_values(
        observations,
        field,
    )

    return sum(
        1
        for value in values
        if value == expected_value
    )


def requirement_is_satisfied(
    observations,
    requirement,
    minimum_occurrences=1,
):
    field = requirement.get("field")
    expected_value = requirement.get("value")

    if not field or expected_value is None:
        return False

    count = count_matching_values(
        observations,
        field,
        expected_value,
    )

    return count >= minimum_occurrences


def pattern_matches(
    pattern,
    observations,
):
    """
    Match a research-backed ObservationPattern.

    Every condition defined by the pattern must satisfy
    its minimum occurrence requirement.
    """

    if not observations:
        return False

    if len(observations) < pattern.minimum_days:
        return False

    requirements = (
        pattern.observation_fields
        or []
    )

    if not requirements:
        return False

    for requirement in requirements:

        if not requirement_is_satisfied(
            observations,
            requirement,
            minimum_occurrences=(
                pattern.minimum_occurrences
            ),
        ):
            return False

    return True


def find_matching_patterns(observations):

    if not observations:
        return []

    patterns = ObservationPattern.objects.filter(
        active=True
    )

    matched_patterns = []

    for pattern in patterns:

        if pattern_matches(
            pattern,
            observations,
        ):
            matched_patterns.append(pattern)

    return matched_patterns


# ============================================================
# ANALYZE RESEARCH PATTERN
# ============================================================

def analyze_pattern_match(
    pattern,
    observations,
):

    if not pattern_matches(
        pattern,
        observations,
    ):
        return None

    trend_result = analyze_patient_trends(
        observations
    )

    matched_fields = {}

    for requirement in (
        pattern.observation_fields or []
    ):

        field = requirement.get("field")
        expected_value = requirement.get("value")

        if not field or expected_value is None:
            continue

        matched_fields[field] = {
            "expected_value": expected_value,
            "occurrences": count_matching_values(
                observations,
                field,
                expected_value,
            ),
        }

    return {
        "pattern_name": pattern.name,
        "pattern_description": pattern.pattern_description,
        "possible_concern": pattern.possible_concern,
        "recommendation": pattern.recommendation,
        "minimum_days": pattern.minimum_days,
        "minimum_occurrences": pattern.minimum_occurrences,
        "matched_fields": matched_fields,
        "trends": trend_result,
    }


# ============================================================
# COMPLETE OBSERVATION ANALYSIS
# ============================================================

def analyze_complete_observations(
    observations,
    minimum_occurrences=2,
):
    """
    Complete analysis used when generating the AI summary.

    It considers ALL possible conditions for:
        - Mood
        - Behaviour
        - Sleep
        - Appetite
        - Hygiene
        - Communication
        - Participation
    """

    if not observations:
        return {
            "condition_analysis": {},
            "repeated_conditions": [],
            "trends": {},
        }

    condition_analysis = analyze_all_conditions(
        observations,
        minimum_occurrences=minimum_occurrences,
    )

    repeated_conditions = get_repeated_conditions(
        condition_analysis,
        minimum_occurrences=minimum_occurrences,
    )

    trends = analyze_patient_trends(
        observations
    )

    return {
        "condition_analysis": condition_analysis,
        "repeated_conditions": repeated_conditions,
        "trends": trends,
    }