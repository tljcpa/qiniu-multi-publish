"""测试夹具：每个用例前重置限流计数，避免跨用例累积导致偶发 429。"""

import pytest

from app.ratelimit import _cost_limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    _cost_limiter.reset()
    yield
