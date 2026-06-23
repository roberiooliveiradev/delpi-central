# Auditoria LMP 2026 — RQ-060 vs dashboard api-delpi

Documento de registro da investigação (jun/2026) sobre divergências entre o **controle interno** (pastas LMP Ano + RQ-060) e a rota **`GET /engineering/lmps/dashboard/items`** da api-delpi.

> **Princípio:** o RQ-060 é **evidência de auditoria**, não regra de listagem. A rota deve refletir o fluxo real no Protheus (`AIJ010` + revisão `AD1010`). Este documento registra o cruzamento manual/automatizado para calibrar critérios de período e homologação. Ver também [playbook_correcao_lmp_repositorio_settings.md](../roadmaps/playbook_correcao_lmp_repositorio_settings.md).

**Última atualização:** 22/06/2026  
**Commit de referência:** `7374a055` — *Implementa work_month_lmp como política padrão de listagem LMP.*

---

## 1. Objetivo

1. Entender por que o **dashboard LMP** (contagem por OV) difere do **controle interno** (contagem por pasta LMP Ano).
2. Extrair a **OV oficial de cada pasta** a partir do campo `OV Nº:` no **RQ-060** (Word), sem inferir pelo Protheus.
3. Cruzar essas OVs com o retorno da API no **mês de referência** (`date_start` / `date_end`).
4. Isolar causas: filtro de período, OVs duplicadas entre pastas, múltiplas OVs por pasta, `first_eng` vs âncora LMP, residence &lt; 30 min.

---

## 2. Escopo e premissas

| Item | Definição |
|------|-----------|
| Controle interno | Pastas `LMP NNN 26` em `X:\ENGENHARIA\1 LMP's\LMP 2026\` |
| Fonte da OV na tabela | **Somente** RQ-060 (`RQ-060 Análise Crítica de Produtos Rev*.docx`) |
| Rota comparada | `GET /engineering/lmps/dashboard/items?listing_type=LMP&date_start=…&date_end=…` |
| Período analisado | Jan–jun/2026 (extração completa); homologação detalhada **mai** e **jun/2026** |
| Ambiente | Container `delpi-api-delpi` (ODBC → TOTVS); extração RQ via **PowerShell** no Windows (`X:`) |

**Restrição operacional:** pastas no WSL não estão montadas; extração RQ-060 roda com `powershell.exe -File …` a partir do host Windows.

---

## 3. Extração RQ-060 (jan–jun/2026)

### 3.1 Script principal

```powershell
# Host Windows — pastas 002 a 098
powershell.exe -File api-delpi/scripts/extract_rq060_via_powershell.ps1 -StartNum 2 -EndNum 98
```

- Lê `.docx` via `System.IO.Compression` (XML interno).
- Parser de OV no cabeçalho (antes de `CLIENTE:`):
  1. Seis dígitos contíguos (`\d{6}`).
  2. Campo `Nº:` com dígitos espaçados / FORMTEXT.
  3. Fallback no corpo do documento.
- Regex de pasta: `LMP\s*0*{n}\s*26` (cobre `LMP 0010 26`).

**Resultado:** **97/97** pastas (002–098) extraídas com sucesso na última execução.

Scripts auxiliares:

| Script | Uso |
|--------|-----|
| `retry_failed_rq060.ps1` | Reprocessa pastas com erro |
| `debug_header.ps1` / `debug_ov_extract.ps1` | Depuração de layout Word |
| `extract_lmp_ovs_from_folders.py` | Variante Python (WSL; depende de mount) |

### 3.2 Artefatos de dados

| Arquivo | Conteúdo |
|---------|----------|
| `scripts/data/lmp_2026_rq060_extract_all.json` | Extração bruta (caminho RQ, texto, OV) |
| `scripts/data/lmp_2026_internal_control_ovs_all.json` | `{ lmp_ano, mes, ov }` por pasta |
| `scripts/data/lmp_may2026_internal_control_ovs.json` | 17 pastas mai/2026 (070–086) |
| `scripts/data/lmp_june2026_internal_control_ovs.json` | 12 pastas jun/2026 (087–098) |
| `scripts/data/lmp_*_internal_control_ovs.csv` | Mesmo conteúdo por mês — **gitignored** (`*.csv`) |

Campo `mes` no JSON consolidado: mês atribuído pela **planilha/controle** (não recalculado pela API).

### 3.3 OVs a conferir manualmente no Word

Alguns RQs têm OV mal digitada ou incompleta (espaços, dígitos faltando). Revisar visualmente antes de usar como verdade absoluta:

- LMP **026** → `000005` (suspeito)
- LMP **033** → `000352`
- LMP **047** → `000051`
- Outros com aviso no log de extração

---

## 4. Metodologia de cruzamento

### 4.1 Fluxo

```text
RQ-060 (Word) → JSON controle → conjunto de OVs por mês
                                      ↓
              GET /engineering/lmps/dashboard/items (mesmo período)
                                      ↓
              diff: interseção | só RQ | só dashboard
                                      ↓
              (opcional) histórico AIJ por OV — motivo de inclusão
