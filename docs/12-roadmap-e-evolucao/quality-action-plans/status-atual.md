# Status atual — PAC Qualidade (jun/2026)

> Atualizar este arquivo ao concluir cada onda do [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md).

---

## Resumo executivo

| Camada | Maturidade | Nota |
|---|---|---|
| Modelo de dados + migrations | Alta | V001–V007 no plugin `quality-action-plans` |
| API PAC (`api-pac-quality`) | Média-alta | CRUD + inteligência + 8D/evidências (Onda 1) |
| API consolidada (`api-delpi`) | Média-alta | Leitura + escrita + 8D + evidências (V006) |
| Plugin MFE | Média | Fluxo analista ok; visão executiva incompleta |
| Agente GPT | Média | Documentado; desalinhado com 8D/evidências |
| Homologação formal | Baixa | Sem roteiro executado ponta a ponta |
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
| V006 | `rnc_8d`, evidências com arquivo, equipe, trilha detecção | Implementada — **confirmar em cada ambiente** |
| V007 | `action_id` em evidências (vínculo com ação do plano) | Implementada — **confirmar em cada ambiente** |

---

## APIs — rotas principais

### api-delpi (`/apps/api-delpi/quality/action-plans`)

| Área | Rotas | Plugin |
|---|---|---|
| Dashboard / lista / detalhe / atrasados | GET | Sim |
| Criar plano, Ishikawa, 5 Porquês, ações, status, eficácia | POST/PUT/PATCH | Sim |
| Relatório 8D | PUT `/rnc-8d`, GET `/export/rnc-8d` | Sim |
| Evidências | GET/POST/DELETE `/evidences`, download arquivo | Sim |
| Inteligência (similaridade, padrões) | — | **Não** (só agente) |

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
| Recorrência / soluções testadas / timeline rica | **Não** |
| Edição completa do plano | Implementada (PATCH identificação no detalhe) |

---

## Débitos conhecidos

1. Template Excel `rnc_8d_template.xlsx` fora do git — copiar no deploy.
2. ~~Export 8D sem imagens na aba Anexos.~~ Imagens embutidas na aba `Anexos(Evidencias)` (requer Pillow).
3. Documentação `quality-action-plans-pac.md` atualizada (V006/V007 + rotas 8D/evidências).
4. ~~Agente sem rotas de evidência e 8D.~~ Paridade API PAC entregue — reimportar OpenAPI no GPT.
5. Indicadores executivos do playbook (tempo médio, reincidência, eficácia por tipo) ausentes no dashboard.

---

## Próxima onda recomendada

**Onda 1 — Operação NC fechada:** aplicar V006+V007, homologar H1–H3 ([HOMOLOGACAO.md](./HOMOLOGACAO.md)), reimportar OpenAPI no GPT.
