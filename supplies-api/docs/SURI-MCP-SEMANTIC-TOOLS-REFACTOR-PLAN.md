# SURI — Plano de refatoração das tools semânticas (SURI-MCP-TOOLS-SEMANTIC-001)

> **Status:** PLANNED — autorizado para execução de refatoração, **não executado neste documento**. Data: 2026-10-29.  
> **Baseline:** SURI-MCP-MASTER-001 entregue no commit `16d18bf17d`, com 8 tools READ/DISCOVERY/ANALYSIS e KEYCLOAK_READY reportado.  
> **Objetivo:** abandonar catálogo orientado a endpoints auxiliares e construir poucas tools **semânticas por capacidade**, alinhadas ao desenho comprovado de TÉO (`transformometro-api/tm_app/interface/mcp/server.py`) e VISTA (`tv-dashboard-api/tv_app/interface/mcp/server.py`), preservando behavior, AuthZ e testes da V1.  
> **Observação:** este plano prevalece **somente sobre nomes e organização de tools** do contract freeze S1 anterior; não altera o resultado histórico de S0–S9. Executor deve revalidar HEAD/authorities e versionar contract freeze rev.2.

## 1. Decisão de produto e resultado final

**Quatro tools expostas na V1:**

| Tool | Operações semânticas v1 | Cobertura legada a preservar |
|---|---|---|
| `get_context` | `action=context\|catalog` quando necessário; responder contexto mínimo autorizado/capabilities reais | `get_my_context`, `get_catalog` |
| `read` | `entity=purchase_orders`, `action=search\|get`; filtros fechados e id específico | `list_purchase_orders`, `get_purchase_order` |
| `analyze` | `analysis=purchase_orders_summary` (ou nome validado pelo owner), escopo e filtros fechados | `analyze_purchase_orders` |
| `knowledge` | `action=search\|get\|sources`, tópico/termo/knowledge_id conforme action | `search_supplies_knowledge`, `get_knowledge_item`, `list_knowledge_sources` |

**Duas famílias previstas, NÃO REGISTRADAS na V1:**
- `execute`: CREATE/UPDATE e workflows não destrutivos **quando futuramente homologados** e com autorização vigente; poderá suportar operações múltiplas em uma solicitação, cada uma com resultado individual, idempotência e postcondition, sem aprovações conversacionais redundantes;
- `delete`: DELETE governado com confirmação explícita do usuário e read-back; não implementado nem exposto agora.

**Confirmação:** default para CREATE/UPDATE = sem confirmação extra imposta pela SURI, *desde que a solicitação já determine a intenção e o contrato de negócio permita execução direta*. Exigir aprovação/segunda confirmação quando regra de negócio, risco material, política da plataforma ou operação ambígua impuser. DELETE exige confirmação explícita. Não contornar etapas obrigatórias no backend.

**Composição multi-capacidade:** ChatGPT pode orquestrar chamadas sucessivas de `read`+`analyze`+`knowledge` para cumprir uma única solicitação. Na expansão, planejar `execute` com suporte a lote controlado somente por capability de domínio real, não executor universal/arbitrary HTTP. Resultados parciais e falhas por item; nada de transação cross-owner implícita.

**Sem prefixo `supplies_`** nas tools do MCP SURI: a identidade de Suprimentos está na descrição, no resource e no owner, não em todas as operações.

## 2. Referências técnicas e guardrails

- TÉO usa famílias semânticas com parâmetros `entity`, `action` (`record_read`) e governança de alteração (`prepare_record_change`, `commit_proposal`).
- VISTA separa `get_catalog`, inspeção, previews, análise e governança de mudanças (`prepare_change`, `commit_proposal`).
- Não copiar blindly seus nomes, fluxos de escrita ou domain rules. `get_context` não é mera decoração e só deve permanecer se houver informação de contexto/catálogo não resolvida pelo `tools/list` nativo. Se houver redundância material, registrar `EXECUTION_DRIFT` e propor alteração fundamentada, não maquiar cobertura.
- Tool compacta **não** é proxy: `entity`/`action`/`analysis` são enums/registries explícitos e versionados; handlers específicos por capability, cada qual reutilizando BFF application/gateways e authorization; rejeitar unknown entity/action/fields com validation.
- Não mexer em Keycloak/production/ChatGPT, regras Core, Flask, schema `shared/delpi_character_profiles` ou avatar.
- Identidade end-user e Core effective permissions são authority; JWT `mcp:tools` não é permissão de negócio; `capability AND unit_scope AND resource_scope/ownership AND business_rule`; fail-closed, negative tests, anti-cross-user leakage.
- O contrato público muda: atualizar schema snapshots, tool descriptions, instructions/branding, `get_catalog` interno (se ainda existir em `get_context`), metadata, README, execução/handoff e testes; não alegar que 8 tools continuam ativas quando somente 4.
- Uma refatoração pré-onboarding pode substituir a superfície de 8 tools de forma atômica sem manter aliases **se não houver consumidores reais dependentes**. Confirmar esse ponto por inventário. Se houver, compatibilidade controlada/depreciação é necessária; não remover silenciosamente.

## 3. RQ e critérios de aceite

