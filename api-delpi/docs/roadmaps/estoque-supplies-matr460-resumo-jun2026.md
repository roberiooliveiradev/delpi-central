# Estoque Suprimentos × MATR460 — resumo executivo (jun/2026)

Documento consolidado do trabalho de reconciliação entre o dashboard Suprimentos (`GET /supplies/stock-value`) e o **Registro de Inventário TOTVS (MATR460)**.

**Documentos relacionados**

| Documento | Conteúdo |
|-----------|----------|
| [playbook-correcao-estoque-supplies-inventario.md](./playbook-correcao-estoque-supplies-inventario.md) | Plano W0–W4, decisões de negócio, DoD |
| [supplies-estoque-historico.md](../api/supplies-estoque-historico.md) | Contrato API, `stock_method`, breakdown |
| [2026-06-estoque-supplies-reconciliacao.md](../changelog/2026-06-estoque-supplies-reconciliacao.md) | Changelog técnico |
| [estoque-reconciliacao-20260531.md](./evidencias/estoque-reconciliacao-20260531.md) | Evidências W0 (maio/2026) |
| [matr460-investigacao-totvs.md](./evidencias/matr460-investigacao-totvs.md) | Investigação TOTVS (jun/2026) |

---

## 1. Problema original

Usuários comparavam o KPI de estoque do dashboard (período maio/2026) com o **MATR460** e viam divergências grandes:

| Filial | Dashboard (estimativa SB9+SD3) | MATR460 EM ESTOQUE | MATR460 TOTAL GERAL |
|--------|-------------------------------|--------------------|---------------------|
| 01 Matriz | R$ 281.491 | R$ 3.598.312 | R$ 3.862.103 |
| 02 UES | R$ 4.911.292 | R$ 9.737.044 | R$ 10.048.510 |

A suspeita inicial era “não consideramos tudo” (locais, EM PROCESSO, etc.).

---

## 2. O que o MATR460 representa

O relatório **MATR460 (Registro de Inventário)** consolida por família contábil e expõe:

- **EM ESTOQUE** — fechamento contábil SB9 na data do inventário (`B9_VINI1` por produto/local).
- **EM PROCESSO** — WIP fabril (MP/PA/PI em produção), **fora** do saldo SB9 por armazém.
- **TOTAL GERAL** — soma dos dois blocos.

A API **nunca replicou** o MATR460 por completo. Antes de jun/2026, com datas preenchidas, usava apenas **estimativa Kardex**: último SB9 antes de `start_date` + movimentos SD3 (ponte + período).

---

## 3. O que foi implementado (ondas W0–W4)

### W0 — Reconciliação e diagnóstico

- Script `scripts/reconcile_stock_value.py` + SQL `scripts/sql/reconcile_stock_value_period.sql`
- Compara API, SQL espelhado, SB9, SB2 e referência manual do print MATR460
- **Conclusão:** API = SQL; gap é **regra + dados TOTVS**, não bug de código

### W1 — Transparência

- Campos de auditoria em `estimation` e `by_branch[]`: `closing_base_*`, `bridge_value`, `period_net_value`, `official_closure_*`, `data_quality_warning`
- MFE: componente `StockEstimationBreakdown` na aba Estoque

### W2 — `stock_method`

Parâmetro `stock_method=auto|estimated|official_closure` (default `auto`):

| Modo | Comportamento |
|------|---------------|
| `auto` | Fechamento SB9 em `end_date` se existir; senão estimativa SB9+SD3 |
| `estimated` | Sempre Kardex SB9+SD3 |
| `official_closure` | Exige SB9 em `end_date`; erro 400 se ausente |

SQL novo: `stock_value_official_closure_sql.py` — `SUM(B9_VINI1) WHERE B9_DATA = end_date`.

### W4 — Payload compartilhado e IDD

- `stock_value_estimation_payload_service.py` — montagem única de `estimation` / `stock_estimation`
- `GET /supplies/inventory-turnover` herda o mesmo contrato via `get_stock_value_bundle`

### W3 — EM PROCESSO (não iniciado)

Aguarda decisão de negócio (D2 no playbook). Investigação TOTVS indica que **SC2 simples não basta** para EM PROCESSO (ver §5).

---

## 4. Investigação TOTVS (24/jun/2026)

Comando:

```bash
docker exec -w /app delpi-api-delpi env PYTHONPATH=/app \
  python scripts/investigate_matr460_inventory.py
```

Evidências: [matr460-investigacao-totvs.json](./evidencias/matr460-investigacao-totvs.json)

### 4.1 Fechamentos SB9 em 2026

| Filial | Datas com fechamento SB9 em 2026 | Última data |
|--------|----------------------------------|-------------|
| 01 | 31/01, 28/02 | **28/02/2026** |
| 02 | 31/01, 28/02 | **28/02/2026** |

**Não existe `B9_DATA = 20260531`** em SB9010. O inventário de maio/2026 do MATR460 **não está gravado** como fechamento SB9 no banco consultado — explica por que `official_closure` falha e por que a estimativa SD3 partiu de fev/26.

### 4.2 Alinhamento com MATR460 (referência prints maio/2026)

| Filial | MATR EM ESTOQUE | SB9 28/02 | SB9 31/05 | SB2 atual | % SB2 vs EM EST. |
|--------|-----------------|-----------|-----------|-----------|------------------|
| 01 | R$ 3.598.312 | R$ 3.474.908 | — | R$ 3.565.793 | **99,1%** |
| 02 | R$ 9.737.044 | R$ 9.635.115 | — | R$ 10.158.352 | **104,3%** |

