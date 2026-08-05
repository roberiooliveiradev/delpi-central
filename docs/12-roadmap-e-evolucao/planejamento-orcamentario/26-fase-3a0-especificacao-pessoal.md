# 26 — Fase 3A.0: Especificação Pessoal (escopo enxuto)

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Tipo:** análise e documentação — sem código, migration, endpoint, tela ou manifesto.

---

## 1. Regras confirmadas

| # | Regra | Fonte |
|---|--------|--------|
| R1 | Filiais oficiais: `01` Santa Catarina (Jaraguá do Sul) e `02` Espírito Santo (Rio Bananal). | Convenção Delpi / brief desta fase |
| R2 | Planejamento pertence a **uma filial**. | Brief 3A.0 |
| R3 | Centro de custo é selecionado **dentro da filial**. | Brief 3A.0 |
| R4 | O mesmo código de CC pode existir nas duas filiais; são **planejamentos distintos**. | Brief 3A.0 |
| R5 | Identidade funcional: `exercício + filial + centro de custo`. | Brief 3A.0 |
| R6 | Responsabilidades, lançamentos, workflow e consolidação **preservam filial**; sem misturar filiais. | Brief 3A.0 |
| R7 | Admin **não digita** CC: filial → lista ERP → grava código, descrição e filial. | Brief 3A.0 |
| R8 | Colaboradores, cargos, salários, folha, benefícios e encargos **não** vêm das integrações atuais; não inventar percentuais/cálculos. | Brief 3A.0 + `06-integracao-erp.md` |
| R9 | Carta pede pessoal por **seção/CC e cargo** e projeção mês a mês; planilha 2027 só tem **unidade + área** e âncoras pontuais. | `01-especificacao-funcional-consolidada.md` § 2.1–2.2; decisão D2 em `10-riscos…` |
| R10 | Estagiários/temporários **fora** do quadro Pessoal (orçar em despesas por CC). | Carta, citada em `01` |
| R11 | Módulo de responsabilidade já existe com `module` (hoje só `capex`); Pessoal reutilizará o mesmo mecanismo com módulo dedicado. | V002 + `responsibility_constants.py` |
| R12 | Material de **Previsão de Receita** não foi localizado; não há evidência textual de pré-requisito Receita→Pessoal nos docs Fase 0. | `00-diagnostico.md`, `01` § 2.4 |

---

## 2. Unidade de planejamento recomendada

### Identidade / ownership / workflow (recomendado)

```text
exercício + filial (unit_id) + centro de custo
```

Alinha com R2–R5, com o padrão já usado no CAPEX (plano por CC) e com a reutilização de `budget_responsibilities`.

### Granularidade do **conteúdo** das linhas (não fechada)

| Opção | Material | Status |
|-------|----------|--------|
| A — Agregado por **área** (PRODUCAO/MOD/MOI, VENDAS, ADMINISTRACAO) + colunas pontuais | Planilha Pessoal 2027 | Contrato implícito do arquivo |
| B — **CC + cargo** + série mensal | Carta | Pedido normativo da Carta; **não** está na planilha |

**Recomendação desta fase:**

1. **Fechar a identidade em filial + CC** (obrigatório para responsabilidades e workflow).  
2. **Não implementar cargo×CC nem série mensal** até decisão explícita do negócio (D2).  
3. Conteúdo MVP, se autorizado a avançar sem D2: apenas **headcounts manuais** nas âncoras da planilha, associados ao plano do CC — **sem** inventar cargos, salários ou encargos.

---

## 3. Campos encontrados nos materiais

### Planilha `ORÇAMENTO PESSOAL 2027` (aba `DELPI`)

