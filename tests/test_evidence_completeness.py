def test_output_token_aggregates_are_missing_when_usage_is_partial(
    evidence,
) -> None:
    partial = (
        evidence.requests[1]
        .model_copy(
            update={
                "output_tokens":
                    None,
            }
        )
    )

    rebuilt = (
        evidence
        .with_aggregate(
            run_id=(
                evidence.run_id
            ),
            backend=(
                evidence.backend
            ),
            model=(
                evidence.model
            ),
            created_at=(
                evidence.created_at
            ),
            completed_at=(
                evidence.completed_at
            ),
            parameters=(
                evidence.parameters
            ),
            workload=(
                evidence.workload
            ),
            requests=[
                evidence.requests[0],
                partial,
            ],
        )
    )

    assert (
        rebuilt.aggregate[
            "output_token_throughput_tps"
        ]
        is None
    )

    assert (
        rebuilt.aggregate[
            "total_output_tokens"
        ]
        is None
    )


def test_total_tokens_use_reported_usage_when_complete(
    evidence,
) -> None:
    rebuilt = (
        evidence
        .with_aggregate(
            run_id=(
                evidence.run_id
            ),
            backend=(
                evidence.backend
            ),
            model=(
                evidence.model
            ),
            created_at=(
                evidence.created_at
            ),
            completed_at=(
                evidence.completed_at
            ),
            parameters=(
                evidence.parameters
            ),
            workload=(
                evidence.workload
            ),
            requests=(
                evidence.requests
            ),
        )
    )

    expected = sum(
        request.total_tokens
        for request in evidence.requests
        if request.total_tokens is not None
    )

    assert (
        rebuilt.aggregate[
            "total_tokens"
        ]
        == expected
    )


def test_total_token_aggregate_is_missing_when_all_usage_paths_are_incomplete(
    evidence,
) -> None:
    partial = (
        evidence.requests[1]
        .model_copy(
            update={
                "input_tokens":
                    None,
                "total_tokens":
                    None,
            }
        )
    )

    rebuilt = (
        evidence
        .with_aggregate(
            run_id=(
                evidence.run_id
            ),
            backend=(
                evidence.backend
            ),
            model=(
                evidence.model
            ),
            created_at=(
                evidence.created_at
            ),
            completed_at=(
                evidence.completed_at
            ),
            parameters=(
                evidence.parameters
            ),
            workload=(
                evidence.workload
            ),
            requests=[
                evidence.requests[0],
                partial,
            ],
        )
    )

    assert (
        rebuilt.aggregate[
            "total_input_tokens"
        ]
        is None
    )

    assert (
        rebuilt.aggregate[
            "total_tokens"
        ]
        is None
    )

    assert (
        rebuilt.aggregate[
            "total_token_throughput_tps"
        ]
        is None
    )