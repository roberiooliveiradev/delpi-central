# DELPI News — Etapa 2 (execução)

## Identificação

| Campo | Valor |
|---|---|
| Tarefa | E2 — Motor RSS, persistência, coleta e normalização |
| Subetapa executada | **E2.S1** (decisão, inventário, contratos) |
| Subetapas **não** iniciadas | E2.S2, E2.S3, E2.S4 |
| Repositório | `roberiooliveiradev/delpi-central` |
| Branch | `main` |
| HEAD remoto de referência (início E2.S1) | `f8e688bbc9e16c9d0e91e8b1c2da25726d916164` |
| HEAD planejamento citado no prompt | `1801c4cd…` (histórico; não usado como autoridade) |
| Working tree na execução | limpa após pull ff |

## Estado da subetapa

```text
ARCHITECTURE_DECISION_REQUIRED
```

**Não** há aprovação formal vigente para criar `delpi-news-api` ou estender outro BC com mandato RSS.

Proposta canônica para avaliação da autoridade:

- [`adr/ADR-001-delpi-news-api-ownership.md`](./adr/ADR-001-delpi-news-api-ownership.md) — status **PROPOSTO**

Este STAGE-02 **não** constitui aprovação.

---

## Ledger RQ-E2 (provisório)

| Requisito | Estado E2.S1 | Nota |
|---|---|---|
| RQ-E2-01 Ownership e decisão formal | **BLOQUEADO_COM_EVIDENCIA** | ADR-001 proposto; sem `STATUS: APPROVED` |
| RQ-E2-02 Reutilização inventariada | ATENDIDO_NO_PLANO | Ver inventário abaixo / ADR-001 §2 |
| RQ-E2-03 Contratos técnicos suficientes | ATENDIDO_PARCIAL | Conceituais E1 em `CONTRACTS.md`; OpenAPI/ops **só após** aprovação |
| RQ-E2-04…RQ-E2-14 | FORA_DO_ESCOPO_COM_JUSTIFICATIVA | Dependem de E2.S2+ |

---

## Inventário (E2.S1) — resumo

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION | Owner |
|---|---|---|---|
| RSS/Atom ingest | NO | NEW (se A aprovada) | BC News PLANNED |
| HTTP resiliente | PARTIAL | EXTEND no BC | caller + regra resilience |
| SSRF safe-fetch | PARTIAL | NEW no BC | — |
| XML (não-feed) | PARTIAL | NEW parser feed | — |
| Scheduler | PARTIAL | ADAPT no BC | — |
| PG plugins | YES | REUSE | BC + infra |
| `external-data-api` | NO p/ RSS | NÃO ESTENDER | cadastral S2S |
| TV Dashboard | NO p/ RSS | NÃO ESTENDER | playlists |

Detalhe e alternativas A/B/C: ADR-001.

---

## Contratos

Os modelos conceituais de [`CONTRACTS.md`](./CONTRACTS.md) permanecem a base:

- `RssSource`, `NewsItem`, `NewsCategory`, `PublicNewsBoard`, fetch events
- Estados editoriais: `collected` → … → `published` (coleta **não** publica)

**Não** foram criadas operações OpenAPI nesta subetapa (pré-condição: ownership aprovado).

---

## Implementação

| Item | Resultado |
|---|---|
| Serviço `delpi-news-api` | **NÃO CRIADO** |
| Migrations | **NÃO CRIADAS** |
| Gateway / Core / compose | **NÃO ALTERADOS** |
| Demo `public-hub` | **NÃO ALTERADA** |

---

## Validação

| Prova | Estado |
|---|---|
| Busca por aprovação formal `delpi-news-api` / ADR APPROVED | FAIL (ausente) → stop correto |
| Inventário código HEAD `f8e688bbc` | PASS (documentado) |
| Testes de coleta | TEST_NOT_RUN (sem implementação) |

---

## Próximo passo permitido

1. Autoridade competente preenche no ADR-001:

```text
STATUS: APPROVED | REJECTED | DEFERRED
OWNER: …
DATE: …
AUTHORITY: …
```

2. Se `APPROVED` com owner `delpi-news-api` → autorizar **E2.S2**.
3. Se `REJECTED` / owner diferente → corrigir ADR/README e só então planejar E2.S2 no owner escolhido.
4. Enquanto pendente → **não** iniciar E2.S2/S3/S4.

---

## Git / documentação desta entrega E2.S1

Arquivos esperados no commit documental:

- `docs/12-roadmap-e-evolucao/delpi-news/adr/ADR-001-delpi-news-api-ownership.md`
- `docs/12-roadmap-e-evolucao/delpi-news/STAGE-02.md`
- atualizações em `README.md` e índice do roadmap
