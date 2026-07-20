# Playbook 22 — Categorias de cálculo de benefício (plano de refatoração)

**Status:** Fases A–C (MFE) entregues — breakdown/chips/hints no plugin; ROI inalterado  
**Escopo:** `transformometro-api` + plugin `transformometro`  
**Restrição de migration:** apenas **DDL** (tabelas/colunas/constraints/índices/views). **Proibido** `UPDATE`/`INSERT` de backfill em migrations — legado fica no **DEFAULT** da coluna + lógica de aplicação.

---

## 1. Objetivo

Explicitar **categorias de cálculo** do benefício da revisão vs. referência, sem quebrar o comportamento atual dos cadastros existentes (tratados como **economia de tempo**).

| Categoria (código) | Significado | Fase |
|---|---|---|
| `economia_tempo` | Mesmo volume implícito / foco em Δtempo (comportamento atual dominante) | **Fase 0 — default** |
| `reducao_volume` | Benefício principal = menos execuções (volumes reais) | Fase 1 (breakdown/UI) |
| `ganho_capacidade` | `vol_rev > vol_ref` → capacidade valorizada à parte | Fase 2 |
| `economia_qualidade` | Retrabalho / erro / outros (já entram na bruta; breakdown) | Fase 1–2 |
| `misto` / `automatico` | Motor deriva breakdown; ROI usa regras declaradas | Fase 2+ |

**Default canônico:** `economia_tempo`.

---

## 2. Princípios

1. **Escopo da categoria:** declaração na **revisão** (ou medição 1:1 da revisão); cálculo em `revisão × competência` vs. referência.
2. **Dados existentes:** nenhuma migration altera linhas. Coluna nova com `DEFAULT 'economia_tempo' NOT NULL` → linhas antigas passam a ler o default no Postgres sem `UPDATE`.
3. **Compatibilidade:** `economia_bruta` / `economia_liquida_mes` / ROI **não mudam numericamente** na Fase 0–1 para revisões em `economia_tempo` (mesmo motor de custo atual).
4. **Separação de KPIs:** capacidade **não** entra em `economia_bruta` até decisão explícita de produto; campo próprio.
5. **Uma fonte de verdade:** fórmulas em `calc_rules` + doc `regras-de-calculo.md`; API e MFE só consomem.

---

## 3. Modelagem de dados (só DDL)

### 3.1 Catálogo (opcional mas recomendado)

```sql
-- V0xx__beneficio_calculo_categoria.sql  (somente DDL)
CREATE TABLE IF NOT EXISTS transformometro.beneficio_calculo_categoria (
    codigo VARCHAR(32) PRIMARY KEY,
    rotulo VARCHAR(120) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    ordem SMALLINT NOT NULL DEFAULT 0
);
-- Sem INSERT na migration: seed via script/CLI/app startup idempotente
-- (fora do Flyway) OU seed documentado em fixtures — nunca UPDATE de linhas de negócio.
```

Se preferir **sem tabela de catálogo** na primeira entrega: `VARCHAR` + check constraint na coluna da revisão (lista fechada no DDL).

### 3.2 Declaração na revisão (preferido)

```sql
ALTER TABLE transformometro.revisoes
  ADD COLUMN IF NOT EXISTS beneficio_calculo_categoria VARCHAR(32)
    NOT NULL DEFAULT 'economia_tempo';

-- Opcional: FK para catálogo, se existir
-- ALTER TABLE ... ADD CONSTRAINT fk_revisao_beneficio_cat
--   FOREIGN KEY (beneficio_calculo_categoria)
--   REFERENCES transformometro.beneficio_calculo_categoria (codigo);

ALTER TABLE transformometro.revisoes
  ADD CONSTRAINT chk_revisao_beneficio_calculo_categoria
  CHECK (beneficio_calculo_categoria IN (
    'economia_tempo',
    'reducao_volume',
    'ganho_capacidade',
    'economia_qualidade',
    'misto',
    'automatico'
  ));
```

**Por que na revisão (não na medição):** a categoria é política de **como interpretar** o Δ vs. referência; a medição continua sendo fatos (volume, tempo, …).

### 3.3 Cache `dashboard_calculos` (colunas novas, default 0)

Somente `ADD COLUMN` — sem recompute na migration. Recalc fica operacional (`POST /dashboard/recalcular`) **depois** do deploy.

```sql
ALTER TABLE transformometro.dashboard_calculos
  ADD COLUMN IF NOT EXISTS beneficio_calculo_categoria VARCHAR(32)
    NOT NULL DEFAULT 'economia_tempo',
  ADD COLUMN IF NOT EXISTS ganho_capacidade NUMERIC(14, 2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS economia_reducao_volume NUMERIC(14, 2) NOT NULL DEFAULT 0;
-- economia_tempo já existe
```

Views V020–V022: nova migration **recria views** incluindo colunas novas (DDL). Sem touch em dados.

### 3.4 JSON backup / OpenAPI

- Incluir `beneficio_calculo_categoria` no export/import de revisões.
- Schema Pydantic + options API (`beneficio_calculo_categoria: [...]`).

---

## 4. Comportamento do motor por categoria

### Fase 0 — `economia_tempo` (default, legado)

Manter o cálculo atual de breakdown (`economia_tempo`, retrabalho, erro, outros, recursos) → `economia_bruta`.

**Orientação de cadastro (doc + hint UI):** para essa categoria, volume da melhoria **deve** espelhar o da referência (1:1). O motor **ainda não força** 1:1 na Fase 0 (evita mudança numérica surpresa); Fase 1 pode emitir **aviso** se `vol_rev ≠ vol_ref`.

### Fase 1 — breakdown + avisos (sem mudar fórmula da bruta)

