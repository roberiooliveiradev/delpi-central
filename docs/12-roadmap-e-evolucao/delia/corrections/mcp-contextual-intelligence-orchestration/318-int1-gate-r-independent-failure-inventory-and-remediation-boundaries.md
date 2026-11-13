# 318 — INT-1 Gate R | Inventário independente de falhas e limites de remediação

**Data:** 2026-11-13  
**Tipo:** REVIEW / INVESTIGATION ONLY (não é correção de runtime nem aceite).  
**HEAD consultado:** `b875c4251f101bc30221e08b3a9c181f05e0b80f` (revalidar antes da execução).  
**Autoridades:** 16 → 293 → 300 → 313–317 → execution ledger → residual register, subordinado às demais autoridades canônicas.  
**Fase:** C3/T2, INT-1 não encerrada. `L/A/O=PASS` são vereditos reportados e ainda sujeitos a revisão; `R=FAIL`. Nenhum avanço de fase ou produção autorizado.

## 1. Evidência positiva preservada

Doc 317 reporta eval real consolidada `or-qwen14b-e069f3b33be8` em `ce96027440378ec788f376136192e968a68f1724`, Qwen 14B, v2-3 `generalist-semantic-v2-3-enumeration-intent`, fp base `95e265ee18cd5d66`, toolset 15 tools:
- P1 DAVI estrutura produto, GROUNDED/complete;
- P2 TÉO listagem sem `q`, total 109 e paginação honesta;
- P3 VISTA `display_format.list` autorizada por TV_READ, GROUNDED/partial.
Não repetir avaliação cognitiva sem mudança relevante em código/contrato/model-visible config ou critério canônico.

## 2. Problemas separados por owner, não apenas um blocker

| ID | Owner | Evidência existente | Classificação atual | Condição objetiva de encerramento |
|---|---|---|---|---|
| R-D1 parity-policy test | DÉLIA runtime config/testes | `test_runtime_profiles_share_execution_policy` compara igualdade de tudo exceto model, generation, effective window; JSON diverge em `prior_turns_limit` e `max_projection_chars`; Documento 300 prevê Qwen 32/20000 e local 4/6000 | **PROVEN_CONTRACT_TEST_MISMATCH; POLICY_RECONCILIATION_REQUIRED** | Decidir em autoridade se diferenças de capacidade são permitidas; testar paridade de invariantes e guardrails; suíte DÉLIA exit 0, sem mudar budgets arbitrariamente |
| R-D2 large-result truncation | DÉLIA projection + owner TÉO | `result_truncated` para árvores >20k, evidência Doc 312; distinto do teste de paridade | **OPEN / DO-D IMPACT TO_VERIFY** | Confirmar se parcial honesto atende DoD; se não, inventariar paginação/continuação owner, corrigir sem criar segundo engine |
| R-T1 TÉO OAuth contract | TÉO/IAM owner | 5 falhas reportadas em `test_teo_mcp_contract` e baseline anterior | **BASELINE_REPORTED; MATERIALITY_TO_VERIFY** | Reproduzir baseline em ambiente equivalente; verificar contrato auth real, sem mexer grants para tornar testes verdes |
| R-T2 TÉO realtime async | TÉO test environment | ~12 falhas envolvendo `pytest.mark.asyncio` não reconhecido | **ENVIRONMENT_REPORTED; REPRODUCTION_PENDING** | Instalar dependência de testes declarada em ambiente isolado, executar suite canônica e comprovar eliminação da classe sem alterar runtime |
| R-T3 TÉO demais falhas | TÉO/domain | Suite reportou 28 FAIL: 5 OAuth + ~12 realtime ≠ 28; cerca de 11 não classificados individualmente | **UNCLASSIFIED_FAIL** | Identificar todos os node IDs, exceções, SHA e causa; classificar individualmente, não inferir ausência de regressão por zero diff |
| R-V1 VISTA baseline/contrato | VISTA | 13 falhas reportadas no baseline e670c61f1b em catálogo/budget, delete, freshness, display_format fixture, m_query | **BASELINE_REPORTED; MATERIALITY_TO_VERIFY** | Reportar casos por node ID e reproduzir em ambiente comparável; definir owner/contrato e consertar defeitos reais autorizados |
| R-V2 VISTA OpenAPI sync | VISTA testing/toolchain | 4 `test_tv_openapi_catalog_sync` falham com generator/monorepo exec env | **ENVIRONMENT_REPORTED** | Executar toolchain canônica disponível, validar OpenAPI/operationId e determinar se drift real de contrato existe |
| R-V3 VISTA generated catalog artifact | VISTA eval runner/fixture | Eval criou `tv-dashboard-api/data/tv-dashboard/catalog/tv_data_routes.json` em working tree montada, influenciando testes de catálogo | **PROVEN_TEST_ISOLATION_DEFECT_IN_REPORT** | Test fixture path temporário/read-only; remover side effect com cuidado e preservar WIP; reproduzir testes sem artifact contaminar, não apagar data alheia |
| R-A1 DAVI fixtures | DAVI/test environment | ~61 falhas reportadas em pinned knowledge/data-dir ausente | **ENVIRONMENT_REPORTED; UNCLASSIFIED_DETAIL** | Executar sob fixture isolada canônica, sem montar/capturar dado produtivo indevidamente; distinguir ausência de fixture de falha de domínio |
| R-X1 report reconciliation | Cross-owner QA | DAVI reporta total 5979, passed 5889, failed 61, skipped 30 → soma 5980. VISTA: 13 baseline + 4 OpenAPI + 1 artifact = 18 categorias para 17 falhas (pode haver sobreposição). | **REPORT_ACCOUNTING_INCONSISTENCY_PROVEN** | Obter output junit/pytest autoritativo e reconciliar contagens sem duplicidade; não declarar `ZERO_NEW_REGRESSIONS=PROVEN` com classes não identificadas |

