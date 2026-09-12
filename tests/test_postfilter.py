from src.search.postfilter import postfilter


def test_postfilter_returns_only_matches():
    meta = {0:{"ok":False}, 1:{"ok":True}, 2:{"ok":True}}
    assert postfilter([0,1,2], lambda r:r["ok"], meta, k=2) == [1,2]