**Interpretação**

- **EM ESTOQUE do MATR460** ≈ **SB2 atual** (saldo corrente), não a estimativa SB9+SD3 com datas de maio.
- Quando Controladoria lançar SB9 em `end_date`, o modo `auto`/`official_closure` deve alinhar com EM ESTOQUE (tolerância ~2%).
- SB9 de fev/26 já está a ~97–99% do EM ESTOQUE de maio — o gap temporal é menor que o da estimativa SD3.

### 4.3 EM PROCESSO — proxy SC2 vs. MATR460

| Filial | MATR EM PROCESSO | Proxy SC2 (OP aberta, C2_VATU1 proporcional) | % proxy |
|--------|------------------|-----------------------------------------------|---------|
| 01 | R$ 263.791 | R$ 39.293 | 15% |
| 02 | R$ 311.466 | R$ 117.967 | 38% |

O MATR460 usa **outra regra** para EM PROCESSO (não é só saldo em aberto de SC2 com valor proporcional). W3 exige mapeamento com Protheus/Controladoria (possível rotina AdvPL do MATR460, estrutura de OP, SD3 de produção, etc.).

### 4.4 SD3 mar–mai/2026 (por que a estimativa cai)

Movimentos SD3 entre março e maio têm **saídas líquidas muito grandes** (TM 999, 502, 503), especialmente filial 01. A estimativa Kardex soma esses movimentos sobre base SB9 de fev/26 e chega a ~R$ 281k — **incompatível** com inventário oficial, mas **coerente com a fórmula** quando faltam fechamentos intermediários.

### 4.5 Objetos SQL no banco

Não há view publicada tipo “MATR460”. Encontrados:

- Tabela canônica **SB9010** (+ backups históricos `SB9010_*`, `ESTOQUEF01_202402`, etc.)
- Views PBI: `VW_PBI_ESTOQUE_OBSOLETO_MP_FIL02`, `VW_PBI_ESTOQUE_OBSOLETO_PA_FIL02` (obsolescência, não inventário total)

**Conclusão:** engenharia reversa do MATR460 no SQL Server resume-se a:

1. **EM ESTOQUE** → SB9010 na data do inventário (já implementado em W2).
2. **EM PROCESSO** → fonte a identificar com equipe Protheus (W3).
3. **Não replicar** Kardex SD3 como substituto do MATR460 quando faltam fechamentos SB9.

---

## 5. Respostas diretas

### Conseguimos alinhar os resultados?

| Cenário | Status |
|---------|--------|
| Estimativa SB9+SD3 vs. MATR460 maio/2026 | **Não alinhado** (por desenho + dados) |
| SB2 atual vs. MATR460 EM ESTOQUE | **~99–104%** — alinhado na prática |
| `official_closure` vs. MATR460 EM ESTOQUE | **Implementado**, aguarda SB9 em `end_date` no TOTVS |
| MATR460 TOTAL GERAL | **Não** — falta W3 (EM PROCESSO) |

### Dá para fazer engenharia reversa do MATR460?

**Parcialmente, sim** — e é o caminho escolhido:

- **EM ESTOQUE:** `SUM(B9_VINI1)` com `B9_DATA = data_inventário` — espelho direto do fechamento SB9.
- **TOTAL GERAL:** exige descobrir a rotina de EM PROCESSO no Protheus; proxy SC2 **subestima** 62–85%.
- **Não vale** forçar SD3 a “ficar igual” ao MATR460 sem fechamentos SB9 mensais.

---

## 6. Modo híbrido implementado (W5)

Documentação: [estoque-supplies-modo-hibrido.md](./estoque-supplies-modo-hibrido.md)

`stock_method=auto` (default) e `hybrid`:

1. SB9 na `end_date` → `official_closure`
2. Caso contrário → `register_snapshot` (SB2 + proxy EM PROCESSO nos locais 99/50/98)
3. `estimated` → Kardex SB9+SD3 (analítico, explícito)

Smoke maio/2026 filial 01: **~99,1%** do EM ESTOQUE MATR460 (antes ~7,8% com Kardex).

**Limitação:** `register_snapshot` não é histórico confiável — snapshot na consulta.

---

## 7. Próximos passos

1. **Controladoria:** confirmar se inventário maio/2026 será lançado em SB9 (`B9_DATA=20260531`) ou se o print MATR460 usa outra data/base.
2. **Re-validar** após fechamento:
   ```bash
   docker exec -w /app delpi-api-delpi env PYTHONPATH=/app \
     python scripts/reconcile_stock_value.py --start-date 2026-05-01 --end-date 2026-05-31
   docker exec -w /app delpi-api-delpi env PYTHONPATH=/app \
     python scripts/investigate_matr460_inventory.py
   ```
3. **Decisão D1–D2** (Suprimentos): KPI default com período fechado = EM ESTOQUE oficial ou total geral? Incluir EM PROCESSO?
4. **W3:** com Protheus, extrair regra EM PROCESSO do MATR460 (menu/rotina, parâmetros, tabelas) antes de codificar.

---

## 8. Commits de referência (delpi-central)

| Commit | Conteúdo |
|--------|----------|
| `1cc4e327` | W0 reconciliação + W1 transparência + W2 `stock_method` |
| `ec15e316` | W4 payload compartilhado + IDD |
| `e47775d3` | Docs módulo Suprimentos |

Scripts e evidências desta investigação ainda **não commitados** (gerados nesta sessão).