| Campo / dimensão | Natureza |
|------------------|----------|
| Unidade (ex.: DELPI JARAGUA - CHICOTES, DELPI ESPIRITO SANTO, TOTAL DELPI) | Estrutura |
| Área (PRODUCAO, VENDAS, ADMINISTRACAO, TOTAL) | Estrutura |
| Sublinha PRODUCAO: MAO OBRA DIRETA / INDIRETA | Estrutura |
| 2025 DEZEMBRO | Headcount (digitável) |
| 2026 OUTUBRO | Headcount (digitável) |
| PREVISTO DEZEMBRO (agrupado sob 2026 no cabeçalho — ambíguo) | Headcount (digitável) |
| 2027 DEZEMBRO | Headcount (digitável) |
| Var. 26/25 (`E/C`), Var. 27/26 (`G/E`) | Calculado na planilha |
| Totais por área / unidade / Delpi | Calculado (soma) |

Valores no arquivo analisado: todos **0** (template).

### Carta (orientações Pessoal)

| Orientação | Campo estruturado na planilha? |
|------------|--------------------------------|
| MO com ganhos de produtividade | Não (narrativa) |
| Previsão por seção/CC e cargo | Não |
| Projeção mês a mês → posição 31/12 | Não (só âncoras) |
| Estagiários/temporários fora do quadro | Regra de exclusão |

---

## 4. Campos que serão manuais (MVP)

Enquanto não houver fonte ERP de quadro/salários:

| Campo | Manual | Observação |
|-------|--------|------------|
| Filial | Seleção | Catálogo `01`/`02` |
| Centro de custo (código + descrição) | Seleção ERP | Snapshot na gravação |
| Headcounts das colunas da planilha (quando adotadas) | Entrada numérica | Inteiros ≥ 0 — validação a confirmar |
| Área / categoria de linha (MOD, MOI, VENDAS…) | Seleção de lista fechada da planilha | Se MVP seguir shape planilha |
| Justificativa de variação | Texto | **Não** exigido pelos materiais — pendente |
| Cargo, salário, encargos, benefícios, admissões, desligamentos, transferências, promoções | — | **Ausentes** nos materiais utilizáveis / ERP; não modelar agora |

Totais e variações percentuais: calculados no servidor **somente** se a regra da planilha for adotada (e após esclarecer ambiguidade PREVISTO DEZEMBRO / uso da coluna OUTUBRO — D9).

---

## 5. Regra filial + centro de custo

```text
Selecionar filial (01|02)
→ GET filtros ERP com branch = filial
→ Usuário escolhe CC (codigo + descricao)
→ Persistir: exercise_id + unit_id(=filial) + cost_center_code + cost_center_name_snapshot
```

- Mesmo `cost_center_code` em `01` e `02` ⇒ **dois** planos / vínculos.  
- Queries e consolidação **sempre** filtram por `unit_id`.  
- Responsabilidade Pessoal: mesmo padrão CAPEX, com `module = personnel` (ou `headcount` — nome a padronizar) e chave lógica incluindo filial.

---

## 6. Fonte ERP reutilizável (centros de custo)

| Item | Valor |
|------|--------|
| Plugin de referência | `plugins/financeiro-centro-custo` |
| Endpoint | `GET /apps/api-delpi/financeiro/despesas-centro-custo/filtros` |
| operationId | `get_financeiro_despesas_centro_custo_filtros` |
| View SQL | `dbo.vw_fin_despesas_centro_custo` (`despesas_centro_custo_sql.py`) |
| Parâmetro filial | `branch` (filtra `filial` na view) |
| Retorno CC | `centros_custo[]`: `{ codigo, descricao }` |
| Retorno filiais | `filiais[]`: `{ codigo }` |

**Ressalva (já em `06-integracao-erp.md`):** a lista vem da view de **despesas** no período informado — pode não cobrir todos os CCs “de orçamento”. Não inventar `CTT010` nesta fase; se a cobertura falhar, decisão de negócio (ampliar período / outra fonte).

Fluxo admin futuro: **não** criar catálogo paralelo digitável; opcionalmente espelhar (código, descrição, filial) como cache/snapshot após seleção ERP.

---

## 7. Impacto no modelo atual

### O que já ajuda

- `org_units` pode representar filiais `01`/`02`.  
- `budget_responsibilities` já carrega `unit_id` + `cost_center_id` + `module`.  
- CAPEX já planeja por CC com `unit_id` denormalizado.

