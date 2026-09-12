import pytest
from src.search.twohop import twohop_search


def test_twohop_requires_verified_integration():
    with pytest.raises(NotImplementedError):
        twohop_search()
