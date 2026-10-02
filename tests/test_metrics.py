from inferdoc.benchmark.metrics import percentile, summary


def test_percentiles_and_empty_summary() -> None:
    assert percentile([], 50) is None
    assert percentile([1, 2, 3], 50) == 2
    assert percentile([1, 2, 3], 90) == 2.8
    assert summary([])["p99"] is None


def test_nonfinite_values_are_ignored() -> None:
    assert percentile([1, float("nan"), 3], 50) == 2
