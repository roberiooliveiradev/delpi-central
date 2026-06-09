# Smoke operacional — checklist manual

Checklist de perguntas para validar o chat operacional após deploy ou alterações no pipeline de inteligência.

**Dica:** para testes multi-turno, use a **mesma conversa** — o histórico importa.

**Agente recomendado** para os cenários GPT/SQL (#G1–G8): **Minha DELPI Chat** (`agent_key=minha-delpi-chat`).

**Configuração do chat:** antes do smoke, alinhe toggles do admin ao perfil **dev** ou **prod** — [`../knowledge/chat-intelligence-settings-profiles.md`](../knowledge/chat-intelligence-settings-profiles.md).

**Ambiente local (maio/2026):** se a **api-delpi** interna estiver indisponível, mantenha o provider **desabilitado** no agente e use só **api-externa** (`https://api.transformamaisdelpi.com.br`). Cenários KPI `/supplies/*` (#6b, #34) e parte do smoke operacional dependem da api-delpi; utilitários (U1–U9) e identidade/small talk não dependem de provider.

## Smokes automatizados (API)

Executar após mudanças em contexto, chips ou presenter (com stack e Keycloak no ar):

| Script | Comando (container ou `PYTHONPATH` na API) |
|--------|---------------------------------------------|
| **Inteligência operacional (10 perguntas E2E)** | `python scripts/smoke_operational_intelligence_e2e.py` — ver [`smoke-operational-intelligence-e2e.md`](smoke-operational-intelligence-e2e.md) |
| **Playbooks produto (data + sessão ativa)** | `python scripts/smoke_playbook_product_routes.py` — ver [`../changelog/2026-06-playbook-rotas-sessao-ativa-parametros.md`](../changelog/2026-06-playbook-rotas-sessao-ativa-parametros.md) |
| **KPIs empresa (12 perguntas, sem produto)** | `python scripts/smoke_empresa_kpi_e2e.py` — ver [`smoke-operational-intelligence-e2e.md`](smoke-operational-intelligence-e2e.md#smoke-empresa--kpi-sem-produto) |
| Chips «Próximos passos» | `python scripts/smoke_follow_up_chips.py` |
| Catálogo + onboarding | `python scripts/smoke_features_catalog.py` |
| Templates de atalhos (sem código fixo) | `python scripts/smoke_shortcut_placeholders.py` |
| Product analyser (roteiro/inspeção em tabelas) | `python scripts/smoke_product_analyser_presentation.py` |
| Product analyser (HTTP opcional) | `SMOKE_BASE_URL=http://delpi-gateway python scripts/smoke_product_analyser_live.py` (SKIP se 403 no gateway) |
| Pacote atalhos (login + API + conteúdo) | `./scripts/run_chat_shortcut_homologation.sh` |
| Homologação no container | `docker exec delpi-minha-delpi-ai-api bash -c 'cd /app && PYTHONPATH=/app SMOKE_BASE_URL=http://delpi-gateway ./scripts/run_chat_shortcut_homologation.sh'` (~3 min; pausas de rate limit) |
| Última execução (31/05) | placeholders + login/perfil + catálogo + chips API — **OK** |
| Product analyser presentation (31/05) | `smoke_product_analyser_presentation.py` — **OK** (tabelas roteiro/inspeção; sem dump QP) |
| Rebuild MFE após fix frontend | `cd infra && docker compose -f docker-compose.dev.yml build minha-delpi-chat && docker compose -f docker-compose.dev.yml --profile chat up -d minha-delpi-chat` |
| Assertividade multi-turno | `python scripts/smoke_context_assertiveness_multiturn.py` |
| Onda 11 + Fase 5 (pytest + smokes) | `./scripts/run_onda11_validation.sh` |
| Visão/OCR documentos (Onda 13) | `python scripts/smoke_document_vision.py` (+ pytest `test_chat_document_vision_service.py`, `test_chat_attachment_context_service.py`) |
| Análise de desenho (Onda 12) | `python scripts/smoke_drawing_analyser.py` |
| Pacote Onda 13 (visão/OCR) | `./scripts/run_onda13_validation.sh` |

Variáveis opcionais: `SMOKE_BASE_URL`, `SMOKE_USER`, `SMOKE_PASSWORD`. Ver [`../changelog/2026-05-contexto-memoria-assertividade.md`](../changelog/2026-05-contexto-memoria-assertividade.md).

### Atalhos com preenchimento (MFE)

**Regressão crítica (maio/2026):** após `hasShortcutPlaceholders()`, `listShortcutFieldIds` deve listar campos — teste Vitest `lista campos após hasShortcutPlaceholders`. Se falhar, o clique em **Consultar produto** trava o navegador (loop `sendMessage` ↔ `onShortcutPromptRequired`).

Após alterar `plugins/minha-delpi-chat`, rebuild do container e hard refresh no navegador:

```bash
docker compose -f infra/docker-compose.dev.yml build minha-delpi-chat
docker compose -f infra/docker-compose.dev.yml up -d minha-delpi-chat
```

| Passo | Esperado |
|-------|----------|
| Home vazia (após skeleton) → **Consultar produto** | Abre diálogo «Consulta ao chat» com campo **Código do produto** (sem travar a aba) |
| Home ao abrir | Skeleton de perfis/cards até o catálogo; não deve aparecer chips «Consultas e autoajuda» genéricos e depois sumir |
| Preencher código → **Enviar pergunta** | Mensagem no histórico **sem** `{{productCode}}` |
| Atalho / quebra-gelo com placeholder → confirmar | Botão **Inserir pergunta** (texto vai ao campo de mensagem; revisar e enviar) — não usar jargão «composer» |
| Cards do agente (home) | Exibem **Ex.: 10080001** no lugar de `{{productCode}}`; clique ainda abre o diálogo |
| Colar `me fale do produto {{productCode}}` no campo de mensagem e Enter | Abre diálogo **Consulta ao chat** (não só banner de erro) |
| **Tentar novamente** com texto incompleto | Reabre o diálogo com o campo de código |

### Contexto ativo (barra acima do campo de mensagem)

| Passo | Esperado |
|-------|----------|
| Após consulta com produto (e opcionalmente filial / tabela) | Barra **Contexto** discreta com **vários chips** (produto, filial, preferências) |
| Várias respostas na mesma sessão | Chips **acumulados** dos últimos turnos (deduplicados por tipo+valor) |
| Hover no chip (desktop) | ✕ para remover só aquele item; ✕ à direita limpa tudo |
| Clique no chip de produto | Menu ou consulta (estoque, fornecedores, etc.) |

---

Se algo falhar após deploy, reinicie ou reconstrua a API:

```bash
# Dev (volume bind — restart basta)
docker compose -f infra/docker-compose.dev.yml restart minha-delpi-ai-api

# Prod/local com Dockerfile.prod (sem volume — rebuild obrigatório após mudar JSON/código)
docker compose -f infra/docker-compose.yml up -d --build minha-delpi-ai-api
```

---

## Smoke utilitário e typos (resposta direta, sem LLM)

Perguntas de hora/data/saudação passam por `ChatMessageNormalizationService` antes do matching — typos comuns são corrigidos na camada base (ex.: `hors`→`horas`, `q horas`→`que horas`, `bo dia`→`bom dia`).

| # | Pergunta | O que esperar |
|---|----------|---------------|
| U1 | que horas são? | Hora real (`America/Sao_Paulo` / `CHAT_UTILITY_TIMEZONE`); ~1 s; **sem** agentic/RAG/LLM |
| U2 | que hors são? | Idem U1 (typo corrigido) |
| U3 | q horas | Idem U1 (abreviação) |
| U4 | que dia é hoje? | Data + dia da semana |
| U5 | que dia é amanhã? | **Amanhã será** + data real (ex.: domingo, 31/05/2026); sem LLM |
| U6 | que dia foi ontem? | **Ontem foi** + data real |
| U7 | q dia | Idem U4 |
| U8 | bo dia | Saudação direta (`small_talk.json`) |
| U9 | olá | Saudação direta |

**E2E HTTP (token dev: rober / 1234):**

```bash
# Validação completa automatizada (U1–U9 + operacional + capabilities)
cd minha-delpi-ai-api && python3 scripts/run_onda11_api_e2e.py

# Persistência incremental no stream (user_persisted → activity → assistant_pending → playback → done)
cd minha-delpi-ai-api && python3 scripts/validate_stream_incremental_persistence_e2e.py

# Ou via script Onda 11 (pytest + smoke + E2E)
bash scripts/run_onda11_validation.sh
```

**Após alterar código da API em dev (volume bind):** reinicie o container para carregar o módulo Python — senão o SSE pode continuar no modo legado (`token` em vez de `user_persisted` / `playback`):

```bash
docker compose -f infra/docker-compose.dev.yml restart minha-delpi-ai-api
```

**Caso manual rápido:**
TOKEN=$(curl -s -X POST "http://localhost/auth/realms/delpi/protocol/openid-connect/token" \
  -d "client_id=delpi-central" -d "username=rober" -d "password=1234" -d "grant_type=password" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

SESSION=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Smoke utilitário"}' "http://localhost/apps/minha-delpi-ai/api/chat/sessions" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"que hors são?"}' \
  "http://localhost/apps/minha-delpi-ai/api/chat/sessions/$SESSION/messages" | python3 -m json.tool
```

**Regressão unitária:** `test_chat_utility_direct_answer_service.py`, `test_chat_message_normalization_service.py`, `test_chat_small_talk_pattern_service.py`.

Conteúdo editável: `app/content/pt-BR/assistant/utility_answers.json`, `small_talk.json`. Typos operacionais (estoque, filial, KPI) ficam em `ChatMessageNormalizationService`.

---

## Persistência incremental no stream (maio/2026)

Com `CHAT_PERSIST_BEFORE_PLAYBACK=true` (default), o turno via **stream** grava checkpoints no banco antes do texto final:

| # | O que validar | Como |
|---|---------------|------|
| P1 | Evento `user_persisted` **antes** de `activity` | `python3 scripts/validate_stream_incremental_persistence_e2e.py` ou inspecionar SSE |
| P2 | Evento `assistant_pending` antes de `done` | Idem |
| P3 | `GET .../messages` após o stream traz user + assistant | Script E2E acima |
| P4 | Plugin troca `optimistic-*` pelo `messageId` real | Enviar mensagem no chat; inspecionar estado (React) ou recarregar histórico mid-stream |
| P5 | Sem piscar ao finalizar resposta | Após `playback` + animação, a resposta **não** some e reaparece; transição direta para a mensagem na timeline (handoff `chatStreamHandoff` + `finalizeAssistantTurn`) |

**Automatizado:** `scripts/validate_stream_incremental_persistence_e2e.py` (9 checks, mensagem «olá», ~5–15 s).

**Unitário:** `tests/unit/application/services/test_chat_stream_checkpoint_service.py`, `tests/unit/application/use_cases/test_stream_incremental_persistence.py`.

**Manual rápido (SSE):**

```bash
TOKEN=$(curl -s -X POST "http://localhost/auth/realms/delpi/protocol/openid-connect/token" \
  -d "client_id=delpi-central" -d "username=rober" -d "password=1234" -d "grant_type=password" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
SESSION=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Smoke persistência"}' "http://localhost/apps/minha-delpi-ai/api/chat/sessions" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -N -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"olá"}' \
  "http://localhost/apps/minha-delpi-ai/api/chat/sessions/$SESSION/messages/stream" 2>&1 | head -40
# Esperado: event: user_persisted → activity → … → assistant_pending → playback → done
```

Ver eventos SSE em [`../api/02-chat-sessoes-mensagens.md`](../api/02-chat-sessoes-mensagens.md).

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
| 9 | *(alternativa)* clique numa linha da tabela (menu contextual) | Abre ações (detalhar, estoque, fornecedores…); «Detalhar» envia ex. `filtre filial 02 armazém 01 do produto 10080022` |

**Local:** smokes HTTP exigem `api_externa.*` (`CHAT_PREFER_API_EXTERNA_PROVIDER=true`). Chip «Ver vendas» é omitido — faturamento só em api-delpi. Ajuste de provider: `scripts/upsert_agent_provider.py` ou `PUT /chat/agents/{agentId}/providers` (não migration SQL).

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

## Interpretação de dados e resumos humanizados (#70–79)

Valida resumo textual na **primeira resposta** (roteiro, estoque, estrutura, inspeção) e **follow-ups** que interpretam dados já obtidos **sem nova API/SQL**.

**Agente:** Minha DELPI Chat — `agent_key=minha-delpi-chat`, UUID `b85edd53-2fd9-4e2f-ab17-92fd288f4f85`. Use a **mesma conversa** nos follow-ups.

**Pipeline (chat base):**

| Etapa | Comportamento |
|-------|----------------|
| Consulta inicial | `ExternalActionResultPresenter` gera `humanizedSummary` (título + linhas) persistido em `toolCalls[].metadata` |
| Follow-up (#74–78) | `ChatAnalysisIntentService.is_data_interpretation_request` → `analysis_mode`; **sem** nova tool/SQL |
| Resposta direta | `ChatDataInterpretationAnswerService.build_answer` monta markdown a partir do último `humanizedSummary` — **sem LLM** quando há linhas substantivas |
| Modo LLM (fallback) | Policy `chat-data-interpretation.md`; bloco «Contexto para interpretar os dados já obtidos»; `skipRag`; **sem** bloco `/me` (perfil RBAC) |
| Conversa vazia (#79) | `is_data_reference_without_tool_data` → resposta direta pedindo consulta prévia (~sub-segundo); **não** chama `POST /data/sql` |

**Limitação conhecida (UI):** na primeira resposta operacional, o corpo do chat pode mostrar só «Consulta SQL» / «Visualização dos dados» enquanto a tabela/gráfico carrega; os follow-ups (#74–78) já usam o resumo humanizado correto.

### Consulta inicial — resumo + tabela

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 70 | roteiro do 90260142 | Tool `GET /products/90260142/guide`; `humanizedSummary` com operações e componentes BOM; tabela abaixo |
| 70b | `90260140` ou informações completas | Ficha em tabela Campo×Valor; **roteiro** e **inspeção** em tabelas markdown (sem `Qp6=[…]`); BOM só na árvore/tabela |
| 71 | estrutura do produto 90260047 | Resumo com produto pai, componentes nível 1 e MPs; árvore/tabela abaixo |
| 72 | inspeção do produto 90260142 | Resumo do plano de inspeção (testes/características); tabela abaixo |
| 73 | estoque do produto 10080022 | Resumo com filiais, totais disponível/atual e detalhe por armazém; tabela/gráfico |

### Follow-up — interpretar dados já mostrados (sem nova consulta)

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 74 | *(após #70)* explique os dados acima | **Sem** tool call; resposta cita 90260142 e operações; **não** erro SQL 400; **não** vaza perfil/SQL |
| 75 | *(após #73)* resume | Idem — filiais e totais do 10080022 |
| 76 | *(após #70)* traduz isso | Idem — linguagem simples |
| 77 | *(após #73)* nao entendi | Idem — reformulação didática |
| 78 | *(após #71)* o que isso quer dizer | Idem para estrutura |
| 79 | explique os dados acima *(conversa vazia)* | Resposta: «Ainda não há dados nesta conversa para interpretar…»; **sem** tool; **sem** SQL |

**Automatizado (preparação do turno):** `scripts/smoke_operational_questions.py` (#70–78).

**E2E HTTP (stream, mesma sessão):**

```bash
# Token Keycloak (dev: rober/1234)
TOKEN=$(curl -s -X POST "http://localhost/auth/realms/delpi/protocol/openid-connect/token" \
  -d "client_id=delpi-central" -d "username=rober" -d "password=1234" -d "grant_type=password" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Smoke prep (#70–78) — user_id e session_id da conversa de teste
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app -e SMOKE_TOKEN="$TOKEN" minha-delpi-ai-api \
  python scripts/smoke_operational_questions.py <user_id> <session_id>
```

Sequência validada (mai/2026): #70 → #74/#76 (roteiro 90260142); #73 → #75/#77 (estoque 10080022); #79 isolado em sessão nova.

**Regressão unitária:** `tests/fixtures/chat_intelligence_regression_cases.py` (`DATA_INTERPRETATION_*`, `PRESENTER_HUMANIZED_CASES`); `tests/unit/application/services/test_chat_data_interpretation_answer_service.py`.

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

### Pesquisa na internet (`web_search` — tool nativa)

**Regressão (31/05/2026):** após falha do SearXNG (403), o gateway deve tentar DuckDuckGo — mensagem «não encontrei resultados úteis» para «WEG» indica bug no fallback.

| Passo | Esperado |
|-------|----------|
| `Pesquise na web sobre WEG` | Resumo menciona **WEG Industries** (equipamentos elétricos), não «sem resultados» |
| Novidades → **Pesquisa web com fontes e confiança** | Abre modal **Pesquisa na web** com campo **O que pesquisar**; botão **Pesquisar** envia |
| Perfil **Administrativo** → E-mail / Corrigir / Ata | Cada card abre modal (destinatário+assunto, texto, notas) antes de enviar |
| Perfil **Engenharia** → Consultar produto | Modal com **Código do produto** |
| Admin → diagnóstico | Tool `web_search`; `provider` duckduckgo ou searxng |

### Pesquisa na internet — checklist W1–W5

Requer `CHAT_WEB_SEARCH_ENABLED=true`, admin `webSearchEnabled=true` e (recomendado) `CHAT_WEB_SEARCH_SYNTHESIS_ENABLED=true`.

| ID | Pergunta | O que esperar (automático) | O que observar no chat (manual) |
|----|----------|----------------------------|----------------------------------|
| W1 | pesquise na internet sobre Python linguagem de programação | 1 tool `web_search`; **sem** `execute_external_action`; `directAnswer` | Resumo **em português** (Wikipedia PT) + URL pt.wikipedia.org; resposta **curta** (1 fonte principal — sem síntese LLM) |
| W2 | pesquise na internet sobre inflação 2026 | Idem W1 | Se `no_results`, texto honesto + conhecimento geral rotulado (não «não pesquiso na internet») |
| W3 | pesquise na internet sobre a empresa TYCO | Idem W1 + stage `web_search_synthesis` quando ≥2 fontes | Resposta **estruturada** (seções, linha do tempo, conclusão); botão **Fontes · N** abre painel de atividade; links inline no texto |
| W4 | *(após W3)* | `adminDebug.pipeline.stages` inclui `web_search_synthesis` | Latência maior (~30–90s com Ollama CPU) é esperada na síntese |
| W5 | *(dev com SearXNG)* `CHAT_WEB_SEARCH_PROVIDER=searxng` ou `auto` sem keys pagas | `metadata.webSearchResearch.provider` = `searxng`; ≥1 URL real (não só duckduckgo.com) | Container `delpi-searxng` no ar; `curl http://localhost:8088/search?q=tyco&format=json` retorna JSON |

**Fontes na UI (W3/W1):** rodapé com badges `scope: web_search`; clique em **Fontes · N** abre drawer **Atividade · Pesquisa web** (`webSearchResearch`: queries, sites, síntese); no markdown, links externos curtos renderizam como pills (`mdc-chat-citation-badge`).

**SearXNG (dev):**

```bash
cd infra
docker compose -f docker-compose.dev.yml --profile chat up -d searxng minha-delpi-ai-api
./scripts/searxng-apply-dev-settings.sh   # se curl abaixo retornar 403 (falta format=json no container)
curl -s 'http://localhost:8088/search?q=tyco&format=json' | head -c 400
```

**403 em `format=json`:** a imagem pode substituir `infra/searxng/settings.yml` por defaults só com `html`. Rode `infra/scripts/searxng-apply-dev-settings.sh` e reinicie o container; espere HTTP 200 e JSON com `results`.

```bash
SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 \
  SMOKE_WEB_SEARCH_HTTP_TIMEOUT=240 \
  python scripts/run_onda11_6_api_e2e.py

# Pacote unitário web_search (inclui síntese, SearXNG e painel de atividade):
cd minha-delpi-ai-api && pytest \
  tests/unit/domain/services/test_web_search_query_service.py \
  tests/unit/application/services/test_chat_web_search_synthesis_service.py \
  tests/unit/application/services/test_chat_web_search_research_activity_service.py \
  tests/unit/infrastructure/gateways/test_web_search_http_gateway.py \
  tests/unit/infrastructure/gateways/test_web_search_providers.py -q
```

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
| Persistência incremental stream | `scripts/validate_stream_incremental_persistence_e2e.py` + `test_stream_incremental_persistence.py` |
| Smoke operacional | `scripts/smoke_operational_questions.py` |
| Interpretação de dados / resumos (#70–79) | `scripts/smoke_operational_questions.py` + `tests/unit/application/services/test_chat_data_interpretation_answer_service.py` + `tests/unit/domain/services/test_chat_intelligence_regression.py` |
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
| Utilitário (hora/data) + typos | `tests/unit/application/services/test_chat_utility_direct_answer_service.py`, `tests/unit/domain/services/test_chat_message_normalization_service.py` |
| Rótulos api-delpi | `tests/unit/application/services/test_chat_action_label_service.py`, `tests/unit/infrastructure/content/test_content_service.py` |
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
| 70 | ☑ | roteiro 90260142 — tool + resumo (mai/2026) |
| 71 | ☑ | estrutura 90260047 |
| 72 | ☐ | inspeção — validar manualmente se necessário |
| 73 | ☑ | estoque 10080022 — filiais/totais |
| 74 | ☑ | follow-up sem SQL; cita produto/operações |
| 75 | ☑ | resume estoque |
| 76 | ☑ | traduz roteiro |
| 77 | ☑ | nao entendi estoque |
| 78 | ☐ | estrutura — validar manualmente se necessário |
| 79 | ☑ | conversa vazia — pede consulta prévia |
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
