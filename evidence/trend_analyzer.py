# evidence/trend_analyzer.py

from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from observation.models import DailyObservation


# These scores are ONLY used for trend analysis.
# They do NOT change the existing POI calculation.

MOOD_SCORES = {
    "HAPPY": 0,
    "CALM": 1,
    "SAD": 2,
    "AGGRESSIVE": 4,
}

BEHAVIOUR_SCORES = {
    "COOPERATIVE": 0,
    "RESTLESS": 1,
    "WITHDRAWN": 2,
    "DISRUPTIVE": 3,
}

SLEEP_SCORES = {
    "GOOD": 0,
    "POOR": 1,
}

APPETITE_SCORES = {
    "GOOD": 0,
    "POOR": 1,
}

HYGIENE_SCORES = {
    "GOOD": 0,
    "POOR": 1,
}

COMMUNICATION_SCORES = {
    "NORMAL": 0,
    "LIMITED": 1,
    "NONE": 2,
}

PARTICIPATION_SCORES = {
    "ACTIVE": 0,
    "REFUSED": 1,
}


def calculate_trend(values):
    """
    Calculate the directional trend of concern scores.

    Higher score = greater concern.

    Increasing score -> Worsening
    Decreasing score -> Improving
    No change -> Stable
    """

    if not values or len(values) < 2:
        return "Insufficient Data"

    changes = []

    for previous, current in zip(values, values[1:]):
        changes.append(current - previous)

    total_change = sum(changes)

    if total_change > 0:
        return "Worsening"

    if total_change < 0:
        return "Improving"

    return "Stable"


def calculate_poi_trend(poi_values):
    """
    Analyze the trend of existing POI scores.

    Higher POI means higher observation priority.

    This function does NOT calculate or modify POI.
    It only analyzes previously calculated POI values.
    """

    if not poi_values or len(poi_values) < 2:
        return "Insufficient Data"

    changes = []

    for previous, current in zip(poi_values, poi_values[1:]):
        changes.append(current - previous)

    total_change = sum(changes)

    if total_change > 0:
        return "Increasing Priority"

    if total_change < 0:
        return "Decreasing Priority"

    return "Stable Priority"


def get_patient_observations(patient, days=7):
    """
    Get a patient's observations from the last given number of days.

    This function only reads existing DailyObservation records.
    It does not create or modify observations.
    """

    end_date = timezone.localdate()

    start_date = end_date - timedelta(
        days=days - 1
    )

    observations = DailyObservation.objects.filter(
        patient=patient,
        date__range=[start_date, end_date]
    ).order_by(
        "date",
        "time"
    )

    return observations


def group_observations_by_day(observations):
    """
    Group observations by calendar date.

    Multiple observations from the same day are kept together.

    Example:

    Day 1 -> 3 observations
    Day 2 -> 3 observations
    Day 3 -> 2 observations
    """

    grouped = defaultdict(list)

    for observation in observations:
        grouped[observation.date].append(
            observation
        )

    return dict(
        sorted(grouped.items())
    )


def calculate_daily_average(observations, field, score_map):
    """
    Calculate the average concern score for a field
    across observations from one day.
    """

    if not observations:
        return 0

    values = [
        score_map.get(
            getattr(observation, field),
            0
        )
        for observation in observations
    ]

    return sum(values) / len(values)


def build_daily_scores(observations):
    """
    Convert multiple observation sessions into
    one daily score for each observation factor.

    This prevents a patient with 3 observations on one day
    from being treated as if those observations occurred
    across 3 different days.
    """

    grouped = group_observations_by_day(
        observations
    )

    daily_scores = []

    for observation_date, daily_observations in grouped.items():

        daily_scores.append({
            "date": observation_date,

            "observation_count": len(
                daily_observations
            ),

            "mood": calculate_daily_average(
                daily_observations,
                "mood",
                MOOD_SCORES
            ),

            "behaviour": calculate_daily_average(
                daily_observations,
                "behaviour",
                BEHAVIOUR_SCORES
            ),

            "sleep": calculate_daily_average(
                daily_observations,
                "sleep_quality",
                SLEEP_SCORES
            ),

            "appetite": calculate_daily_average(
                daily_observations,
                "appetite",
                APPETITE_SCORES
            ),

            "hygiene": calculate_daily_average(
                daily_observations,
                "personal_hygiene",
                HYGIENE_SCORES
            ),

            "communication": calculate_daily_average(
                daily_observations,
                "communication",
                COMMUNICATION_SCORES
            ),

            "participation": calculate_daily_average(
                daily_observations,
                "participation",
                PARTICIPATION_SCORES
            ),

            "poi": sum(
                observation.poi_score
                for observation in daily_observations
            ) / len(daily_observations),
        })

    return daily_scores


def analyze_patient_trends(observations):
    """
    Analyze trends from a patient's DailyObservation records.

    Multiple observations can exist on the same day.

    Trend analysis is therefore performed using daily
    averages rather than treating every observation session
    as a separate day.
    """

    observations = list(observations)

    if not observations:
        return {
            "status": "Insufficient Data",
            "observation_count": 0,
            "observation_days": 0,
        }

    daily_scores = build_daily_scores(
        observations
    )

    observation_days = len(
        daily_scores
    )

    if observation_days < 2:
        return {
            "status": "Insufficient Data",
            "observation_count": len(observations),
            "observation_days": observation_days,
            "daily_scores": daily_scores,
        }

    mood_values = [
        day["mood"]
        for day in daily_scores
    ]

    behaviour_values = [
        day["behaviour"]
        for day in daily_scores
    ]

    sleep_values = [
        day["sleep"]
        for day in daily_scores
    ]

    appetite_values = [
        day["appetite"]
        for day in daily_scores
    ]

    hygiene_values = [
        day["hygiene"]
        for day in daily_scores
    ]

    communication_values = [
        day["communication"]
        for day in daily_scores
    ]

    participation_values = [
        day["participation"]
        for day in daily_scores
    ]

    poi_values = [
        day["poi"]
        for day in daily_scores
    ]

    return {
        "status": "Success",

        "observation_count": len(
            observations
        ),

        "observation_days": observation_days,

        "average_observations_per_day": round(
            len(observations) / observation_days,
            2
        ),

        "mood": calculate_trend(
            mood_values
        ),

        "behaviour": calculate_trend(
            behaviour_values
        ),

        "sleep": calculate_trend(
            sleep_values
        ),

        "appetite": calculate_trend(
            appetite_values
        ),

        "hygiene": calculate_trend(
            hygiene_values
        ),

        "communication": calculate_trend(
            communication_values
        ),

        "participation": calculate_trend(
            participation_values
        ),

        "poi": calculate_poi_trend(
            poi_values
        ),

        "daily_scores": daily_scores,
    }