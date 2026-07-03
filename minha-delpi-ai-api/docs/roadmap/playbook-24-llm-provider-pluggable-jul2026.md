# Playbook 24 — Provedores LLM plugáveis (Ollama padrão, API externa opcional)

**Projeto:** Minha DELPI Chat IA · Pacote: `minha-delpi-ai-api`  
**Status:** P0–P4 implementados (jul/2026) · P5 backlog  
**Pré-requisitos:** [Playbook 11 — clean architecture](./playbook-11-clean-architecture-chat-api.md), [Playbook 19 — inferência LLM](./playbook-19-inferencia-llm-universal.md)

---

## 1. Objetivo

Deixar o código **pronto para trocar o motor de inferência** sem reescrever o pipeline do chat:

| Requisito | Significado |
|-----------|-------------|
| **Ollama continua padrão** | Dev/homolog CPU e Compose atual seguem funcionando sem mudança de comportamento. |
| **Troca por API externa** | Produção ou tenants podem apontar para OpenAI-compatible, Azure OpenAI, Groq, vLLM remoto, etc. |
| **Um ponto por capacidade** | Chat texto, embeddings, visão VLM e fine-tuning local têm **porta + composer** — não `if ollama` espalhado. |
| **Config declarativa** | URLs, modelos, timeouts e custos por **env + perfil de latência**; sem constantes mágicas em serviço de domínio. |

**Fora de escopo inicial:** trocar modelo de embedding sem migração pgvector; multi-tenant com provedor diferente por agente (backlog P5).

---

## 2. Diagnóstico — estado atual (jul/2026)

### 2.1 O que já está desacoplado ✅

| Camada | Módulo canônico | Comportamento |
|--------|-----------------|---------------|
| Contrato inferência texto | `LlmGatewayPort` | `generate`, `stream`, `generate_with_tools`, `supports_native_tools` |
| Wiring | `composition/llm_composer.py` → `make_llm_gateway()` | `LLM_PROVIDER=ollama \| vllm` |
| Implementações | `OllamaLlmGateway`, `VllmLlmGateway` | vLLM usa `/v1/chat/completions` (OpenAI-compatible) |
| Consumo no chat | Use cases send/stream, `ChatTurnLlmAssemblyService`, síntese operacional | Dependem só da **porta** |
| Modos Rápida/Normal/Pensador | `ChatResponseModeService` + `llm_request_context` | Modelo/tokens por turno via `LlmGenerationConfig` |
| Custo admin | `LlmCostEstimatorService` | Tabela por provider |

**Conclusão:** o **caminho crítico do chat (prosa LLM)** já suporta troca via `LLM_PROVIDER=vllm` + `VLLM_*` apontando para API externa OpenAI-compatible.

### 2.2 Acoplamentos remanescentes ao Ollama ⚠️

| # | Capacidade | Onde hoje | Impacto ao trocar só `LLM_PROVIDER` |
|---|------------|-----------|--------------------------------------|
| A1 | **Embeddings RAG** | `LocalEmbeddingGateway` → `OLLAMA_BASE_URL/api/embeddings` | RAG quebra se Ollama sumir |
| A2 | **Warmup startup** | `ollama_warmup_service.warmup_ollama()` em `root_composer` | Sempre dispara, mesmo com provider externo |
| A3 | **Visão documentos (VLM)** | `ChatDocumentVisionStageService` → `ollama_vlm` + `CHAT_DOCUMENT_VISION_OLLAMA_*` | OCR/VLM ainda no Ollama |
| A4 | **Fine-tuning deploy** | `OllamaModelCreateGateway`, `get_active_deployed_ollama_model` | Só cria modelo local Ollama |
| A5 | **Resolver de modelo** | `ChatFineTuningDeployResolverService` → repositório Ollama | Ignorado quando `vllm`; sem equivalente externo |
| A6 | **Health / system check** | `PostgresAdminSystemCheckRepository` — ramos `ollama` / `vllm` | Sem status unificado multi-capacidade |
| A7 | **Nomenclatura env** | `OLLAMA_*` usado em latência (`OLLAMA_NUM_CTX`) mesmo com `vllm` | Confusão operacional |
| A8 | **Composer único** | Só dois providers; erro `Unsupported LLM provider` | Não há `openai` explícito nem registry extensível |
| A9 | **Testes** | Vários monkeypatch `Settings.LLM_PROVIDER=ollama` | OK; falta matriz ollama × vllm × openai |

