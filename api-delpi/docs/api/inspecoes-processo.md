# Inspeções de Processo — `/inspecoes-processo`

Consultas operacionais de **inspeção em processo** (QIP), alimentadas pelo **TOTVS Protheus**.

**Permissão:** `inspecoes-processo.view`, `inspecoes-processo.view.filial-01`, `inspecoes-processo.view.filial-02` ou `api-delpi.access`

**Validação por filial:** usuários com permissão apenas de uma filial recebem `403` ao consultar a outra (exceto superadmin ou `inspecoes-processo.view`).

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

Parâmetro comum:

| Parâmetro | Descrição |
|---|---|
| `branch` | Filial `01` ou `02` (obrigatório em todas as rotas) |

Plugin consumidor: `plugins/inspecoes-processo` · Auditoria: [ESPECIFICACAO-AUDITORIA-APONTAMENTOS.md](../../../docs/12-roadmap-e-evolucao/inspecoes-processo/ESPECIFICACAO-AUDITORIA-APONTAMENTOS.md).

---

## Endpoints

| Método | Rota | `meta.shape` | Descrição |
|---|---|---|---|
| GET | `/inspecoes-processo/resumo` | `scalar` | KPIs da filial |
| GET | `/inspecoes-processo/ranking-ensaio` | `list` | Ranking por ensaio |
| GET | `/inspecoes-processo/por-produto` | `list` | Ranking por produto |
| GET | `/inspecoes-processo/por-operacao` | `list` | Ranking por operação |
| GET | `/inspecoes-processo/por-ensaiador` | `list` | Ranking por ensaiador |
| GET | `/inspecoes-processo/historico` | `paged_list` | Histórico por OP (janela de 12 meses) |
| GET | `/inspecoes-processo/historico/detalhe` | `object` | Detalhe/medições da OP |
| GET | `/inspecoes-processo/auditoria-apontamentos` | `paged_list` | Apontamentos com inspeção amarrada sem QPR |

---

## GET `/inspecoes-processo/historico`

**Query:**

| Parâmetro | Obrigatório | Descrição |
|---|---|---|
| `branch` | sim | `01` \| `02` |
| `ordem_producao` | um dos dois | Filtro por OP |
| `codigo_produto` | um dos dois | Filtro por produto |
| `page` | não | Página (≥ 1, default 1) |
| `page_size` | não | 1–50 (default 25) |
| `resultado` | não | `A` \| `R` \| `T` (API; a UI da 1ª entrega não expõe) |
| `data_inicio` / `data_fim` | não | Opcional; `data_inicio` nunca anterior aos **últimos 12 meses** |

**`meta.operationId`:** `get_inspecoes_processo_historico`  
**`meta.entity`:** `inspecoes_processo_historico`

Sem OP nem produto a API rejeita a busca (evita full scan no TOTVS). A UI exibe a 1ª página (25) na hora e pré-carrega páginas seguintes em cache local.

---

## GET `/inspecoes-processo/auditoria-apontamentos`

**Query:**

| Parâmetro | Obrigatório | Descrição |
|---|---|---|
| `branch` | sim | `01` \| `02` |
| `data` | não | Data de produção `YYYY-MM-DD` (default: hoje) |
| `page` | não | Página (≥ 1, default 1) |
| `page_size` | não | 1–100 (default 50) |

**`meta.operationId`:** `get_inspecoes_processo_auditoria_apontamentos`  
**`meta.entity`:** `inspecoes_processo_auditoria_apontamentos`

**Regra:** lista apontamentos do dia (`vw_Apontamentos_Eficiencia`) e confronta se o **mesmo operador** lançou ensaio em `QPR010` para a mesma OP+operação (matrícula `QPR_ENSR` → login via view por ensaiador).

**Campos `data`:**

| Campo | Descrição |
|---|---|
| `summary.apontamentos_total` | Linhas agregadas no dia (operador + OP + operação) |
| `summary.operadores_pendentes` | Operadores distintos sem inspeção própria |
| `summary.apontamentos_pendentes` | Linhas em que o mesmo operador não inspecionou |
| `summary.ops_operacoes_pendentes` | Pares OP+operação com pelo menos uma pendência |
| `summary.apontamentos_com_inspecao` | Linhas em que o mesmo operador inspecionou |
| `items[]` | Apontamentos do dia (pendências primeiro) |
| `data` | Data efetiva da consulta |
| `page` / `page_size` / `has_next` | Paginação |

Campos principais de cada item: `cod_operador`, `login_operador`, `nome_operador`, `op`, `produto`, `operacao`, `centro_trabalho`, `hora_inicio`, `hora_final`, `qtd_apontamentos`, `operador_inspecionou`, `tem_inspecao_na_op_operacao`.

### Exemplo

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-processo" \
     "http://localhost/apps/api-delpi/inspecoes-processo/auditoria-apontamentos?branch=01&data=2026-07-13" \
  | jq '.meta.operationId, .data.summary, .data.items[0]'
```
