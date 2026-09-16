# Portal Suprimentos — Roadmap Transforma+

> **Papel:** visão de negócio e backlog Transforma+ para Suprimentos.  
> **Não substitui** contratos técnicos, ADRs nem o plano executável página-a-página.  
> **Não autoriza** implementação, cutover, migration, permission nova ou mudança de regra OTD/ESTSEG/fiscal.  
> **BASE HEAD de consolidação:** `d9e2fe1a94ab3556119afc0e44a26f72bae5763a` (2026-09-16).

## 1. Como ler este documento

| Símbolo / rótulo | Significado |
|---|---|
| Informado/Observado | Fato relatado pela área (sem prova de código) |
| Calculado | Resultado determinístico a partir de dados homologados |
| Hipótese | Precisa de validação |
| Proposto | Futuro / requisito candidato |
| Ainda não sabemos | Lacuna explícita |
| Existente / Parcial / Em validação | Estado no monorepo (ver matriz §7) |

**Playbook solicitado** `playbook_transforma_suprimentos_controladoria.md`: **Ainda não localizado** no workspace (2026-09-16). Conteúdo abaixo usa o EXECUTION BRIEF Transforma+ + corpus canônico de `docs/12-roadmap-e-evolucao/supplies/` + inventário de código. Sem o arquivo físico, itens do brief permanecem **Proposto / Em validação**, não “Existente”.

### Autoridades técnicas (não duplicar aqui)

| Documento | Uso |
|---|---|
| [README.md](./README.md) | Status E1–E8, fila, gates |
| [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) | Plano executável / ledger |
| [API-ROUTES.md](./API-ROUTES.md) | Contratos BFF |
| [MATRIZ-BOUNDARIES.md](./MATRIZ-BOUNDARIES.md) | Ownership |
| [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) | Ativos e legado |
| [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) | RBAC |
| [DATA-MODEL.md](./DATA-MODEL.md) | Postgres produto |
| [INTEGRACOES.md](./INTEGRACOES.md) | HTTP / authz |
| [KPI-FICHAS.md](./KPI-FICHAS.md) | Indicadores homologados |
| [DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md) | IA / UX |
| [DECISOES_FUNCIONAIS_PENDENTES.md](./DECISOES_FUNCIONAIS_PENDENTES.md) | Decisões abertas |
| ADRs `./adr/` | Decisões arquiteturais |

**Boundaries vigentes:** Core = RBAC · `api-delpi` = SQL/TOTVS · `supplies-api` = composição Portal · `plugins/supplies` = UX · `purchase-requests-api` = owner SC até C2.

**Irmão Controladoria:** [../financeiro-controladoria/ROADMAP.md](../financeiro-controladoria/ROADMAP.md) — custos de importação compartilham **fonte de dados**, visões por perfil.

---

## 2. Contexto de produto

O Portal Suprimentos (`supplies`) já entrega jornadas operacionais E1–E8 (Início, Overview, OTD analytics, SC C1, PC lista/detalhe). A fila nativa (Entregas, ESTSEG no portal, Fornecedores 360, Importações, etc.) continua **bloqueada** até autorização página-a-página.

Transforma+ acrescenta **necessidades de negócio** (qualidade da SC, contexto Vendas→Compras, pré-validação de NF, importações, inteligência de compras) que **não** estão todas no código e **não** devem ser confundidas com páginas já fechadas.

---

## 3. Temas Transforma+ (descoberta)

### 3.1 Contexto Vendas → Compras (SUP-001 / SUP-002)

**Problema (Informado/Observado — brief):** informações usadas na formação do preço de venda não chegam estruturadas ao comprador.

**Necessidade proposta:** relacionar proposta/orçamento, produto/material, fornecedor de referência, quantidade/preço de referência, tabela, demanda, pedido efetivo, quantidade/preço comprados — com comparação **ORÇADO × TABELA × COMPRADO**, sem acesso indiscriminado à formação inteira.

**Chamados citados (sem significado técnico inferido):** 691, 593.

**Estado:** Proposto · identificador formação↔pedido = Ainda não sabemos.

### 3.2 Solicitação de Compra — SC (SUP-003 / SUP-004 / SUP-005)

