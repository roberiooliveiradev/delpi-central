# TÉO — Semantic MCP V3 | Plano mestre de evolução

**Data de registro:** 2026-10-30  
**Status do desenho:** `ACCEPT_WITH_RESIDUAL`  
**Status de execução:** `DEPLOYED — PRODUCTION SHA 7017df3d0a` (coexistência V3+V2)  
**Implementação:** concluída em coexistência; tombstone das 23 tools V2 aguarda aceite de consumers  
**Controle operacional e progresso:** [GitHub Issue #124](https://github.com/roberiooliveiradev/delpi-central/issues/124)

> Este documento registra o alvo arquitetural e a estratégia de execução. **Não comprova código, deploy, runtime ou resultado**. A issue #124 é o ledger vivo que o Devin deverá preencher com evidências por gate. As fontes canônicas de capability e execution policy continuam no código do domínio.

## 1. Objetivo

Refatorar a superfície MCP do TÉO para seis tools semânticas, conforme o padrão de interação desejado e os contratos comparados de CAIO e SURI:

| Tool | Responsabilidade | Requisito |
|---|---|---|
| `get_context` | Contexto, workspace, discovery e capabilities | Contexto nunca concede AuthZ |
| `read` | Leitura tipada por entidade + ação | Sem escrita implícita |
| `analyze` | Análise estruturada, diagnósticos, cálculos não-persistentes | Fato, cálculo, hipótese e proposta separados |
| `knowledge` | Guias de produto e metodologias, incluindo Methodology Intelligence V2 | Conhecimento não é fonte de verdade operacional |
| `execute` | Criação, atualização e operações governadas | Execution policy canônica; PREPARE/ACT/read-back |
| `delete` | Exclusões realmente destrutivas | Proposta exata e confirmação explícita |

**Resultado esperado:** substituir a complexidade exposta das 23 tools MCP por seis entradas estáveis, preservando as capabilities tipadas, os contratos existentes, a autorização e a integridade transacional. O número de tools é meta de interface, não medida isolada de sucesso.

## 2. Baseline do levantamento (informado pelo Devin, requer revalidação)

- HEAD de trabalho informado: `6c99b1e131` (worktree `my-tasks-delegated`).
- `origin/main` no levantamento: `d5946547db` — divergência/concorrência a reconciliar antes de qualquer diff.
- Inventário em código informado: 23 nomes de tools, 37 bindings de capability, 56 registros de política, 20 entidades e 21 operações GPT Actions.
- `tm_app/application/intelligence/capability_registry.py` — fonte do vínculo capability/transporte.
- `tm_app/application/governed_writes/confirmation_policy.py` — política de confirmação.
- `tm_app/application/governed_writes/orchestrator.py` — resolução de ações.
- `tm_app/application/gpt_actions/entities.py` — entidades.
- `tm_app/interface/mcp/tool_bridge.py`, `server.py` — superfície do transporte.
- `shared/delpi_mcp/` — taxonomia compartilhada.

**Classificação:** `PROVEN` no levantamento de código do SHA informado; runtime atual e paridade em produção = `TO_INVENTORY`. A comparação de CAIO/SURI como servidores externos deve ser validada por seus próprios contratos vivos, sem inferir ausência por busca local.

## 3. Decisões de arquitetura

1. Construir adapter semântico sobre os use cases existentes. Nenhuma autoridade paralela.
2. Derivar as operações V3 do registry canônico; não inventar registry concorrente.
3. Preservar `TÉO capability <= authenticated user capability`, backend-first/fail-closed e ownership Keycloak/Core/Domain API/Portal/Transformômetro.
4. `auto_act/direct`: preparar, validar, aplicar e verificar no mesmo pedido, sem confirmação conversacional extra, com AuthZ no ACT.
5. `confirm_before_act`: mostrar mudança exata; exigir confirmação; vincular proposta ao ator/alvo/estado; ACT com read-back.
6. `blocked`: não executar. Confirmação do usuário não é autorização.
7. `delete` é restrita a exclusões destrutivas comprovadas. Cancelamentos, rejeições e transições de negócio permanecem em `execute` com política específica, salvo contrato canônico em contrário.
8. `effect_class` nos 56 registros não é aprovado automaticamente: realizar Abstraction Gate.
9. Multi-action usa composição de operações tipadas, IDs reais de read-back e dependências explícitas; sem batch/proxy arbitrário.
10. Preservar GPT Actions atuais nesta fase, Methodology Intelligence V2 e os contratos BPMN comprovados. Não substituir documentos de modelagem por inferências legadas.
11. Coexistir temporariamente com as tools MCP antigas. Tombstone apenas após inventário de consumers e aceite.
12. Nenhum write pode ser declarado concluído sem read-back autoritativo e postcondition. Divergência = `OUTCOME_VERIFICATION_FAILED`.

## 4. Plano de execução e checkpoints

| Marco | Escopo | Estado | Gate de saída |
|---|---|---|---|
| G0 | HEAD seguro, consumers, schemas V3, risco, classificação delete, rollback, contrato e autorização | `PASS` | Inventário PROVEN: 23 tools, 37 bindings, 56 policies, 21 Actions ops |
| F1 | Projeção V3 derivada do registry | `PASS` | `DESTRUCTIVE_DELETE_OPERATIONS` fechado em confirmation_policy; `V3_TOOL_CLASS`/`SEMANTIC_V3_COEXISTENCE` em constants |
| F2 | Seis handlers MCP, tipagem e envelopes de erro | `PASS` | `tool_bridge_v3.py` (864 linhas); `analyze` unificada (flat + params + meeting_minute_transcript); schemas com enums fechados |
| F3 | Execution policy, AuthZ, multi-action, idempotência | `PASS` | 23 testes `test_teo_mcp_v3_surface.py`: auto_act 1-chamada, confirm→proposal, commit por proposal_id, delete fail-closed, ops[] com `$ops.N` refs, parada em falha, unauth 401 |
| F4 | Regressões, integração, segurança, correções, residual search | `PASS` | Suíte integral 1976 pass; 26 falhas pré-existentes do baseline (async/fixture, comprovado via stash) — zero falha atribuída ao diff |
| F5 | Aceite conversacional no host e em consumers | `TEST_NOT_RUN` | Requer sessão autenticada no ChatGPT/host — ação manual pendente |
| F6 | Commit, push, rollout controlado e pós-deploy | `PASS` | SHA prod `7017df3d0a`; health 200; `tools/list` runtime = 28 tools (6 V3 presentes); MCP sem bearer = 401; rollback = `git revert` + redeploy do SHA anterior |

**Operação do ledger:** em cada checkpoint, o Devin atualiza os checkboxes e tabela da [issue #124](https://github.com/roberiooliveiradev/delpi-central/issues/124), incluindo BASE/FINAL HEAD, arquivos, testes, AuthZ, policies, contratos, read-back, gaps, PR/commit, deploy e ações do Builder. Só classificar `PASS` quando a prova pertinente existir.

## 5. Critérios de aceite

- Preservação das capabilities realmente suportadas, com mapeamento `capability → legacy route → semantic V3 → consumer`.
- Input schemas e action enums fechados; operação não suportada falha tipada, sem fallback arbitrário.
- Read não produz write; PREPARE não persiste; ACT revalida ator, escopo, fingerprint e policy.
- Exclusão exige proposta exata e confirmação; `confirmation=true` isolado não autoriza.
- `auto_act` sem interrupção conversacional desnecessária; outras operações respeitam a policy canônica.
- Operações dependentes usam apenas IDs de read-back; falha upstream impede downstream.
- Suite MCP + GPT Actions + AuthZ + integração + host smoke, incluindo erros e regressões.
- Nenhum 2xx isolado, teste verde isolado ou documentação é prova suficiente de resultado.
- Rollout em produção somente após gates; validar `tools/list`, schemas, AuthN/AuthZ, read e write de teste autorizado, SHA implantado e postcondition.
- Alterar OpenAPI/Builder apenas se o respectivo contrato ou material efetivamente mudou.

## 6. Riscos e dependências

- Divergência entre worktree do levantamento e `origin/main`: revalidar Git e preservar código concorrente.
- Compatibilidade de consumidores desconhecidos: inventariar antes de tombstone.
- Classificação de destrutividade: não confundir delete com cancel/reject.
- Capabilities MCP-native, inclusive diagnóstico: não criar falsa paridade com GPT Actions.
- Budget de catálogo MCP e ergonomia de schemas: medir, não presumir redução.
- Contratos reais CAIO/SURI são externos à árvore inspecionada; referência comparativa não concede autoridade ao TÉO.
- Deploy de runtime exige release mesmo sem mudança OpenAPI; schema novo só deve ser reimportado quando existir mudança na superfície GPT Actions.
- Registrar rollback e decisões go/no-go antes do deploy.

## 7. Relatório obrigatório e governança

Toda implementação deve retornar `TRANSFORMÔMETRO EXECUTION REPORT` com TASK, BASE/FINAL HEAD, STATUS, owner/source/contract, arquivos, testes, MCP/OpenAPI/Actions, AuthZ, policy, multi-action, postcondition, authoritative read-back, residual search, riscos, commit/push, deploy e intervenções manuais no GPT Builder.

Esta iniciativa complementa o roadmap histórico de produto e o [ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md); **não substitui automaticamente a sequência de outras iniciativas**. Qualquer conflito com a fonte canônica ou o runtime deve ser registrado como drift e submetido à revisão.

**Fonte operacional de progresso:** [TÉO Semantic MCP V3 — issue #124](https://github.com/roberiooliveiradev/delpi-central/issues/124).
