# Demo video outline

1. State the pain point: an inference engineer needs evidence that a tuning
   decision helped.
2. Run the two-request Token Factory baseline and show the saved
   `EvidenceBundle`.
3. Show Nemotron using read-only tools and producing a typed `ExperimentSpec`.
4. Show policy admission rejecting an impossible server-side control, or
   admitting a bounded concurrency change.
5. Run the candidate and show Python’s `PASS`, `FAIL`, or `INCONCLUSIVE`.
6. Close with the claim boundary: the model reasons, but measurements and the
   decision remain deterministic and auditable.
