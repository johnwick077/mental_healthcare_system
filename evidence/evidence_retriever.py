from evidence.models import ResearchPaper


def paper_to_evidence(paper):
    """
    Convert a ResearchPaper object into the structured
    evidence format used by the AI summarizer.
    """

    return {
        "title": paper.title,
        "authors": paper.authors,
        "journal": paper.journal,
        "publication_year": paper.publication_year,
        "doi": paper.doi,
        "paper_url": paper.paper_url,
        "abstract": paper.abstract,
        "dataset_name": paper.dataset_name,
        "key_finding": paper.key_finding,
        "source": paper.source,
        "verified": paper.verified,
    }


def get_verified_papers_for_pattern(pattern):
    """
    Return only verified research papers linked
    to the supplied observation pattern.
    """

    papers = pattern.supporting_papers.filter(
        verified=True
    ).order_by(
        "-publication_year"
    )

    return papers


def get_evidence_for_pattern(pattern):
    """
    Get structured evidence from verified papers
    linked to an observation pattern.
    """

    papers = get_verified_papers_for_pattern(pattern)

    return [
        paper_to_evidence(paper)
        for paper in papers
    ]


def get_general_research_evidence():
    """
    Return verified research papers maintained in the
    project when no specific observation pattern matches.

    These papers provide general research context for
    the AI summary.
    """

    papers = ResearchPaper.objects.filter(
        verified=True
    ).order_by(
        "-publication_year"
    )

    return [
        paper_to_evidence(paper)
        for paper in papers
    ]