- Expor no payload: `economia_tempo`, componentes já existentes, `delta_volume`, flags:
  - `volume_acima_referencia` → sugere capacidade
  - `volume_abaixo_referencia` → sugere redução de execuções
- UI: chips explicativos; categoria default `economia_tempo`.

### Fase 2 — `ganho_capacidade` e regras explícitas

```text
Δvolume = max(0, vol_rev − vol_ref)
ganho_capacidade = Δvolume × (tempo_ref / 60) × custo_hora_ref
                   × fração_vigência
```

- `economia_bruta` (ROI): continua só custo operacional (sem capacidade), **salvo** flag futura `incluir_capacidade_no_roi`.
- Categoria `ganho_capacidade`: UI enfatiza os dois KPIs; motor sempre calcula `ganho_capacidade` quando Δvolume > 0 (mesmo se categoria = `economia_tempo`, como métrica informativa).

### Fase 2b — `reducao_volume`

Volumes **reais** (já é o caso do motor atual). Categoria só **rotula** e pode destacar na UI a parcela atribuível a Δvolume (decomposição analítica opcional, sem double-count na bruta).

### Fase 3 — `automatico` / `misto`

Motor escolhe ênfase de apresentação; totais financeiros seguem regras fixas (bruta = soma de componentes de custo; capacidade = campo à parte).

---

## 5. API e contratos

| Endpoint / artefato | Mudança |
|---|---|
| `GET/POST/PUT` revisões | Campo `beneficio_calculo_categoria` (default `economia_tempo`) |
| `GET /options` | Lista de categorias + rótulos |
| `GET .../comparativo` | `beneficio_calculo_categoria`, `ganho_capacidade`, breakdown |
| Dashboard live/snapshot | Mesmos campos nas linhas/resumo (capacidade **fora** do ROI até decisão) |
| Backup JSON | Campo na entidade `revisoes` |

Versionar contrato no doc de integração; MFE render-only.

---

## 6. Plugin (MFE)

| Tela | Mudança |
|---|---|
| Vigência / identificação da revisão | Select **Categoria de cálculo** (default Economia de tempo) |
| Medição | Hints por categoria; aviso se volume diverge da referência em `economia_tempo` |
| Comparativo | Colunas/séries: Economia (custo) · Capacidade (se > 0) · chips de categoria |
| Dashboard | KPI opcional “Ganho de capacidade”; tooltip explicando exclusão do ROI |
| Help tooltips | Textos em `helpTooltips.ts` + sync se houver bundle compartilhado |

Sem reimplementar fórmula no front.

---

## 7. Fases de entrega (ordem sugerida)

### Fase A — Fundação (DDL + default + UI declaração)
1. Migration DDL: coluna em `revisoes` + colunas em `dashboard_calculos` + (opc.) tabela catálogo **sem seed SQL**.
2. Seed de catálogo via código idempotente no boot **ou** script operacional documentado (fora do Flyway).
3. API + options + formulário revisão (default `economia_tempo`).
4. Doc: seção em `regras-de-calculo.md`.
5. Testes: default na criação; leitura de revisão sem coluna preenchida (DEFAULT).
6. Recalc operacional pós-deploy (não na migration).

### Fase B — Transparência (sem mudança de ROI)
1. Comparativo/dashboard expõem breakdown + `delta_volume` + avisos.
2. Testes de regressão golden: mesmos totais de `economia_bruta` para fixtures atuais.

### Fase C — Capacidade
1. Cálculo `ganho_capacidade` em `calc_rules`.
2. Persistência no cache (colunas já criadas na Fase A).
3. UI dual KPI; ROI inalterado.

### Fase D — Categorias avançadas / política ROI
1. `reducao_volume` / `economia_qualidade` / `automatico` com copy e eventual decomposição.
2. Flag opcional incluir capacidade no ROI (produto).

---

## 8. Testes e gates

| Tipo | O quê |
|---|---|
| Unit `calc_rules` | Default tempo; capacidade com Δvolume; redução volume não zera economia |
| Golden `test_dashboard_calculator` | Fixtures atuais = mesma `economia_bruta` sob categoria default |
| API | Create revisão sem campo → `economia_tempo` |
| Migration | `--info` / apply: só DDL; zero `UPDATE` no arquivo |
| MFE | Select default; hint volume |

---

## 9. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Mudança silenciosa de economia | Fase A–B sem alterar fórmula; golden tests |
| Cache velho sem colunas novas | DEFAULT 0 + recalc pós-deploy documentado |
| Seed em migration | Proibido; DEFAULT + seed app/script |
| Confusão ROI × capacidade | Labels explícitos; capacidade fora do ROI na Fase C |
| Views desatualizadas | Migration só recria views (DDL) |

---

## 10. Critério de pronto (MVP do plano)

- [ ] Coluna `beneficio_calculo_categoria` em `revisoes` com default `economia_tempo` (DDL only)
- [ ] Colunas de capacidade/breakdown no cache (DDL only)
- [ ] API + MFE permitem ver/editar categoria; default visível
- [ ] `regras-de-calculo.md` atualizado
- [ ] Golden tests verdes sem mudança numérica do legado
- [ ] Runbook: recalc após migrate

---

## 11. Fora de escopo (este plano)

- Backfill SQL de categorias por heurística de volume
- Alterar histórico materializado dentro da migration
- Receita, ESG, lead time, risco (categorias futuras — só menção)
- Mudança do chat/plataforma

---

## 12. Decisão registrada (produto)

- Cadastros até hoje = **economia de tempo**.
- Default de novas revisões = **economia de tempo**.
- Migrations = **somente tabelas e colunas** (e views/constraints); **sem alteração de dados** via migration.
