# SURI — Inventário comparativo dos MCPs TÉO, VISTA, CLARA e DAVI

> **Data:** 2026-10-27. **Status:** INVENTORY_PARTIAL — interfaces MCP e catálogos READ inspecionados; inspeção de código/infra/contratos no HEAD ainda **TO_INVENTORY**.  
> **Referência de código consultada:** `main` em `486831a025bfad52694a5aa0a0711dffc2340f95` no início desta inspeção; working tree local indisponível via conector GitHub.  
> **Sem alterações de runtime:** nenhuma escrita MCP, BFF, permissão ou deploy. Esta entrega contém somente documentação.

## 1. Alcance e metodologia

Foram examinadas as descrições/schemas das ferramentas disponibilizadas nesta sessão para os quatro MCPs e executados exclusivamente `get_catalog` READ em TÉO, VISTA e CLARA. Não foram executadas operações `prepare*` ou `commit*` nem consultas de dados operacionais privados. Foi consultada a documentação canônica de Suprimentos `README.md`, `IMPLEMENTATION-PLAN.md`, regras e instrução oficial no GitHub. Pesquisas textuais no GitHub por nomes de MCP/tools não localizaram código; **search miss não prova ausência**: abrir paths concretos via Cursor e inventariar a árvore é obrigatório.

A contagem abaixo representa ferramentas expostas ao assistente nesta sessão, não a superfície completa de todo deployment, versão ou usuário.

| Agente | Tools observadas | Catálogo vivo consultado | Natureza |
|---|---:|---|---|
| TÉO | 23 | PASS | Processos, evidências, guia, operações governadas |
| VISTA | 12 | PASS | TV Dashboard, modelos/rotas, sugestões, PREPARE/ACT |
| CLARA | 18 | PASS | Fechamento, conhecimento, análise, propostas/lotes |
| DAVI | 2 | NÃO EXECUTADO | Descoberta e execução READ governada |

## 2. TÉO — Transformômetro

**Padrão de ferramentas observado:** `get_my_context`, `get_workspace_context`, `get_catalog`, `get_methodology_guide`, `get_product_guide`, `solution_read`, `helpdesk_read`, `get_process_context`, `analyze`, `record_read`, `evidence_read`, `get_process_timeline`, `meeting_minute_read`, `collaboration_read`, `diagnostic_read`; `prepare_record_change`, `prepare_governed_operation`, `prepare_evidence_change`, `prepare_meeting_minute_change`, `prepare_collaboration_change`, `prepare_diagnostic_change`, `prepare_helpdesk_change`; `commit_proposal`.

**Catálogo READ em runtime — PROVEN na sessão:** entidades `process`, `instance`, `revision`, `measurement`, `decomposition_tree`, `meeting_minute` etc.; `registration_guide` e regras `GOVERNED_PREPARE_COMMIT_V2`. PREPARE não persiste; proposta tem política `auto_act` ou `confirm_before_act`; ACT somente com `proposal_handle`; após ACT, read-back e verificação. Catálogo diferencia conhecimento de processo (`process_document`) de estados estruturados e histórico de decisões.

**Reuso SURI:** catálogo de capabilities, guia operacional, leitura de contexto somente como hint, análise distinta de persistência, classificação da evidência, proposta selada e read-back.

**Limites:** catálogo não prova arquitetura de hosting, testes, token delegation, source path ou acesso de outro usuário.

## 3. VISTA — Painéis Operacionais

**Tools observadas:** `list_playlists`, `get_playlist_context`, `get_playlist_history`, `get_catalog`, `search_data_routes`, `inspect_data_model`, `preview_data_model`, `preview_data_block`, `get_product_guide`, `suggest_change`, `prepare_change`, `commit_proposal`.

**Catálogo READ em runtime — PROVEN na sessão:** capacidade de upsert/patch/delete governada para playlist, slide, bloco, data source e DataModel, com operações tipadas, risco e `confirmationPolicy`. PREVIEW e SUGGEST são análise, não gravação. `prepare_change` devolve `proposal_handle`, `canCommit`, risco, política de confirmação e diff candidato; `commit_proposal` exige `proposal_handle` + `idempotency_key`, e confirmação quando a política requer. Resultado é verificado pelo backend (`VERIFIED` / `OUTCOME_NOT_VERIFIED`).

