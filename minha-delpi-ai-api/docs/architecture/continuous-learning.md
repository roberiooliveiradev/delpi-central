# Aprendizagem contínua — Fase 1 (fundação)

Implementação inicial do playbook `docs/roadmap/playbook-aprendizagem-continua.md`.
O objetivo é deixar o chat mais inteligente com o uso, **sem contaminar** o modelo:
aprender = observar + validar + armazenar + recuperar (playbook §2).

Esta fase entrega a **fundação não paramétrica**: candidatos de conhecimento
revisáveis, glossário/typos aprendidos por escopo, governança (safety + human-in-the-loop)
e aplicação das regras aprovadas na normalização base. Tudo atrás de feature flags,
**ligado por padrão** no Docker (promoção continua exigindo revisão admin).

## Componentes

| Camada | Componente | Papel |
|---|---|---|
| Domínio | `ChatVocabularyLearningService` | Detecta definição explícita ("quando eu falar X é Y", "X significa Y") e candidatos de normalização (typos). Puro/sem DB. |
| Domínio | `ChatLearningSafetyGuard` | Bloqueia aprendizado tóxico/sensível: segredos, PII (CPF/CNPJ/e-mail/telefone), códigos operacionais e dados de preço/cliente (playbook §7, §26). |
| Domínio | `ChatMessageNormalizationService` | Ganhou registro de **regras aprendidas** (`set_learned_rules`/`clear_learned_rules`) aplicadas após as regras estáticas. Permanece puro. |
| Aplicação | `ChatKnowledgeCandidateService` | Orquestra captura: safety → dedup/evidência → confiança → status. Promove candidato a termo de vocabulário (playbook §14, §15, §27). |
| Aplicação | `ChatLearningCaptureService` | Captura candidatos a partir de **feedback negativo** e de **definições explícitas ditas no turno** ("quando eu falar X é Y"), com isolamento por SAVEPOINT. |
| Aplicação | `ChatLearnedNormalizationService` | Carrega termos aprovados (cache TTL) e injeta as regras no normalizador base. |
| Domínio | `ChatUserMemoryDurabilityService` | Decide, de forma conservadora e de alta precisão, o que de um turno vira memória durável (preferências de estilo, dados de perfil declarados). Puro/sem DB. |
| Aplicação | `ChatUserMemoryService` | Captura memória persistente do usuário/projeto (safety + dedup/evidência, SAVEPOINT) e monta o bloco de prompt injetado no turno. |
| Domínio | `ChatTermExtractionService` | Detecta perguntas de definição ("o que é X?") e classifica termos desconhecidos (sigla/técnico/código/cliente — playbook §9, §13). Puro/sem DB. |
| Domínio | `ChatWebMeaningResearchService` | Decide elegibilidade de pesquisa web (termo público, não sensível) e monta a query (playbook §12, §35). Puro/sem rede. |
| Aplicação | `ChatGlossaryRetrievalService` | Carrega definições aprovadas (cache TTL) e injeta no contexto do turno os termos do glossário citados na pergunta. |
| Aplicação | `ChatMeaningDiscoveryService` | Cascata de descoberta de significado: glossário interno → pesquisa web autorizada → candidato `term_definition` pendente (SAVEPOINT). |
| Infra | `PostgresLearningCandidateRepository` / `PostgresVocabularyTermRepository` / `PostgresMemoryItemRepository` | Persistência. |
| Infra | Tabelas `ai_learning_candidates`, `ai_vocabulary_terms` (`r0s1t2u3v4w5`), `ai_memory_items` (`s1t2u3v4w5x6`) | Esquema. |
| Interface | `GET/POST /admin/learning/candidates*`, `GET/POST /admin/learning/vocabulary`, `GET/POST /admin/learning/memory*`, `GET /admin/metrics/learning/summary` | Revisão, CRUD de termos, gestão de memória (esquecer/restaurar) e KPIs. |

## Fluxo (Fase 1)

