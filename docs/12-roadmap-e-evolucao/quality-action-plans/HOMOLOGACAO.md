# Homologação — PAC Qualidade

> Roteiro para validar excelência operacional antes de declarar uma onda concluída.  
> Executar com dados **anonimizados**; nunca usar PII real em ambiente de dev compartilhado.

---

## Pré-requisitos

- [ ] Migration V006 **e V007** aplicadas (`quality-action-plans`)
- [ ] Template `rnc_8d_template.xlsx` no servidor (`PAC_EVIDENCE_UPLOAD_DIR` / pasta de templates)
- [ ] Volume persistente de evidências PAC (`${DELPI_DATA_HOST_DIR}/pac-evidences` → `/app/data/pac-evidences` no `api-delpi`)
- [ ] Plugin publicado (`remoteEntry.js` 200)
- [ ] JWT com `quality-action-plans.read` + `.write`
- [ ] `PAC_QUALITY_API_KEY` configurada (testes do agente)

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality-action-plans
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin quality-action-plans  # V007 = APLICADA
bash api-delpi/scripts/deploy_rnc_8d_template.sh
cd plugins/quality-action-plans && npm run build
bash scripts/homologacao/check-quality-action-plans.sh
# Produção (agente GPT) — opcional após deploy api-pac:
# bash scripts/homologacao/check-pac-api-server.sh
```

### Smoke H1 automatizado (**api-delpi** + JWT)

Homologação local e plugin usam **somente** a api-delpi. A api-pac-quality é deploy de produção para o GPT.

```bash
export TOKEN="<jwt quality-action-plans.read/write>"
# ou, em dev local com api-delpi:
export TOKEN="$(grep '^API_DELPI_INTERNAL_SERVICE_TOKEN=' infra/.env | cut -d= -f2)"
python3 scripts/homologacao/run_h1_api_smoke.py
python3 scripts/homologacao/run_h1_api_smoke.py --h3   # inclui fechamento H3
# ou: BASE_URL=https://minhadelpi.com.br python3 scripts/homologacao/run_h1_api_smoke.py
```

Cria plano `[H1-SMOKE]`, preenche 8D, evidências com `action_id`, exporta Excel e avança status. Anote `PLAN_ID` para H3 ou remova manualmente após validar no plugin.

### Smoke H2 — agente GPT (**api-pac-quality** produção)

> **Adiado** até a Onda 1 estar 100% na api-delpi e o agente ser re-sincronizado. Homologação corrente é **somente api-delpi local** (H1, H3, H4, H5, H6).

Pré-requisito futuro: deploy recente no srv-api (`check-pac-api-server.sh` sem rotas faltando).

```bash
# Gate deploy (OpenAPI produção)
bash scripts/homologacao/check-pac-api-server.sh

# Fluxo automatizado (paridade plugin via api-delpi local)
export PAC_QUALITY_API_KEY="<token do srv-api>"
export DELPI_TOKEN="$(grep '^API_DELPI_INTERNAL_SERVICE_TOKEN=' infra/.env | cut -d= -f2)"
python3 scripts/homologacao/run_h2_pac_api_smoke.py
```

Valida: `search_similar_cases` → criar plano PAC → visível no plugin → Ishikawa/5 Porquês/ações → evidência → 8D/export.

### Smoke H4 — plano interno (api-delpi)

```bash
python3 scripts/homologacao/run_h4_internal_smoke.py
```

Cria NC `internal` sem template `rnc_8d`.

### Smoke Onda 1 — gate de fechamento (**api-delpi**)

```bash
chmod +x scripts/homologacao/run_onda1_gate.sh
bash scripts/homologacao/run_onda1_gate.sh
# Casos anonimizados (1.10) isolados:
export TOKEN="$(grep '^API_DELPI_INTERNAL_SERVICE_TOKEN=' infra/.env | cut -d= -f2)"
python3 scripts/homologacao/run_onda1_anonymized_cases.py
```

### Smoke Onda 2 — recorrência e padrões (**api-delpi**)

```bash
export TOKEN="$(grep '^API_DELPI_INTERNAL_SERVICE_TOKEN=' infra/.env | cut -d= -f2)"
python3 scripts/homologacao/run_onda2_local_smoke.py
```

Valida: dois planos com mesma `recurrence_key` aparecem em `GET /recurrence`; `GET /solution-patterns` responde com contrato paginado; `GET /evidences/search?q=…` retorna envelope paginado.

### Smoke Onda 6 — inteligência avançada (**api-delpi**)

```bash
export TOKEN="$(grep '^API_DELPI_INTERNAL_SERVICE_TOKEN=' infra/.env | cut -d= -f2)"
python3 scripts/homologacao/run_onda6_intelligence_smoke.py
```

Valida: `GET /intelligence/knowledge-graph` (6.5), `POST /intelligence/recurrence-opening-assessment` (6.4), `POST /intelligence/suggest-evidence-tags` (6.3).

---

## Cenários obrigatórios (Onda 1)

### H1 — Abertura NC externa crítica

| Passo | Ação | Esperado |
|---|---|---|
| 1 | Criar plano: escopo `external`, severidade `critical`, filial `01` | Código `PAC-YYYY-####` |
| 2 | Ativar template `rnc_8d` | `customer_template = rnc_8d` |
| 3 | Preencher identificação NC (cliente, produto, registro cliente) | Campos persistidos |
| 4 | Registrar contenção (3 áreas se aplicável) | `template_payload` atualizado |
| 5 | Ishikawa com ≥ 2 hipóteses por eixo relevante | GET detalhe ok |
| 6 | 5 Porquês ocorrência + detecção | Ambas trilhas salvas |
| 7 | Criar ações: contenção, corretiva, preventiva, verificação | `cause_track` quando aplicável |
| 8 | Anexar ≥ 2 evidências (PDF + imagem); vincular imagem a uma ação (`action_id`) | Listagem + download + coluna ação ok |
| 9 | Exportar planilha 8D | Arquivo `.xlsx` abre; aba `Anexos(Evidencias)` contém a foto |
| 10 | Avançar status até `waiting_validation` | Pipeline correto |