**Reuso SURI:** diffs antes de ações de escrita, previsualização de consequências, idempotência, classificação de risco, preservação de alterações pontuais e pós-condição.

**Limites:** as ferramentas VISTA são particulares ao contexto TV Dashboard; não portar sua vocabulary de slides para o domínio de Suprimentos.

## 4. CLARA — Controladoria e Finanças

**Tools observadas:** `get_my_context`, `get_catalog`, `get_competence_state`, `get_checklist_items`, `list_documents`, `get_p3_reconciliation`, `list_pendencies`, `get_package_review`, `analyze_closing_blockers`, `search_closing_knowledge`, `get_knowledge_item`, `list_knowledge_sources`, `prepare_governed_operation`, `commit_proposal`, `prepare_batch`, `confirm_batch`, `execute_batch`, `get_batch_status`.

**Catálogo READ em runtime — PROVEN na sessão:** responde `access`/`manage` no escopo do usuário da sessão (não generalizar); cinco operações governadas expostas `evidence.decide_version`, `evidence.decide_item_set`, `review.record_decision`, `clarification.open`, `clarification.resolve`. Corpus: **1.713 itens, 56 fontes**, versão `5d546360-ab37-410c-80e8-e1a5748ed56e`, com timestamp de publicação em 2026-10-27 09:11 -03; catálogo determina citar `citation_locator` e `evidence_classification`.

**Segurança e operações observadas pelos contratos de tools:** operação PREPARE sela estado/expiração. ACT demanda `proposal_handle` e consentimento verificável via `consent_record` de etapa adicional no Portal (não produzível pela conversa), revalida ator/estado/permissions e verifica pós-condição; `resume=true` reconcilia estado incerto sem repetir efeito. Lotes possuem PREPARE, confirmação consolidada vinculada ao `plan_hash`, execução em dependências com status por operação.

**Reuso SURI:** modelo operacional + base de conhecimento versionada/proveniente + análise explicável + consentimento confiável + lote somente se houver caso de negócio. **Não assumir que a SURI já possui corpus ou consentimento/step-up.**

## 5. DAVI — Dados e Informações

**Tools observadas (schemas de interface):**
- `discover_delpi_information(query, top_k <= 10)`: identifica candidatos READ autorizados e retorna `candidate_token` opaco, vinculado ao ator, `argument_schema` e hints de paginação.
- `execute_delpi_information(candidate_token, arguments)`: executa somente candidato proveniente da descoberta; não aceita URL, rota, HTTP method, SQL ou `operationId` arbitrário. Backend é authority de AuthZ; retorno declara `projection`, `truncated`, `is_complete`, e limites de resposta.

**Reuso SURI:** descoberta de operações READ sem criar executor genérico perigoso, argumentos tipados, limite de payload, retorno parcial explícito e autorização no backend.

**Limites:** execução de dados não realizada; não comprova saúde, disponibilidade de cada capability, biblioteca interna ou eventual corpus de conhecimento.

## 6. Matriz de princípios para SURI

| Dimensão | Referência | Proposta SURI | Gate |
|---|---|---|---|
| Discovery/catalog | TÉO, CLARA, VISTA | `get_catalog` ou equivalente que mostre capacidades realmente publicadas | TO_INVENTORY contratos |
| Leitura governada | DAVI, CLARA | leitura por tools específicas, ou discovery com candidate token com escopo | Core AuthZ + BFF |
| Conhecimento | CLARA, TÉO, VISTA | `get_product_guide`, `search_supplies_knowledge`, `get_knowledge_item` candidatos; não publicados | owner/fonte/index/RBAC/version |
| Inteligência | CLARA, VISTA | análise por contexto autorizado, facts vs recommendations | fórmulas e fontes homologadas |
| Escrita governada | TÉO, CLARA, VISTA | `prepare_operation` + `commit_proposal` candidatos | consent + RBAC + idempotência |
| Ações em lote | CLARA | somente se houver demanda e contrato; bloqueios por dependência | semântica de lote provada |
| AuthN/AuthZ | Todos, instrução oficial | identidade de usuário propagada com segurança; Core effective permissions checadas na BFF | fail-closed positivo/sibling/negativo |
| Resultado | CLARA, VISTA, TÉO | read-back e pós-condição; `INCONCLUSIVE` se impossível comprovar | testes + runtime |