```
Captura (best-effort):
 a) Feedback negativo  (flag CHAT_LEARNING_CAPTURE_FROM_FEEDBACK)
    → detecta definição explícita OU candidato de normalização
 b) Turno (send/stream) (flag CHAT_LEARNING_CAPTURE_FROM_TURN)
    → detecta definição explícita dita pelo usuário, isolada em SAVEPOINT
 → ChatLearningSafetyGuard (bloqueia sensível)
 → ChatKnowledgeCandidateService.register (dedup + evidência + confiança)
   → ai_learning_candidates (status: pending)

Admin revisa em /admin/learning/candidates
 → approve | reject | promote
   → promote cria ai_vocabulary_terms (approved=true)
     → ChatLearnedNormalizationService.refresh()
       → ChatMessageNormalizationService.set_learned_rules(...)

Próximos turnos (send/stream)
 → _warm_learned_normalization() (flag CHAT_LEARNING_ENABLED + APPLY_VOCABULARY)
   → normalização passa a corrigir o typo/abreviação aprendido
```

## Confiança e governança

- Confiança em `[0, 0.95]`. Evidência repetida sobe a confiança (dedup incremental).
- Status: `pending → approved/rejected → promoted` (e `auto_approved` quando habilitado).
- **Human-in-the-loop por padrão**: auto-aprovação exige `CHAT_LEARNING_AUTO_APPROVE_ENABLED=true`
  e confiança ≥ `CHAT_LEARNING_AUTO_APPROVE_MIN_CONFIDENCE` (0.95) com risco baixo.
- Toda captura no caminho de feedback é **best-effort** (try/except): nunca quebra o feedback nem o turno.

## Feature flags (`Settings`)

| Flag | Default | Efeito |
|---|---|---|
| `CHAT_LEARNING_ENABLED` | `true` | Liga a camada (captura + aplicação). `false` na env desliga. |
| `CHAT_LEARNING_APPLY_VOCABULARY` | `true` | Aplica termos aprovados na normalização (se a camada estiver ligada). |
| `CHAT_LEARNING_CAPTURE_FROM_FEEDBACK` | `true` | Captura candidatos a partir de feedback negativo. |
| `CHAT_LEARNING_CAPTURE_FROM_TURN` | `true` | Captura definição explícita dita durante o turno. |
| `CHAT_LEARNING_AUTO_APPROVE_ENABLED` | `false` | Auto-aprovar candidatos de altíssima confiança. |
| `CHAT_LEARNING_AUTO_APPROVE_MIN_CONFIDENCE` | `0.95` | Limiar de auto-aprovação. |
| `CHAT_LEARNING_VOCABULARY_MAX_RULES` | `500` | Teto de regras aprendidas aplicadas. |
| `CHAT_USER_MEMORY_ENABLED` | `true` | Liga a memória persistente do usuário (captura + injeção). |
| `CHAT_USER_MEMORY_CAPTURE` | `true` | Captura preferências/perfil duráveis ditos no turno. |
| `CHAT_USER_MEMORY_APPLY` | `true` | Injeta a memória persistente no contexto do turno. |
| `CHAT_USER_MEMORY_MAX_ITEMS` | `20` | Teto de itens de memória injetados por turno. |
| `CHAT_USER_MEMORY_RAG_INDEX` | `true` | Indexa memórias ativas no RAG por embedding. |
| `CHAT_LEARNING_GLOSSARY_RETRIEVAL` | `true` | Injeta definições do glossário citadas na pergunta. |
| `CHAT_LEARNING_GLOSSARY_CAPTURE` | `true` | Captura termo desconhecido perguntado ("o que é X?") como candidato. |
| `CHAT_LEARNING_TERM_CONFIRMATION_ENABLED` | `true` | Pede confirmação ao usuário antes de registrar significado de baixa confiança. |
| `CHAT_LEARNING_GLOSSARY_WEB_MEANING` | `true` | Pesquisa significado público na web para enriquecer o candidato. |
| `CHAT_LEARNING_GLOSSARY_MAX_TERMS` | `300` | Teto de definições carregadas/injetadas por turno. |
| `CHAT_LEARNING_GLOSSARY_RAG_INDEX` | `true` | Indexa termos aprovados como conhecimento RAG recuperável por embedding (Fase 5). |
| `CHAT_LEARNING_EVALUATION_ENABLED` | `true` | Liga casos de regressão e execução automática (Fase 6). |
| `CHAT_LEARNING_EVALUATION_BLOCK_PROMOTION` | `true` | Bloqueia promoção se casos ativos falharem com a regra simulada. |
| `CHAT_LEARNING_EVALUATION_CAPTURE_FROM_FEEDBACK` | `true` | Cria caso de regressão a partir de feedback negativo. |
| `CHAT_LEARNING_FINE_TUNING_ENABLED` | `true` | Liga curadoria/export/jobs de fine-tuning offline. |
| `CHAT_LEARNING_FINE_TUNING_CAPTURE_POSITIVE_FEEDBACK` | `true` | Captura amostra em feedback positivo (anonimizada). |

