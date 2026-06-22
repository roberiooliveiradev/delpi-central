# Auditoria LMP 2026 — RQ-060 vs dashboard api-delpi

Documento de registro da investigação (jun/2026) sobre divergências entre o **controle interno** (pastas LMP Ano + RQ-060) e a rota **`GET /engineering/lmps/dashboard/items`** da api-delpi.

> **Princípio:** o RQ-060 é **evidência de auditoria**, não regra de listagem. A rota deve refletir o fluxo real no Protheus (`AIJ010` + revisão `AD1010`). Este documento registra o cruzamento manual/automatizado para calibrar critérios de período e homologação. Ver também [playbook_correcao_lmp_repositorio_settings.md](../roadmaps/playbook_correcao_lmp_repositorio_settings.md).

**Última atualização:** 22/06/2026  
**Commit de referência:** `28091c4a` — *Investiga divergência LMP 2026 e extrai OVs dos RQ-060 por LMP Ano.*

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

### 5.2 Maio/2026 — **divergência estrutural**

| Métrica | Controle (pastas) | Dashboard API |
|---------|-------------------|---------------|
| Itens | **17** pastas (070–086) | **23** OVs |
| Diferença | — | +6 OVs extras |

**Causas identificadas:**

1. **Unidade de contagem:** dashboard conta **OVs**; controle conta **pastas**. Uma pasta pode mapear para a mesma OV de outra (ex.: `000090` nas pastas 072 e 079).
2. **Filtro de período legado (`anchor OR first_eng`):** OVs com âncora LMP **fora de maio** entram pelo `first_eng` no mês — ex.: `003562`, `003578`, `000120` (âncora em **jun/2026**) ainda aparecem no filtro **mai/2026**.
3. **Múltiplas OVs Protheus vs uma pasta RQ:** pasta **073 26** — RQ cita só `000102`; Protheus também lista `000088`, `000089`, `000095` (Wanke).
4. **OVs extras sem pasta mai:** `000087`, `003561`, `002871`, `003578`, `000120` (parte já explicada pelo item 2).
5. **Residence &lt; 30 min** e revisão medida no período — casos pontuais analisados via SQL em `scripts/sql/lmp_may2026_*`.

OVs maio/2026 no RQ-060 (070–086):

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

## 6. Código preparatório (opt-in, defaults legados)

Investigação motivou serviços de semântica **desacoplados do SQL**, ainda com default compatível com produção:

| Serviço | Responsabilidade |
|---------|------------------|
| `LmpPeriodInclusionSemanticsService` | Política de inclusão no período |
| `LmpListingKindSemanticsService` | Tipo efetivo LMP / Amostra / Outro |
| `LmpListingCycleSemanticsService` | Ciclo homologação / `cycle_index` |

**Settings novos** (`lmp_query_settings`):

| Setting | Default | Alternativa |
|---------|---------|-------------|
| `period_inclusion_policy` | `anchor_or_first_eng` | `homolog_in_period` |
| `strict_residence_after_homolog` | `False` | `True` (opt-in) |

Campos adicionais no dashboard (quando wiring ativo): `homolog_revision`, `measurement_revision`, `homolog_date`, `cycle_index`.

Testes: `tests/test_lmp_listing_cycle_semantics_service.py`, extensões em `tests/test_lmp_query_repository_sql.py`.

> **Não ativado em produção** sem homologação — usar scripts/SQL desta pasta para medir impacto antes.

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

## 10. Pendências

- [ ] Homologar **abril/2026** (16 pastas vs 21 dashboard — mencionado no playbook).
- [ ] Repetir cruzamento `--dashboard-only` para **jan–mai/2026**.
- [ ] Validar OVs ⚠ (026, 033, 047, …) no Word.
- [ ] Medir impacto de `homolog_in_period` + `strict_residence_after_homolog=True` vs planilha.
- [ ] Fase 2: múltiplas linhas por ciclo homolog (ex.: `000061`×3, `003562`×2) no dashboard.
- [ ] Decidir se contagem oficial do MFE deve ser **pastas** (RQ) ou **OVs** (Protheus) — produto.

---

## 11. Referências

- [playbook_correcao_lmp_repositorio_settings.md](../roadmaps/playbook_correcao_lmp_repositorio_settings.md) — regras de listagem, residence, tipo efetivo
- Rotas OpenAPI: `/engineering/lmps`, `/engineering/lmps/dashboard/items`
- Chat / registry: `minha-delpi-ai-api` → `operational_route_registry.json` (`lmp_dashboard_items`)
