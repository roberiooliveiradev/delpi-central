# Documento 99 — GO de implementação P6-MIN + P2-READ e handoff de execução incremental

**Data da decisão:** 2026-10-24. **GO ID:** `CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001`. **Decisor:** Product Owner, manifestação expressa nesta conversa: “Autorizo expressamente a implementação CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001, exclusivamente no escopo do Documento 98. Registre o GO no GitHub e prepare o prompt de execução incremental para o Devin, com testes, checkpoints e stop conditions. Não autorize deploy de produção.”  
**HEAD remoto inspecionado antes do registro:** `ff17fee920c85f583e5ad83823125b4fb671d291` (main). **Git status local:** indisponível via GitHub connector; Devin deve provar `git status --short` e revalidar HEAD antes de qualquer diff.  
**GATE:** `IMPLEMENTATION_AUTHORIZED=YES / SCOPE=P6-MIN+P2-READ_ONLY`. **DEPLOY_PRODUCTION_AUTHORIZED=NO**. GO restrito ao menor diff correto. Nenhuma implementação foi executada neste registro.

## 1. Authorities e decisões congeladas

1. [98 — revisão transversal e solicitação textual de GO](./98-ciclo3-go-review-transversal-p6-min-p2-read.md), `GO_RECOMMENDED` aceito como suporte técnico, sem usurpação do PO;
2. [97 — escolhas vinculantes](./97-ciclo3-p6-min-p2-read-decisoes-po-e-solicitacao-go-transversal.md): `CP-D01=A` (schema próprio na BFF), `CP-D04=A` (seed com 53 itens DRAFT), `CP-D05=A` (admin por API apenas);
3. [96 — design de persistência/DTO](./96-ciclo3-gate-contrato-e-persistencia-p6-min-p2-read.md), [95 — 53 itens](./95-ciclo3-cp00-cp01-rebaseline-e-brief-primeiro-slice-p2.md), [23 — ledger RQ/AC](./23-ledger-rq-ac-testes.md), [93 — roadmap](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md);
4. Instruções oficiais do arquiteto, .cursor aplicável, ADRs/contratos e código no HEAD mantêm precedência técnica e de segurança sobre planos.

**Sem nova decisão de produto** por preferência. Se o HEAD invalidar premissa de authority, `EXECUTION_DRIFT` e STOP do subgrafo.

## 2. Escopo autorizado (somente este)

- **BFF/persistência:** `controllership-finance-api`, Clean Architecture + Ports/Adapters; schema `controllership_finance` no `postgres-plugins`, `psycopg`, configurações `PLUGINS_DB_*`, runner e migrations versionadas/checksum SHA-256, flag de execução gated, audit append-only, idempotência/concorrência e falha fechada.
- **P6-MIN:** V001 schema/tabelas e V002 seed **53 itens DRAFT**, não publicação automática. API administrativa mínima list/create/update DRAFT/publish/inactivate prospectivo, `manage` efetivo **AND** admin scope **AND** business rule, controle `revision`, audit real; **sem página administrativa P6**.
- **P2-READ:** abertura de competência (`POST`) idempotente por competência mensal, somente com template PUBLISHED e vigente, snapshot dos 53 itens `EXPECTED`, listagem de competências/itens/detalhe, erros tipados; `access` efetivo, escopo/ownership e regras aplicáveis fail-closed.
- **MFE:** uma deep route de checklist, manifest atualizado somente com a rota protegida por `controllership-finance.access`, reuso `@delpi/plugin-ui`, estados verdadeiros, F5/deep link, mobile/desktop, teclado/foco, light/dark e Help atualizada no mesmo slice.
- **RQ/AC + testes:** registrar RQ-P2-13/14 no ledger após confrontar contratos vigentes; testes domínio, BFF, autorização, PG real isolado, MFE/manifest/build, positive+sibling+negative, concorrência/idempotência, testes de migration e auditoria; scripts/relatórios com logs/commits.

**Explicitamente proibidos por este GO:** deploy/restart ou migrations em produção, grants/reconfiguração de Core real, anexos/upload/validação P2, P3/P4/P5, relatórios oficiais R01–R15, SQL/TOTVS write, CLARA MCP tools ou servidor, página/permission DRE, novas permissions, novas arquiteturas/bancos, outras páginas comuns, envio de pacote. Publicação administrativa somente por usuário e scope autorizados, nunca por seed/migration ou atalho.

