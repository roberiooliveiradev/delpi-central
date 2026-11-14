# Entry audit · Front-end · Página 01 — Entrada e execução

| Campo | Valor |
|---|---|
| Rota | `/apps/controllership-finance/entry-audit` |
| Família visual | lista / bancada de dados (padrão visual §9.1) |
| Permissão | `controllership-finance.access` |
| Wireframe | seção 2 do [HTML](./wireframes-auditoria-entradas.html) |
| Contrato | reconciliado com a BFF publicada (T10.0, 2026-11-14) — [README](./README.md#reconciliação-t100) |

## 1. Objetivo

É a porta de entrada. O usuário informa **o período (De/Até)** e **os tipos de documento** — os mesmos dois filtros que hoje são feitos na exportação do Protheus e no Excel — e as filiais, executa a auditoria e acompanha o andamento. Abaixo, a lista de **análises anteriores** para abrir uma já feita. Quando a análise termina, a página leva ao dashboard (doc 02).

Entradas possíveis:
- menu do Portal → «Auditoria de entradas»;
- atalho do Fechamento mensal → abre com `from=<1º dia da competência>&to=<último dia>`;
- link de uma análise em andamento (`?analysis=<id>`), por exemplo enviado pela CLARA.

## 2. Estado na URL

`from`, `to`, `docs`, `branches`, `analysis` (análise em andamento acompanhada). O período é livre: nenhuma data vem fixada nem sugerida — o usuário informa De e Até (pode ser um dia, uma semana, um mês). `docs` vem com NF-e e CT-e marcados; `branches` com todas as filiais permitidas.

## 3. Estrutura e dimensionamento

```text
┌ PageHero (compact) ───────────────────────────────────────────────────────────┐
│ eyebrow: Controladoria · Fiscal                                               │
│ h1: Auditoria de entradas                                    [▶ Executar]    │
│ descrição: Protheus × XML de NF-e e CT-e                                      │
│ ┌ FilterBar ────────────────────────────────────────────────────────────────┐ │
│ │ De [__/__/____]  Até [__/__/____]  Tipos de documento ▾  Filiais ▾              │ │
│ │                                                                           │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
[ StateBanner: análise em andamento + ProgressTracker + barra ]   (só quando há)
[ EmptyGuidance: nenhuma auditoria para este período ]           (só quando não há)
┌ SectionCard «Análises anteriores» ────────────────────────────────────────────┐
│ DataTableSection: Período · Filiais · Documentos · Executada em · Origem · Status │
└───────────────────────────────────────────────────────────────────────────────┘
```

| Bloco | > 1100px | ≤ 1100px | ≤ 768px | ≤ 480px |
|---|---|---|---|---|
| PageHero | título e ação na mesma linha | igual | ação abaixo do título, largura total | igual |
| FilterBar | uma linha (quebra natural do `FiltersRow`, `variant="extended"`) | duas linhas | botão «Filtros (n)» abre `DrawerShell` com os campos empilhados | igual |
| Banner de execução | largura total; etapas numa linha | etapas quebram | etapas em lista vertical | igual |
| Análises anteriores | tabela, 6 colunas | tabela, oculta «Origem» | cards (`DataRecordCard`) | igual |

Alturas: PageHero compacto pelo kit; banner de execução ~120px; tabela com `pageSize` 10.

## 4. Componentes

### 4.1 `CfPageHero` (← `PageHero`) — existe

| Prop | Valor |
|---|---|
| `density` | `"compact"` |
| `eyebrow` | `"Controladoria · Fiscal"` |
| `title` | `"Auditoria de entradas"` |
| `description` | `"Protheus × XML de NF-e e CT-e"` |
| `actions` | `CfActionButton` «Executar auditoria» (primário; `disabled` enquanto o período for inválido ou houver análise igual em andamento) |
| `children` | a `FilterBar` (4.2) |
| `highlights` | não usa nesta página |

### 4.2 `FiltersRow`/`FilterBar` (← `createDashboardFiltersKit`) — existe

| Prop | Valor |
|---|---|
| `ariaLabel` | `"Filtros da auditoria"` |
| `variant` | `"extended"` |
| `trailing` | `ClearFiltersButton` («Restaurar padrão») |

Campos dentro da barra, nesta ordem:

| Campo | Componente | Props principais |
|---|---|---|
| De | `CfDateField` (← `DateField`) | `label="De"`, `type="date"`, `value={from}`, `onChange`, `required` |
| Até | `CfDateField` | `label="Até"`, `type="date"`, `value={to}`, `onChange`, `required`; `hint="Data de recebimento das notas (como na exportação da SF1)."` |
| Tipos de documento | `CfMultiSelectField` (← `MultiSelectField`) | `label="Tipos de documento"`, `options` de `GET …/analyses/options` → `document_types[]` mapeado `{value: code, label: label}` (`nfe` «NF-e», `cte` «CT-e»; o campo de texto é `label`, não `description`), `selectedValues={docs}` (padrão: os de `default: true`), `showBulkActions`, mínimo 1 |
| Filiais | `CfMultiSelectField` | `label="Filiais"`, `options` de `branches[]` (`code`, `name`, `state`, `tax_id`) mapeado `{value: code, label: "<name> (<code>)"}`, `selectedValues`, `showSelectedTags={false}`, `showBulkActions`, `emptyLabel="Todas"`. `tax_id` não é exibido |

Validação da página (sem componente novo): De e Até preenchidos e `De ≤ Até`; erro mostrado no `hint` do campo Até e «Executar» desabilitado.

**Tipos de documento — decisão do owner (2026-11-13).** Hoje o usuário filtra a SF1 pela coluna **Espécie do documento** (`F1_ESPECIE`) em **SPED** e **CTE**, e exporta do Questor **NF-e** e **CT-e**. Na Delpi, SPED = NF-e (modelo 55) e CTE = CT-e (modelo 57), nos dois sistemas. O campo mostra «NF-e» e «CT-e» e aplica o mesmo filtro aos dois lados: Protheus por espécie (SPED/CTE), Questor por tipo (NF-e/CT-e). Outras espécies (NFS, CF…) ficam fora da auditoria.

### 4.3 Execução em andamento — `CfStateBanner` + `CfProgressTracker` + `CfInlineLoadingProgress` — existem

Visível quando há `analysis` na URL ou uma análise com `status in (queued, running)` (`GET …/analyses?status=running|queued`).

| Componente | Props |
|---|---|
| `CfStateBanner` | `variant="default"`; texto: «Auditoria em andamento — Matriz e Filial, 01/10 a 31/10/2026»; `role="status"` no wrapper |
| `CfInlineLoadingProgress` | **sem percentual** (a BFF não devolve `progress.percent` e a UI não o calcula). Sempre modo indeterminado, `showPercent={false}`; na etapa `reading_xml` o `label` mostra o contador do contrato: «XML lidos: 418 de 680» (`counts.xml_read` de `counts.xml_expected`) |
| `CfProgressTracker` (uma linha por filial = um item de `runs[]`) | `steps=[reading_protheus, reading_xml, auditing, saving, done]` com `label` «Notas do Protheus», «XML do Questor», «Regras», «Gravando», «Resultado»; o `state` de cada passo é **derivado de `runs[].stage`** (passos anteriores `complete`, o do estágio `current`, os seguintes `available`; `runs[].status = failed` → `error` no passo em que parou; `stage = failed` não é passo); `statusLabel` só no passo `reading_xml`: «418/680» de `counts.xml_read`/`counts.xml_expected` (e `documents_read` como contagem de notas do Protheus no 1º passo); `currentStepId`; `interactive={false}`; `density="compact"`; `ariaLabel="Andamento da Matriz"` |
| Texto auxiliar | «Pode sair desta página: a execução continua.» |

Estágios: `runs[].stage` ∈ `reading_protheus` · `reading_xml` · `auditing` · `saving` · `done` (concluída) · `partial` (concluída, mas com XML indisponível) · `failed`; vazio na fila. Estágio fora da lista = «Preparando». `runs[].status` ∈ `queued` · `running` · `done` · `partial` · `failed`.

Falha: `CfStateBanner variant="error"` por filial com `runs[].status = failed`, com o motivo de `runs[].error` (código, ex.: `XML_LISTING_UNAVAILABLE`, traduzido em texto do MFE) e `CfActionButton` «Tentar de novo a Filial» → `POST /entry-audit/analyses/{id}/rerun {branches:["02"]}` (202; 409 `RUN_IN_PROGRESS` se a filial já está na fila → mensagem «Esta filial já está sendo auditada»). Filial `partial`: aviso informativo «N notas sem XML» (`runs[].counts.xml_unavailable_count`), sem tratar como falha.

Atualização: `GET /entry-audit/analyses/{id}` a cada 3s enquanto `queued`/`running` (React Query `refetchInterval`), parando em `done`/`partial`/`failed`. Ao concluir: anúncio «Auditoria concluída» e navegação para o dashboard (doc 02), com botão «Abrir resultado» caso o usuário tenha saído do foco. As leituras de resultado respondem 409 `ANALYSIS_NOT_READY` até existir ao menos uma filial concluída.

### 4.4 Vazio — `CfEmptyGuidance` (← `EmptyGuidance`) — existe

| Prop | Valor |
|---|---|
| `variant` | `"panel"` |
| `title` | `"Nenhuma auditoria para este período"` |
| `message` | `"A auditoria confere cada nota de entrada do Protheus com o XML do fornecedor e aponta o que a contabilidade costuma devolver: CT-e, CFOP, CST, base de ICMS/IPI, chave, CNPJ, Simples e presumido de SC."` |
| `children` | `CfActionButton` «Executar auditoria» |
| `role` | `"status"` |

### 4.5 Análises anteriores — `CfSectionCard` + `DataTableSection` (cfDataTableUi) — existem

`CfSectionCard`: `title="Análises anteriores"`, `subtitle="Clique para abrir o resultado"`.

`DataTableSection`:

| Prop | Valor |
|---|---|
| `title` | `"Análises anteriores"` (oculto visualmente: o título já está no card) |
| `rows` | `GET /entry-audit/analyses?date_from&date_to&page&page_size=10` → `data.items[]` |
| `rowKey` | `row => row.id` |
| `serverPagination` | `{page, pageSize: 10, total, onPageChange}` |
| `hideSearch` | `true` |
| `onRowClick` | navega para `entry-audit/analyses/:id` |
| `emptyMessage` | `"Nenhuma análise anterior."` |

Colunas (`DataTableColumn`):

Colunas **somente com campos de `_public_analysis`** (`id`, `date_from`, `date_to`, `document_types`, `branches`, `status`, `requested_via`, `created_at`, `finished_at`). A lista não traz quem pediu (nome), pendentes nem altas: esses números só existem em `summary` da análise aberta e **não** entram na tabela (nada de N chamadas de `summary` por linha).

| `key` | `header` | Campo | `render` | `align` |
|---|---|---|---|---|
| `period` | Período | `date_from`, `date_to` | «01/10–31/10/2026» | left |
| `branches` | Filiais | `branches` (`01`, `02`) | «Matriz, Filial» (nome vem de `options`) | left |
| `documents` | Documentos | `document_types` | «NF-e, CT-e» (`label` de `options`) | left |
| `executedAt` | Executada em | `created_at` (e `finished_at` no `title`) | data e hora | left |
| `origin` | Origem | `requested_via` | `user` → «Manual»; `clara` → «CLARA» | left |
| `status` | Status | `status` | `CfStatusBadge` (`success` Concluída `done` · `info` Em andamento `queued`/`running` · `danger` Falhou `failed` · `warning` Parcial `partial` — XML indisponível em alguma nota) | left |

Mobile (≤ 768px): `DataTableSection` alterna para cards nativos; cada card usa `CfDataRecordCard` com `title`=período, `subtitle`=filiais, `status`=badge, `fields`=[Documentos, Executada em, Origem].

## 5. Dados

| Bloco | Rota da BFF |
|---|---|
| Opções | `GET /entry-audit/analyses/options` → `{branches:[{code,name,state,tax_id}], document_types:[{code,label,species,default}]}` |
| Executar | `POST /entry-audit/analyses` com `{date_from, date_to, document_types, branches, via}` → 202 `{id, status, created}` (`via` omitido = `user`; o MFE nunca envia `clara`) |
| Andamento | `GET /entry-audit/analyses/{id}` → `{id, status, date_from, date_to, document_types, branches, runs[{branch,status,stage,documents_read,xml_downloaded,counts,error}], counts, config}` |
| Reexecutar filial | `POST /entry-audit/analyses/{id}/rerun` `{branches}` → 202 |
| Histórico | `GET /entry-audit/analyses?date_from&date_to&branch&status&page&page_size` → `{items, page, page_size, total}` |

`POST` com `created: false` = já existia análise `queued`/`running` com o mesmo período, tipos e filiais: o MFE passa a acompanhar o `id` devolvido. Análise `done`, `partial` ou `failed` não é reaproveitada (nasce outra). Erros 422 (`INVALID_PERIOD`, `INVALID_BRANCH`, `INVALID_DOCUMENT_TYPE`) viram mensagem no formulário. `config` (`presumed_credit_tes`, `freight_cfop_suffix`, `xml_lookback_days`, `unmatched_grace_days`, `tolerance`) é só leitura e não é exibido nesta página.

## 6. Estados

| Estado | Comportamento |
|---|---|
| Carregando opções | `CfLoadingCard` no lugar da FilterBar (padrão de loading do Portal) |
| Período inválido (vazio ou `De > Até`) | erro no campo Até; «Executar» desabilitado |
| Análise igual já em andamento | o POST devolve a existente (`created: false`); a página passa a acompanhá-la e mostra «Já existe uma auditoria em andamento para estes filtros.» |
| Erro ao executar | `CfStateBanner variant="error"` com a mensagem da BFF; filtros preservados |
| Histórico vazio | `emptyMessage` da tabela |

## 7. Acessibilidade

`h1` no PageHero; `h2` «Análises anteriores». O banner de andamento é `aria-live="polite"` e anuncia só mudança de etapa e conclusão (não cada contador de XML). O botão Executar tem `aria-describedby` para o resumo dos filtros. No mobile, o painel de filtros é um diálogo com foco preso e retorno ao botão que o abriu.
