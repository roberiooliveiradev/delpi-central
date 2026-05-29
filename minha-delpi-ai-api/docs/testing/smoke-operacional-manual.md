# Smoke operacional — checklist manual

Checklist de perguntas para validar o chat operacional após deploy ou alterações no pipeline de inteligência.

**Dica:** para testes multi-turno, use a **mesma conversa** — o histórico importa.

**Agente recomendado** para os cenários GPT/SQL (#G1–G8): **Minha DELPI Chat** (`agent_key=minha-delpi-chat`).

**Configuração do chat:** antes do smoke, alinhe toggles do admin ao perfil **dev** ou **prod** — [`../knowledge/chat-intelligence-settings-profiles.md`](../knowledge/chat-intelligence-settings-profiles.md).

Se algo falhar após deploy, reinicie a API:

```bash
docker compose -f infra/docker-compose.dev.yml restart minha-delpi-ai-api
```

---

## Smoke operacional (6/6)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 1 | estoque do produto | Pede o código; não chama API de estoque/ROL |
| 2 | estouque do produto | Mesmo comportamento (corrige typo) |
| 3 | estoque do produto 10080022 | Consulta estoque; tabela/gráfico com dados |
| 4 | quem te criou? | Resposta canônica sobre Minha DELPI; rápida, sem RAG |
| 5 | olá | Saudação direta (`ChatSmallTalkService`); sem RAG/LLM |
| 6 | *(após #3)* filtre filial 02 | Refina estoque da filial 02 do produto anterior |
| 6b | *(após KPI estoque empresa)* filial 01 | Refina `/supplies/stock-value` na filial 01; **sem** SQL/agentic |

---

## E2E HTTP — estoque + drill-down

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 7 | estoque do produto 10080022 | Tabela com filiais/armazéns |
| 8 | *(mesma sessão)* filtre filial 02 | Só filial 02; não erro «API não retornou registros» |
| 9 | *(alternativa)* clique numa linha da tabela (tooltip «Clique para detalhar») | Envia algo como `filtre filial 02 armazém 01 do produto 10080022` |

---

## Multi-turn operacional (9 passos)

### Cenário A — estoque → filial → completo

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 10 | estoque do produto 10080047 | Estoque completo (todas filiais) |
| 11 | filtre filial 02 | Só filial 02 |
| 12 | completo de novo | Estoque completo de novo, sem filtro |
| 13 | estoque completo | Idem — remove filtro de filial |

### Cenário B — dois produtos + filial

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 14 | estoque dos produtos 10080047 e 10080055 | Dois estoques (dois produtos) |
| 15 | filtre filial 01 | Ambos filtrados na filial 01 |
| 16 | mostre completo | Remove filtro de filial nos dois |

### Cenário C — contexto sem repetir código

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 17 | resumo dos produtos 10080047 e 10080055 | Dois resumos |
| 18 | estoque do produto | Estoque do último produto citado (10080055) |

---

## Regressão de intenção (roteamento)

| # | Pergunta | Rota esperada |
|---|----------|---------------|
| 19 | descrição do produto 10080047 | Descrição do produto |
| 20 | busque o estoque desse produto | Estoque (após citar produto antes) |
| 21 | informações completas do produto 10080055 | Analyser/ficha completa |
| 22 | resumo do produto 10080047 | Summary (não analyser) |
| 23 | ficha completa do produto 10080047 | Analyser (não summary) |
| 24 | qual o valor total de estoque da empresa | KPI suprimentos (não produto individual) |
| 25 | faturamento do produto 10080047 | Faturamento do produto |
| 26 | detalhe da LMP da OV 123456 | LMP por OV |
| 27 | kpis do painel de LMPs | Dashboard LMP |
| 28 | pmr da filial 02 | PMR com filial 02 |
| 29 | colunas da tabela SB1 | Metadados da tabela SB1 |

---

## Comparação / insights (não deve disparar nova consulta operacional)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 30 | compare as duas estruturas e traga insights | Análise comparativa, sem nova action de estrutura |
| 31 | estrutura do produto 90260088 | Consulta estrutura normalmente (não é comparação) |

---

## Datas automáticas (11.1.2)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 32 | cpv de 01/04/2026 a 30/04/2026 | CPV com intervalo de datas |
| 33 | listar ov de 01/04/2026 a 30/04/2026 | OVs no período (`GET /sales`, tabela); **não** `/products/{data}/sales` |

---

## Lousa / canvas (multi-turno)

Use agente com `capabilities.canvas: true` (ex.: Minha DELPI Chat).

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 56 | me diga quem sou eu e o que consigo fazer aqui, quem é você? | Resposta em seções (perfil, capacidades, assistente) |
| 57 | *(após #56)* coloque em uma lousa | Lousa abre com o conteúdo da resposta #56; chat confirma «Coloquei …» |
| 58 | *(após #57)* acrescente na lousa a descrição do produto 10080049 | Consulta produto + lousa **atualizada** (perfil + descrição); **não** repete só a confirmação da lousa |
| 59 | *(alternativa)* acrescente isso na lousa | Merge da lousa existente + última resposta útil do chat |

---

## Refinamento KPI / métricas (11.1.1)

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 34 | qual o cpv → filtre filial 02 | CPV refinado na filial 02 |
| 35 | faturamento comercial → filtre filial 02 | KPI comercial filtrado |

---

## Follow-up de sub-rota produto (11.1.1)

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 36 | estrutura do produto 10080047 → e os pais desse produto | Consulta parents do mesmo produto |
| 37 | resumo do produto 10080047 → ultimas compras | Compras do mesmo produto |

---

## Drill-down frontend (11.4.2)

| # | Ação | Mensagem gerada ao clicar |
|---|------|---------------------------|
| 38 | Clique em linha com filial + armazém + produto | `filtre filial 02 armazém 01 do produto 10080022` |
| 39 | Clique só com filial + produto | `filtre filial 01 do produto 10080022` |
| 40 | Clique em linha só com código/descrição | `Detalhe do item 90260077 (Parafuso)` |

---

## Identidade e capacidades (não são perguntas de produto)

| # | Como testar | O que esperar |
|---|-------------|---------------|
| 41 | Login rober / 1234 → portal carrega | `/core-api/me` retorna 200 |
| 42 | DevTools → `GET /apps/minha-delpi-ai/api/chat/capabilities` | `knowledgeDocumentMaxChars: 2000000` |

---

## Apresentação rica (11.4.3 — UI)

| # | Pergunta | O que observar |
|---|----------|----------------|
| 43 | estoque do produto 10080022 | Tabela/gráfico aparece antes do texto markdown |
| 44 | Na resposta com tabela | Toolbar Texto / Gráfico / Tabela / Expandir no topo |
| 45 | Expandir tabela → clique na linha | Drill-down funciona também no modal expandido |

---

## Parents / árvore / paginação (onda 11 — apresentação rica)

Use o agente **Especialista em Produtos** (ou agente com actions `api-delpi`).

### Consulta inicial + apresentação

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 46 | onde é usado o 10080022 | Comentário curto + banner parcial **uma vez** + toggle Árvore/Tabela (sem aba Texto redundante) |
| 47 | *(na resposta #46)* | Banner âmbar com página X de Y; **sem** bloco duplicado «Cobertura dos dados:» no texto |
| 48 | estrutura do produto 90260047 | Árvore PA→MPs; **sem** banner de profundidade se a estrutura estiver completa |

### Follow-up de paginação (mesma conversa)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 49 | *(após #46)* aumente para 50 linhas | Reconsulta rápida; mais linhas; **sem** RAG irrelevante; resposta **não** fica vazia |
| 50 | *(após #46 ou #49)* proxima pagina | Página 2 da mesma consulta; árvore/tabela atualizados |
| 51 | *(após #50)* pagina anterior | Volta à página anterior |
| 52 | *(alternativa)* botões **Anterior** / **Próxima** no card | Mesmo efeito de #50/#51; indicador «Página X de Y» |

### Consolidação automática (total / completo)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 56 | *(após #46 com banner parcial)* traga tudo | Várias chamadas API; lista consolidada; banner parcial some ou indica conclusão |
| 57 | *(após #46)* tabela completa | Consolida + apresentação em **tabela** (não só árvore) |
| 58 | *(após #46)* árvore completa | Consolida + apresentação em **árvore** |
| 59 | *(se #56 parou no limite)* sim, continue | Novo lote de páginas; contagem consolidada aumenta |
| 60 | *(alternativa)* listagem completa em tabela | Idem #57 — qualquer tipo de listagem paginada |

### Profundidade hierárquica

| # | Pergunta / ação | O que esperar |
|---|-----------------|---------------|
| 53 | *(se houver aviso de max_depth)* clique **Ampliar níveis** | Reconsulta com profundidade maior; mais níveis na árvore |
| 54 | *(alternativa)* aumente a profundidade para 99 | Idem ao botão Ampliar níveis |

### Regressão de resposta vazia

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 55 | #46 → #49 ou #50 | Conteúdo visível ao concluir o stream; **não** precisa dar F5 para ver texto/árvore |

---

## GPT_instructions + SQL produção (agente minha-delpi-chat)

Valida sync dos docs `GPT_instructions`, roteamento SQL de produção (não confundir com busca de catálogo) e visibilidade de fontes RAG.

**Smoke automatizado (preparação do turno, sem LLM lento):**

```bash
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  python scripts/smoke_gpt_instructions_improvements.py [user_id] [session_id]
```

**Teste manual no chat (E2E com stream):** mesmas perguntas abaixo; observe resposta, tools no `adminDebug` (admin) e badges de fontes.

### Produção / SQL — fast path (POST /data/sql), não `/products/search`

| ID | Pergunta | O que esperar (automático) | O que observar no chat (manual) |
|----|----------|----------------------------|----------------------------------|
| G1 | quais produtos serão produzidos hoje? | Fast path; 1 tool `POST /data/sql`; **sem** `search_products`; `skipRag` | Tabela com produtos programados (~segundos, como estoque) |
| G2 | me traga a programação de produção de hoje | Idem G1 — execução SQL direta | Dados de programação/OPs do dia |
| G3 | monte uma query que liste os produtos que vão ser produzidos hoje | Resposta direta com bloco SQL; **sem** tool; `skipRag` | Markdown com ` ```sql ` pronto para executar |
| G9 | quais ordens de produção estão programadas para hoje? | Idem G1 — SQL produção; **sem** search | Sinônimo de programação/OP (`ordens de produção`) |
| G10 | o que vai ser produzido amanhã? | SQL ou RAG produção; **sem** `/products/search` | Vocabulário temporal alternativo |
| G11 | liste a produção do dia na SC2010 | SQL `/data/sql`; menciona SC2010 | Vocabulário explícito da tabela |
| G12 | monte o SQL da programação de produção de hoje sem executar | Resposta direta com SQL; **sem** tool (como G3) | Modo «autoria» de query |

### Regressão — rotas REST que devem continuar funcionando

| ID | Pergunta | O que esperar (automático) | O que observar no chat (manual) |
|----|----------|----------------------------|----------------------------------|
| G4 | estoque do produto 10080047 | Fast path; 1 tool `stock`; `skipRag` | Tabela/gráfico de estoque do código |
| G5 | busque parafuso m8 | 1 tool `search`; `skipRag` | Resultado de catálogo (`GET /products/search`); **não** confundir com G1–G3 |

### RAG documental — docs GPT ingeridos no agente

| ID | Pergunta | O que esperar (automático) | O que observar no chat (manual) |
|----|----------|----------------------------|----------------------------------|
| G6 | qual rota da API DELPI retorna a ficha analyser completa? | RAG com `analyser`, `/products/`, `product_api` | Cita `GET /products/{code}/analyser` |
| G7 | como listar tabelas do dicionário de dados protheus na API? | RAG com `system`, `SX2`, `/system/` | Cita rotas de metadados (`/system/…`) antes de SQL |
| G13 | quais campos usar no POST /data/sql para consulta de produção? | RAG `data_sql_api_instructions` | Cita payload, SC2010 ou exemplos do doc SQL |
| G14 | quais regras de validação de desenho técnico existem? | RAG agente `drawing_*` / `validation_rules` | Não confundir com Normas de **descrição** (N*) |

### Visibilidade de fontes (UI)

| ID | Como testar | O que esperar |
|----|-------------|---------------|
| G8 | Faça G1 ou G7 com admin logado; veja badges de fontes na mensagem | Contexto RAG usa docs do agente internamente; **badges visíveis só** para anexos de **sessão** e **projeto** — **não** exibir `agent_source` |
| G8b | Anexe um PDF/txt na conversa e pergunte sobre o anexo | Badge de fonte **session** aparece; docs internos do agente continuam ocultos |

### Perguntas extras úteis (manual / homologação)

| # | Pergunta | Objetivo |
|---|----------|----------|
| 61 | quais ordens de produção estão abertas na SC2010? | RAG + SQL; vocabulário produção |
| 62 | como consulto apontamento de produção via API? | Doc `data_sql_api_instructions` no contexto |
| 63 | busque produtos com descrição parafuso m8 | Regressão: pede código ou usa search com parâmetro correto (não SQL produção) |
| 64 | liste 3 produtos do grupo 1008 | Regressão: `search_products` com filtro de grupo |
| 65 | ficha completa do produto 90264130 | RAG drawing + rota analyser (pré-Onda 12 PDF) |
| 66 | quais produtos serão produzidos hoje? | **Não** usar search; SQL ou resposta operacional rápida |
| 67 | produzidos hoje e busque parafuso m8 | Prioriza produção (G1) ou pede clarificação — **não** misturar SQL + search numa resposta incoerente |
| 68 | como descrever um terminal pino 4mm? | Normas grupo 1008 — ver N1/N3 |
| 69 | monte SQL de estoque SB2 — *(após G1 na mesma sessão)* | **Não** herdar intenção produção; SQL de estoque ou pedir código |

---

## Normas Técnicas — descrição de matéria-prima (chat base)

Valida intent `ChatTechnicalDescriptionIntentService` + RAG global `normas-tecnicas-delpi.md` (`company-knowledge`).

**Pré-requisito:** documento ingerido em `docs/knowledge/domains/global/` (`--sync-global --ingest-global`).

| ID | Pergunta | O que esperar |
|----|----------|---------------|
| N1 | como descrever um terminal? | Resposta com **grupo 1008**, estrutura de campos, exemplo; **sem** tool `search_products` |
| N2 | o que significa o campo material na descrição técnica de cabo? | Explicação a partir das Normas (grupo cabos 1001–1005) |
| N3 | normas técnicas DELPI para terminais pino | Seção terminais pino: sequência, campos, exemplo |
| N4 | qual a descrição do produto 10080047 | **Regressão:** consulta cadastral REST — **não** confundir com N1–N3 |
| N5 | como descrever um cabo PP? | Grupo cabos **1001–1005**; sequência de campos + exemplo |
| N6 | normas para descrição de isolador | Grupo **1009** isoladores |
| N7 | estrutura da descrição de resistor grupo 1016 | Campos típicos resistores; exemplo das Normas |
| N8 | o que significa bitola AWG na descrição técnica? | Explicação de campo; RAG Normas |
| N9 | como pesquisar produto por descrição na API DELPI? | Explica `/products/search?description=` **e** difere de «como escrever» a descrição |
| N10 | exemplo de descrição padrão termoencolhível | Grupo **1013/1050** |
| N11 | como montar descrição de terminal forquilha | Subtipo 1008 forquilha |
| N12 | quais campos são obrigatórios na descrição de tubo isolante? | Grupo **1012** |
| N13 | diretrizes de criação de descrição de produto | Pode usar RAG agente (`diretrizes_*`) **referenciando** Normas |
| N14 | como descrever materia prima no totvs? | Visão cadastro + Normas; **sem** API de produto |

### Regressão cruzada — Normas × operacional × SQL

| ID | Pergunta | O que esperar |
|----|----------|---------------|
| X1 | como descrever terminal + estoque do 10080047 | Responde **uma** intenção por turno ou pede separar; ideal: priorizar Normas se sem código |
| X2 | normas técnicas cabo e programação produção hoje | Pergunta composta — separar ou responder em seções; produção **não** vira search |
| X3 | busque terminal m8 | **Search** catálogo — **não** Normas (N*) |
| X4 | descrição do produto 10080047 vs como descrever terminal | Turnos distintos: #19 REST vs N1 RAG |

**Automatizado (preparação do turno):** `scripts/smoke_gpt_instructions_improvements.py` (#G1–G14, #N1–N6, #N4 regressão).

---

## Download de arquivos (UI + API)

| ID | Onde | Ação | O que esperar |
|----|------|------|---------------|
| D1 | Agente → Conhecimento | Clicar **Baixar** numa fonte | Arquivo `.md`/`.txt` com nome original ou canônico |
| D2 | Projeto → Fontes | Clicar **Baixar** | Idem |
| D3 | Mensagem com anexo | Clicar **Baixar** no chip | Arquivo anexado na conversa |
| D4 | Nota de texto do agente (fonte manual) | Baixar | Exporta como `.md` |
| D5 | Fonte grande (`sql-data-api-instructions.md`) | Baixar | Arquivo completo; nome canônico no header |

**API:** `GET /chat/sources/{id}/download`, `GET /chat/attachments/{id}/download` — ver [`../api/05-projetos-fontes-anexos-artefatos.md`](../api/05-projetos-fontes-anexos-artefatos.md).

---

## Export / import bundle do agente

| ID | Ação | O que esperar |
|----|------|---------------|
| E1 | Rodar `export_agent_knowledge_bundle.py` | Pasta `domains/agents/minha-delpi-chat/` com 12 arquivos + `manifest.json` |
| E2 | Reimportar arquivos no admin do agente | Nomes canônicos (`sql-data-api-instructions.md`, …); dedup por conteúdo |
| E3 | Comparar `manifest.json` com UI do agente | Mesma contagem de fontes; nomes batem com cards |

---

## Referência — testes automatizados

Estes cenários têm cobertura em pytest / scripts do repositório:

| Área | Onde rodar |
|------|------------|
| Smoke operacional | `scripts/smoke_operational_questions.py` |
| GPT_instructions + SQL produção + fontes | `scripts/smoke_gpt_instructions_improvements.py` |
| Regressão unitária SQL operacional | `tests/unit/domain/services/test_chat_sql_operational_intent_service.py`, `test_chat_sql_production_query_service.py` |
| Intent Normas / descrição técnica | `tests/unit/domain/services/test_chat_technical_description_intent_service.py` |
| Download anexos/fontes | `tests/unit/application/use_cases/test_download_chat_file_use_cases.py` |
| Sync / ingest GPT_instructions (agente) | `scripts/sync_gpt_instructions_knowledge.py --ingest` |
| Sync conhecimento global | `scripts/sync_gpt_instructions_knowledge.py --sync-global --ingest-global` |
| Export bundle agente | `scripts/export_agent_knowledge_bundle.py` |
| Refinamento paginação | `tests/unit/domain/services/test_chat_operational_refinement_service.py` |
| Turn preparation paginação | `tests/unit/application/services/test_chat_turn_preparation_pagination_refinement.py` |
| Consolidação paginada | `tests/unit/domain/services/test_chat_pagination_consolidation_service.py`, `tests/unit/application/services/test_chat_paginated_external_action_service.py` |
| Apresentação frontend | `plugins/minha-delpi-chat/scripts/verify-pagination-presentation.ts` |
| Lousa / canvas | `tests/unit/application/services/test_chat_canvas_content_service.py` |
| Small talk | `tests/unit/application/services/test_chat_small_talk_service.py` |
| Meta composta | `tests/unit/application/services/test_chat_meta_direct_answer_service.py` |
| OV / datas | `tests/unit/domain/services/test_chat_analysis_intent_action_planning.py` |

```bash
# GPT/SQL + Normas + visibilidade (casos G*, N*, G8)
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  python scripts/smoke_gpt_instructions_improvements.py

# Intent Normas (unitário)
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  pytest tests/unit/domain/services/test_chat_technical_description_intent_service.py -q

# Backend (no container)
docker exec delpi-minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_operational_refinement_service.py \
  tests/unit/application/services/test_chat_turn_preparation_pagination_refinement.py \
  tests/unit/domain/services/test_chat_pagination_consolidation_service.py \
  tests/unit/application/services/test_chat_paginated_external_action_service.py -q

# Frontend (script de verificação)
docker run --rm -v "$(pwd)/plugins/minha-delpi-chat:/app" -w /app node:22-alpine \
  npx tsx scripts/verify-pagination-presentation.ts
```

---

## Anotações do teste

Use esta seção para marcar o que passou/falhou durante a validação manual.

| # | OK | Observação |
|---|:--:|------------|
| G1 | ☐ | |
| G2 | ☐ | |
| G3 | ☐ | |
| G4 | ☐ | |
| G5 | ☐ | |
| G6 | ☐ | |
| G7 | ☐ | |
| G8 | ☐ | |
| G9 | ☐ | |
| G10 | ☐ | |
| G11 | ☐ | |
| G12 | ☐ | |
| G13 | ☐ | |
| G14 | ☐ | |
| N1 | ☐ | |
| N2 | ☐ | |
| N3 | ☐ | |
| N4 | ☐ | |
| N5 | ☐ | |
| N6 | ☐ | |
| N7 | ☐ | |
| N8 | ☐ | |
| N9 | ☐ | |
| N10 | ☐ | |
| N11 | ☐ | |
| N12 | ☐ | |
| N13 | ☐ | |
| N14 | ☐ | |
| X1 | ☐ | |
| X2 | ☐ | |
| X3 | ☐ | |
| X4 | ☐ | |
| D1 | ☐ | |
| D2 | ☐ | |
| D3 | ☐ | |
| D4 | ☐ | |
| D5 | ☐ | |
| E1 | ☐ | |
| E2 | ☐ | |
| E3 | ☐ | |
| … | ☐ | |