**Arquitetura-alvo:** ChatGPT → SURI MCP adapter → `supplies-api` (Flask/AuthZ) → Core e contextos autorizados via contratos. **Proibido:** SURI MCP → `api-delpi` direto; duplicar domínio, Postgres TOTVS ou permissões no MCP. `supplies-api` permanece owner de composição; hosts/transport não comprovados.

## 7. Gaps críticos não resolvidos (TO_INVENTORY)

1. **Código e hosting real:** paths dos quatro MCPs, frameworks/SDKs, registros de servidor, protocolo/transporte, deployment, environment, CI/CD e regras `.cursor` específicas. GitHub search retornou zero, mas isso não prova ausência; inspeção de árvore/HEAD no Cursor é obrigatória.
2. **Identidade ChatGPT → serviço:** discovery de OAuth/OIDC, audience/scope, token exchange, user binding, expiry, PKCE, consentimento, proteção contra confused deputy e logs, sem exibir segredos.
3. **Interação com BFF:** endpoints reais dos MCPs de referência, adapters, contexto de usuário, tratamento de erros/retries, fronteiras de serviços e leitura do código.
4. **SURI capabilities:** inventário por rota e use case reais em `supplies-api`; diferenciar BFF implementado, MFE, deploy, write ERP OFF e contratos parciais.
5. **Conhecimento:** corpus/índice/citações da CLARA no código; estratégia canônica para Ajuda do Portal Suprimentos e fontes adicionais autorizadas.
6. **Operações materiais:** política de confirmação aplicável em Suprimentos, step-up, ledger de idempotência, postcondition, audit e rollback; nenhuma solução copiada automaticamente.
7. **Testes/evidência:** positive+sibling+negative por operação/unidade/recurso, stale/403/timeout, execução duplicada/concorrente, prompt injection, não vazamento, smoke autenticado ChatGPT ↔ MCP ↔ BFF.

## 8. Próxima execução proposta — SURI.S0 (somente inventário)

**TASK:** Cursor confirmar no HEAD e working tree os paths, contratos, infra e testes dos MCPs TÉO/VISTA/CLARA/DAVI e da `supplies-api` para congelar contrato inicial da SURI.  
**GOAL:** substituir `TO_INVENTORY` por evidência auditável antes de implementar.  
**AUTHORITIES:** instrução oficial; regras `.cursor` globais + plan-construction, platform-security-identity-authorization, platform-api-contracts-integration, platform-architecture-boundaries; docs Suprimentos e ADRs.  
**OWNER:** MCP adapter = transporte/UX conversacional; `supplies-api` = domínio/composição/AuthZ; Core = permissions; api-delpi/others = owners de dados/regra.  
**ALLOWED:** leitura de código, documentação, schema, testes, config sanitizada, evidence, relatório e proposta contratual.  
**FORBIDDEN:** implementar MCP/endpoint, novos secrets, migrations, RBAC novo, chamar downstream fora BFF, testes com side effect produtivo.  
**EVIDENCE_REQUIRED:** BASE/FINAL HEAD, git status, paths/SHAs, matriz `tool → adapter → endpoint → AuthZ → postcondition`, fluxo de credencial, dependências, gaps e riscos.  
**STOP_CONDITION:** conflito de owner/authn/AuthZ, ausência de contrato de usuário final, implausibilidade de BFF-only, segredos expostos ou divergência material → `EXECUTION_DRIFT`; não ajustar silenciosamente.

**Estado final deste inventário:** interfaces e catálogos observados = **PASS (read-only)**; código/infra = **INCONCLUSIVE/TO_INVENTORY**; implementação SURI = **TEST_NOT_RUN / PLANNED**.
