# SURI MCP — Programa autorizado para 100% de paridade com o Portal

**TASK:** `SURI-MCP-FULL-PARITY-CONTINUOUS-EXECUTION-001`  
**Data:** 2026-11-01  
**Decisão PO:** executar, implementar, testar, validar, commitar, publicar e homologar todas as capacidades **existentes e autorizadas** do Portal, por lotes sequenciais até cobertura completa, sem pedir nova autorização genérica a cada lote.  
**Estado:** `AUTHORIZED / PLANNED` — a criação deste programa **não equivale a código implementado ou deploy**.  
**Baseline reportada G3:** 21/45 capacidades (46,7%), catálogo MCP V6, exatamente 5 tools.

## Bloqueio documental verificado — GATE ZERO

A leitura do GitHub de `supplies-api/docs/SURI-MCP-FULL-PARITY-MATRIX.md` e `supplies-api/docs/SURI-MCP-FULL-PARITY-IMPLEMENTATION-PLAN.md` em 2026-11-01 retornou conteúdo com **marcadores de conflito Git** `<<<<<<< Updated upstream`, `=======` e `>>>>>>> Stashed changes`, incluindo snapshots contraditórios da matriz. **Classificação: EXECUTION_DRIFT.** Antes de iniciar código de G4, Cursor deve:
1. Obter `HEAD`, `origin/main`, `git status` e arquivo real do HEAD; confirmar se os marcadores persistem, pois a leitura de conector pode diferir do working tree e branches.
2. Confrontar conteúdo com código, commits V4–V6, evidências e cinco-tool governance; resolver conflitos **sem sobrepor alterações concorrentes**, preferindo worktree isolada e PR/commit bounded. Preservar histórico em arquivos de evidência, não como marcadores em fontes canônicas.
3. Reconciliar a contagem e as linhas R-01..R-34/W-01..W-11; nunca promover cobertura sem runtime comprovado. `search miss != ausência`.
4. Remover **somente na documentação vigente** sugestões ultrapassadas de sexta tool `delete` e replay cache in-process, preservando as decisões canônicas: exatamente `get_context,read,analyze,knowledge,execute`, store durável V005 para supplier writes.
5. Testar/verificar links, diff, concordância de HEAD e matrizes, commitar/push e produzir evidência. Se o conflito for de ownership ou contratos e não puder ser reconciliado, interromper o programa em `EXECUTION_DRIFT` e trazer decisão ao GPT Arquiteto.

## Definição de 100%

`SURI_AUTHORIZED_PORTAL_PARITY=100%` significa que **cada uma das 45 linhas de capacidade que o Portal realmente oferece** tem contrato equivalente e autorizado na SURI, com evidência por operação, inclusive artefatos/efeitos compatíveis com a interface MCP. Não significa liberar capacidades futuras ou bloqueadas. Linhas `PLANNED/TARGET/BLOCKED` (por exemplo SC workflow não existente no Portal, fonte em quarentena) **não entram** no denominador enquanto não aprovadas e implementadas no Portal. Recontar denominador no HEAD. A meta 45/45 **não é um fato atual**.

As 24 linhas pendentes no snapshot G3: `R-01,R-02,R-03,R-13,R-14,R-23,R-24,R-25,R-26,R-27,R-28,R-29,R-30,R-31,R-32,W-01,W-02,W-03,W-04,W-05,W-06,W-07,W-08,W-09`. `R-33,R-34` já contabilizadas, mas seus corpos de knowledge/analyze podem demandar extensão do corpus e testes, sem dupla contagem.

## Lotes sequenciais autorizados — não executar todos no mesmo diff/deploy

| Gate | Escopo/linhas | Saída |
|---|---|---|
| G0 | Resolver conflito documental e rebaseline owners, contratos, testes e runtime | Authority consistente e ledger provado |
| G4 | Safety stock `R-13,R-14` | `read(safety_stock)` filtros/summary/items/details/suppliers, branch explícita para detalhe |
| G5 | Overview/OTD `R-02,R-03` | `analyze(overview_summary)`, `read(otd)`; parcial-honesto |
| G6 | Consumo de OP `R-23,R-24,R-25` | `read(production_orders)`, `analyze` comparação 2–10 OPs |
| G7 | Mercado/Comex READ `R-26,R-27,R-28,R-29` | cinco séries de mercado, comex products, views e NCM read |
| G8 | Home/users/preferences READ `R-01,R-30,R-31,R-32` | contexto/capabilities, perfil+foto guard, SC relacionadas, preferences |
| G9 | Ampliação analyze/knowledge `R-33,R-34` (já contadas) | corpus e análises determinísticas, provenance, integridade, sem inflar numerador |
| G10 | Fundação escrita governada (não altera numerador) | registry `execute`, proposals/consent aprovado, auditoria, idempotência durável, readback, AuthZ |
| G11 | Comex WRITE `W-06,W-07,W-08` | NCM request/transition + views save; manage/consent quando requerido |
| G12 | Enrichment WRITE `W-03,W-04,W-05` | reviews, decisions/bulk, prepare-update; revision/rate-limit/idempotência |
| G13 | Preferences/profile WRITE `W-01,W-02` | preferências e perfil self-only, decidir owner real |
| G14 | Exclusão governada de views `W-09` | dentro de `execute` **sem sexta tool**, confirmação efetiva, auditoria, recuperação/retention segundo contrato |
| G15 | Auditoria final transversal e matriz 45/45 | cada linha comprovada em runtime, cinco tools, release documental |

