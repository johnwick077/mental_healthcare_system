from evidence.models import ObservationPattern


def pattern_matches(pattern, observations):
    """
    Check whether an ObservationPattern matches
    the supplied DailyObservation records.

    The pattern uses the observation_fields JSON field.
    """

    if not observations:
        return False

    # Check minimum number of observations.
    if len(observations) < pattern.minimum_days:
        return False

    # Get matching requirements from JSON.
    requirements = pattern.observation_fields or []

    if not requirements:
        return False

    # Check every requirement using the pattern's
    # minimum occurrence requirement.
    for requirement in requirements:

        if not requirement_is_satisfied(
            observations,
            requirement,
            minimum_occurrences=pattern.minimum_occurrences
        ):
            return False

    return True


def find_matching_patterns(observations):
    """
    Find all active ObservationPatterns that match
    the patient's recent observations.
    """

    if not observations:
        return []

    patterns = ObservationPattern.objects.filter(
        active=True
    )

    matched_patterns = []

    for pattern in patterns:

        if pattern_matches(pattern, observations):
            matched_patterns.append(pattern)

    return matched_patterns


def get_field_values(observations, field):
    """
    Get the values of a specific observation field
    from the supplied observations.
    """

    values = []

    for observation in observations:
        value = getattr(observation, field, None)

        if value is not None:
            values.append(value)

    return values


def count_matching_values(
    observations,
    field,
    expected_value
):
    """
    Count how many observations contain
    the expected field value.
    """

    values = get_field_values(
        observations,
        field
    )

    return sum(
        1
        for value in values
        if value == expected_value
    )


def requirement_is_satisfied(
    observations,
    requirement,
    minimum_occurrences=1
):
    """
    Check whether an observation requirement
    occurs at least the required number of times.
    """

    field = requirement.get("field")
    expected_value = requirement.get("value")

    if not field or expected_value is None:
        return False

    count = count_matching_values(
        observations,
        field,
        expected_value
    )

    return count >= minimum_occurrences

def analyze_pattern_match(pattern, observations):
    """
    Combine pattern matching with the patient's
    observation trends.

    Returns structured information that can later
    be passed to the research evidence layer.
    """

    if not pattern_matches(pattern, observations):
        return None

    from evidence.trend_analyzer import analyze_patient_trends

    trend_result = analyze_patient_trends(observations)

    matched_fields = {}

    for requirement in pattern.observation_fields or []:

        field = requirement.get("field")
        expected_value = requirement.get("value")

        if not field or expected_value is None:
            continue

        matched_fields[field] = {
            "expected_value": expected_value,
            "occurrences": count_matching_values(
                observations,
                field,
                expected_value
            )
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