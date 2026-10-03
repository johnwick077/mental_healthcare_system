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
        description=(
            "A concise summary of the patient's "
            "recorded observations."
        )
    )

    repeated_conditions: List[str] = Field(
        description=(
            "Repeated observation conditions identified "
            "from the supplied repeated_conditions data. "
            "Only include conditions explicitly supported "
            "by the supplied data."
        )
    )

    observed_changes: List[str] = Field(
        description=(
            "Important changes or trends identified "
            "from the supplied observations and analysis."
        )
    )

    evidence_interpretation: str = Field(
        description=(
            "Explanation of what the supplied research "
            "evidence says about the observed pattern."
        )
    )

    recommended_follow_up: str = Field(
        description=(
            "A cautious recommendation for continued "
            "observation or professional review."
        )
    )

    disclaimer: str = Field(
        description=(
            "A clear statement that this is not "
            "a medical diagnosis."
        )
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

Your task is to summarize the supplied patient observation
data and interpret the observations using ONLY the information
provided in the structured input below.

IMPORTANT RULES:

1. Do NOT diagnose the patient.

2. Do NOT claim that the patient has a disease, disorder,
   or medical condition.

3. Do NOT invent symptoms, conditions, research findings,
   datasets, statistics, or conclusions.

4. Clearly distinguish between:

   - observations recorded for the patient
   - repeated conditions calculated by the system
   - analysis and trends calculated by the system
   - research evidence supplied in the input

5. Research papers are provided for general contextual
   and methodological support only.

6. A research paper must NEVER be presented as proof that
   the individual patient has a particular condition.

7. If research evidence is supplied, use only the supplied
   research information.

8. Do not use outside knowledge to add research findings.

9. Use the supplied trend values exactly as provided.

10. Do NOT change, reverse, or reinterpret trend values.

11. Mention worsening, improving, or stable only when
    that trend is present in the supplied analysis.

12. The summary must be suitable for a counsellor reviewing
    recorded daily observations.

13. Recommended follow-up should be limited to continued
    observation, review of recorded changes, or appropriate
    professional assessment.

14. Do NOT provide treatment instructions.

15. Do NOT provide a medical diagnosis.

16. Always state that the generated result is not
    a medical diagnosis.

17. In this system, POI means exactly:
    "Patient Observation Index".

18. Never interpret POI as "Priority of Interest".

19. If POI is mentioned, use:
    "Patient Observation Index (POI)".

20. Do not infer information that is not present
    in the supplied input.

21. Do not invent repeated conditions.

22. The repeated_conditions field contains conditions
    identified by the system from repeated observation
    values.

23. Only report repeated conditions that are present
    in the supplied repeated_conditions data.

24. Repeated observations must NOT be converted into
    medical diagnoses.

--------------------------------------------------
REPEATED CONDITIONS
--------------------------------------------------

Use the supplied "repeated_conditions" field.

If repeated conditions exist, summarize them clearly.

For example:

- Poor sleep was repeatedly recorded.
- Withdrawn behaviour was repeatedly recorded.

Do not say that these observations prove a disorder
or medical condition.

If no repeated conditions exist, return an empty list.

--------------------------------------------------
RESEARCH EVIDENCE
--------------------------------------------------

The supplied research papers are supporting evidence,
not patient-specific clinical evidence.

For each relevant paper, use only the supplied fields:

- title
- authors
- publication_year
- abstract
- key_finding
- dataset_name
- source
- DOI or paper URL when available

Do not invent missing information.

If research evidence is general rather than directly
related to the observed pattern, clearly state that it
provides general context rather than patient-specific
evidence.

--------------------------------------------------
STRUCTURED OBSERVATION AND RESEARCH DATA
--------------------------------------------------

{data}

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

observation_summary:

Provide a concise summary of the recorded observations
and important trends.

repeated_conditions:

Return a list of repeated observation conditions
supported by the supplied repeated_conditions data.

Do not invent conditions.

Do not diagnose the patient.

observed_changes:

Return important observed changes or trends supported
by the supplied analysis.

evidence_interpretation:

Explain relevant supplied research evidence.

When research evidence exists, mention the relevant
paper title and publication year when available.

Do not claim that research proves anything about
this individual patient.

recommended_follow_up:

Provide cautious follow-up focused on continued
observation, review, or professional assessment.

disclaimer:

Clearly state that this is an AI-generated observation
summary and is not a medical diagnosis.
"""


def generate_evidence_summary(data):
    """
    Generate an evidence-grounded AI summary.
    """

    client = get_gemini_client()

    prompt = build_summary_prompt(
        data
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AISummary,
        ),
    )

    return AISummary.model_validate_json(
        response.text
    )