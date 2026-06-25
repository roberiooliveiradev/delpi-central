# Homologação — PAC Qualidade

> Roteiro para validar excelência operacional antes de declarar uma onda concluída.  
> Executar com dados **anonimizados**; nunca usar PII real em ambiente de dev compartilhado.

---

## Pré-requisitos

- [ ] Migration V006 **e V007** aplicadas (`quality-action-plans`)
- [ ] Template `rnc_8d_template.xlsx` no servidor (`PAC_EVIDENCE_UPLOAD_DIR` / pasta de templates)
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
python3 scripts/homologacao/run_h1_api_smoke.py
# ou: BASE_URL=https://minhadelpi.com.br python3 scripts/homologacao/run_h1_api_smoke.py
```

Cria plano `[H1-SMOKE]`, preenche 8D, evidências com `action_id`, exporta Excel e avança status. Anote `PLAN_ID` para H3 ou remova manualmente após validar no plugin.

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

---

## Registro de execução

| Data | Ambiente | Executor | Cenários | Resultado | Observações |
|---|---|---|---|---|---|
| | | | H1–H3 | | |

---

## Critério de go-live (Onda 1)

Todos **H1, H2, H3** passam sem workaround manual (planilha paralela, e-mail fora do sistema).

Qualidade assina checklist; TI arquiva evidência (screenshot + código PAC) no ticket de release.
