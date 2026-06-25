# Status atual — PAC Qualidade (jun/2026)

> Atualizar este arquivo ao concluir cada onda do [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md).

---

## Resumo executivo

| Camada | Maturidade | Nota |
|---|---|---|
| Modelo de dados + migrations | Alta | V001–V007 no plugin `quality-action-plans` |
| API PAC (`api-pac-quality`) | Média-alta | **Produção** (agente GPT); paridade de escrita — validar localmente só na **api-delpi** |
| API consolidada (`api-delpi`) | Média-alta | **Canônica** para plugin + homologação local (V007) |
| Plugin MFE | Média | Fluxo analista ok; imagem `delpi-quality-action-plans` reconstruída |
| Agente GPT | Média-alta | OpenAPI **produção** reimportado pelo usuário (jun/2026) |
| Homologação formal | Média | H1/H3 smoke OK; H2 GPT pendente |
| Integrações (TOTVS, notificações) | Não iniciado | Previsto onda 4+ |

**Estimativa global:** ~55% do caminho até excelência operacional.

---

## Migrations aplicadas

| Versão | Conteúdo | Status |
|---|---|---|
| V001 | Tabelas core PAC | Implementada |
| V002 | Sequência `PAC-YYYY-####` | Implementada |
| V003 | Knowledge layer (`similarity_index`, `solution_patterns`) | Implementada |
| V004 | `branch_code` | Implementada |
| V005 | `nonconformity_scope` | Implementada |
| V006 | `rnc_8d`, evidências com arquivo, equipe, trilha detecção | APLICADA (local + prod) |
| V007 | `action_id` em evidências (vínculo com ação do plano) | APLICADA (local + prod) |

---

## APIs — rotas principais

### api-delpi (`/apps/api-delpi/quality/action-plans`)

| Área | Rotas | Plugin |
|---|---|---|
| Dashboard / lista / detalhe / atrasados | GET | Sim |
| Criar plano, Ishikawa, 5 Porquês, ações, status, eficácia | POST/PUT/PATCH | Sim |
| Relatório 8D | PUT `/rnc-8d`, GET `/export/rnc-8d` | Sim |
| Evidências | GET/POST/DELETE `/evidences`, download arquivo | Sim |
| Inteligência (similaridade, padrões) | GET `/similar-cases`, GET `/recurrence` | Parcial (Onda 2.1–2.3) |

### api-pac-quality

| Área | Rotas | Agente GPT |
|---|---|---|
| CRUD transacional | Sim | Sim |
| Inteligência | `/intelligence/*` | Sim |
| 8D + evidências | Sim | Sim |

---

## Plugin — telas

| Tela | Status |
|---|---|
| Dashboard (KPIs + gráficos) | Implementada |
| Lista + filtros básicos | Implementada |
| Novo plano | Implementada (`customer_template` + registro NC) |
| Detalhe (pipeline, Ishikawa, 5 Porquês, ações, histórico) | Implementada |
| Relatório 8D + export Excel | Implementada (após ativar `rnc_8d`) |
| Painel de evidências | Implementada (vínculo opcional com ação) |
| Atrasados | Implementada |
| Recorrência / soluções testadas / timeline rica | Parcial (recorrência + similar-cases ok) |
| Edição completa do plano | Implementada (PATCH identificação no detalhe) |

---

## Débitos conhecidos

1. Template Excel `rnc_8d_template.xlsx` fora do git — copiar no deploy.
2. ~~Export 8D sem imagens na aba Anexos.~~ Imagens embutidas na aba `Anexos(Evidencias)` (requer Pillow).
3. Documentação `quality-action-plans-pac.md` atualizada (V006/V007 + rotas 8D/evidências).
4. ~~Agente sem rotas de evidência e 8D.~~ Paridade API PAC — OpenAPI reimportado em **produção** (validar com `check-pac-api-server.sh`).
5. Indicadores executivos do playbook (tempo médio, reincidência, eficácia por tipo) ausentes no dashboard.
6. ~~Índice `quality_case_similarity_index` não atualizado pela api-delpi.~~ Sincronizado em create / 5 Porquês / eficácia (paridade api-pac).

---

## Próxima onda recomendada

**Onda 1 — fechamento:** H1/H3/H4 smoke OK local; **H2** aguarda deploy api-pac produção + `run_h2_pac_api_smoke.py`.

### Stack local (canônico — plugin + api-delpi)

```bash
cd infra && docker compose -f docker-compose.dev.yml build api-delpi quality-action-plans
docker compose -f docker-compose.dev.yml up -d --force-recreate api-delpi quality-action-plans
bash ../api-delpi/scripts/deploy_rnc_8d_template.sh
bash ../scripts/homologacao/check-quality-action-plans.sh
export TOKEN="<jwt>" && python3 ../scripts/homologacao/run_h1_api_smoke.py
```

A **api-pac-quality** não sobe no dev local — mesmo Postgres; após passar na api-delpi, deploy em produção (`pac-api.minhadelpi.com.br`) para o agente GPT.