### H2 — Agente GPT (mesmo caso, fluxo paralelo)

| Passo | Ação | Esperado |
|---|---|---|
| 1 | Colar descrição anonimizada no GPT | Extrai cliente/produto/sintoma |
| 2 | Agente chama `search_similar_cases` | Cita casos no chat |
| 3 | Confirmar e criar plano via API | Plano visível no plugin |
| 4 | Gravar Ishikawa + 5 Porquês via API | Paridade com plugin |
| 5 | Anexar evidência via API PAC | Arquivo no detalhe do plugin |
| 6 | Gravar bloco 8D via API PAC | Export idêntico ao H1 |

### H3 — Eficácia e fechamento

| Passo | Ação | Esperado |
|---|---|---|
| 1 | Marcar ações como concluídas | Status `completed` |
| 2 | Registrar revisão de eficácia `effective` | Histórico atualizado |
| 3 | Fechar plano `completed` | Sai de “abertos” no dashboard |
| 4 | Verificar índice de similaridade | Entrada em `quality_case_similarity_index` |

---

## Cenários recomendados (Onda 2+)

| ID | Cenário | Onda |
|---|---|---|
| H4 | Plano interno (`internal`) — sem 8D | 1 |
| H5 | Detectar recorrência (mesmo produto + modo falha) | 2 |
| H6 | Painel casos similares no detalhe | 2 |
| H7 | Dashboard: tempo médio fechamento | 3 |
| H8 | Filtro por responsável + atrasados | 3 |
| H9 | Reabrir plano cancelado com motivo | 4 |
| H10 | Notificação de ação vencendo em 48 h | 4 |
| H11 | Aprovação de eficácia (submit → approve/reject) | 4 |
| H12 | Chat Minha DELPI — skill PAC + modo só consulta | 5 |
| H13 | Evals agente GPT — 20 cenários anonimizados (≥ 90%) | 5 |

### H13 — Evals agente GPT (Onda 5.4)

| Passo | Ação | Esperado |
|---|---|---|
| 1 | CI: catálogo válido | `run_pac_agent_eval.py --check-catalog` exit 0 |
| 2 | Rodar EVAL01–EVAL20 no Custom GPT (produção) | Salvar respostas em `eval_responses.json` |
| 2b | Gerar esqueleto | `run_pac_agent_eval.py --export-template eval_responses.json` |
| 3 | Pontuar | `run_pac_agent_eval.py --score-file eval_responses.json --min-pass-rate 0.9` |
| 4 | Verificar `similar_cases_decision_log` | Agente cita `influence_factors` ao usar histórico |

```bash
cd api-pac-quality
.venv/bin/python scripts/run_pac_agent_eval.py --check-catalog
.venv/bin/pytest tests/unit/test_pac_agent_eval_cases.py tests/unit/test_run_pac_agent_eval_script.py -q

# Ou, a partir do delpi-central (gate CI):
bash scripts/homologacao/check-pac-agent-eval.sh
# Pontuação após homologação manual no GPT:
PAC_EVAL_RESPONSES_FILE=/caminho/eval_responses.json bash scripts/homologacao/check-pac-agent-eval.sh
```

---

### H12 — Chat Minha DELPI (skill PAC, Onda 5.6–5.7)

Pré-requisitos: agente com provider `api-delpi` habilitado; OpenAPI reimportado (`sync_api_delpi_openapi.py`).

| Passo | Ação | Esperado |
|---|---|---|
| 1 | Agente analista: `allowRead` + `allowWrite` no provider | Skill `quality-action-plans-delpi` ativa; writes após confirmação |
| 2 | Perguntar «dashboard dos planos PAC» | Action `get_quality_action_plans_dashboard` |
| 3 | Agente liderança: `allowRead` only (`allowWrite: false`) | `qualityActionPlansReadOnly`; sem tools POST |
| 4 | Pedir «criar plano PAC» no agente liderança | Recusa orientando plugin/analista |

Gates CI (minha-delpi-ai-api):

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/audit_api_delpi_pac_onda1.py --check
.venv/bin/python -m pytest tests/unit/domain/skills/test_chat_skill_registry.py \
  tests/unit/domain/services/test_chat_quality_action_plans_access_service.py \
  tests/unit/application/services/test_pac_quality_auto_tier_c_selection.py -q
```

---

## Registro de execução

| Data | Ambiente | Executor | Cenários | Resultado | Observações |
|---|---|---|---|---|---|
| 2026-06-24 | local (api-delpi) | agente CI | H1 | OK | `run_h1_api_smoke.py` — plano PAC-2026-0003; 680 KB export xlsx; token interno |
| 2026-06-24 | local (api-delpi) | agente CI | H3 | OK | `--h3` — PAC-2026-0004/0005; índice `quality_case_similarity_index` validado |
| 2026-06-25 | local (api-delpi) | agente CI | H4 | OK | `run_h4_internal_smoke.py` — PAC-2026-0007 internal |
| | | | H2 (GPT prod) | bloqueado | OpenAPI prod sem rnc-8d/evidences; `check-pac-api-server.sh` falha — **deploy srv-api** + API key válida |

---

## Critério de go-live (Onda 1)

Todos **H1, H2, H3** passam sem workaround manual (planilha paralela, e-mail fora do sistema).

Qualidade assina checklist; TI arquiva evidência (screenshot + código PAC) no ticket de release.
