# Entry audit · Front-end · Página 01 — Entrada e execução

| Campo | Valor |
|---|---|
| Rota | `/apps/controllership-finance/entry-audit` |
| Família visual | lista / bancada de dados (padrão visual §9.1) |
| Permissão | `controllership-finance.access` |
| Wireframe | seção 2 do [HTML](./wireframes-auditoria-entradas.html) |

## 1. Objetivo

É a porta de entrada. O usuário informa **o período (De/Até)** e **os tipos de nota** — os mesmos dois filtros que hoje são feitos na exportação do Protheus e no Excel — e as filiais, executa a auditoria e acompanha o andamento. Abaixo, a lista de **análises anteriores** para abrir uma já feita. Quando a análise termina, a página leva ao dashboard (doc 02).

Entradas possíveis:
- menu do Portal → «Auditoria de entradas»;
- atalho do Fechamento mensal → abre com `from=<1º dia da competência>&to=<último dia>`;
- link de uma análise em andamento (`?analysis=<id>`), por exemplo enviado pela CLARA.

## 2. Estado na URL

`from`, `to`, `types`, `branches`, `analysis` (análise em andamento acompanhada). O período é livre: nenhuma data vem fixada nem sugerida — o usuário informa De e Até (pode ser um dia, uma semana, um mês). `types` vem com os tipos de nota padrão (a definir com os exemplos do Gustavo, mcp §7 P8); `branches` com todas as filiais permitidas.

## 3. Estrutura e dimensionamento

```text
┌ PageHero (compact) ───────────────────────────────────────────────────────────┐
│ eyebrow: Controladoria · Fiscal                                               │
│ h1: Auditoria de entradas                                    [▶ Executar]    │
│ descrição: Protheus × XML de NF-e e CT-e                                      │
│ ┌ FilterBar ────────────────────────────────────────────────────────────────┐ │
│ │ De [__/__/____]  Até [__/__/____]  Tipos de nota ▾  Filiais ▾              │ │
│ │                                                                           │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
[ StateBanner: análise em andamento + ProgressTracker + barra ]   (só quando há)
[ EmptyGuidance: nenhuma auditoria para este período ]           (só quando não há)
┌ SectionCard «Análises anteriores» ────────────────────────────────────────────┐
│ DataTableSection: Período · Filiais · Executada em · Por · Status · Pendentes │
└───────────────────────────────────────────────────────────────────────────────┘
```

| Bloco | > 1100px | ≤ 1100px | ≤ 768px | ≤ 480px |
|---|---|---|---|---|
| PageHero | título e ação na mesma linha | igual | ação abaixo do título, largura total | igual |
| FilterBar | uma linha (quebra natural do `FiltersRow`, `variant="extended"`) | duas linhas | botão «Filtros (n)» abre `DrawerShell` com os campos empilhados | igual |
| Banner de execução | largura total; etapas numa linha | etapas quebram | etapas em lista vertical | igual |
| Análises anteriores | tabela, 7 colunas | tabela, oculta «Por» | cards (`DataRecordCard`) | igual |

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
| Tipos de nota | `CfMultiSelectField` (← `MultiSelectField`) | `label="Tipos de nota"`, `options` da BFF (`GET …/options` → tipos de nota do Protheus com código e descrição), `selectedValues={types}`, `showBulkActions`, `searchable`, mínimo 1 |
| Filiais | `CfMultiSelectField` | `label="Filiais"`, `options` da BFF (filiais permitidas, rótulo «Matriz (01)», «Filial (02)»), `selectedValues`, `showSelectedTags={false}`, `showBulkActions`, `emptyLabel="Todas"` |

Validação da página (sem componente novo): De e Até preenchidos e `De ≤ Até`; erro mostrado no `hint` do campo Até e «Executar» desabilitado.

**Tipos de nota — a confirmar (TO_INVENTORY).** Hoje o usuário filtra no Excel por tipo de nota depois de exportar a SF1. A skill lê as colunas `Tipo da Nota` (F1_TIPO: N normal, D devolução, B beneficiamento, C complemento de preço/frete, I complemento de ICMS, P complemento de IPI) e `Espec.Docum.` (F1_ESPECIE: SPED, CTE, NFS…). Falta saber qual das duas o Gustavo filtra e quais valores ficam marcados — vem dos exemplos dele (mcp §7, P8).

### 4.3 Execução em andamento — `CfStateBanner` + `CfProgressTracker` + `CfInlineLoadingProgress` — existem