**Observação:** os números das suítes pertencem ao reporte Doc 317, não são resultados de novas execuções neste review. Falhas de owners externas podem ou não bloquear o Gate R conforme o DoD canônico: a decisão exige cobertura contratual, não conveniência. `PREEXISTING` não equivale a `ACCEPTED`; `zero task diff` não elimina regressão de integração.

## 3. Política de profiles: evidência direta do código

`delia-api/tests/test_composition_surface_regression.py::test_runtime_profiles_share_execution_policy` exclui de comparação somente `model`, `generation` e `context.effective_context_window_tokens`. Compara, portanto, `context.prior_turns_limit` e `tool_results.max_projection_chars`, embora Doc 300 configure conscientemente `openrouter_qwen` com 32/20000 vs `local_ollama` com 4/6000.

A configuração `delia-api/config/pydantic_ai.runtime.delpi.json` mostra `openrouter_qwen` janela 40960 e `local_ollama` janela 16384, budgets operacionais (timeouts, attempts, retries) equivalentes.

**Decisão sugerida, ainda não congelada pelo documento:** preservar proporcionalidade de histórico/projeção dentro do limite validado, exigir paridade em política/governança (retries, tool calls, timeouts, autorização, tentativas) e testes negativos para divergência proibida. Esta recomendação **não autoriza** mudar o teste antes de reconciliar 16/50/17/49/51/52/21/20/25 e decisões congeladas. Não esconder possível `result_truncated` sob o mesmo residual.

## 4. Trilha finita para corrigir todos os problemas confirmados

- **Slice 0: baseline and logs** — HEAD/status, autoridade canônica, fixar comandos/containers/fixtures, capturar resultados junit/pytest com IDs de todos os fails. Classificar por owner/categoria; proibir sucesso por skips. Corrigir inconsistências numéricas.
- **Slice 1: DÉLIA** — resolver decisão de profiles (política vs capacidades técnicas), atualizar teste com RED→GREEN e regressão completa; tratar truncamento separadamente caso viole critério obrigatório.
- **Slice 2: TÉO** — restaurar ambiente de testes declarado, classificar/reparar OAuth e os demais fails com owner autorizado; baseline/candidato comparáveis.
- **Slice 3: VISTA** — isolar artefatos gerados; restaurar toolchain OpenAPI; identificar e corrigir baseline material; preservar TV_READ/TV_WRITE e catálogo canônico.
- **Slice 4: DAVI** — restaurar fixtures DEV legítimas, provar ausência de uso indevido de dados prod e classificar falhas restantes.
- **Slice 5: Gate R review** — reexecutar suítes obrigatórias sem exclusões, avaliar outcomes de integração, revalidar L/A/O/R, registrar blockers legítimos; decisão `ACCEPT | REWORK | EXECUTION_DRIFT | INCONCLUSIVE` pela coordenação. Sem autoaceite, phase advance ou prod.

Para qualquer componente/contracto antes de modificação: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`; primeira divergência, owner, contrato, teste e Outcome. No máximo um rework bounded por classe comprovada antes de STOP e nova decisão. Não abrir uma task distinta para cada falha repetida da mesma causa.

## 5. Evidência/limitação deste review

**PROVEN_FROM_REPOSITORY:** lógica de comparação do teste; valores do JSON; orientação do Doc 300; relatórios 317/ledger; inconsistência numérica no relatório.  
**NOT_EXECUTED:** pytest em ambiente dos serviços, container/CI, baseline externo, avaliação real do modelo. GitHub conectado oferece fonte e edição de arquivos, não executa a stack DEV/infra; portanto nenhum FAIL é declarado corrigido por este documento.  
**INT1_CLOSED=NO; R_GATE=FAIL** até nova evidência e revisão independente.

**NEXT=COORDINATION_INT1_GATE_R_ALL_FAILURE_CLASSES_OWNER_BOUNDED_REMEDIATION** — tarefa(s) de execução sujeitas aos contratos reais dos owners e autoridade superior; zero deploy/phase advance.