Consolidar qualidade da SC, campos obrigatórios, especificação por categoria, aprovação/alçadas, responsável atual, cobrança, devolução/correção, retrabalho, valor aprovado × pedido.

**Destacar (Proposto):** TEMPO DE APROVAÇÃO versus TEMPO SOB RESPONSABILIDADE DE COMPRAS.

**Chamado citado:** 635.

**Estado no código:** lista/detalhe/export C1 **Existente** (`purchase-requests-api` + BFF). Workflow de alçada/aprovação = P-06 **BLOQUEADO_COM_EVIDENCIA** — não criar permission de aprovação sem prova.

### 3.3 Inteligência de Compras (SUP-006)

Referências candidatas (Proposto, sem inventar fontes): LME/LMI, dólar, petróleo, outros índices **somente se homologados**.

**Chamado citado:** 527.

### 3.4 Estoque de Segurança (SUP-007)

Relacionar ESTSEG cadastrado, lead time, consumo, referência ideal.

**Fórmula oficial de “referência ideal”:** `A DEFINIR / REQUER HOMOLOGAÇÃO DA ÁREA` — não inventar.

**Estado:** plugin `estoque-seguranca` + api-delpi `/supplies/safety-stock*` = **Existente**; absorção Portal `/safety-stock` = **Proposto** (fila E11). Ver [../estoque-seguranca/README.md](../estoque-seguranca/README.md).

### 3.5 Item sem consumo / descontinuado (SUP-008)

Relacionar produto, MP, estrutura, consumo, status, estoque, pedidos abertos, risco de recompra sem demanda.

**Primeira solução proposta:** alerta/recomendação. **Não** bloqueio automático sem regra oficial.

### 3.6 Fornecedores / OTD (SUP-009)

| Camada | Estado | Evidência |
|---|---|---|
| KPI OTD compras Overview/analytics | Existente | `KPI-FICHAS.md` KPI-OTD; api-delpi `get_supplies_otd` |
| Página `/suppliers/otd` no Portal | Proposto | fila README; placeholder |
| BI Atraso SC × regra nativa | Em validação | P-03 |
| Supplier 360 | Proposto | P-11 Qualidade fora do P0 |

**Não alterar** lógica do indicador neste roadmap. Separar: regra atual · mudanças já implementadas · regra desejada · naturezas/itens excluídos (homologação).

### 3.7 Entrada de Nota Fiscal (SUP-010 / SUP-011)

Pré-validação futura (Proposto) para pedido, SC, datas, valores, condição de pagamento, CNPJ, fornecedor, produto, ICMS, IPI, origem, faturamento parcial, código fornecedor × código interno — **sem inventar regra fiscal**.

Separar fluxo normal de exceções (retorno, devolução, beneficiamento, consumo, demais cenários localizados).

**Estado:** app próprio `lancamento-notas-fiscais` = **Existente** ([../lancamento-notas-fiscais/](../lancamento-notas-fiscais/)); absorção no Portal Suprimentos = **Ainda não localizado** / fora da fila imediata.

### 3.8 Importações (SUP-012 / SUP-013)

Consolidar processo, fornecedor, produtos, status, valores, despesas, custo internalizado, previsão × realizado, vínculo pedido/estoque, pendências.

**ACSI:** string/app **Ainda não localizado** no monorepo; Core local sem “Análise - Importações” (P-05 / INVENTARIO). Inventariar antes de cadastro novo.

**Custos de importação:** mesma fonte de dados que Controladoria · visões por perfil — ver [../financeiro-controladoria/ROADMAP.md](../financeiro-controladoria/ROADMAP.md) CTL-007. Owner técnico = `TO_INVENTORY`.

---

## 4. Capacidades transversais (CORE-*)

