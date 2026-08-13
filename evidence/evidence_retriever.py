from evidence.models import ResearchPaper


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

    evidence = []

    for paper in papers:
        evidence.append({
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
        })

    return evidence