| RQ | Requisito | AC mensurável |
|---|---|---|
| ST-RQ-01 | 4 tools semânticas v1 | `initialize`/`tools/list` reporta exatamente os 4 nomes canônicos, classes DISCOVERY/READ/ANALYSIS apropriadas e zero ACT/PREPARE |
| ST-RQ-02 | Paridade de respostas legadas | Matriz 8→4 com casos determinísticos, filtros/paginação/errors/status/citações, nenhum comportamento autorizado perdido |
| ST-RQ-03 | Schemas seguros | Enum por entity/action/analysis, validação condicional, unknown/ambiguous/oversized rejeitado; nenhum método/URL arbitrário |
| ST-RQ-04 | AuthZ inalterada | Positive/sibling/negative/cross-unit/cross-user/Core-down/service-token/wrong-aud; mesma proteção que BFF |
| ST-RQ-05 | Composição | Multi-turn compound request READ→ANALYZE→KNOWLEDGE, resultado fundamentado sem falsa execução; partial failure explícita |
| ST-RQ-06 | Extensibilidade | Registry/dispatch semântico tipado para adicionar `entity`/action nova via contract/test/owner, sem novas tools obrigatórias |
| ST-RQ-07 | Operações futuras | `execute` e `delete` documentadas apenas como TARGET, não registradas no servidor, sem writes no MCP V1 |
| ST-RQ-08 | UX de confirmações | Regra de confirmação somente DELETE por default, ressalvadas aprovações obrigatórias/alto risco/ambiguidade; não aplicada a writes inexistentes |
| ST-RQ-09 | Deploy readiness | runtime local container/transport e gateway não regredidos; handoff Keycloak atualizado para 4 tools |
| ST-RQ-10 | Versionamento/evidência | contract freeze rev.2, docs, tests, diff review, SHA, report; apontar `KEYCLOAK_READY` atualizado só quando smoke/provas completarem |

## 4. Etapas da execução delegada ao Cursor/Dev

### R0 — Rebaseline e inventário
Ler authorities, `.cursor` aplicáveis, docs supplies, plano mestre e S1 freeze; obter HEAD/working tree; comparar referências TÉO/VISTA reais (server, handlers, constants, tests); inspecionar SURI (server, tool_bridge, knowledge, oauth, tests, docs, persona). Buscar consumers da surface antiga e evidências de cadastro/deploy. Resultado: matriz 8→4 + riscos/compat.

### R1 — Freeze semântico rev.2
Congelar `get_context`, `read`, `analyze`, `knowledge`; discriminadores/enum admissíveis, parâmetros, limites, output envelopes, error mapping e security; comportamento quando `get` requer identificador; `read search` só aceita filtros validados para rota owner. Decidir `get_context` real versus catálogo nativo, explicitando valor de domínio.

### R2 — Implementação mínima
Refatorar registro e bridges em `supplies-api/app/interfaces/mcp`; manter handlers reusáveis privados, juntar somente a interface pública; sem acoplamento cruzado, sem mutações; atualização dos metadados e instruções da SURI. Priorizar passos atômicos com testes; remover aliases públicos somente após inventory consumer.

### R3 — Testes de paridade e composição
Matriz que exercita todas as 8 capacidades legadas nos 4 envelopes; positive/sibling/negative; invalid combos; filtros/unit, vazio/paginação, citations, análise, permission; `initialize/tools/list/call_tool`; compound 2–3 tools; errors/partial; budgets; zero leaks; metamorphic inputs. Garantir regressões da Flask BFF e shared MCP.

### R4 — Build, smoke e docs
Executar testes completos pertinentes, architecture guardrails, Docker build/compose, smoke container `/healthz`, metadata, 401 challenge, initialize/list_tools e 4 calls controladas; atualizar S1 freeze rev.2, handoff Keycloak (espera quatro tools), relatório, manual/Help se afetado, executar residual search (nomes antigos em instruções/testes/catálogos/fixtures/docs); preservação de histórico em relatório em vez de reescrever fato passado.

### R5 — Verify-final e commit
Relatório final no padrão do projeto com BASE/FINAL HEAD, FILES, CONTRATOS, AuthZ, test results, smoke, residuals, RQ/AC, status. Commit e push só conforme políticas. Sinalizar se `KEYCLOAK_READY` continua PASS para **nova superfície**; se integração/CI não puder ser executada: `INCONCLUSIVE`, sem presumir PASS.

## 5. STOP CONDITIONS

`EXECUTION_DRIFT` se owner/permissions/contratos mudaram, alguma tool legada tem consumer ativo, `get_context` não tem valor real, registry genérico pode burlar autorização, modelo de lote força writes fora do escopo, authn/authz se enfraquece, gateway mudou, schema ChatGPT não suporta discriminadores, ou smoke revela comportamento não equivalente. Parar somente cadeia afetada; revalidar e documentar decisão. **Não fazer deploy produtivo ou Keycloak registration.**

## 6. Resultado final pretendido

`SURI_SEMANTIC_TOOLS=4`; `LEGACY_BEHAVIORS=8/8_PRESERVED`; `V1_WRITE_TOOLS=0`; `FUTURE_EXECUTE_DELETE=TARGET`; `CORE_AUTHZ=UNCHANGED`; `KEYCLOAK_REGISTERED=NO`; `CHATGPT_CONNECTED=NO`. Valores são TARGETs, não resultado desta publicação de plano.
