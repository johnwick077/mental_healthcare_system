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
   - analysis/trends calculated by the system
   - research evidence supplied in the input

5. Research papers are provided for general contextual
   and methodological support only.

6. A research paper must NEVER be presented as proof that
   the individual patient has a particular condition.

7. If one or more research papers are supplied in
   "research_evidence":

   - Identify the most relevant paper or papers by their
     exact supplied title.
   - Mention the publication year when available.
   - Briefly describe the relevant finding, method, or
     research approach using ONLY the supplied abstract,
     key_finding, and dataset information.
   - Explain how the research provides general context
     for the observed pattern.
   - Do NOT create a connection that is not supported by
     the supplied research information.

8. If "research_evidence" contains one or more papers,
   DO NOT say:
   "No research evidence was provided."
   Instead, reference the supplied research evidence.

9. If the supplied research papers are only generally
   related to the observations and do not directly support
   the specific observation pattern, clearly state this
   limitation.

10. If "research_evidence" is empty, explicitly state that
    research evidence was not available for interpretation.

11. Use the supplied trend values exactly as provided.

12. Do NOT change, reverse, or reinterpret trend values.

13. Mention a trend such as worsening, improving, or stable
    only when that trend is present in the supplied analysis.

14. The summary must be suitable for a counsellor reviewing
    recorded daily observations.

15. Recommended follow-up should be limited to continued
    observation, review of recorded changes, or appropriate
    professional assessment.

16. Do NOT provide treatment instructions or medical
    diagnosis.

17. Always state that the generated result is not a
    medical diagnosis.

18. In this system, POI means exactly:
    "Patient Observation Index".

19. Never interpret POI as "Priority of Interest".

20. If POI is mentioned, use:
    "Patient Observation Index (POI)".

21. Do not infer information that is not present in the
    supplied input.

22. Do not use outside knowledge to add research findings.
    Use only the research information supplied below.

--------------------------------------------------
RESEARCH EVIDENCE HANDLING
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

Do not invent information that is missing from these fields.

If multiple papers are supplied, select only the papers
that are relevant to the observed pattern instead of
mentioning every paper unnecessarily.

If the evidence is general rather than directly related
to the observed pattern, explicitly state that it provides
general context rather than patient-specific evidence.

--------------------------------------------------
STRUCTURED OBSERVATION AND RESEARCH EVIDENCE
--------------------------------------------------

{data}

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

Return the result according to the requested structured schema.

The fields must contain:

observation_summary:
A concise summary of the recorded observations and
important trends.

observed_changes:
A list of important observed changes or trends supported
by the supplied data.

evidence_interpretation:
Explain the relevant supplied research evidence.
When research evidence exists, mention the relevant
paper title and publication year and explain its
general relevance. Do not claim that the paper proves
anything about this individual patient.

recommended_follow_up:
Give a cautious follow-up focused on continued observation,
review, or professional assessment when appropriate.

disclaimer:
Clearly state that the result is an AI-generated
observation summary and is not a medical diagnosis.
"""

def generate_evidence_summary(data):
    """
    Generate an evidence-grounded AI summary.
    """

    client = get_gemini_client()

    prompt = build_summary_prompt(data)

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