## Endpoints admin

- `GET /admin/learning/candidates?status=&type=&limit=&offset=`
- `POST /admin/learning/candidates/{id}/review` — body `{ "action": "approve|reject|promote", "term?", "normalizedTerm?", "meaning?" }`
- `GET /admin/learning/vocabulary?scope=&approved=&type=&limit=&offset=`
- `POST /admin/learning/vocabulary` — cria/edita termo aprovado (ex.: regra de typo `como vc s chama → como voce se chama`).
- `POST /admin/learning/vocabulary/reindex?limit=2000` — backfill do índice RAG do glossário (Fase 5).
- `GET /admin/learning/evaluation-cases?category=&status=&limit=&offset=`
- `POST /admin/learning/evaluation-cases` — cria caso (`input`, `category`, `expectedIntent`, …).
- `POST /admin/learning/evaluation-cases/run` — body `{ caseId? }` ou roda todos os ativos.
- `POST /admin/learning/evaluation-cases/{id}/review` — body `{ "action": "enable|disable" }`.
- `GET /admin/learning/memory?userId=&scope=&type=&status=&limit=&offset=` — lista memórias persistentes.
- `POST /admin/learning/memory/{id}/review` — body `{ "action": "forget|restore" }` (esquecer/restaurar).
- `POST /admin/learning/memory/reindex?limit=2000` — backfill do índice RAG de memórias ativas.
- `GET /admin/metrics/learning/summary?hours=168` — KPIs agregados (funil + destaques + memória).

## Memória persistente do usuário (Fase 3)

Complementa a memória de **sessão** (`ai_chat_session_memory`) com memória
**cross-sessão** por `user_id`/`project_id` em `ai_memory_items`:

- **Captura** (`ChatUserMemoryService.capture_from_turn`, best-effort + SAVEPOINT):
  só afirmações explícitas e estáveis — preferências de estilo/idioma/formato e
  dados de perfil declarados (`ChatUserMemoryDurabilityService`). Tudo passa pelo
  `ChatLearningSafetyGuard` (mensagem inteira + conteúdo) e por dedup/evidência.
  Respeita o anti-padrão "não salvar tudo que o usuário fala" (playbook §43).
- **Injeção** (`ChatTurnPreparationService`): quando ligada, um bloco
  "Memória persistente do usuário" é mesclado ao `conversation_context` do turno.
- **Governança/esquecer**: status `active → forgotten` (e `restore`), via admin
  (`/admin/learning/memory`), atendendo ao requisito de permitir apagar memória.
- Recuperação lexical: `user_id`/`project_id` + recência/evidência (`list_active_for_context`).
- Recuperação semântica (RAG): `ChatMemoryKnowledgeIndexService` indexa itens `active` com
  `source_type=user_memory`, `scope=user_memory` e `userId` no metadata; flag
  `CHAT_USER_MEMORY_RAG_INDEX` (default `true`). Backfill: `POST /admin/learning/memory/reindex`.

