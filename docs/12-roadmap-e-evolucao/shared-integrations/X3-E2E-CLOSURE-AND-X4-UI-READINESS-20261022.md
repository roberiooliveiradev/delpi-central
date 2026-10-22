# SHARED-INTEGRATIONS-01 — aceite X3.E2E e entrada na fase X4 (2026-10-22)

> **DECISÃO GPT ARQUITETO: X3.E2E = ACCEPT (backend/runtime de enriquecimento); X4.P0 = AUTHORIZED FOR INVENTORY & CONTRACT FREEZE ONLY.** Não equivale a `GATE-FEATURE` de nova página, não autoriza desenvolvimento visual, manifest, deploy MFE ou escrita ERP. Relatório Cursor X3.E2E/REWORK commit `72427d5017` (verificar no HEAD). Product Owner solicitou atualizar docs e iniciar fase de interface.

## 1. Fatos de implementação e runtime

| Capacidade | Classificação | Evidência |
|---|---|---|
| `external-data-api` interna, BrasilAPI CNPJ v1 | **PROVEN / PASS reportado no runtime** | [X3 runtime evidence](./X3-RUNTIME-EVIDENCE-20261022.md) |
| BFF `supplies-api` consumidor HTTP/S2S, identidade Keycloak, effective permissions Core | **PROVEN / PASS reportado** | X2 e X3.E2E |
| Redis DELPI, rate limit distribuído, 429 | **PASS reportado** | X3.FINAL e X3.E2E |
| REST SA2 flat via `api-delpi`; adapter corrigido | **PROVEN / PASS reportado** | X3.E2E, commit `2dbebb0ad1` |
| Gate PJ `person_type=J`; ausência/F rejeitada | **PROVEN** em código e evidência produtiva read-only | X3.E2E/REWORK |
| Consulta real CNPJ, comparador S1 de 16 campos | **PASS reportado** | X3.E2E |
| Review S2 em Postgres `supplies`: 1 review, 16 proposals, 16 decisions, 2 operations, 18 events | **PASS reportado** | X3.E2E, testes autorizados; registros mantidos |
| Replay idêntico individual/bulk; conflito em payload distinto; revisão obsoleta | **PASS em testes reportados** | X3.E2E/REWORK (+6 testes) |
| `prepare-update` | **PASS reportado**, `write_gate_enabled=false`, draft vazio porque todas propostas rejeitadas | X3.E2E |
| Escrita POST/PUT Protheus | **DISABLED / NOT EXECUTED** | Flags OFF, fora do escopo |
| Serviço técnico e fluxo de negócio em produção | **ACCEPT para backend X3.E2E** | Evidência + rework, sem alterar código de aplicação |
| MFE de enriquecimento | **PLANNED / NOT IMPLEMENTED** | Não inferir UI da existência das rotas BFF |

### Escopo exato do aceite

X3.E2E demonstrou fluxo técnico e persistência de negócio com usuário autorizado. **Não** demonstrou campo aceito apto a gerar `draft_fields` não vazio ou gravação ERP; teste produtivo rejeitou todas as propostas. Não afirmar PUT aprovado, cobertura ampla de todos fornecedores ou frontend pronto.

## 2. Residuais não apagados pelo aceite

- **LGPD/ROPA:** proposta específica pendente de revisão/incorporação institucional; plano [LGPD status/deferred remediation](./X3-LGPD-STATUS-AND-DEFERRED-REMEDIATION-20261022.md). Aprovação PO não se apresenta como parecer DPO.
- **Persistência/testes:** skips PostgreSQL preexistentes não equivalem a PASS para cenários ignorados; smoke produtivo controlado comprovou o caminho exercitado.
- **Operação:** monitorar rate limit/erros e evitar testes com credenciais persistidas; não ampliar coleta de contato, QSA/CPF.
- **Evidência histórica:** `X3-RUNTIME-EVIDENCE-20261022.md` é cronologia; blocos antigos com provider `unavailable` descrevem um momento anterior, não o estado final. Últimos adendos prevalecem para a linha do tempo.

## 3. X4 — fase de interface: somente P0 autorizado

**TASK X4.P0:** inventariar e congelar escopo UX de consulta/enriquecimento/revisão por campo na experiência de fornecedores do `plugins/supplies`. Não desenvolver nesta task.

### Reconciliação obrigatória de fila

A documentação geral [supplies README](../supplies/README.md) e [IMPLEMENTATION-PLAN](../supplies/IMPLEMENTATION-PLAN.md) ainda indicam **E10 / WF-15** como página em foco e gate federado `INCONCLUSIVE` na última evidência. E13/WF-09 e E14/WF-10 permanecem itens futuros no [roadmap fornecedores](../supplies/FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md). O sucesso de X3 backend **não promove automaticamente E13/E14 nem desbloqueia E10**.

P0 deve verificar HEAD/runtime federado da página atualmente em foco, mapear onde X4 se encaixa (lista E13, ficha E14 ou subexperiência própria) e apresentar ao PO decisão expressa de sequenciamento/rota caso a mudança de foco seja necessária. Se evidências invalidarem a fila atual, registrar `EXECUTION_DRIFT` em vez de reordenar silenciosamente.

### Inventário mínimo X4.P0

1. HEAD, `git status`, regras `.cursor`, ADRs/contratos, manifesto `schemaVersion 1.0.0` e rotas Core `/me/apps`.
2. MFE `plugins/supplies`: lista/busca e ficha de fornecedores atuais, rotas, placeholder e padrões de página; não usar `plugins/dashboard-supplies` como alvo.
3. Kit `@delpi/plugin-ui` via Module Federation: componentes existentes de identidade, busca, tabela, diff, decisões, feedback, loading/empty/partial/error, focus/keyboard e responsividade.
4. BFF S2 efetivo: endpoints review/list/detail/decisions/bulk/prepare-update, DTOs, erros 401/403/404/409/410/422/429/502/503, `expected_revision`, `idempotency_key`, ownership e TTL.
5. UX desejada: comparar SA2 e fonte externa com timestamp/proveniência; aceitar/rejeitar campo somente quando elegível; batch, conflitos, atualização baseline, revisão expirada/stale e draft-only; nunca prometer gravação real.
6. Permissões: `supplies.access` + Core effective; não criar permissão por botão/CRUD; owner e unidade conforme contrato real.
7. Help sincronizada e acessibilidade; URL/F5, tema claro/escuro, desktop/mobile; positive+sibling+negative e smoke federado para o futuro DoD.
8. Matriz RQ/AC e dependências da página em foco, com proposta de **X4.S1** somente após P0 aprovado e autorização explícita de execução.

### Entregáveis X4.P0

- Contract / UX freeze com jornadas, componentes reutilizáveis, estados, wireframe textual, RQ/AC, riscos e decisões pendentes.
- Matriz `BFF route → UI action → effective AuthZ → state/error → test`.
- Resultado de sequenciamento: `READY_TO_AUTHORIZE | BLOCKED_BY_E10 | EXECUTION_DRIFT | INCONCLUSIVE`.
- Nenhum diff MFE necessário na fase P0; nenhuma alteração de permissão, banco, provider, escrita ERP, rota/manifest ou deploy.

**Next step:** Cursor executa X4.P0 de forma bounded e devolve inventário/contrato; GPT revisa; PO autoriza a página/etapa de UI conforme gate da fila vigente.