```mermaid
flowchart LR
  subgraph desacoplado [Desacoplado hoje]
    UC[Send/Stream Use Cases]
    PORT[LlmGatewayPort]
    OC[ollama_llm_gateway]
    VC[vllm_llm_gateway]
    UC --> PORT
    PORT --> OC
    PORT --> VC
  end

  subgraph acoplado [Ainda acoplado Ollama]
    RAG[SearchKnowledge / RAG]
    EMB[LocalEmbeddingGateway]
    VIS[Document Vision VLM]
    FT[Fine-tuning create]
    RAG --> EMB
    VIS --> OC2[Ollama /api/chat + images]
    FT --> OC3[Ollama /api/create]
  end
```

---

## 3. Arquitetura alvo

### 3.1 Princípio — três eixos independentes

| Eixo | Porta | Default | Troca típica |
|------|-------|---------|--------------|
| **Texto (chat)** | `LlmGatewayPort` | `ollama` | `vllm` / `openai` → URL + API key |
| **Embeddings** | `EmbeddingGatewayPort` | `ollama` | `openai` / `vllm` / serviço dedicado |
| **Visão (VLM)** | `VisionLlmGatewayPort` (nova) | `ollama_vlm` | OpenAI vision / Gemini / desligado |

Fine-tuning permanece **opcional e local** (`FineTuningModelGatewayPort`); com provider externo → modo `export_only` (já parcialmente existe).

### 3.2 Registry de providers (composition)

```text
composition/
  llm_composer.py           → make_llm_gateway()
  embedding_composer.py     → make_embedding_gateway()   # hoje só cache; gateway em external_action_composer
  vision_llm_composer.py    → make_vision_llm_gateway()  # novo
  provider_registry.py      → resolve_provider(kind, name)  # novo — único mapa
```

**Regra:** `domain/` e `application/` **nunca** importam `OllamaLlmGateway` nem leem `OLLAMA_BASE_URL` diretamente — só `ChatDomainConfigService` / `AppConfigPort`.

### 3.3 Configuração unificada (env)

| Variável (alvo) | Papel | Default |
|-----------------|-------|---------|
| `LLM_PROVIDER` | Motor de **texto** do chat | `ollama` |
| `LLM_TEXT_BASE_URL` | URL base (substitui acoplamento nome Ollama) | derivado de `OLLAMA_BASE_URL` ou `VLLM_BASE_URL` |
| `LLM_TEXT_MODEL` | Modelo default | derivado de `OLLAMA_MODEL` / `VLLM_MODEL` |
| `LLM_TEXT_API_KEY` | Bearer (vazio para Ollama local) | `VLLM_API_KEY` |
| `EMBEDDING_PROVIDER` | Motor de embedding | `ollama` |
| `EMBEDDING_BASE_URL` | URL embeddings | `OLLAMA_BASE_URL` |
| `EMBEDDING_MODEL` | ex. `bge-m3` | inalterado |
| `VISION_LLM_PROVIDER` | VLM documentos | `ollama` |
| `VISION_LLM_MODEL` | ex. `qwen2.5vl:7b` | `CHAT_DOCUMENT_VISION_OLLAMA_MODEL` (alias legado) |

**Compatibilidade:** manter `OLLAMA_*` e `VLLM_*` como **aliases** por 1–2 releases; `Settings` resolve para `LLM_TEXT_*` internamente.

### 3.4 OpenAI-compatible como estratégia padrão

| Provider externo | Implementação alvo | Notas |
|------------------|-------------------|-------|
| OpenAI / Azure / Groq / Together | `OpenAiCompatibleLlmGateway` (renomear ou generalizar `VllmLlmGateway`) | `/v1/chat/completions`, tools |
| Ollama local | `OllamaLlmGateway` | `/api/chat`, tools nativos |
| Anthropic nativo (sem compat) | `AnthropicLlmGateway` | Backlog P4 — só se necessário |
| Gemini nativo | `GeminiLlmGateway` | Backlog P4 |

---

## 4. Roadmap de implementação

### P0 — Inventário e guardrails (1 sprint, baixo risco) ✅

| # | Entrega | Onde | DoD |
|---|---------|------|-----|
| P0.1 | Script `audit_llm_provider_coupling.py --check` | `scripts/` | Falha CI se `domain/` ou `application/` importar `infrastructure.llm.ollama_*` (allowlist documentada) |
| P0.2 | ADR `adr-00N-llm-provider-ports.md` | `docs/architecture/adr/` | Três eixos texto/embedding/visão |
| P0.3 | Doc operacional «trocar para API externa» | `docs/operations/llm-provider-switch.md` | Matriz env + smoke + rollback |
| P0.4 | Smoke `scripts/smoke_llm_provider_switch.py` | `scripts/` | Com `LLM_PROVIDER=vllm`, send+stream+tools passam |

