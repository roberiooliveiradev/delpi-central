# 06 — Integração ERP (TOTVS)

**Regra:** não inventar tabelas/campos. Classificação por evidência no código.  
**SELECT live:** não executado — Docker/TOTVS indisponível nesta sessão.

## Legenda

| Status | Significado |
|--------|-------------|
| Confirmado no código | SQL/rota/repositório existente |
| Confirmado no banco | Validado com SELECT (pendente) |
| Parcialmente confirmado | Existe via view/heurística; cadastro nativo não mapeado |
| Não encontrado | Sem evidência no repo |
| Depende do negócio | Precisa decisão / material |

---

## Inventário por necessidade do orçamento

| Dado do escopo | Status | Evidência | Notas |
|----------------|--------|-----------|-------|
| Receita Operacional Líquida | Confirmado no código | `financial_repository.py` → `GET /financial/rol`; SD2010/SD1010, SF4, SA1 | Cache `financial_rol_cache`; `D_E_L_E_T_=''` |
| Faturamento realizado | Confirmado no código | ROL + `management_revenue_monthly` (reports) + séries pedidos | |
| Pedidos em carteira | Confirmado no código | `pedidos_venda_abertos` (SC5, SF2, SD2) | |
| Clientes | Confirmado no código | `customer_repository` SA1010; propostas | |
| Grupos econômicos | Não encontrado | — | Sem `A1_GRPVEN` / termo no código |
| Vendedores | Confirmado no código | SA3010 (propostas, LMP) | |
| Segmentos | Parcialmente confirmado | `CommercialCustomerSegmentService` — heurística `weg` / `new_business` | **Não** é SX de segmento genérico |
| Unidades / filiais | Confirmado no código | Convenção `01`/`02`; `padroes-totvs/filiais.md` | Mapear nomes Jaraguá/ES |
| Centros de custo | Parcialmente confirmado | View `dbo.vw_fin_despesas_centro_custo` (`centro_custo_*`) | **Sem** SQL `CTT010` no repo |
| Contas contábeis | Parcialmente confirmado | Campo `conta_contabil` na mesma view | Lista CAPEX da planilha pode ser domínio app |
| Fornecedores | Confirmado no código | SA2010 `totvs_supplier_repository` | |
| Cargos / quadro pessoal | Não encontrado (TOTVS) | `/hr` usa Portal RH Postgres | CAPEX/pessoal RH Protheus não mapeado |
| Histórico CAPEX / imobilizado | Não encontrado | Investimento em Kaizen/TM é Postgres app | |
| Prospects | Confirmado no código (comercial) | SUS010 em propostas | Reuso a decidir |

---

## Estratégia de integração (MVP)

1. **Não escrever** no Protheus.
2. Reusar rotas existentes para baseline (ROL, clientes, fornecedores, filtros CC).
3. Espelhar mestres necessários (CC, contas CAPEX) em tabelas de domínio **ou** consultar view sob demanda com cache.
4. Qualquer SQL novo: seguir `sql-query-development.mdc` + `padroes-totvs`; documentar em seção nova se regra transversal.

## Consultas planejadas (não executadas)

```sql
-- Exemplo seguro futuro (somente leitura): centros distintos na view
SELECT DISTINCT LTRIM(RTRIM(centro_custo_codigo)) AS codigo,
       LTRIM(RTRIM(centro_custo_descricao)) AS descricao
FROM dbo.vw_fin_despesas_centro_custo WITH (NOLOCK)
WHERE centro_custo_codigo IS NOT NULL;
```

Homologação: rodar no container `delpi-api-delpi` com bind params e limite.

## Riscos

- View financeira pode não cobrir todos os CCs “de orçamento”.
- Lista de contas da planilha CAPEX ≠ plano de contas contábil TOTVS.
- Headcount não tem fonte ERP confirmada → entrada manual no MVP.