## KPIs (playbook §36)

`GetAdminLearningSummaryUseCase` agrega contagens dos repositórios e o
`ChatLearningMetricsService` (puro) monta o funil/derivados:

- **Funil**: criados (total e na janela `hours`), pendentes, aprovados, rejeitados,
  promovidos, taxa de aprovação (`(aprovados+promovidos)/revisados`) e taxa de
  promoção (`promovidos/total`).
- **Destaques**: definições de termo, regras de normalização (typos), candidatos
  pendentes de alta confiança e termos aprendidos ativos no vocabulário.

A faixa de KPIs aparece no topo da aba **Conhecimento → Aprendizagem** do MFE e é
informativa (falha na coleta não bloqueia a revisão).

## Glossário vivo (Fase 4)

Quando um termo do glossário aprovado (`ai_vocabulary_terms` tipo `term_definition`,
com `meaning`) aparece na pergunta, sua definição é injetada no `rag["context"]`
do turno (`ChatGlossaryRetrievalService`, cache TTL atualizado em promoção/edição).

Quando o usuário pergunta o significado de um termo desconhecido ("o que é X?"):

```
ChatTermExtractionService.detect_definition_question(message) → termo
→ se já existe no glossário interno → nada a aprender
→ senão ChatMeaningDiscoveryService:
   1. lookup interno (glossário)
   2. (autorizado) pesquisa web pública  [flag CHAT_LEARNING_GLOSSARY_WEB_MEANING]
      → WebSearchHttpGateway + ChatWebSearchSourceEvaluationService
      → só termos públicos/seguros (ChatWebMeaningResearchService.is_eligible)
   3. registra candidato term_definition (status pending) para revisão admin
```

Os candidatos entram no fluxo já existente de `/admin/learning/candidates`
(aprovar/rejeitar/promover com `meaning`), e a promoção atualiza o cache do glossário.

## RAG adaptativo — glossário indexável (Fase 5)

Além da injeção lexical da Fase 4, termos de glossário aprovados são indexados como
conhecimento recuperável pelo RAG existente (recuperação **semântica** por embedding),
com fonte citável.

`ChatGlossaryKnowledgeIndexService` faz upsert por `source_ref` estável:

```
sync_term(term)  (apenas type=term_definition)
  aprovado + ativo + com meaning → index_term:
    source_type = "glossary"
    source_ref  = "glossary:{vocabularyTermId}"
    content     = "{term}: {meaning}"  → embedding → ai_knowledge_chunks
    metadata    = {scope: global|project_source, projectId?, vocabularyTermId,
                   term, type, contentHash}
    - já existe e contentHash igual → skip
    - já existe e mudou → update_document + recria chunk (re-embed)
    - não existe → create_document + chunk
  inativo/sem meaning → deindex_term (delete_document por source_ref)
```

- **Atualização contínua:** disparado na promoção de candidato e no upsert admin de
  termo (`chat_learning_use_cases`), best-effort e isolado da transação principal.
- **Fonte citável:** documentos `sourceType=glossary` são visíveis ao cliente mesmo
  com `scope=global` (`ChatSourceVisibilityService`).
- **Backfill:** `POST /admin/learning/vocabulary/reindex` (`?limit=`) reindexa termos
  já aprovados ao habilitar a feature em uma base existente.
- **Coexistência com a Fase 4:** a injeção lexical (`ChatGlossaryRetrievalService`)
  e o chunk semântico são complementares; pode haver leve sobreposição no prompt
  quando o termo exato aparece e também é recuperado por similaridade.
- **Flag:** `CHAT_LEARNING_GLOSSARY_RAG_INDEX` (default `true`; requer também
  `CHAT_LEARNING_ENABLED`). Embedding via `LocalEmbeddingGateway`.

Repositório: novo `KnowledgeRepositoryPort.find_document_by_source_ref(source_ref,
source_type=)` para upsert por origem.

## Avaliação automática (Fase 6)

