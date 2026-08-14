def build_summary_data(
    observations,
    pattern_result,
    research_evidence,
):
    """
    Build a structured, non-identifying data object
    for the AI summarization layer.
    """

    return {
        "observation_period": {
            "observation_count": len(observations),
        },

        "analysis": {
            "trends": pattern_result.get("trends", {}),
            "matched_fields": pattern_result.get(
                "matched_fields",
                {}
            ),
        },

        "matched_pattern": {
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
        },

        "research_evidence": research_evidence,
    }