# Playbook 08 — Pesquisa Web Confiável

Projeto: Minha DELPI Chat IA  
Escopo: busca externa, fontes públicas, validação de confiabilidade, síntese, segurança e transparência.

> **Princípio:** Web para informação externa e atual. API para dados internos. RAG para conhecimento interno. LLM para síntese e escrita.

Documento de referência alinhado ao playbook operacional; implementação no **chat base** (não duplicar em agentes).

---

## Implementação (jun/2026)

| Componente | Responsabilidade |
|------------|------------------|
| `ChatWebSearchResearchService` | Fachada: intenção, planejamento, sanitização, avaliação |
| `ChatWebSearchIntentService` | Triggers, `resolve()` → tool `web_search` |
| `ChatWebSearchPlanningService` | Modos `quick`/`deep`, queries, `site:` oficial |
| `ChatWebSearchQuerySecurityService` | Remove dados sensíveis da query (§17–18) |
| `ChatWebSearchSourceEvaluationService` | `sourceType`, `qualityScore`, `sourceEvaluation` |
| `ChatWebSearchResearchActivityService` | Metadata `webSearchResearch` + `sourceQuality` |
| `ChatWebSearchSynthesisService` | Síntese multi-fonte |
| `ChatWebSearchIntegrationService` | Web + anexo, produto interno, comparação |
| MFE `ChatWebSearchResearchPanel` | Painel de atividade e fontes |

Legado detalhado: `docs/roadmap/melhorias/playbook_melhoria_pesquisa_web_minha_delpi_chat.md`.

---

## Pipeline

```
Mensagem → ChatWebSearchResearchService.should_use_web
        → ChatWebSearchQuerySecurityService.sanitize
        → ChatWebSearchPlanningService.plan
        → web_search (gateway) → SourceEvaluation → Synthesis
        → webSearchResearch na metadata
```

---

## Metadata `webSearchResearch` (exemplo)

```json
{
  "sourceCount": 4,
  "searchStatus": "success",
  "attemptedQueries": ["WEG CFW500 manual oficial", "site:weg.net CFW500 manual PDF"],
  "searchMode": "deep",
  "preferOfficial": true,
  "confidence": "high",
  "sites": [
    {
      "hostname": "weg.net",
      "sourceQuality": {
        "type": "official_manufacturer",
        "confidence": "high"
      }
    }
  ],
  "querySecurity": {
    "redacted": true,
    "warnings": ["Dados internos omitidos da consulta enviada à web."]
  }
}
```

---

## Testes de regressão

| Caso | Entrada | Esperado |
|------|---------|----------|
| W1 | pesquise na web | usa web |
| W2 | correção de texto | não usa web |
| W3 | dado interno (estoque) | não usa web |
| W4 | fonte oficial | `site:` + `preferOfficial` |
| W5 | notícia recente | query com recência |
| W6 | datasheet | intent técnico |
| W7 | sem fonte confiável | aviso em `sourceEvaluation` |
| W8 | termos em inglês | retry EN na query |
| W9 | web + anexo | `attachment_compare` |
| W10 | dado interno na pergunta | query sanitizada |
| W11 | não pesquise | bloqueio |
| W12 | fontes divergentes | modo `source_compare` |
| W13 | pesquisa profunda | modo `deep`, várias queries |
| W14 | pesquisa rápida | modo `quick` |
| W15 | dados sensíveis | redação / bloqueio |

Arquivos: `tests/fixtures/web_search_research_cases.py`, `tests/unit/domain/services/test_web_search_research.py`.

Smokes: `scripts/smoke_web_search_planning.py`, `scripts/smoke_web_search_routing.py`.

---

## Roadmap

| Fase | Status |
|------|--------|
| 1 — Transparência | Concluída (`webSearchResearch`, painel MFE) |
| 2 — Planejamento | Concluída + heurística ABNT/gov e domínio inferido |
| 3 — Avaliação de fonte | Concluída + `sourceQuality` por site |
| 4 — Integração avançada | Concluída (anexo, ERP, lousa, chips) |
| 5 — Segurança e governança | Concluída (`ChatWebSearchQuerySecurityService`, `webSearchMetrics`, feedback web, painel admin, `adminDebug.webSearch`) |

Endpoint admin: `GET /admin/metrics/web-search/summary`. Auditoria: `chat.web_search.blocked`, `chat.web_search.query_redacted`, `chat.feedback.web`, `chat.web_search.follow_up_clicked`.

---

## Resumo executivo

Pesquisar não basta; é preciso **avaliar fonte**, **mostrar transparência** e **não vazar dados internos** para buscadores. Toda melhoria neste playbook deve atualizar serviços do chat base, fixtures W* e painel de fontes no MFE.