| ID | Tema | Estado | Nota |
|---|---|---|---|
| CORE-001 | Tarefas vinculadas a objetos | Proposto no Portal Suprimentos (`/my-tasks` placeholder); Existente no Comercial (outro BC) | Não copiar ownership Comercial |
| CORE-002 | Comunicação contextual | Proposto | Preocupação com Teams / e-mail / WhatsApp / Minha DELPI — canal oficial = Ainda não sabemos |
| CORE-003 | Governança de notificações | Parcial | Jobs SC/PC em `purchase-requests-api` → Core; canal Portal = INTEGRACOES |
| CORE-004 | IA contextual | Proposto (doc) | [DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md); guardrails: permissões, não inventar dados, fonte, sugestão≠decisão, sem gravação ERP sem fluxo |
| CORE-005 | Integração/RBAC entre portais | Em validação | Boundaries; sem permission por botão |

---

## 5. Backlog estável (SUP-*)

Cada item: problema · objetivo · estado · dependências · fonte · requisito · aceite · pendências. **Sem datas.** Prioridade = `PRIORIDADE PROPOSTA` quando houver recomendação.

### SUP-001 — Contexto Vendas → Compras

| Campo | Conteúdo |
|---|---|
| Problema | Formação de preço não chega estruturada ao comprador |
| Objetivo | Contexto mínimo autorizado na jornada de compra |
| Estado | Proposto |
| Dependências | Identificador formação↔pedido; campos autorizados; CRM/comercial |
| Fonte | Brief Transforma+; chamados 691/593 (sem semântica inferida) |
| Requisito | Relacionar proposta/material/fornecedor/qtd/preço ref. × demanda/pedido |
| Aceite | Comprador vê contexto autorizado; sem exposição indiscriminada |
| Pendências | Contrato CRM; campos; ownership de leitura |

### SUP-002 — Orçado × tabela × comprado

| Campo | Conteúdo |
|---|---|
| Problema | Comparação de preços fragmentada |
| Objetivo | Visão ORÇADO × TABELA × COMPRADO |
| Estado | Proposto |
| Dependências | SUP-001; histórico de preços (P-15) |
| Fonte | Brief |
| Requisito | Comparação auditável no escopo autorizado |
| Aceite | Três valores distinguíveis com fonte |
| Pendências | Definição de “tabela” canônica |

### SUP-003 — Qualidade / especificação da SC

| Campo | Conteúdo |
|---|---|
| Problema | SC incompleta gera retrabalho |
| Objetivo | Campos obrigatórios / especificação por categoria |
| Estado | Proposto (lista SC Existente) |
| Dependências | Categorias homologadas; C2 se escrita |
| Fonte | Brief; chamado 635 |
| Requisito | Validação de qualidade antes de seguir fluxo |
| Aceite | Regras homologadas; mensagens claras |
| Pendências | Catálogo de campos por categoria |

### SUP-004 — Aprovação / alçadas / relógios

| Campo | Conteúdo |
|---|---|
| Problema | Mistura tempo de aprovação × tempo de Compras |
| Objetivo | Separar relógios; alçadas claras |
| Estado | Proposto · P-06 bloqueado |
| Dependências | Workflow real; SoD |
| Fonte | Brief; DECISOES P-06 |
| Requisito | Indicadores de tempo separados |
| Aceite | Definição de início/fim homologada |
| Pendências | Alçadas; eventos de status |

### SUP-005 — Valor aprovado SC × pedido

| Campo | Conteúdo |
|---|---|
| Problema | Divergência valor aprovado × PC |
| Objetivo | Transparência da diferença |
| Estado | Proposto / Em validação vs dados SC7–SC1 |
| Dependências | Contratos SC/PC |
| Fonte | Brief |
| Requisito | Exibir e justificar delta |
| Aceite | Números auditáveis no escopo |
| Pendências | Regra de tolerância |

### SUP-006 — Inteligência de compras

| Campo | Conteúdo |
|---|---|
| Problema | Falta referência de mercado homologada |
| Objetivo | Índices oficiais quando existirem |
| Estado | Proposto |
| Dependências | Fontes externas homologadas |
| Fonte | Brief; chamado 527 |
| Requisito | Não inventar provedor |
| Aceite | Fonte + vigência documentadas |
| Pendências | Homologação de índices |

### SUP-007 — Estoque de segurança