### P1 — Texto 100% configurável (1 sprint) ✅

| # | Entrega | Onde | DoD |
|---|---------|------|-----|
| P1.1 | `LlmProviderConfigService` (domain) | `domain/services/` | `resolve_text_config()` — URL, model, key, timeout sem nome «ollama» no consumidor |
| P1.2 | Generalizar `VllmLlmGateway` → `OpenAiCompatibleLlmGateway` | `infrastructure/llm/` | Aceita qualquer base URL; logs sem «vllm» no path de erro |
| P1.3 | `provider_registry.py` + extensão `llm_composer` | `composition/` | Registro: `ollama`, `openai_compatible` (alias `vllm`) |
| P1.4 | Warmup condicional | `LlmWarmupService` | Só aquece provider ativo; skip se URL externa |
| P1.5 | `GetLlmProviderStatusUseCase` | application | Retorna `text`, `embedding`, `vision` separados |
| P1.6 | Testes paridade | `tests/unit/infrastructure/llm/` | Mock HTTP: ollama vs openai_compatible mesmos cenários tools/stream |

### P2 — Embeddings plugáveis (1–2 sprints) ✅

| # | Entrega | Onde | DoD |
|---|---------|------|-----|
| P2.1 | `make_embedding_gateway()` canônico | `embedding_composer.py` | Único wiring (hoje espalhado em `external_action_composer`) |
| P2.2 | `OpenAiCompatibleEmbeddingGateway` | `infrastructure/embeddings/` | `/v1/embeddings` |
| P2.3 | `EMBEDDING_PROVIDER` | `settings.py` + Compose | Default `ollama`; doc dimensões `EMBEDDING_DIMENSIONS` |
| P2.4 | Health embedding | admin system check | Status por provider |
| P2.5 | Teste + smoke RAG | `test_search_knowledge_*` | Indexação + busca com provider mock |

**⚠ Migração de dimensão:** trocar modelo de embedding exige reindex — documentar em `docs/knowledge/`; **não** automatizar no P2.

### P3 — Visão (VLM) plugável (1 sprint) ✅

| # | Entrega | Onde | DoD |
|---|---------|------|-----|
| P3.1 | `VisionLlmGatewayPort` | `domain/ports/` | `describe_image`, `describe_pdf_page` (contrato mínimo) |
| P3.2 | `OllamaVisionLlmGateway` | infrastructure | Extrair de `ChatDocumentVisionStageService` |
| P3.3 | `OpenAiCompatibleVisionLlmGateway` | infrastructure | GPT-4o-mini vision / equivalente |
| P3.4 | `VISION_LLM_PROVIDER` + composer | settings + composition | Fallback Tesseract-only se provider off |
| P3.5 | Regressão | `test_chat_document_vision_*` | Pipeline não referencia `OLLAMA_BASE_URL` direto |

### P4 — Fine-tuning e deploy (opcional, 1 sprint) ✅

| # | Entrega | Onde | DoD |
|---|---------|------|-----|
| P4.1 | `FineTuningModelGatewayPort` | domain | `create_local_model` / `export_only` |
| P4.2 | Resolver genérico | `ChatFineTuningDeployResolverService` | Provider-aware; sem `get_active_deployed_ollama_model` no domain |
| P4.3 | UI admin | mensagem clara | «Fine-tuning local só com Ollama; com API externa use export» |

### P5 — Multi-tenant / por agente (backlog) ⬜

- Metadata do agente: `llmProviderOverride` (só se produto exigir).
- Rate limit e custo por provider no admin metrics.

---

## 5. Mapa canônico — o que NÃO fazer

| Anti-padrão | Canônico |
|-------------|----------|
| `if Settings.LLM_PROVIDER == "ollama"` em serviço de domínio | `ChatDomainConfigService.llm_provider()` + policy JSON |
| `requests.post(OLLAMA_BASE_URL...)` fora de `infrastructure/llm` ou `infrastructure/embeddings` | Gateway na infra + porta no domain |
| Novo use case importando `OllamaLlmGateway` | Injetar `LlmGatewayPort` via composer |
| Troca só no MFE ou no prompt do agente | Env + composer + smoke API |
| Remover Ollama do Compose sem embedding alternativo | `EMBEDDING_PROVIDER` explícito antes de desligar serviço `ollama` |

Alinhado a: `clean-architecture-chat-api.mdc`, `clean-code-architecture-guardrails.mdc`.

---

## 6. Checklist operacional — trocar para API externa (alvo P1)

### 6.1 Pré-requisitos