## 3. Trilho incremental autorizado e checkpoints de STOP

| Etapa | Entrega mínima | Verificação para avançar |
|---|---|---|
| `E0.S1` | Baseline HEAD, branch, `git status`, .cursor/authority, runner/ports e dependências reais | Contratos e paths do doc 96 confirmados no HEAD; preexistências preservadas; drift material ⇒ STOP |
| `E0.S2` | Congelar sub-slices, DTO/operationIds, erros, actor scope, migrations V001/V002 e testes previstos, sem estender escopo | `READY_TO_EXECUTE` documentado com RQ/AC, owners, consumidores e rollback |
| `E1.S1 / CP02-DB` | Migrations, config, runner/startup gated, domínio mínimo e ports | PG real isolado: esquema separado, seed 53/53 DRAFT, sem PUBLISHED/competência auto-criados, checksum/restart e schema alheio preservados |
| `E1.S2 / CP02-P6` | Use cases, adapters e API admin mínima com controle de revisão/audit | PUBLISH autorizado via API cria versão vigente; ACCESS-only e MANAGE sem admin_scope recebem 403; double publish/stale/OCC e falha Core; audit append-only |
| `E1.S3 / CP03-P2` | Open/list/get competente/snapshot e idempotência | Duas requisições concorrentes mesma competência ⇒ uma única; replay retorna existente; nenhuma abertura com DRAFT; snapshot 53 EXPECTED e v1 preservada após v2 |
| `E1.S4 / CP03-UX` | Página checklist + manifest/nav + Help no mesmo diff | URL/F5, mobile, teclado/foco, tema claro/escuro, loading/empty/partial/error/403; páginas existentes e permissions sem regressão |
| `E1.S5 / CP03-INTEGRATION` | Verificação cross-layer + residual search; commit final | Testes PG/contract/BFF/MFE e build reais; positive/sibling/negative, authz 403/503, leitura posterior/audit; `TEST_NOT_RUN` quando smoke não autorizado; veredito GPT REVIEW antes do próximo slice |

**Não executar deploy de produção após E1.S5.** A homologação e o release exigem outro GO.

## 4. Invariantes e bloqueios

- `DRAFT != PUBLISHED`, `EXPECTED != ATTACHED/VALIDATED`, `publish != competence open`; não auto-publicar template para fabricar caso positivo.
- `ACCESS != MANAGE`; JWT não autoriza sozinho; Core effective permission + scope/ownership + regra, fail-closed com Core indisponível.
- Snapshot é imutável por competência, published versions não mutáveis; inserção concorrente e idempotência provadas em banco PostgreSQL real (mock não prova atomicidade).
- Checklist original sanitizado — sem bancos/contas/pessoas/valores/arquivos privados em seed ou logs. CP-D02 (responsáveis/validadores/recipients físicos) segue TO_INVENTORY e CP-D03 (CK-E-27) sem R-ID; não inventar dados.
- Nenhum acesso a banco de bounded context vizinho; sem imports de application/domain de outro contexto.
- Se operação real de publish ou teste exigir permission extra, acesso administrativo inexistente, alteração de lifecycle, persistência fora do schema ou contrato breaking, STOP e DECISION_REQUIRED; não improvisar workaround.
- Não ajustar teste por skip/default permissivo; CI verde isolado não prova outcome; E2E humano não rodado => INCONCLUSIVE.
- Gestão de branch/PR/commit conforme protocolo executor, sem sobrescrever trabalho concorrente. Testar no SHA pós-diff.

## 5. Entrega e evidência do Devin

Produzir `CF-C3-P6-MIN-P2-READ-RUNTIME-EXECUTION-REPORT-001` com **BASE_SHA, FINAL_SHA, git status**, paths/diffs, decisões respeitadas, `RQ/AC → teste → postcondition`, log de comandos, PG real, authz, UX/Help, ci/build, evidência de snapshot, publicação e idempotência, smoke (ou TEST_NOT_RUN), residual search, riscos/owners e parecer `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. Se uma etapa bloquear, encerrar antes de tocar próximos owners.

**GO registrado, não execução realizada.** `IMPLEMENTATION_AUTHORIZED=YES / SCOPE=P6-MIN+P2-READ_ONLY`; `DEPLOY_PRODUCTION_AUTHORIZED=NO`.