| Campo | Conteúdo |
|---|---|
| Problema | ESTSEG × consumo × lead time pouco acionáveis no Portal |
| Objetivo | Relacionar cadastro × consumo × referência ideal |
| Estado | Parcial (plugin ESTSEG Existente; Portal Proposto) |
| Dependências | Homologação fórmula ideal; E11 |
| Fonte | estoque-seguranca README; KPI-CRITICAL-MP |
| Requisito | Fórmula ideal só após área |
| Aceite | Sem inventar fórmula; UI deixa fonte clara |
| Pendências | Fórmula; absorção UX |

### SUP-008 — Item sem demanda / descontinuado

| Campo | Conteúdo |
|---|---|
| Problema | Risco de recompra sem demanda |
| Objetivo | Alerta/recomendação |
| Estado | Proposto |
| Dependências | Evento de descontinuação; estrutura BOM |
| Fonte | Brief |
| Requisito | Sem bloqueio automático sem regra |
| Aceite | Alerta com evidência de consumo/estoque/PC |
| Pendências | Evento canônico de status |

### SUP-009 — Homologação OTD

| Campo | Conteúdo |
|---|---|
| Problema | Regra desejada vs nativa vs BI |
| Objetivo | Homologar regra final e exclusões |
| Estado | Parcial (KPI Existente; página fornecedor Proposta; P-03) |
| Dependências | Dump BI; natureza/itens excluídos |
| Fonte | KPI-FICHAS; P-03 |
| Requisito | Não alterar lógica sem homologação |
| Aceite | Documento de regra + evidência numérica |
| Pendências | Comparação BI; exclusões |

### SUP-010 — Pré-validação de NF

| Campo | Conteúdo |
|---|---|
| Problema | Divergências descobertas tarde |
| Objetivo | Pré-validação assistida |
| Estado | Proposto (LNF Existente como app) |
| Dependências | Regras fiscais oficiais; ownership LNF vs Portal |
| Fonte | Brief; lancamento-notas-fiscais |
| Requisito | Sem inventar regra fiscal |
| Aceite | Checklist homologado; exceções separadas |
| Pendências | Owner de pré-validação |

### SUP-011 — Código fornecedor × item interno

| Campo | Conteúdo |
|---|---|
| Problema | Equivalência de materiais |
| Objetivo | Cruzamento seguro |
| Estado | Proposto / Parcial (SA2/outros contextos) |
| Dependências | SUP-010; cadastro TOTVS |
| Fonte | Brief |
| Requisito | Mapeamento auditável |
| Aceite | Divergência explícita |
| Pendências | Tabela de equivalência |

### SUP-012 — Importações / descoberta ACSI

| Campo | Conteúdo |
|---|---|
| Problema | Processo de importação opaco no Portal |
| Objetivo | Inventário ACSI + jornada |
| Estado | Em validação / Ainda não localizado (ACSI) |
| Dependências | P-05; dump Core prod |
| Fonte | INVENTARIO; P-05 |
| Requisito | Não criar cadastro paralelo sem inventário |
| Aceite | Owner + fontes + gaps documentados |
| Pendências | ACSI; app Core |

### SUP-013 — Custos compartilhados de importação

| Campo | Conteúdo |
|---|---|
| Problema | Duplicidade potencial Suprimentos × Controladoria |
| Objetivo | Uma fonte · duas visões |
| Estado | Proposto · owner TO_INVENTORY |
| Dependências | SUP-012; CTL-007 |
| Fonte | Brief |
| Requisito | Sem segunda fonte de custo |
| Aceite | Matriz de ownership publicada |
| Pendências | Owner técnico |

---

## 6. Ondas (sem datas)

| Onda | Foco | Itens típicos |
|---|---|---|
| **0 — Descoberta** | Processos, regras, planilhas, ACSI, alçadas, fórmula ESTSEG, OTD, NF | SUP-012, SUP-007 fórmula, SUP-009, SUP-004 |
| **1 — Visibilidade** | Consultas, contexto, checklist, pendências, tarefas | SUP-001/002 (leitura), CORE-001, SUP-005 |
| **2 — Padronização** | Formulários, validações, classificação, indicadores | SUP-003, SUP-009 homologado |
| **3 — Automação** | Alertas, pré-validação, cálculos homologados | SUP-008, SUP-010, SUP-006 |
| **4 — Inteligência** | IA contextual, similaridade, previsões com governança | CORE-004 |