```

### 4.2 Script canônico (pós-investigação)

```bash
# Rápido (~1,5 s) — só dashboard + diff
docker exec -w /app delpi-api-delpi \
  python scripts/investigate_lmp_period_vs_rq060.py --month 2026-06 --dashboard-only

# Completo — inclui histórico por OV (lento; pode estourar timeout ODBC)
docker exec -w /app delpi-api-delpi \
  python scripts/investigate_lmp_period_vs_rq060.py --month 2026-05
```

Parâmetro `--month YYYY-MM` lê `lmp_2026_internal_control_ovs_all.json`.

Scripts legados (mai/2026):

| Script | Função |
|--------|--------|
| `investigate_lmp_period_vs_rq060.py` | Cruzamento mês a mês (`--dashboard-only` ou completo) |
| `investigate_lmp_may2026_divergence_history.py` | Histórico AIJ das OVs divergentes de mai/2026 |
| `investigate_lmp_may2026_divergence.py` | Investigação profunda maio (categorias A–E) |
| `validate_lmp_period_filter_may2026.py` | Dashboard mai + OVs com âncora em junho |
| `simulate_lmp_period_by_revision.py` | Simula políticas via HTTP + SQL |
| `run_sql_investigation.py` | Executa SQLs de `scripts/sql/` via `/data/sql` |

---

## 5. Resultados por mês

### 5.1 Junho/2026 — **alinhamento total**

| Métrica | RQ-060 | Dashboard API |
|---------|--------|---------------|
| Pastas / itens | **12** (087–098) | **12** |
| OVs únicas | **12** | **12** |
| Só RQ-060 | 0 | — |
| Só dashboard | — | 0 |

Mapeamento 1:1 (pasta → OV RQ → âncora dashboard):

| Pasta | OV (RQ-060) | Âncora | Descrição (dashboard) |
|-------|-------------|--------|------------------------|
| 087 26 | 000124 | 02/06/2026 | ATUALIZAÇÃO DES.WANKE-4 ITENS |
| 088 26 | 003506 | 10/06/2026 | WEG MOTORES |
| 089 26 | 003523 | 11/06/2026 | PROJ. M.O. CHICOTE-WITC-0032 |
| 090 26 | 003562 | 11/06/2026 | PROJ. TRR-ITCC-0039-FLEX |
| 091 26 | 003410 | 22/06/2026 | WEG LINHARES |
| 092 26 | 000133 | 11/06/2026 | DES. WANKE ATUALIZ. 3 ITENS |
| 093 26 | 003377 | 11/06/2026 | WEG LINHARES |
| 094 26 | 003578 | 15/06/2026 | BUHLER - 1 ITEM |
| 095 26 | 000120 | 15/06/2026 | WEG LINHARES |
| 096 26 | 000125 | 15/06/2026 | WEG LINHARES |
| 097 26 | 003092 | 15/06/2026 | WEG LINHARES |
| 098 26 | 003595 | 18/06/2026 | MODIFICAÇÃO 90264050 |

**Conclusão:** com filtro `2026-06-01` → `2026-06-30`, a API reflete exatamente as OVs documentadas nos RQs de junho.

### 5.2 Maio/2026 — **divergência estrutural** (homologado 22/06/2026)

Comando: `investigate_lmp_period_vs_rq060.py --month 2026-05 --dashboard-only`  
Relatório JSON: `scripts/data/lmp_may2026_rq060_vs_dashboard_report.json`

| Métrica | RQ-060 | Dashboard `listing_type=LMP` |
|---------|--------|------------------------------|
| Pastas / linhas | **17** (070–086) | — |
| OVs únicas | **16** (`000090` em 072+079) | **23** |
| Interseção (conjuntos) | — | **15** OVs |
| Só RQ-060 | **1** (`003567`) | — |
| Só dashboard | — | **8** OVs |
| Pastas com OV no dashboard | **16/17** | — |
| Pastas sem OV no dashboard | **1** (078 → `003567`) | — |

**Conclusão:** maio **não** fecha como junho. O dashboard lista **+8 OVs** que não constam no RQ de maio e **omite 1 OV** documentada no RQ (`003567`).

#### 5.2.1 Mapeamento pasta → OV → dashboard

| Pasta | OV (RQ) | No dashboard LMP? | Âncora LMP | Observação |
|-------|---------|-------------------|------------|------------|
| 070 26 | 003562 | ✓ | **11/06/2026** | Entra em mai por `first_eng` 04/05; pasta mai, homolog jun |
| 071 26 | 003403 | ✓ | 04/05/2026 | |
| 072 26 | 000090 | ✓ | 15/05/2026 | OV compartilhada com 079 |
| 073 26 | 000102 | ✓ | 18/05/2026 | RQ só cita esta OV; Protheus tem mais Wanke |
| 074 26 | 003568 | ✓ | 08/05/2026 | |
| 075 26 | 000111 | ✓ | 12/05/2026 | |
| 076 26 | 000084 | ✓ | 13/05/2026 | |
| 077 26 | 003571 | ✓ | 14/05/2026 | |
| 078 26 | 003567 | **✗** | — | **Ausente** em LMP, Amostra, Outro e Todos (25 itens) |
| 079 26 | 000090 | ✓ | 15/05/2026 | Mesma OV que 072 |
| 080 26 | 003551 | ✓ | 19/05/2026 | |
| 081 26 | 000054 | ✓ | 20/05/2026 | |
| 082 26 | 000097 | ✓ | 25/05/2026 | |
| 083 26 | 003574 | ✓ | 25/05/2026 | |
| 084 26 | 003572 | ✓ | 25/05/2026 | |
| 085 26 | 003573 | ✓ | 25/05/2026 | |
| 086 26 | 000061 | ✓ | 27/05/2026 | |

#### 5.2.2 As 8 OVs no dashboard sem pasta RQ em maio

| OV | Âncora | Motivo provável | Categoria |
|----|--------|-----------------|-----------|
| 000088 | 04/05/2026 | Wanke 9048 — não citada no RQ 073 (`000102`) | **Multi-OV Wanke** |
| 000089 | 04/05/2026 | idem | **Multi-OV Wanke** |
| 000095 | 04/05/2026 | idem | **Multi-OV Wanke** |
| 000087 | 04/05/2026 | LMP válida Protheus; sem pasta mai no controle | **Extra operacional** |
| 003561 | 05/05/2026 | idem | **Extra operacional** |
| 002871 | 27/05/2026 | idem (`first_eng` antigo 09/2025) | **Extra operacional** |
| 000120 | **15/06/2026** | `first_eng` 27/05 → vazamento para mai | **Bleed de período** |
| 003578 | **15/06/2026** | `first_eng` 20/05 → vazamento para mai | **Bleed de período** |

> `003562` (pasta 070) **não** está nesta lista — consta no RQ de maio e no dashboard, mas com **âncora em junho** (inclusão via `first_eng`).

#### 5.2.3 OV `003567` (pasta 078) — ausente totalmente

Investigação pontual (`get_lmp` + histórico):

| Campo | Valor |
|-------|-------|
| `listing_kind` efetivo | **OUTRO** (não LMP) |
| Âncora LMP | vazia |
| `first_eng` | 14/05/2026 (rev. 02) |
| No dashboard mai (`Todos`=25 itens) | **Não** |

Hipótese: candidata com engenharia no mês, mas **sem marcador LMP** e **fora dos critérios** de listagem como OUTRO no período (residência / revisão medida). Divergência **RQ diz LMP** vs **Protheus classifica OUTRO** — conferir RQ-060 e eventos `AIJ010` da OV.

#### 5.2.4 Causas consolidadas

1. **Unidade de contagem:** 17 pastas → 16 OVs únicas no RQ (`000090` duplicada).
2. **Filtro `anchor OR first_eng`:** `003562`, `000120`, `003578` entram em mai sem âncora LMP no mês.
3. **Multi-OV Wanke:** RQ 073 documenta `000102`; Protheus lista também `000088`, `000089`, `000095` (âncora 04/05).
4. **Extras operacionais:** `000087`, `003561`, `002871` — LMP Protheus sem pasta no controle mai.
5. **Classificação / exclusão:** `003567` no RQ mas **não listada** — tipo efetivo OUTRO, não passa no filtro LMP nem aparece em `Todos` no período.

#### 5.2.5 Histórico AIJ010 — divergências (investigado 22/06/2026)

Script: `scripts/investigate_lmp_may2026_divergence_history.py`  
Relatório: `scripts/data/lmp_may2026_divergence_history_report.json`

##### A — `003567` (pasta 078): RQ presente, dashboard ausente

| Campo | Valor |
|-------|-------|
| Filial ativa | 01 (rev. **06**) |
| `AD1_DESCRI` | `BUHLER - 1 ITEM` (sem marcador LMP explícito) |
| Tipo efetivo | **OUTRO** |
| `first_eng` | 14/05/2026 rev. 02, estágio 000003 |
| Eventos mai | **42** linhas AIJ — ciclo completo em **14/05** (rev. 02, 04, 05): estágios 000003–000012, incl. **000008 Amostra** |
| Homologação | 000012 em 14/05 (rev. 05 encerra 18/05) |
| Produto ADJ | `80014553` |

**Por que diverge:** o RQ-060 registra a pasta como LMP de maio, mas no Protheus a OV **não recebe classificação LMP** (sem âncora LMP utilizável; fluxo com estágio Amostra no mesmo dia). Com `listing_type=LMP` fica fora; com `Todos` também não entra — candidata **OUTRO** que não satisfaz o predicado de listagem do período (homolog/âncora medida vs. `first_eng` isolado). **Ação:** conferir se o RQ foi aberto antes da homologação LMP real ou se a OV deveria ser outra (ex. `003578`, BUHLER homologada em **junho**).

##### B — Wanke: `000088`, `000089`, `000095` vs RQ `000102` (pasta 073)

| OV | No RQ 073? | Âncora dashboard | Evento AIJ dominante em mai | `first_eng` |
|----|------------|------------------|----------------------------|-------------|
| 000102 | **Sim** | 18/05 | Eng. 07/05 → homolog **18/05** rev. 04 (fluxo completo) | 07/05 |
| 000088 | Não | 04/05 | Só cadeia homolog **04/05** rev. 11 (estágios 000005–000013, mesmo dia) | 21/04 |
| 000089 | Não | 04/05 | Idem rev. 06 em 04/05 | 21/04 |
| 000095 | Não | 04/05 | Idem rev. 07 em 04/05 | 28/04 |

Produtos ADJ: `000089` e `000102` compartilham **`90480113`** (família Wanke 9048). O Protheus **fragmenta o projeto em 4 OVs**; o controle interno documenta **apenas `000102`** no RQ-060 da pasta 073.

**Por que diverge:** não é erro de filtro de período — são **OVs distintas** com homologação LMP em 04/05 que o controle não vinculou à pasta. A API lista cada OV com âncora no mês.

##### C — Extras operacionais: `000087`, `003561`, `002871`

| OV | Âncora | Histórico mai | Observação |
|----|--------|---------------|------------|
| 000087 | 04/05 | Homolog rev. 08 em 04/05 (1 evento) | COLORMAQ — LMP válida, sem pasta RQ |
| 003561 | 05/05 | Eng. 04/05 + homolog 05/05 rev. 03 | FRANKLIN — LMP válida, sem pasta RQ |
| 002871 | 27/05 | Âncora 27/05; `first_eng` **09/2025** | TRACTIAN — entra por âncora no mês |

**Por que diverge:** LMP reais no Protheus **sem linha correspondente** na planilha RQ de maio (atraso de controle ou critério de pasta diferente).

##### D — Bleed `first_eng`: `000120`, `003578`, `003562`

| OV | Pasta RQ | Âncora LMP | `first_eng` mai | Homolog LMP no mês |
|----|----------|------------|-----------------|-------------------|
| 000120 | 095 (**jun**) | **15/06** | 27/05 rev. 03 | Não — só eng. pontual em mai |
| 003578 | 094 (**jun**) | **15/06** | 20/05 rev. 03–09 (7 eventos eng.) | Não em mai |
| 003562 | 070 (**mai**) | **11/06** | 04/05 rev. 08–09 (+ homolog 04/05 aberta) | Parcial 04/05; homolog final jun |

**Por que diverge:** política atual **`anchor OR first_eng`** inclui essas OVs em **maio** porque houve engenharia no mês, **mesmo sem homologação LMP no mês de referência**. `003562` ilustra pasta de **mai** com homologação final em **junho** (também pasta 090 em jun).

**Mitigação preparada:** `period_inclusion_policy=homolog_in_period` (opt-in) alinharia o dashboard ao mês da homologação LMP, não ao `first_eng`.

OVs maio/2026 no RQ-060 (070–086) — referência:

| Pasta | OV |
|-------|-----|
| 070 26 | 003562 |
| 071 26 | 003403 |
| 072 26 | 000090 |
| 073 26 | 000102 |
| 074 26 | 003568 |
| 075 26 | 000111 |
| 076 26 | 000084 |
| 077 26 | 003571 |
| 078 26 | 003567 |
| 079 26 | 000090 |
| 080 26 | 003551 |
| 081 26 | 000054 |
| 082 26 | 000097 |
| 083 26 | 003574 |
| 084 26 | 003572 |
| 085 26 | 003573 |
| 086 26 | 000061 |

### 5.3 OVs reutilizadas entre pastas (histórico RQ-060)

| OV | Pastas / meses |
|----|----------------|
| 003562 | 070 (mai), 090 (jun) |
| 003506 | 037, 038 (mar), 068 (abr), 088 (jun) |
| 003523 | 045 (mar), 055 (abr), 089 (jun) |
| 000090 | 072, 079 (mai) |
| 000061 | 064, 086 (mai) — erro de controle conhecido |

Isso **não invalida** a listagem da API; indica limitação do controle por pasta quando a mesma OV é reutilizada.

---

## 6. Correção SQL — `anchor_in_period` (jun/2026)

### Problema

A política legada `anchor_or_first_eng` incluía OVs no mês quando **`first_eng`** caía no período, mesmo com **âncora LMP em outro mês** — bleed em mai/2026 (`000120`, `003578`, `003562`).

### Solução

Nova política padrão **`anchor_in_period`** em `LMPQuerySettings.period_inclusion_policy`:

- Filtra candidatos só quando **`L.ANCHOR_START_DATE`** (âncora LMP em `ListingAnchorEventos`) está no intervalo.
- Remove o CTE `OvFirstEngineeringArrival` do batch (sem JOIN `first_eng`).
- Corrige branch OUTRO com `homolog_in_period`: usa `R.ANCHOR_START_DATE`, não `LF` sem JOIN.

| Política | Comportamento |
|----------|---------------|
| **`anchor_in_period`** | Padrão — âncora LMP no mês |
| `anchor_or_first_eng` | Legado — âncora **OU** first_eng |
| `homolog_in_period` | Só homologação 000012 (`LF`) no mês |

### Impacto homologado

| Mês | Legado (`anchor_or_first_eng`) | `anchor_in_period` | RQ-060 pastas |
|-----|-------------------------------|-------------------|---------------|
| Mai/2026 | 23 OVs | **20** OVs | 17 |
| Jun/2026 | 12 OVs | **12** OVs | 12 ✓ |

Script histórico divergências: `scripts/investigate_lmp_may2026_divergence_history.py`  
Relatórios: `scripts/data/lmp_may2026_rq060_vs_dashboard_report.json`, `lmp_may2026_divergence_history_report.json`.

### Serviços e settings

| Serviço / setting | Responsabilidade |
|-------------------|------------------|
| `LmpPeriodInclusionSemanticsService` | Predicado SQL por política |
| `LmpListingKindSemanticsService` | Tipo efetivo LMP / Amostra / Outro |
| `LmpListingCycleSemanticsService` | Ciclo homologação / `cycle_index` |
| `period_inclusion_policy` | Default **`work_month_lmp`** (ver §6.1) |
| `strict_residence_after_homolog` | Opt-in — LMP homologada com &lt; 30 min → OUTRO |

Campos adicionais no dashboard: `homolog_revision`, `measurement_revision`, `homolog_date`, `cycle_index`.

Testes: `tests/test_lmp_query_repository_sql.py`, `tests/test_lmp_listing_cycle_semantics_service.py` (42 casos no container).

---

## 6.1 Política atual — `work_month_lmp` (jun/2026)

Evolução após `anchor_in_period`: o controle RQ-060 organiza pastas pelo **mês do trabalho recebido/feito**, não só pela data de homologação 000012. A política **`work_month_lmp`** (padrão em `LMPQuerySettings.period_inclusion_policy`) combina:

1. **Revisões com trabalho LMP no mês** — `first_eng` ou âncora LMP na revisão, com ≥30 min em engenharia (AIJ010).
2. **Fallback âncora OV** — candidatos de `anchor_in_period` quando não há revisão qualificada no mês (`NOT EXISTS WorkMonthRevisionKeys`).
3. **Múltiplas linhas** — mesma OV, revisões diferentes no período → linhas distintas com `cycle_index` 1, 2, …

**Módulo SQL:** `LMPQueryRepository._sql_work_month_lmp_candidates_cte`  
**Histórico medido por revisão do candidato:** `uses_per_revision_candidate_listing()` (`per_candidate_revision=True` no batch).

### Cruzamento RQ-060 (jan–jun/2026, pós-deploy)

| Mês | Pastas RQ | Interseção API | Só RQ (não na API) |
|-----|-----------|----------------|---------------------|
| Jan | 8 | 6 | 2 |
| Fev | 25 | 21 | 4 |
| Mar | 16 | 14 | 2 |
| Abr | 16 | 12 | 4 |
| Mai | 16 | 14 | 2 |
| Jun | 12 | **12** | **0** |

**Recall global:** 79/93 (84,9%). Jun/2026 fecha 1:1 com o controle.

### Políticas comparadas (gate)

| Política | Critério | Jun/2026 vs RQ |
|----------|----------|----------------|
| `anchor_or_first_eng` | Legado — bleed por `first_eng` | Infla (mai 23 OVs) |
| `anchor_in_period` | Âncora LMP no mês, 1 linha/OV | 12/12 ✓ |
| `homolog_cycles_in_period` | Homolog 000012 no mês, multi-ciclo | 8/12 ✗ |
| **`work_month_lmp`** | Trabalho na revisão no mês + fallback âncora | **12/12** ✓, multi-revisão |

Validar antes de alterar SQL: `scripts/validate_lmp_period_policies_vs_rq060.py`, `scripts/sql/lmp_period_policy_gate_compare.sql`.

### Campos expostos no dashboard

| Campo | Significado |
|-------|-------------|
| `homolog_revision` | Revisão AD1010 do ciclo medido (homologação) |
| `measurement_revision` | Revisão usada nas métricas de engenharia |
| `homolog_date` | Data da homologação 000012 do ciclo |
| `cycle_index` | Índice do ciclo de trabalho no mês para a mesma OV (1, 2, …) |

---

## 7. SQL de investigação (mai/2026)

Pasta `scripts/sql/` — executar via `run_sql_investigation.py` ou `/data/sql`:

| Arquivo | Propósito |
|---------|-----------|
| `lmp_may2026_period_filter_compare.sql` | Comparar totais por critério de período |
| `lmp_may2026_period_filter_diff_only.sql` | OVs só em um critério |
| `lmp_may2026_sql50_vs_dashboard23.sql` | SQL bruto vs 23 do dashboard |
| `lmp_may2026_extras_why_listed.sql` | Por que extras entram |
| `lmp_may2026_extras_sem_pasta_audit.sql` | Extras sem pasta no controle |
| `lmp_may2026_historico_mes_*` | Residence / gap / cross-check |
| `lmp_period_policy_simulation_by_revision.sql` | Simular políticas por revisão |
| `lmp_extras_full_history_eng.sql` | Histórico engenharia das extras |

---

## 8. Diagrama — por que mai ≠ jun na percepção do controle

```text
                    ┌─────────────────────┐
                    │  Controle interno   │
                    │  (1 linha = pasta)  │
                    └──────────┬──────────┘
                               │
         RQ-060 OV             │              Dashboard API
              │                │              (1 linha = OV)
              ▼                ▼                       │
    ┌─────────────────────────────────────────────────────────┐
    │  Filtro período: (âncora LMP no mês) OR (first_eng)     │
    └─────────────────────────────────────────────────────────┘
              │                              │
    Jun/2026: 12 pastas = 12 OVs = 12 API   │  Alinhado
    Mai/2026:  17 pastas ≠ 23 OVs           │  +6 extras (OR first_eng,
              │                              │   multi-OV Wanke, dup OV)
              └──────────────────────────────┘
