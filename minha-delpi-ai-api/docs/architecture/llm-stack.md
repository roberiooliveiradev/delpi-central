# Stack LLM canônico

**Status:** vigente (set/2026)  
**Regra Cursor:** [`llm-stack-centralized.mdc`](../../../.cursor/rules/llm-stack-centralized.mdc)  
**Operação:** [`../operations/llm-provider-switch.md`](../operations/llm-provider-switch.md)

## Princípio

**Um seletor:** `LLM_PROVIDER` (`ollama` | `openai_compatible`; aliases `vllm` / `openai`).

O ambiente atual usa **Kimi/OpenRouter** (`LLM_PROVIDER=openai_compatible` + `KIMI_*`). Trocar o motor é mudar o seletor e as credenciais — **não** apontar `http://ollama:11434` em use case, RAG, visão ou MFE.

Ollama só existe como **implementação de infra** escolhida pelo registry quando o provedor efetivo é `ollama`.

## Fluxo

```text
LLM_PROVIDER
  → make_llm_gateway()           texto, tools, prosa
  → make_embedding_gateway()     RAG / embeddings de actions
  → make_vision_llm_gateway()    VLM de documentos (stage_vlm)
```

Herança: se `EMBEDDING_PROVIDER` ou `VISION_LLM_PROVIDER` estão vazios, o eixo usa o mesmo valor de `LLM_PROVIDER`.

Override pontual (agente): `metadata.intelligence.llmProviderOverride` → `ChatLlmGatewayResolverService`.

## Código

| Papel | Path |
|-------|------|
| Herança de eixos | `app/infrastructure/config/llm_stack_config.py` |
| Texto | `resolve_llm_text_config` · `composition/llm_composer.py` |
| Embeddings | `resolve_embedding_config` · `composition/embedding_composer.py` |
| Visão | `resolve_vision_llm_config` · `composition/vision_llm_composer.py` · `ChatDocumentVisionStageService.stage_vlm` |
| Status admin | `GET /admin/llm/status` |

Com Kimi + modelo de embed local (`bge-m3`), o vetor fica `off` e o RAG usa palavra-chave até haver modelo `/v1/embeddings` + reindex.