Dataset de regressão em `ai_evaluation_cases`, executado de forma determinística (sem LLM)
via `ChatEvaluationCaseRunnerService` (intenção/turno simples, normalização, flags
`mustNotUseTools`/`mustNotUseRag`, trecho de resposta direta opcional).

```
Feedback negativo (opcional) → ChatEvaluationCaseService.capture_from_negative_feedback
Admin cria caso manualmente
Promoção de candidato → ChatLearningPromotionGateService:
  simula vocabulário + regra proposta → roda casos ativos → bloqueia se falhar
POST /admin/learning/evaluation-cases/run → atualiza lastPassed / lastFailureReason
```

Categorias sugeridas: `routing`, `normalization`, `small_talk`, `security`, `memory`.
KPIs: `evaluationCasesFailing`, `evaluationCasesActive` no summary admin.

## Fine-tuning offline (Fase 7)

Pipeline de curadoria para treino **fora da API** (sem fine-tune em tempo real):

```
Feedback positivo (opcional) → amostra captured + anonimizada
Admin aprova amostras → agrupa em dataset → aprova dataset (≥3 amostras)
POST .../runs → export → train (validação) → deploy / rollback
GET .../datasets/{id}/export → JSONL {messages, intent?, category?}
```

Tabelas: `ai_fine_tuning_samples`, `ai_fine_tuning_datasets`, `ai_fine_tuning_runs`.
`ChatFineTuningAnonymizationService` redige PII/segredos antes de persistir.
`execute_run_training` valida o export e, com `CHAT_LEARNING_FINE_TUNING_OLLAMA_CREATE_ENABLED`,
cria um adaptador Ollama via Modelfile (`delpi-ft-d{dataset}-r{run}`) com exemplos aprovados.
`deploy_run` marca `active_deploy` e o chat passa a resolver o modelo via
`ChatFineTuningDeployResolverService`. Opcional: `CHAT_LEARNING_FINE_TUNING_TRAIN_WEBHOOK_URL`
dispara POST com `runId`, `datasetId`, `exportStats` após validação.

| Flag | Default |
|------|---------|
| `CHAT_LEARNING_FINE_TUNING_ENABLED` | `true` |
| `CHAT_LEARNING_FINE_TUNING_CAPTURE_POSITIVE_FEEDBACK` | `true` |
| `CHAT_LEARNING_FINE_TUNING_BASE_MODEL` | `OLLAMA_MODEL` | Modelo base para Modelfile Ollama. |
| `CHAT_LEARNING_FINE_TUNING_OLLAMA_CREATE_ENABLED` | `true` | Cria adaptador `delpi-ft-d{id}-r{run}` no Ollama após train. |

Endpoints: `/admin/learning/fine-tuning/samples`, `/datasets`, `/datasets/{id}/export`,
`/datasets/{id}/runs`, `/runs/{id}/{export|train|deploy|rollback}`.

## Dashboard e telemetria (playbook §36–§38)

- `GetAdminLearningSummaryUseCase` enriquece KPIs com `ragIndex` (documentos ativos por
  `source_type`), `dashboard.topTypoRules` (typos aprovados mais usados) e destaques RAG.
- `ChatLearningEventService` emite logs estruturados `learning_event` (promoção, memória
  criada/esquecida) para integração event-driven futura.

## Confirmação de termos ambíguos (playbook §9, §27)

Quando o usuário pergunta «o que é X?» e o significado vem da web com confiança baixa
(< 0,5), o chat pede confirmação antes de registrar o candidato:

```
"o que é OP?" → pesquisa web (se autorizada)
 → resposta direta pedindo confirmação
 → workingMemory.learningTermConfirmation
"sim" / "OP significa ordem de produção"
 → candidato term_definition (pending) + ack
```

Serviços: `ChatLearningTermAmbiguityService` (domínio),
`ChatLearningTermConfirmationService` (aplicação). Textos em `learning_content.json`.

## Fora do escopo da API

- Fine-tune paramétrico real (alteração de pesos/GPU); o adaptador Ollama injeta exemplos via SYSTEM.
