# Documento 111 — CLARA: smoke MCP autenticado no ChatGPT e retomada da Central de Fechamento

**Data:** 2026-10-26 (America/Sao_Paulo). **Processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria. **Produto:** Portal Controladoria & Finanças / Central de Fechamento. **Execução:** `CF-PROC0072-CLARA-CHATGPT-AUTH-READ-SMOKE-20261026-001`. **Natureza:** registro de evidência de integração e handoff; **não é novo GO de implementação nem aceite global P1–P6**.

**Authority e antecedentes:** [README do produto](./README.md), [ledger RQ/AC 23](./23-ledger-rq-ac-testes.md), [roadmap 93](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md), [CLARA 94](./94-clara-especialista-mcp-controladoria-financas.md), [plano 104](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md), [release/ChatGPT 107](./107-clara-validacao-antecipada-chatgpt-release-hoje.md), [G2 108](./108-homologacao-guiada-g2-g3-2026-10-26.md) e [handoff IAM 110](./110-g3-handoff-operator-iam-clara-chatgpt-2026-10-26.md). Target de código conciliado: [`f0abb8f0341a75cbcffed80ded893010f3c2ac41`](https://github.com/roberiooliveiradev/delpi-central/commit/f0abb8f0341a75cbcffed80ded893010f3c2ac41). Investigação IAM read-only registrada no Doc 107, Adendo 11, commit documental `38c000c969` reportado pelo executor.

## 1. Mudança observada desde o Adendo 11

1. **Keycloak, realm `delpi`:** usuário responsável apresentou screenshot do mapper dedicado ao client `mcp-controllership-finance`, `audience-controllership-finance-api`, após edição: `Included Client Audience` vazio, `Included Custom Audience = https://minhadelpi.com.br/apps/controllership-finance-api/mcp`, `Add to access token = On`, `Add to ID token = Off`, `Add to token introspection = On`; toast **“Mapping successfully updated”**. **PROVEN por captura da UI** de configuração salva; leitura posterior independente do banco/claims brutos do token **TEST_NOT_RUN**.
2. **ChatGPT:** screenshot posterior indicou toast **“Primary agora está conectado”**, plugin CLARA com OAuth usado, URL MCP canônica, versão `dev mode` / revisão `DEVELOPMENT`. **PROVEN por captura da conexão**; não equivale a publicação no workspace.
3. **ChatGPT — MCP efetivo nesta conversa:** o conector disponibilizou **18 definições de ferramentas** à sessão do assistente. Chamadas diretas reais às tools `get_catalog`, `get_my_context` e `search_closing_knowledge` retornaram `structuredContent.success=true` e `message=ok`. Isso supera o estado anterior `TEST_NOT_RUN` para esse **smoke de leitura autenticada**. Não se executou ACT, batch, `get_competence_state` ou leitura de competência operacional real.

**Proveniência:** screenshots e outputs MCP na conversa de 26/10/2026; evidências observadas pelo GPT durante a sessão. Não afirmar que prints, HTTP trace completo ou tokens foram anexados ao repositório. Nenhuma credencial/token foi incluída neste documento.

## 2. Matriz de evidência e resultado

| ID | Verificação | Evidência observada | Resultado |
|---|---|---|---|
| CLARA-AUTH-01 | Correção do mapper de audience no Keycloak | Screenshot com toast de sucesso e resource URL completa | **PASS** (salvamento na UI); token `aud` independente **TEST_NOT_RUN** |
| CLARA-AUTH-02 | Conta OAuth conectada no ChatGPT | Screenshot “Primary agora está conectado” | **PASS** (conexão apresentada pela UI) |
| CLARA-MCP-01 | Discovery de ferramentas no host | 18 tools CLARA expostas ao assistente, incluindo READ, DISCOVERY, ANALYSIS, PREPARE e ACT | **PASS** (visibilidade das definições de tools na sessão) |
| CLARA-MCP-02 | `get_catalog` | `success=true`; `capabilities.access=true`, `manage=true`; 14 entradas no catálogo retornado, lista distinta das 18 definições expostas pelo host | **PASS**; discrepância **18 versus 14 = TO_INVENTORY**, sem presumir defeito |
| CLARA-MCP-03 | `get_my_context` | `success=true`; identidade contextual e duas capabilities efetivas `access/manage=true` | **PASS** (READ autenticado); JWT não é autoridade final de permissão |
| CLARA-MCP-04 | `search_closing_knowledge` | `success=true`; 3 itens relativos ao PROC-0072 com locator, documento, linhas, versão, `APPROVED_RULE` e autoridade `OWNER` | **PASS** (READ knowledge e proveniência) |
| CLARA-MCP-05 | Corpus | `corpus_version_id=5541097a-8608-4470-b971-7c28b3ae6c40`, `source_count=52`, `item_count=1298`, publicação 2026-10-26 07:07:09 -03 | **PASS** (metadados retornados em chamada MCP, não auditoria de conteúdo integral) |
| CLARA-MCP-06 | Estado de competência `get_competence_state` e regras P1–P6 | Não chamado | **TEST_NOT_RUN** |
| CLARA-MCP-07 | PREPARE/ACT/batch, consentimento V014, read-back/auditoria de efeitos | Não chamados | **TEST_NOT_RUN** |
| CLARA-ADMIN-01 | Publicação no workspace | Falha anterior “Não foi possível carregar ou salvar a configuração do aplicativo”; sem nova comprovação após correção | **INCONCLUSIVE**; dev mode funcional não prova publicação |
| CLARA-IAM-01 | Estado canônico do engine `mcp-audience-clara` vs mapper client-level manual | Forense anterior apontou drift; não houve novo `--check` | **PENDING / TO_INVENTORY** |
| CLARA-DEPLOY-01 | SHA em runtime | `f0abb8f034` informado pela execução do Devin, sem SSH independente nesta sessão | **OWNER_REPORTED / TO_VERIFY** |

**Amostra verificável da consulta knowledge:** Doc 93, linhas 3–10, `source_version=6bb25b4c29e9`; Doc 94, linhas 21–34, `source_version=a4c9597b63a1`; Doc 104, linhas 3–9, `source_version=c9e2f52d176d`. Cada resultado continha `citation_locator`, `evidence_classification=APPROVED_RULE` e `origin_authority=OWNER`. Trata-se de busca documental, **não** de confirmação de número oficial TOTVS/ERP nem de conclusão mensal.

## 3. Conclusão delimitada

**`ACCEPT_WITH_RESIDUAL` — integração CLARA/ChatGPT para DISCOVERY e READ autenticados.** As chamadas reais responderam com dados úteis e localizadores; não apenas HTTP 200. O problema de audience observado anteriormente foi corrigido na UI, e o outcome autenticado de READ foi comprovado na sessão. **Não declarar `ACCEPT` para publicação no workspace, fluxo ACT, consentimento end-to-end, operação P1–P6 ou homologação global da Central.**

Persistem: verificar `aud` por token de teste redigido ou prova equivalente pelo owner IAM; reconciliar desired-state Keycloak sem alterar clientes irmãos; discriminar 18 definições de ferramentas expostas vs 14 do catálogo; publicação do plugin no workspace; testes de leitura de competência real e ACT apenas em ambiente/dados expressamente autorizados. Não criar credenciais, nem executar `--apply` ou ACT em produção com base neste registro.

## 4. Retomada do desenvolvimento da Central de Fechamento

A solicitação atual do PO é **retornar ao desenvolvimento do fechamento mensal**. Este documento registra a transição de foco, **não fornece GO irrestrito para novos slices**.

**Próxima execução recomendada — inventário e priorização, READ-ONLY:**

1. Capturar HEAD novo e `git status` do worktree do executor; consultar regras `.cursor` aplicáveis e contratos P1–P6 no HEAD, inclusive produtores/consumidores/testes, ledger 23 e docs 93/104/108/110.
2. Consolidar matriz **P1–P6** por página/fluxo com `RQ/AC → owner → evidência runtime → testes → pendências → autoridade → status`, distinguindo código existente, deploy, smoke real, aceite humano, dados ERP oficiais e fontes/relatórios ainda ausentes.
3. Revalidar dependências G1 (T03/T05, R04+, seeds/reports, G5/G6), G2 com limitações registradas e G3 por release; não inferir quitação de gate pelo sucesso da CLARA.
4. Propor **um** próximo slice por prioridade e bloqueio real, com diff mínimo e teste verificável; se surgir nova decisão material (boundary, owner, contrato, persistência, IAM, integração, breaking change), retornar `DECISION_REQUIRED` antes de implementar. Nenhum novo runtime está autorizado por este documento.
5. Registrar no mesmo ciclo: evidência, `EXECUTION_DRIFT` quando aplicável, testes `TEST_NOT_RUN`, decisão humana, commit SHA e próximo gate.

**Frente CLARA:** manter integração de READ operacional; tratar publicação ChatGPT e convergência IAM como residuais acompanhados sem bloquear automaticamente o inventário P1–P6 e sem declarar encerrados os gates do produto.

## 5. Resultado e next action

`CLARA_CHATGPT_TOOL_DISCOVERY=PASS` (18 definições de tools disponíveis nesta sessão).  
`CLARA_AUTHENTICATED_GET_CATALOG=PASS`.  
`CLARA_AUTHENTICATED_GET_MY_CONTEXT=PASS`.  
`CLARA_AUTHENTICATED_SEARCH_KNOWLEDGE=PASS`.  
`CLARA_AUTHENTICATED_COMPETENCE_SMOKE=TEST_NOT_RUN`.  
`CLARA_BATCH_CONSENT_E2E=TEST_NOT_RUN`.  
`CHATGPT_WORKSPACE_PUBLICATION=INCONCLUSIVE`.  
`KEYCLOAK_DESIRED_STATE_RECONCILIATION=PENDING`.  
`CENTRAL_P1_P6_GLOBAL_ACCEPTANCE=NOT_PROVEN_BY_THIS_SMOKE`.  
`NEXT_ACTION=READ_ONLY_P1_P6_INVENTORY_AND_NEXT_SLICE_GATE`.

**Regra:** READ → VERIFY → CLASSIFY → DECIDE → (GO explícito) IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME → DOCUMENT → REPORT.
