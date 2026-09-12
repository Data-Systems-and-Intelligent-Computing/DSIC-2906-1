from src.workload.stratify_match_rate import match_rate


def test_match_rate():
    assert match_rate(25, 100) == 0.25
