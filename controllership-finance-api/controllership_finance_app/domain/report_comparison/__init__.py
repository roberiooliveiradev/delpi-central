"""Report comparison domain — governed cross-report analysis (doc 126 §§6-8).

Owner of the orchestration contract is the ``controllership-finance-api``
BFF (decision D-03). The domain owns three things only:

- the real-capability catalog (GATE A) — which reports exist, what each
  one actually measures, its grain, filters and parity status;
- the semantic compatibility matrix (GATE C) — ``COMPARABLE`` /
  ``RELATED_REQUIRES_EXPLANATION`` / ``NOT_COMPARABLE``, default
  ``INSUFFICIENT_EVIDENCE``;
- the result model — subjects, diffs, normalizations, explanations and
  partial-honesty states (D-08).

Financial calculation never lives here: every value comes from the
governed producer contracts (api-delpi) via the BFF gateway. The engine
applies only the comparative operations authorized by doc 126 §D4.
"""
