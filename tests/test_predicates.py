from src.workload.build_filters import equals, all_of


def test_compound_predicate():
    p = all_of(equals("region", "Tanggamus"), equals("source_type", "news"))
    assert p({"region": "Tanggamus", "source_type": "news"})
    assert not p({"region": "Tanggamus", "source_type": "wikipedia"})
