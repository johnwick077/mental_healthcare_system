# evidence/trend_analyzer.py

# These scores are ONLY used for trend analysis.
# They do NOT change the existing POI calculation.
from datetime import timedelta
from django.utils import timezone

from observation.models import DailyObservation
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
    Calculate the trend of a concern score.

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
    start_date = end_date - timedelta(days=days - 1)

    observations = DailyObservation.objects.filter(
        patient=patient,
        date__range=[start_date, end_date]
    ).order_by("date", "time")

    return observations

def analyze_patient_trends(observations):
    """
    Analyze trends from a patient's DailyObservation records.

    The observations must already be ordered chronologically.
    """

    if not observations or len(observations) < 2:
        return {
            "status": "Insufficient Data",
            "observation_count": len(observations),
        }

    mood_values = []
    behaviour_values = []
    sleep_values = []
    appetite_values = []
    hygiene_values = []
    communication_values = []
    participation_values = []
    poi_values = []

    for observation in observations:

        mood_values.append(
            MOOD_SCORES.get(observation.mood, 0)
        )

        behaviour_values.append(
            BEHAVIOUR_SCORES.get(observation.behaviour, 0)
        )

        sleep_values.append(
            SLEEP_SCORES.get(observation.sleep_quality, 0)
        )

        appetite_values.append(
            APPETITE_SCORES.get(observation.appetite, 0)
        )

        hygiene_values.append(
            HYGIENE_SCORES.get(observation.personal_hygiene, 0)
        )

        communication_values.append(
            COMMUNICATION_SCORES.get(observation.communication, 0)
        )

        participation_values.append(
            PARTICIPATION_SCORES.get(observation.participation, 0)
        )

        poi_values.append(observation.poi_score)

    return {
        "status": "Success",
        "observation_count": len(observations),

        "mood": calculate_trend(mood_values),

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
    }