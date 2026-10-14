# DAVI — Governed Knowledge / Product Guide Index V1 (Stage 02/03)

## Identity and scope
- Baseline: `8c9cb64ac3ab96de067836dc03068836b58761a1` based on DAVI Stage 1 / PR #62. Branch `feat/davi-governed-knowledge-topic-index-v1-002` is stacked on its exact commit; no merge to main authorized.
- Scope: provider-neutral metadata index, guarded bundle builder, source-contract regression tests and manual Agent Studio runbook. No new MCP tools, SQL, HTTP, AuthZ logic, business rules or provider API calls.
- Owner: `api-delpi` governed Knowledge corpus for Workspace Agent DAVI. External vendor information is separate. Agent Files are not authoritative operational data.

## Frozen corpus evidence
- Source commit: `f37f2fa720391256e6da8ea9faae0d1d2b51f6fe`; pinned freeze commit: `d9926cc14a8a4edd1b52775b82cf7353aede75b4`.
- Corpus: `davi-governed-knowledge` v1; membership = 15 approved documents.
- Manifest digest: `dc646f04243581bd35bb04025ddd7177e04e1c780e3bf5fe64c4a2fd2b9347e2`.
- Independent GitHub checks in preparatory inventory: all 15 current source blob SHAs matched the pinned source commit; current freeze membership equals pinned membership, despite a narrative edit to freeze artifact.
- Deterministic topic registry includes exactly 15 source pointers and aliases; the generated `DAVI-topic-index.md` only indexes the approved corpus. It is not the 16th authoritative source.
- `criterios-escoamento-lotes-fifo-best-fit.md`: `TO_INVENTORY`, TOTVS external supplier documentation, not tested as configured inside DELPI. Deliberately absent from distributable agent files.

## Acceptance ladder
| Gate | State |
|---|---|
| JSON registry and source review | PROVEN (GitHub source inspection) |
| Bundle verify with real pinned Git objects | PENDING (CI on branch) |
| Tests B01–B10 / C01–C08 + topic guard regressions | PENDING (CI on branch) |
| Generated bundle | PENDING (CI on branch) |
| Provider Agent Studio Files sync | TEST_NOT_RUN; manual operator action |
| Provider preview K01–K10 | TEST_NOT_RUN |
| Second-user identity / negative business AuthZ | PENDING |
| Production deployment / wide publication | NOT AUTHORIZED |

No Agent Studio/provider claims or production outcome may be inferred from source or CI alone.
