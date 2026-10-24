# BRANCH-AUTHZ.DOCS.R1 — Reconciliação global: filial é filtro, nunca autorização

**Data:** 2026-10-23 · **BASE HEAD:** `b3e1fc46b7` → **`eebcaa6c07`** (origin/main avançou +10 durante a execução; rebase fast-forward limpo) · **Escopo:** documental global. **Zero** alterações de código, manifest, RBAC, migrations ou runtime.

**Decisão de referência confirmada:** commit `611cb8c0dc` — «formalize PO decision branch as filter not permission» — é ancestral do HEAD e gravou no próprio R1 a seção «Decisão explícita do Product Owner» + a «Revisão GPT» (que já havia apontado o drift `SAFETY_STOCK_BRANCH_VIEW_PERMS → supplies.unit.filial-*` e o README §7 desatualizado).

## Decisão do Product Owner (inegociável)

No Portal Suprimentos, **filial é filtro de dados — não existe autorização por filial**.

- `supplies.access` = uso operacional · `supplies.manage` = administração (ADR-009).
- Não existem `supplies.unit.*`, `supplies.unit.filial-*` nem `view-all` no Portal.
- Filiais `01`/`02` (catálogo operacional do domínio) são opções de consulta.
- Regras legítimas de recurso/ownership e a AuthZ própria de outros contextos seguem intactas.

## Verificação de autoridade e de implementação

