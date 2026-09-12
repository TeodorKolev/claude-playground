from verification import find_uncited_claims


def make_finding(**overrides):
    finding = {
        "claim": "placeholder",
        "source_url": None,
        "document_name": None,
        "page_number": None,
        "confidence": "high",
        "retrieved_by": "web-search",
    }
    finding.update(overrides)
    return finding


def test_cited_url_claim_passes():
    findings = [make_finding(source_url="https://example.com/a")]
    report = "Solar capacity grew sharply in 2026. [https://example.com/a]"

    assert find_uncited_claims(report, findings) == []


def test_cited_document_page_claim_passes():
    findings = [make_finding(document_name="Internal Report 1", page_number=12)]
    report = "Wind turbines reached 20 MW offshore. [Internal Report 1, p. 12]"

    assert find_uncited_claims(report, findings) == []


def test_claim_with_no_citation_is_flagged():
    findings = [make_finding(source_url="https://example.com/a")]
    report = "Solar capacity grew sharply in 2026."

    uncited = find_uncited_claims(report, findings)

    assert uncited == ["Solar capacity grew sharply in 2026."]


def test_citation_not_backed_by_any_finding_is_flagged():
    findings = [make_finding(source_url="https://example.com/a")]
    report = "Solar capacity grew sharply in 2026. [https://example.com/b]"

    uncited = find_uncited_claims(report, findings)

    assert len(uncited) == 1


def test_wrong_page_number_is_flagged():
    findings = [make_finding(document_name="Internal Report 1", page_number=12)]
    report = "Wind turbines reached 20 MW offshore. [Internal Report 1, p. 99]"

    uncited = find_uncited_claims(report, findings)

    assert len(uncited) == 1


def test_multiple_sentences_checked_independently():
    findings = [
        make_finding(source_url="https://example.com/a"),
        make_finding(document_name="Internal Report 1", page_number=12),
    ]
    report = (
        "Solar capacity grew sharply in 2026. [https://example.com/a] "
        "Wind turbines reached 20 MW offshore. [Internal Report 1, p. 12] "
        "This claim has no citation at all."
    )

    uncited = find_uncited_claims(report, findings)

    assert uncited == ["This claim has no citation at all."]
