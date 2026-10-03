from datetime import date, datetime


def make_json_safe(value):
    """
    Convert Python values into JSON-safe values.

    Important because Django JSONField cannot directly store
    datetime.date or datetime objects.
    """

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            make_json_safe(item)
            for item in value
        ]

    return value


def build_observation_data(observations):
    """
    Convert observations into structured information
    for the AI model.
    """

    data = []

    for observation in observations:

        data.append(
            {
                "date": (
                    observation.date.isoformat()
                    if observation.date
                    else None
                ),

                "time": (
                    observation.time.isoformat()
                    if observation.time
                    else None
                ),

                "mood": observation.mood,

                "behaviour": observation.behaviour,

                "sleep_quality": (
                    observation.sleep_quality
                ),

                "appetite": observation.appetite,

                "personal_hygiene": (
                    observation.personal_hygiene
                ),

                "communication": (
                    observation.communication
                ),

                "participation": (
                    observation.participation
                ),

                "poi_score": observation.poi_score,

                "priority_level": (
                    observation.priority_level
                ),

                "remarks": observation.remarks,
            }
        )

    return data


def build_summary_data(
    observations,
    pattern_result,
    research_evidence,
    complete_analysis=None,
):
    """
    Build the complete structured input for AI summarization.
    """

    if complete_analysis is None:
        complete_analysis = {}

    # ========================================================
    # ANALYSIS DATA
    # ========================================================

    trends = complete_analysis.get(
        "trends",
        {},
    )

    condition_analysis = complete_analysis.get(
        "condition_analysis",
        {},
    )

    repeated_conditions = complete_analysis.get(
        "repeated_conditions",
        [],
    )


    # ========================================================
    # OBSERVATION PERIOD
    # ========================================================

    observation_count = len(
        observations
    )

    observation_dates = {
        observation.date
        for observation in observations
        if observation.date
    }

    observation_days = len(
        observation_dates
    )

    average_observations_per_day = (
        round(
            observation_count / observation_days,
            2
        )
        if observation_days > 0
        else 0
    )


    # ========================================================
    # MATCHED PATTERN
    # ========================================================

    matched_pattern = {}

    if pattern_result:

        matched_pattern = {

            "name": pattern_result.get(
                "pattern_name"
            ),

            "description": pattern_result.get(
                "pattern_description"
            ),

            "minimum_days": pattern_result.get(
                "minimum_days"
            ),

            "minimum_occurrences": pattern_result.get(
                "minimum_occurrences"
            ),

            "possible_concern": pattern_result.get(
                "possible_concern"
            ),

            "recommendation": pattern_result.get(
                "recommendation"
            ),
        }


    # ========================================================
    # COMPLETE STRUCTURED DATA
    # ========================================================

    data = {

        # ----------------------------------------------------
        # Observation period
        # ----------------------------------------------------

        "observation_period": {

            "observation_count": (
                observation_count
            ),

            "observation_days": (
                observation_days
            ),

            "average_observations_per_day": (
                average_observations_per_day
            ),
        },


        # ----------------------------------------------------
        # Individual observations
        # ----------------------------------------------------

        "observations": (
            build_observation_data(
                observations
            )
        ),


        # ----------------------------------------------------
        # Complete condition analysis
        # ----------------------------------------------------

        "complete_condition_analysis": {

            "mood": condition_analysis.get(
                "mood",
                {},
            ),

            "behaviour": condition_analysis.get(
                "behaviour",
                {},
            ),

            "sleep_quality": condition_analysis.get(
                "sleep_quality",
                {},
            ),

            "appetite": condition_analysis.get(
                "appetite",
                {},
            ),

            "personal_hygiene": condition_analysis.get(
                "personal_hygiene",
                {},
            ),

            "communication": condition_analysis.get(
                "communication",
                {},
            ),

            "participation": condition_analysis.get(
                "participation",
                {},
            ),
        },


        # ----------------------------------------------------
        # Repeated conditions
        # ----------------------------------------------------

        "repeated_conditions": (
            repeated_conditions
        ),


        # ----------------------------------------------------
        # Analysis
        # ----------------------------------------------------

        "analysis": {

            "trends": (
                trends
            ),

            "matched_fields": (
                pattern_result.get(
                    "matched_fields",
                    {},
                )
                if pattern_result
                else {}
            ),
        },


        # ----------------------------------------------------
        # Matched pattern
        # ----------------------------------------------------

        "matched_pattern": (
            matched_pattern
        ),


        # ----------------------------------------------------
        # Research evidence
        # ----------------------------------------------------

        "research_evidence": (
            research_evidence
            or []
        ),
    }

    return make_json_safe(data)