| Fonte | Estado |
|---|---|
| **ADR-009** (vigente) | Correto — «Não existem `supplies.unit.*`»; unidade = filtro `01`/`02 |
| **ADR-006** | `SUPERSEDED BY ADR-009` já marcado — histórico preservado |
| **ADR-007** | Histórico do catálogo antigo — preservado |
| **ADR-008** | «Parcialmente vigente» com nota de supersede de unidade/view-all — correto |
| **`supplies.manifest.json`** | `MANIFEST_BRANCH_PERMISSION_DRIFT = NONE` — só `supplies.access`/`supplies.manage` |
| **`supplies_permissions.py`** | Código já correto: `OPERATIONAL_UNITS=("01","02")` é **catálogo de domínio**; `allowed_units()` devolve o catálogo para qualquer `supplies.access` — docstring «Not a permission grant» |
| **`AuthorizationService.require_units`** | Valida o filtro `branch` contra o catálogo operacional (fail-closed por filtro inválido/sem acesso), **não** grants por filial |

**Conclusão de contrato:** implementação e manifest já seguem a decisão do PO. O drift era **exclusivamente documental** — nenhum `CODE_RUNTIME_DRIFT` de autorização por filial no BFF.

## Inventário e classificação

| Arquivo | Ocorrência | Classificação | Ação |
|---|---|---|---|
| `ROADMAP-REBASELINE-R1-20261023.md` | 3× `supplies.unit.*` como mapeamento E11/AuthZ | `DOC_DRIFT` | **corrigido upstream** por `611cb8c0dc` (decisão PO + revisão GPT já no HEAD) — texto vigente: filial é filtro, sem `supplies.unit.*`, `BranchAccessGate` = regra do produtor a reconciliar em E11.P0 |
| `INTEGRACOES.md` | `allowedUnits` «derivado de permissions ∩ `supplies.unit.filial-*`» + fluxo citando ADR-006 | `DOC_DRIFT`/`CONTRACT_MISMATCH` | **corrigido** — catálogo operacional do domínio para todo `supplies.access` |
| `HELP-AND-ONBOARDING.md` | «403 sem permissão para esta filial» | `DOC_DRIFT` | **corrigido** — 403 é módulo/operação; filial nunca causa 403 |
| `WIREFRAMES.md` | `allowedUnits` «união autorizada» | `AMBIGUOUS` | **corrigido** — catálogo operacional, não grants |
| `DECISOES_FUNCIONAIS_PENDENTES.md` | «Unidade = `supplies.unit.filial-{TOTVS}`» em decisões fechadas | `DOC_DRIFT` | **corrigido** — marcado SUPERSEDED por ADR-009 |
| `00-DIAGNOSTICO.md` | prescrição «Eixo B `supplies.unit.*`» sem banner | `HISTORICAL_VALID` | **banner SUPERSEDED adicionado** (mesma convenção dos demais docs) |
| `adr/ADR-006` | modelo `supplies.unit.filial-*` | `HISTORICAL_VALID` | preservado — já marcado SUPERSEDED |
| `adr/ADR-007` | catálogo fragmentado + `view-all` | `HISTORICAL_VALID` | preservado |
| `MANIFEST-DRAFT.md` | permissions `supplies.unit.filial-01/02` | `HISTORICAL_VALID` | preservado — banner SUPERSEDED já existente |
| `PLAYBOOK-MODULO-SUPRIMENTOS.md` | catálogo antigo (`supplies.unit.*`, `view-all`, `operations.access`) | `HISTORICAL_VALID` | preservado — banner já existente |
| `PERSONA-EXPERIENCE-MAP.md` | «Unit canônica futura `supplies.unit.filial-*`», `view-all` | `HISTORICAL_VALID` | preservado — banner já existente |
| `INVENTARIO-ATIVOS.md` | lista legada `supplies.unit.filial-01/02` | `HISTORICAL_VALID` | preservado — banner já existente (inventário de migração) |
| `HOMOLOGACAO-PARIDADE.md` | «unit aliases → `supplies.unit.*` pendente» | `HISTORICAL_VALID` | preservado — banner já existente; pendência de paridade refere-se aos legados, não ao Portal |
| `DUPLICIDADES-E-SOBREPOSICOES.md` | D1 aliases de filial legados | `HISTORICAL_VALID` | preservado — banner já existente |
| `DATA-MODEL.md` | `default_branch` ∈ `allowedUnits` | `CURRENT_CORRECT` | `allowedUnits` = catálogo operacional — semântica correta no contexto (doc já com banner) |
| `evidence/*.json`, docs de execução (S1/S2/S3, E10, X4) | `allowed_units`, `require_units` | `CURRENT_CORRECT`/`HISTORICAL_VALID` | descrevem o mecanismo real de filtro; execuções datadas preservadas |
| `docs/12-roadmap-e-evolucao/solicitacoes-compras/*` | `purchase-requests.unit.filial-*` | `CROSS_CONTEXT` | **preservado** — RBAC real do produto standalone (ADR-009 § «O módulo standalone mantém o próprio RBAC») |
| `docs/08-plugins/README.md` | `travel-expenses.unit.filial-*` | `CROSS_CONTEXT` | preservado — outro produto |
| `docs/12-roadmap-e-evolucao/cipa/PLAYBOOK.md` | `cipa.unit.filial-*` | `CROSS_CONTEXT` | preservado — outro produto |
| `SUPPLIERS-P2-CONTRACT-READINESS.md` | «unidade `01`/`02` **não se aplica** a fornecedores» | `CURRENT_CORRECT` | exceção documentada (SA2 por empresa) |
| `supplies-api/docs/supplier-enrichment-resource-scope-contract.md` | `allowed_units` = catálogo fixo | `CURRENT_CORRECT` | — |
| `USERS-PROFILE-S2` | «recorte autorizado do caller» | `AMBIGUOUS`→resolvido por contexto | doc de evidência datada; o termo descreve o mesmo catálogo operacional — sem edição para não reescrever evidência |

## E11 — impacto na receita

`SAFETY_STOCK_BRANCH_VIEW_PERMS`/`BranchAccessGate` (api-delpi) é **RBAC do produtor legado** — permanece intacto upstream como defense-in-depth, mas **não vira permission do Portal**. Em E11.P0: `supplies.access` autoriza; `branch` é filtro validado contra o catálogo operacional no BFF; incompatibilidade residual = nenhuma permission nova a mapear (só alinhar semântica de quais filiais o contrato aceita). A receita E11 no R1 já reflete a decisão do PO (`611cb8c0dc`): «confirmar filial somente como filtro (sem `supplies.unit.*`), reconciliar eventual `BranchAccessGate` de ESTSEG com o owner correto».

## Formulação canônica adotada

- **Autorização:** Core effective permissions — `supplies.access`/`supplies.manage`. Sem permission por filial.
- **Filtro de filial:** seleção dentro do catálogo operacional `01`/`02`; valor fora do catálogo = erro de contrato.
- **BFF:** valida autenticação + capabilities + recurso; `branch` validado como filtro de domínio.
- **Integrações:** RBAC de produtores legados não é herdado — divergências se reconciliam no owner do contrato.

## Residual search (pós-correção)

- 39 ocorrências de `supplies.unit` em docs → 0 normativas vigentes restantes (todas as sobreviventes estão sob banner SUPERSEDED, são históricas, de outro contexto ou descrevem o código real como filtro).
- `view-all` em docs do Portal → somente referências a `purchase-requests` standalone (CROSS_CONTEXT) ou histórico com banner.
- Sem `unit_scope`/`branch permission`/`filiais autorizadas` em formulário normativo vigente fora dos contextos acima.
- `.cursor/rules` e `AGENTS.md`: zero ocorrências de `supplies.unit` — nada a corrigir nas regras de engenharia.

## Divergências abertas (não resolvidas nesta task — fora de escopo)

- Fixtures de teste BFF carregam `supplies.unit.filial-*` como permissions extras em alguns mocks — inócuo (não gateiam nada), classificado `HISTORICAL_VALID` cosmético; limpeza opcional em task futura de testes.
- `estoque-seguranca.access` permanece como permissão real do app legado (gate do deep link) — CROSS_CONTEXT, não muda.

## Próximos passos

1. E11.P0 pode seguir com a receita corrigida (sem grants por filial).
2. Nenhuma ação de Core/manifest necessária — já conformes.