Visível quando há `analysis` na URL ou uma análise do usuário com `status in (queued, running)`.

| Componente | Props |
|---|---|
| `CfStateBanner` | `variant="default"`; texto: «Auditoria em andamento — Matriz e Filial, 01/10 a 31/10/2026»; `role="status"` no wrapper |
| `CfInlineLoadingProgress` | `percent` = `progress.percent` da BFF, `label="Andamento"`, `showPercent` |
| `CfProgressTracker` (uma linha por filial quando houver mais de uma) | `steps=[protheus, tes_book, xml, rules, result]` com `label` «Notas do Protheus», «TES e livro fiscal», «XML do Questor», «Regras», «Resultado»; `state` vindo da BFF (`complete`/`current`/`available`/`error`); `statusLabel` com contagem («612», «418/680»); `currentStepId`; `interactive={false}`; `density="compact"`; `ariaLabel="Andamento da Matriz"` |
| Texto auxiliar | «Pode sair desta página: a execução continua.» |

Falha: `CfStateBanner variant="error"` por filial que falhou, com o motivo devolvido pela BFF e `CfActionButton` «Tentar de novo a Filial» → `POST /entry-audit/analyses/{id}/rerun {branches:["02"]}`.

Atualização: `GET /entry-audit/analyses/{id}` a cada 3s enquanto `running` (React Query `refetchInterval`), parando em `done`/`failed`. Ao concluir: anúncio «Auditoria concluída» e navegação para o dashboard (doc 02), com botão «Abrir resultado» caso o usuário tenha saído do foco.

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
| `rows` | `GET /entry-audit/analyses?date_from&date_to&page` |
| `rowKey` | `row => row.id` |
| `serverPagination` | `{page, pageSize: 10, total, onPageChange}` |
| `hideSearch` | `true` |
| `onRowClick` | navega para `entry-audit/analyses/:id` |
| `emptyMessage` | `"Nenhuma análise anterior."` |

Colunas (`DataTableColumn`):

| `key` | `header` | `render` | `align` |
|---|---|---|---|
| `period` | Período | «01/10–31/10/2026» | left |
| `branches` | Filiais | «Matriz, Filial» | left |
| `executedAt` | Executada em | data e hora | left |
| `requestedBy` | Por | nome; «CLARA para Michael» quando pedida pela CLARA | left |
| `status` | Status | `CfStatusBadge` (`success` Concluída · `info` Em andamento · `danger` Falhou · `warning` Parcial) | left |
| `pending` | Pendentes | número | right |
| `high` | Altas | número | right |

Mobile (≤ 768px): `DataTableSection` alterna para cards nativos; cada card usa `CfDataRecordCard` com `title`=período, `subtitle`=filiais, `status`=badge, `fields`=[Pendentes, Altas, Executada em].

## 5. Dados

| Bloco | Rota da BFF |
|---|---|
| Opções | `GET /entry-audit/analyses/options` → filiais permitidas (código, nome, UF) e tipos de nota (código, descrição, padrão marcado) |
| Executar | `POST /entry-audit/analyses` (corpo no plano §4A.4) → 202 `{analysis}` |
| Andamento | `GET /entry-audit/analyses/{id}` |
| Reexecutar filial | `POST /entry-audit/analyses/{id}/rerun` |
| Histórico | `GET /entry-audit/analyses` |

> A rota `GET /entry-audit/analyses/options` é **nova** em relação ao plano (§4A.4) e entra no contrato da E1.

## 6. Estados

| Estado | Comportamento |
|---|---|
| Carregando opções | `CfLoadingCard` no lugar da FilterBar (padrão de loading do Portal) |
| Período inválido (vazio ou `De > Até`) | erro no campo Até; «Executar» desabilitado |
| Análise igual já em andamento | o POST devolve a existente; a página passa a acompanhá-la e mostra «Já existe uma auditoria em andamento para estes filtros.» |
| Erro ao executar | `CfStateBanner variant="error"` com a mensagem da BFF; filtros preservados |
| Histórico vazio | `emptyMessage` da tabela |

## 7. Acessibilidade

`h1` no PageHero; `h2` «Análises anteriores». O banner de andamento é `aria-live="polite"` e anuncia só mudança de etapa e conclusão (não cada percentual). O botão Executar tem `aria-describedby` para o resumo dos filtros. No mobile, o painel de filtros é um diálogo com foco preso e retorno ao botão que o abriu.
