from typing import List

from django.conf import settings
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class AISummary(BaseModel):
    """
    Structured response returned by the AI.
    """

    observation_summary: str = Field(
        description="A concise summary of the patient's observed changes."
    )

    observed_changes: List[str] = Field(
        description="Important changes identified from the supplied observations."
    )

    evidence_interpretation: str = Field(
        description="Explanation of what the supplied research evidence says about the observed pattern."
    )

    recommended_follow_up: str = Field(
        description="A cautious recommendation for continued observation or professional review."
    )

    disclaimer: str = Field(
        description="A clear statement that this is not a medical diagnosis."
    )


def get_gemini_client():
    """
    Create the Gemini API client.
    """

    return genai.Client(
        api_key=settings.GEMINI_API_KEY
    )


def build_summary_prompt(data):
    """
    Build a controlled prompt using only the
    structured observation and research evidence.
    """

    return f"""
You are an evidence-based summarization assistant
for a mental healthcare observation management system.

Your task is to summarize the supplied observation data
using ONLY the information provided below.

IMPORTANT RULES:

1. Do NOT diagnose the patient.
2. Do NOT claim that the patient has a disease.
3. Do NOT invent symptoms, conditions, research findings,
   datasets, or conclusions.
4. Clearly distinguish observed patient information from
   research evidence.
5. Use the research evidence only for contextual interpretation.
6. If the research evidence does not support a conclusion,
   explicitly say that the evidence is insufficient.
7. Mention trends such as worsening, improving, or stable
   only when they are supplied in the input.
8. The summary must be suitable for a counsellor reviewing
   daily observations.
9. Recommend continued observation or professional assessment
   when appropriate.
10. Always state that the result is not a diagnosis.
11. In this system, POI means "Patient Observation Index".
    Never interpret POI as "Priority of Interest".
    If POI is mentioned, use the exact terminology
    "Patient Observation Index (POI)".
12. Do not change or reinterpret the supplied trend values.

STRUCTURED OBSERVATION AND EVIDENCE DATA:

{data}

Return the result according to the requested structured schema.
"""


def generate_evidence_summary(data):
    """
    Generate an evidence-grounded AI summary.
    """

    client = get_gemini_client()

    prompt = build_summary_prompt(data)

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AISummary,
        ),
    )

    return AISummary.model_validate_json(
        response.text
    )