Roadmap ≠ autorização de implementação.

---

## 7. Matriz estado atual × necessidade

| Capacidade | Estado atual | Evidência | Necessidade | Próximo passo |
|---|---|---|---|---|
| Portal SC/PC operacionais | Existente | `plugins/supplies`, `supplies-api`, README E6–E8 | Manter; evoluir qualidade SC | Homologar SUP-003/004 |
| Overview + OTD KPI | Existente | KPI-FICHAS; `/analytics/otd` | Homologar OTD desejado | P-03 |
| ESTSEG | Parcial | `plugins/estoque-seguranca`; placeholder Portal | Absorção + fórmula ideal | E11 + homologação |
| Fornecedor 360 / OTD página | Proposto | Placeholder `App.tsx` | Página nativa | Contrato SA2; P-11 |
| Importações / ACSI | Ainda não localizado / Em validação | P-05; ACSI=0 hits | Inventário | Dump Core; ACSI |
| Contexto Vendas→Compras | Proposto | Brief | SUP-001/002 | Descoberta CRM |
| Pré-validação NF | Proposto | LNF Existente (app) | SUP-010 | Owner + regras oficiais |
| My tasks Portal | Proposto | Placeholder | CORE-001 | Não copiar Comercial |
| IA Suprimentos | Documentado, não localizado como runtime de agente | DESIGN-IA | CORE-004 | Guardrails |

---

## 8. Matriz de integrações (resumo)

| Origem | Destino | Informação | Direção | Estado | Necessidade |
|---|---|---|---|---|---|
| CRM / Comercial | Suprimentos | Contexto formação/preço | consulta | Ainda não localizado / Proposto | SUP-001 |
| TOTVS/Protheus | api-delpi → supplies-api | SC7, SC1, ESTSEG, OTD | consulta | Existente (parcial por domínio) | Manter boundaries |
| Minha DELPI | TOTVS | Gravação | — | Sem escrita neste programa | Não assumir write |
| Helpdesk | Roadmap | Chamados 691/593/635/527 | descoberta | Ainda não localizado no monorepo | Mapear tickets |
| ACSI | Importações | Processo/custos | TO_INVENTORY | Ainda não localizado | SUP-012 |
| Portal Suprimentos | Portal Financeiro/Controladoria | Custos importação | consulta compartilhada | Proposto | SUP-013 / CTL-007 |

Distinguir sempre: consulta · preparação · pré-validação · gravação.

---

## 9. Questões em aberto

- Identificador formação ↔ pedido; campos autorizados ao comprador  
- Fórmula ESTSEG “ideal”; evento de descontinuação  
- Regra final OTD; início/fim dos indicadores de tempo SC  
- Alçadas; divergências NF; equivalência materiais; estrutura ACSI  

---

## 10. Conflitos / drifts conhecidos (não “limpar” silenciosamente)

| Drift | Onde | Tratamento |
|---|---|---|
| Prosa E1–E8 concluída vs YAML `e6-s5 pending` / `e7`/`e8` blocked | IMPLEMENTATION-PLAN + README | KNOWN DOCUMENTATION_DRIFT — registrar; não alterar histórico só para cosmético |
| `/me/routes` vs `/me/apps` | README/instruções oficiais vs Core atual | Contrato vigente = `/me` + `/me/apps`; documentado no README supplies |
| Cutover OTD → `/suppliers/otd` vs placeholder | CUTOVER-RUNBOOK vs código | Target documentado; código ainda não |
| DESIGN-IA “foco SC” vs E8 fechado | DESIGN-IA status | Doc de status atrasada |
| KPI-PO-LATE “aguarda E7” | KPI-FICHAS | Em validação pós-E7 |
| Manifest schemaVersion 1.0.0 supplies vs “Manifesto v2” genérico nas instruções oficiais | supplies README vs doc arquiteto | Dual surface documental — não inventar manifest novo aqui |

---

## 11. Garantias

- Nenhum item Proposto foi marcado como Existente sem path de código.  
- Nenhuma fórmula ESTSEG/OTD/fiscal inventada.  
- Este arquivo **não** autoriza implementação.