```

---

## 9. Como reproduzir

### Pré-requisitos

- Stack dev: `docker compose -f infra/docker-compose.dev.yml up -d api-delpi`
- Rede/VPN TOTVS acessível pelo container
- Para reextrair RQs: Windows + drive `X:` mapeado

### Passo a passo

```bash
# 1. Extração RQ (Windows PowerShell)
powershell.exe -File api-delpi/scripts/extract_rq060_via_powershell.ps1 -StartNum 2 -EndNum 98

# 2. Cruzamento mês a mês
docker exec -w /app delpi-api-delpi \
  python scripts/investigate_lmp_period_vs_rq060.py --month 2026-06 --dashboard-only

docker exec -w /app delpi-api-delpi \
  python scripts/investigate_lmp_period_vs_rq060.py --month 2026-05 --dashboard-only

# 3. Dashboard direto (debug)
docker exec -w /app delpi-api-delpi python -c "
import json, sys; sys.path.insert(0,'/app')
from app.composition.engineering_composer import build_engineering_list_lmps_dashboard_use_case
from app.interface.http.routes.engineering.lmp_route_helpers import build_list_lmp_request
uc = build_engineering_list_lmps_dashboard_use_case()
dto = build_list_lmp_request(date_start='2026-06-01', date_end='2026-06-30', listing_type='LMP', page_size=500)
print(json.dumps(uc.execute_summary(dto, status_filter='Todos'), indent=2))
"
```

---

## 10. Gate — testar políticas no SQL antes de alterar o repositório

**Regra:** nenhuma mudança em `LMPQueryRepository` / `period_inclusion_policy` sem rodar o gate e comparar com RQ-060.

| Artefato | Função |
|----------|--------|
| `scripts/sql/lmp_period_policy_gate_compare.sql` | Simula 4 políticas no TOTVS (sem deploy) |
| `scripts/validate_lmp_period_policies_vs_rq060.py` | Cruza totais + OVs com RQ e dashboard atual |
| `scripts/investigate_lmp_period_vs_rq060.py` | Auditoria mês a mês (RQ ↔ API) |
| `scripts/simulate_lmp_period_by_revision.py` | Variante via `/data/sql` (token) |

```bash
docker exec -w /app delpi-api-delpi python scripts/validate_lmp_period_policies_vs_rq060.py --month 2026-06
docker exec -w /app delpi-api-delpi python scripts/validate_lmp_period_policies_vs_rq060.py --month 2026-05 --json
```

### Políticas simuladas no gate (jun/2026, RQ=12 OVs)

| Política | Critério de mês | OVs vs RQ (interseção) | Observação |
|----------|-----------------|------------------------|------------|
| **dashboard_atual** (`anchor_in_period`) | Âncora LMP na revisão atual | **12/12** ✓ | Padrão após revert |
| `anchor_in_period_ov` | Idem (SQL simplificado) | 10/12 | Aproximação — dashboard real bate 12 |
| `homolog_rev_in_period` | Homolog 000012 no mês | 8/12 | Desalinha mês da pasta (jun) |
| `eng_rev_work_month` | ≥30 min eng + first_eng ou âncora na revisão no mês | 7/12 | Evoluiu para **`work_month_lmp`** (implementado) |
| `eng_rev_first_eng_only` | ≥30 min + first_eng no mês (sem exigir homolog) | — | Só investigação; infla demais |

**Conclusão (jun/2026):** política em produção é **`work_month_lmp`** — alinha jun/2026 12/12, permite múltiplas linhas por OV no mês e melhora recall jan–jun vs só `anchor_in_period`. Manter gate antes de novas alterações no repositório.

---

## 11. Histórico da OV sem pesar o banco

Princípio: **listagem leve**, **histórico sob demanda**, **investigação offline**.

```text
┌─────────────────────────────────────────────────────────────┐
│  Dashboard / listagem mensal                                 │
│  • Candidatos do período → #temp (batch único)               │
│  • AIJ010 só para OVs/revisões candidatas                    │
│  • Sem varrer histórico completo do banco                    │
└───────────────────────────┬─────────────────────────────────┘
                            │ clique / drill-down
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  GET …/lmps/{ov}/history/events  (+ revision opcional)       │
│  • WHERE AIJ_NROPOR = ?  (+ AIJ_REVISA = ?)                  │
│  • Índice natural: filial + OV — custo O(eventos da OV)      │
└───────────────────────────┬─────────────────────────────────┘
                            │ análise / auditoria
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Scripts SQL (gate, investigate_*) — fora do request path    │
│  • Não entram no pipeline do dashboard                       │
└─────────────────────────────────────────────────────────────┘
```

| Camada | Custo | Quando usar |
|--------|-------|-------------|
| Listagem | Baixo — escopo por período + temp tables | Painel mensal |
| `history/events` | Baixo — 1 OV por request | Rastrear revisões, reaberturas, status |
| `history/flow` | Baixo — 1 OV, eventos de fluxo | Linha do tempo simplificada |
| Gate SQL | Médio — manual/CI, não em produção | Validar filtro antes de codar |

**Futuro (se listagem multi-revisão exigir):** snapshot materializado `LmpRevisionCycle` (filial, OV, revisão, first_eng, homolog_date, eng_minutes, cycle_index) atualizado por job noturno — listagem lê snapshot; histórico bruto continua em `history/events`.

**O que não fazer:** JOIN em `AIJ010` sem filtro de OV no batch do dashboard; replicar histórico completo em cada linha da listagem.

---

## 12. Pendências

- [ ] Rodar gate para **jan–abr/2026** e fixar critério de aceite formal (interseção RQ vs política).
- [ ] Investigar **só-RQ** (14 OVs jan–jun) — pasta sem trabalho ≥30 min ou OV mal extraída do Word.
- [ ] Homologar **abril/2026** (16 pastas vs 12 dashboard).
- [x] Jun/2026 1:1 com `work_month_lmp` (12/12, 0 só-RQ).
- [x] Política **`work_month_lmp`** implementada e default na API.
- [x] Colunas **Revisão** e **Ciclo** nos MFEs `dashboard-lmps` e `dashboard-engineering`.
- [ ] Decidir contagem oficial MFE: **pastas** (RQ) vs **linhas** (revisão/ciclo) — UI já exibe linhas.

---

## 14. Frontend — dashboards LMP

Os plugins **`dashboard-lmps`** e **`dashboard-engineering`** (aba LMPs) consomem `GET /engineering/lmps/dashboard/items` e exibem na tabela principal:

| Coluna | Campo API | Descrição |
|--------|-----------|-----------|
| Revisão | `homolog_revision` → fallback `measurement_revision` | Revisão AD1010 do ciclo medido no período |
| Ciclo | `cycle_index` | 1 = primeiro ciclo no mês; 2+ = reabertura ou nova revisão |

**Implementação:**

- `plugins/dashboard-lmps` — `DashboardLmpsPage.tsx`, `lmpListingDisplay.ts`, export CSV, tooltips em `helpTooltips.ts`
- `plugins/dashboard-engineering` — `LmpPage.tsx`, `lmpDisplay.ts`

**Chave de linha:** `filial-tipo-OV-revisão-ciclo` — evita colisão React quando a mesma OV aparece mais de uma vez no período.

**Detalhe da OV:** clique continua em `/ov/{sale_number}`; histórico completo em `/history/events` (revisão opcional na query).

Doc MFE: `plugins/dashboard-lmps/docs/API_MAPPING.md`, `plugins/dashboard-lmps/docs/DOCUMENTACAO.md`.

---

## 13. Referências

- [playbook_correcao_lmp_repositorio_settings.md](../roadmaps/playbook_correcao_lmp_repositorio_settings.md) — regras de listagem, residence, tipo efetivo
- Rotas OpenAPI: `/engineering/lmps`, `/engineering/lmps/dashboard/items`
- Chat / registry: `minha-delpi-ai-api` → `operational_route_registry.json` (`lmp_dashboard_items`)