### O que **não** atende R4/R5 hoje

| Artefato | Problema |
|----------|----------|
| `org_cost_centers.code` **PRIMARY KEY** | Impede o mesmo código nas duas filiais |
| `capex_plans` `UNIQUE (exercise_id, cost_center_id)` | Colapsa filiais distintas |
| Responsabilidades ativas `UNIQUE (…, cost_center_id)` | Idem |
| Escopos Fase 1 (`user_org_scopes`) | Referenciam `cost_center_code` global |

**Correção incremental necessária (não implementar agora):** chave composta `(unit_id, code)` no catálogo de CC (ou PK surrogate + unique composta); atualizar FKs/uniques de responsabilidades, planos CAPEX, investimentos e escopos; migrar dados existentes; selects admin via ERP filtrados por filial.

Até essa correção, **não** é seguro gravar CCs homônimos nas duas filiais.

### Extensão Pessoal

- Novo `module` em responsabilidades (`personnel` / `headcount`).  
- Subject de workflow análogo ao CAPEX: um plano por `(exercise_id, unit_id, cost_center_id)`.  
- Reutilizar máquina de estados já usada no CAPEX (`draft` → `submitted` → …), sem acoplar tabelas CAPEX.

---

## 8. Decisões pendentes (negócio)

| ID | Pergunta | Bloqueia |
|----|----------|----------|
| D-PE-1 | Conteúdo das linhas: shape **planilha (área)** ou Carta (**cargo×CC** + mensal)? | Modelagem de linhas |
| D-PE-2 | “PREVISTO DEZEMBRO” é competência 2026? Coluna OUTUBRO entra nas variações? (D9) | Cálculos |
| D-PE-3 | Receita aprovada é pré-requisito para liberar Pessoal? (**não confirmado** nos materiais) | Ordem de módulos |
| D-PE-4 | View de despesas basta como mestre de CC ou exige outra fonte? | Cadastro admin |
| D-PE-5 | Cadeia de aprovação Pessoal (gestor CC → diretor → diretoria) — espelhar CAPEX? | Workflow |
| D-PE-6 | Nome canônico do módulo: `personnel` vs `headcount` | Perms / API |
| D-PE-7 | Justificativa obrigatória para variação de headcount? | UX / validação |

---

## 9. Roadmap (etapas pequenas — não implementar agora)

### Etapa 1 — Filial + centro de custo (pré-requisito transversal)

- Corrigir identidade `unit_id + cost_center_code` no catálogo e FKs/uniques afetados.  
- Endpoint/admin: select filial → `filtros` ERP → persistir snapshot.  
- Ajustar responsabilidades e CAPEX para a nova chave (migração cuidadosa, só `up`).

### Etapa 2 — Backend Pessoal

- Schema: plano por `(exercise, unit, CC)` + linhas conforme D-PE-1.  
- CRUD + autosave + validação mínima (inteiros, escopo).  
- Responsabilidades `module=personnel`.  
- **Sem** cálculos inventados; totais só se D-PE-1/2 fecharem com a planilha.

### Etapa 3 — Frontend de preenchimento

- Lista “meus CCs” Pessoal; grade de headcount; estados vazios/erro.  
- Selects org via ERP (filial→CC), sem digitação livre de código.

### Etapa 4 — Workflow

- Reusar padrão CAPEX (submit / request-changes / reject / approve, SoD, locks).  
- Perms `.headcount.*` / `.personnel.*` + approve.

### Etapa 5 — Consolidação e exportação

- Indicadores e Excel por filial / área (se houver) / CC — sempre com filtro de filial.  
- Sem misturar `01` e `02`.

---

## 10. Status desta fase

**STATUS: CONCLUÍDO COM RESSALVAS**

Ressalvas: D2 (área vs cargo×CC) e pré-requisito Receita continuam abertos; modelo atual de PK de CC **impede** homônimos entre filiais até a Etapa 1.