- [ ] API suporta **chat completions** + **function calling** (tools).
- [ ] Latência aceitável para modos Normal/Pensador (ver `CHAT_LLM_LATENCY_PROFILE`).
- [ ] `LLM_PROMPT_TOKEN_COST_PER_1K` / `LLM_COMPLETION_TOKEN_COST_PER_1K` configurados no admin.

### 6.2 Variáveis (exemplo OpenAI-compatible)

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://api.openai.com/v1
LLM_TEXT_MODEL=gpt-4o-mini
LLM_TEXT_API_KEY=sk-...
LLM_TIMEOUT_SECONDS=120

# Embeddings: manter Ollama local até P2
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
EMBEDDING_MODEL=bge-m3
```

### 6.3 Validação pós-deploy

```bash
# Restart obrigatório (flask sem --reload)
docker compose restart minha-delpi-ai-api

# Smokes
cd minha-delpi-ai-api
PYTHONPATH=. SMOKE_BASE_URL=http://delpi-gateway \
  SMOKE_USER=rober SMOKE_PASSWORD=1234 \
  python scripts/smoke_llm_provider_switch.py

pytest tests/unit/infrastructure/llm/ -q
```

### 6.4 Rollback

```env
LLM_PROVIDER=ollama
# remover LLM_TEXT_* overrides
```

Restart do container; conferir `GET /chat/llm-provider` (ou admin system check).

---

## 7. Gates CI (após P0–P1)

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/audit_llm_provider_coupling.py --check
pytest tests/unit/infrastructure/llm/ -q
pytest tests/unit/composition/test_llm_composer.py -q
# opcional homologação
PYTHONPATH=. python scripts/smoke_llm_provider_switch.py
```

---

## 8. Impacto infra (`delpi-central/infra`)

| Serviço Compose | Ollama padrão | Só API externa (futuro) |
|-----------------|---------------|-------------------------|
| `ollama` | **obrigatório** (chat + embeddings + VLM) | Opcional se P2+P3 com APIs externas |
| `minha-delpi-ai-api` | `LLM_PROVIDER=ollama` | `LLM_PROVIDER=openai_compatible` |
| `vllm` | Opcional (GPU local) | Pode substituir Ollama para texto |

Atualizar: `infra/README-ambiente.md`, `docs/02-infraestrutura/variaveis-de-ambiente.md`, `env.local.example`.

---

## 9. Relação com outros playbooks

| Playbook | Relação |
|----------|---------|
| [19 — inferência LLM universal](./playbook-19-inferencia-llm-universal.md) | Mais chamadas LLM por turno → **custo/latência** sobem com API externa |
| [11 — clean architecture](./playbook-11-clean-architecture-chat-api.md) | Ports + composition root |
| [Onda 11 — paridade assistentes](./inteligencia-chat-onda-11-paridade-assistentes.md) | Native tool calling — validar no provider externo |
| [Onda 13 — visão documentos](./inteligencia-chat-onda-13-skill-visao-documentos-ocr.md) | P3 deste playbook |
| [RAG calibração](./rag-context-min-score-calibracao.md) | `OLLAMA_NUM_CTX` → generalizar para perfil de latência |

---

## 10. Critérios de «pronto» (Definition of Done global)

- [ ] Zero import de `infrastructure.llm.ollama_*` fora de `infrastructure/` e `composition/` (gate P0.1).
- [ ] Troca texto Ollama → API externa **só com env** + restart + smoke verde.
- [ ] Embeddings e visão têm porta + composer documentados (mesmo que default ainda seja Ollama).
- [ ] Admin exibe status por eixo (texto / embedding / visão).
- [ ] README e guia de desenvolvimento referenciam este playbook.

---

## 11. Referências no código (baseline jul/2026)

| Artefato | Caminho |
|----------|---------|
| Porta LLM | `app/domain/ports/llm_gateway_port.py` |
| Composer | `app/composition/llm_composer.py` |
| Ollama gateway | `app/infrastructure/llm/ollama_llm_gateway.py` |
| OpenAI-compatible | `app/infrastructure/llm/vllm_llm_gateway.py` |
| Embeddings | `app/infrastructure/embeddings/local_embedding_gateway.py` |
| Settings | `app/infrastructure/config/settings.py` |
| Modos resposta | `app/domain/services/chat_response_mode_service.py` |
| Warmup | `app/infrastructure/llm/ollama_warmup_service.py` |
| Visão VLM | `app/application/services/chat_document_vision/chat_document_vision_stage_service.py` |

---

*Última atualização: jul/2026 — playbook proposto; implementação nas fases P0–P5.*