O sequenciamento acima é uma proposta técnica inicial. Ajustar lotes conforme dependencies provadas no G0, sem ignorar gates nem reclassificar writes perigosas como simples reads. Se o caminho de consentimento obrigatório for indisponível no cliente, a operação destrutiva deve **falhar fechada**; não simular consentimento nem declarar W-09 PASS. Se a execução exigir contrato material novo ou autoridade de outro contexto, parar somente esse subgrafo como `EXECUTION_DRIFT`.

## Gates obrigatórios para **cada** lote

**S0 Inventory:** HEAD/origin/status, autoridades oficiais `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`, regras `.cursor` globais e especializadas, roadmap, contratos, código producer/consumer, owner, scope, RQ/AC, testes, runtime, interfaces e possíveis drifts. Inspecionar `supplies-api/docs/SURI-MCP-FULL-PARITY-EXECUTION-BRIEFS.md` somente como apoio, subordinado ao contrato.

**S1 Contract freeze:** `entity/action` ou `analysis` fechados; schema Pydantic `extra=forbid`, filters/identities/defaults, page budgets, errors, partial behavior, capability/resource/unit/business guards, autoria/ownership, idempotency/consent em writes. Em R-14, branch `all` no detalhe deve exigir escolha explícita. Não expor dados reais de fonte em quarentena.

**S2 Minimal implementation:** MFE não chama `api-delpi` diretamente; MCP reutiliza serviços BFF, sem importar domain/application alheio; Flask BFF preservada; zero SQL TOTVS em MCP. `get_context, read, analyze, knowledge, execute` permanecem as **únicas cinco tools**, com registries fechados, validação fail-closed. `execute` recebe ações de delete somente com contrato de confirmação aprovado.

**S3 Tests:** por ação positive+sibling+negative, owner upstream, unknown 422, 401/403, offline/fail-closed, impersonation e forbidden unit/CC, JSON-RPC real `initialize→tools/list→tools/call→Pydantic union→dispatch`, exact BFF parity, regressão das capacidades anteriores, compatibilidade retroativa do schema, segurança, testes de retries e idempotência para writes. Nenhuma escrita ERP real como smoke automatizado.

**S4 Review:** gate de código com `PASS` técnico e evidência, seguido de revisão independente necessária pelo processo. Nunca autoatribuir aceite do GPT. Erro ou falta de evidência bloqueante = `INCONCLUSIVE/REWORK`.

**S5 Git:** diff mínimo por owner, testes, docs + evidências, commits isolados, push para `main` pelo fluxo canônico; respeitar mudanças concorrentes, revalidar origem; Source SHA fixado.

**S6 Deploy:** aprovação do gate de código, health/rollback prévio, build in-image do source SHA, deploy apenas de serviços afetados, sem reiniciar Core/Keycloak/producers à toa; monitorar erros, logs saneados, oauth, authz e regressão, rollback na falha.

**S7 Prod validation:** OAuth real user-delegated, `tools/list=5`, catálogo incrementado sequencialmente, 200 para positivos, 401/403/422 para negativos aplicáveis, comparação de filtros, contagens, payload/parcial com Portal. Registrar separadamente MCP público e ChatGPT conector; refresh exige usuário quando schema stale. Não inventar PASS se smoke indisponível.

**S8 Report and next:** atualizar matriz por operação e evidence docs; relatório `BASE HEAD, FINAL HEAD, STATUS, FACTS PROVEN, TO_INVENTORY, EXECUTION_DRIFT, FILES INSPECTED/CHANGED, CONTRACT IMPACT, TESTS, SECURITY CHECKS, RQ/AC, RESIDUAL SEARCH, POSTCONDITION/OUTCOME, UNRESOLVED, NEXT STEP, SOURCE SHA, IMAGE, ROLLBACK`; aceitar `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`. Só iniciar o lote seguinte após gate final do lote anterior, sem necessidade de nova autorização genérica.

## Proteções adicionais das escritas

A autoridade de permissões efetivas é Core API; JWT não autoriza. `supplies.access` e `supplies.manage` conforme contrato, sem criar uma permission por ação/botão/CRUD. Self-only estrito em perfil; `view-all` nunca amplia unidade. PREPARE→consent→COMMIT para exclusões/transições críticas, com idempotência durável, audit, target echo ou canal aprovado, token de proposta com expiração/escopo e readback. Cliente sem consentimento verificável → `confirmation_unavailable` honesto. Não usar SQL direto no Postgres de outro owner. Nunca efetuar write em produção com dados reais de negócio sem intenção específica legítima do ator; homologação de writes pode usar ator/fixture autorizado e dados segregados ou controles não-destrutivos.

## Regra de prontidão e parada

A autorização presente é **para o programa**, não bypass de cada gate. Cumprir `READ → VERIFY → CLASSIFY → DECIDE → IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME → RESIDUAL SEARCH → DOCUMENT → REPORT`. Se G0/documentos conflitantes continuarem, **não iniciar G4**. Se um lote encontrar `EXECUTION_DRIFT`, documentar e encerrar subgrafo afetado, continuando somente lotes independentes e já seguros; não declarar 100% até a última linha ser `AUTHENTICATED_RUNTIME_PROVEN`. Não criar sexta tool sob nenhuma hipótese sem nova decisão explícita e alteração da regra canônica.
