# ADR 007 — Provedores LLM plugáveis por porta

**Status:** Aceito (jul/2026)  
**Playbook:** [playbook-24-llm-provider-pluggable-jul2026.md](../../roadmap/playbook-24-llm-provider-pluggable-jul2026.md)

## Contexto

O chat dependia de Ollama para texto, embeddings e VLM. Parte do texto já usava `LlmGatewayPort`, mas configuração (`OLLAMA_*` / `VLLM_*`), warmup e status admin ainda acoplavam nomes de implementação.

Produção pode exigir API OpenAI-compatible sem reescrever o pipeline send/stream.

## Decisão

1. **Texto:** `LlmGatewayPort` + `provider_registry` com `ollama` e `openai_compatible` (aliases `vllm`, `openai`).
2. **Config unificada:** `LLM_TEXT_*` com fallback para `OLLAMA_*` / `VLLM_*`; resolução em `infrastructure/config/llm_text_config.py`.
3. **Domain:** `LlmProviderConfigService` expõe texto/embedding/visão via `AppConfigPort` — sem import de gateways.
4. **Warmup:** `llm_warmup_service` só aquece quando provider normalizado é `ollama`.
5. **Embeddings e VLM:** variáveis `EMBEDDING_PROVIDER` e `VISION_LLM_PROVIDER` declaradas; implementação plugável nas fases P2/P3.

## Consequências

- Troca de LLM de chat = env + restart + smoke.
- `VllmLlmGateway` permanece como alias de `OpenAiCompatibleLlmGateway`.
- Gate CI `audit_llm_provider_coupling.py --check` impede import direto de gateways em `domain/` e `application/`.
- Fine-tuning local (`ollama_model_create_gateway`) permanece allowlisted até P4.

## Alternativas rejeitadas

- **Um único `LLM_PROVIDER` para tudo** — embeddings e VLM têm ciclos de vida e custos diferentes.
- **`if path` por vendor no use case** — viola clean architecture; registry + composer.
