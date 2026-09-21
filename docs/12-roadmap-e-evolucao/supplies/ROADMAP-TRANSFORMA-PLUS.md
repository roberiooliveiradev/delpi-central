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

**Fonte Transforma+:** conteúdo adicional fornecido externamente ao processo de consolidação em **16/09/2026** (playbook / briefing do Product Owner, inclusive deltas revisados pelo GPT). Classificado como Informado/Observado, Calculado, Hipótese, Proposto ou Ainda não sabemos. **A fonte não é prova de runtime.** O arquivo `playbook_transforma_suprimentos_controladoria.md` **ainda não está persistido** no monorepo neste HEAD — gaps do playbook entram via deltas obrigatórios do REWORK BRIEF; itens continuam **Proposto / Em validação**, não “Existente”, até inventário de código.

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

**Implementação vs gate (evidence vigente em [README.md](./README.md), HEAD revalidado):**

| Faixa | Status documental |
|---|---|
| E1–E7 | Jornadas **implementadas / deploy documentados** conforme documentação mestra vigente |
| E8 / WF-06 Detalhe do Pedido | **IMPLEMENTATION PRESENT / DEPLOYED** (ficha `/purchase-orders/:branch/:number`) |
| GATE-FEATURE WF-06 | **INCONCLUSIVE** enquanto o smoke federado live não estiver comprovado — **não** confundir com `GATE-FEATURE PASS` |

Formulação canônica deste roadmap: E1–E7 possuem jornadas implementadas conforme documentação vigente; E8/WF-06 possui implementação/deploy documentados, mas seu GATE-FEATURE permanece INCONCLUSIVE enquanto o smoke federado live não estiver comprovado.

A fila nativa (Entregas, ESTSEG no portal, Fornecedores 360, Importações, etc.) continua **bloqueada** até autorização página-a-página.

Transforma+ acrescenta **necessidades de negócio** (qualidade da SC, contexto Vendas→Compras, similaridade de materiais, pré-validação de NF, importações, inteligência de compras) que **não** estão todas no código e **não** devem ser confundidas com páginas já entregues nem com gates PASS.

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

### 3.9 Similaridade de materiais (SUP-014)

**Informado/Observado (fonte Transforma+):** em alguns casos usa-se apoio de especialista para identificar materiais similares; o tema pode exigir Engenharia.

**Proposto:** sugestão assistida, claramente identificada como sugestão, com evidência técnica, dependente de validação de Engenharia ou área competente — **nenhuma substituição automática**.

---

## 4. Capacidades transversais (CORE-*) — definição canônica

> Este documento é a **fonte documental transversal** de CORE-001…005.
> Isso **não** transfere ownership técnico para Suprimentos. Controladoria referencia por link; Comercial e Core permanecem owners dos próprios bounded contexts.

Cada item: problema · objetivo · estado · dependências · fonte · requisito · critérios de aceite · questões pendentes.

### CORE-001 — Tarefas vinculadas a objetos

| Campo | Conteúdo |
|---|---|
| Problema | Follow-ups dispersos fora do objeto de negócio |
| Objetivo | Tarefas com responsável, prazo, prioridade, objeto relacionado, status e histórico |
| Estado | Proposto no Portal Suprimentos (`/my-tasks` placeholder); Existente no Comercial (outro BC) |
| Dependências | Modelo de objeto; RBAC; não copiar ownership Comercial |
| Fonte | Brief Transforma+; fonte externa 16/09/2026 |
| Requisito | Objetos candidatos: SC, pedido, fornecedor, NF, importação, fechamento, relatório, pendência |
| Critérios de aceite | Tarefa sempre ligada a um objeto; histórico audível; sem permission por botão |
| Questões pendentes | Owner do serviço de tasks; paridade com Comercial |

### CORE-002 — Comunicação contextual

| Campo | Conteúdo |
|---|---|
| Problema | Conversas sobre SC/PC/NF/fechamento fora de contexto |
| Objetivo | Comunicação vinculada ao objeto |
| Estado | Proposto |
| Dependências | CORE-001; governança de canais |
| Fonte | Brief Transforma+; fonte externa 16/09/2026 |
| Requisito | Não criar novo chat genérico por default; Teams / e-mail / WhatsApp / Minha DELPI = questão de governança |
| Critérios de aceite | Mensagem/thread referenciável ao objeto; canal oficial documentado quando definido |
| Questões pendentes | Canal oficial; retenção; RBAC de leitura |

### CORE-003 — Governança de notificações

| Campo | Conteúdo |
|---|---|
| Problema | Eventos sem catálogo / canal oficial |
| Objetivo | Eventos candidatos governados |
| Estado | Parcial (jobs SC/PC em `purchase-requests-api` → Core); canal Portal = [INTEGRACOES.md](./INTEGRACOES.md) |
| Dependências | Catálogo de eventos; preferências Core |
| Fonte | Brief; INTEGRACOES; fonte externa 16/09/2026 |
| Requisito | Documentar eventos candidatos; **não inferir** delivery channel oficial |
| Critérios de aceite | Evento nomeado + payload mínimo + escopo RBAC; canal explícito só após decisão |
| Questões pendentes | Canal oficial; migração C2 das notif SC |

### CORE-004 — IA contextual com guardrails

| Campo | Conteúdo |
|---|---|
| Problema | Pressão por automação sem governança |
| Objetivo | Apoio contextual (consulta, resumo, exceções, estoque, similares, acompanhamento) sem virar owner de regra |
| Estado | Proposto (doc) — [DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md) |
| Dependências | CORE-005; SUP-014; validação humana/técnica |
| Fonte | Brief; DESIGN-IA; fonte externa 16/09/2026 (REWORK) |
| Requisito | Guardrails obrigatórios: (1) respeitar permissions; (2) não inventar dados; (3) indicar fonte quando possível; (4) sugestão ≠ decisão; (5) regra fiscal/contábil/técnica exige validação oficial/humana; (6) substituição ou **similaridade de material** exige **validação técnica**; (7) nenhuma substituição automática; (8) nenhuma gravação no ERP sem fluxo autorizado |
| Critérios de aceite | UI/API deixam claro “sugestão”; bloqueio de write ERP sem fluxo; similaridade nunca aplica sozinha |
| Questões pendentes | Escopo de tools; avaliação R1–R11 quando material |

### CORE-005 — Integração / RBAC entre portais

| Campo | Conteúdo |
|---|---|
| Problema | Risco de authority cruzada ou permission por botão |
| Objetivo | Integração entre portais sob Core |
| Estado | Em validação |
| Dependências | Core effective permissions; unit/resource scope |
| Fonte | Brief; MATRIZ-BOUNDARIES; fonte externa 16/09/2026 |
| Requisito | Core continua authority; capability + unit/resource scope quando aplicável; **não** permission por botão; **não** criar authority entre Suprimentos e Controladoria |
| Critérios de aceite | Consumo via BFF/owner; fail-closed; sem bypass MFE→api-delpi |
| Questões pendentes | Matriz de capabilities cruzadas quando houver feature compartilhada |

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

### SUP-014 — Similaridade de materiais

| Campo | Conteúdo |
|---|---|
| Problema | Identificação de materiais similares depende de especialista em alguns casos; pode exigir Engenharia |
| Objetivo | Sugestão assistida de similares com evidência técnica |
| Estado | Proposto |
| Dependências | Engenharia / área técnica competente + fonte de dados a inventariar; CORE-004 |
| Fonte | Fonte Transforma+ externa 16/09/2026 (playbook / REWORK BRIEF) — Informado/Observado + Proposto |
| Requisito | Sugestão identificada como sugestão; evidência técnica; validação humana/técnica obrigatória; **nenhuma substituição automática**; não implementar regra de equivalência neste roadmap |
| Critérios de aceite | UI deixa claro “sugestão”; bloqueio de apply sem validação; sem gravação ERP automática |
| Questões pendentes | Fonte de similaridade (estrutura, atributos, histórico); owner Engenharia; critérios de evidência |

---

## 5.1 Indicadores candidatos — requerem homologação

> **Não** são KPIs implementados. Authority de indicadores já homologados: [KPI-FICHAS.md](./KPI-FICHAS.md).
> Candidatos abaixo = descoberta Transforma+; **não** promover sem checklist completo.

**Regra geral — promoção de KPI candidato exige:** nome; definição; unidade; fórmula/regra homologada; início/fim da medição; direção; baseline; meta; periodicidade; fonte oficial; responsável.

| Candidato | Domínio | Nota |
|---|---|---|
| Tempo de aprovação da SC | Suprimentos | Fórmula/eventos a validar |
| Tempo de Compras após liberação | Suprimentos | Evento final oficial a definir |
| Retrabalho de SC | Suprimentos | Fórmula a validar |
| Desvio preço comprado × referência | Suprimentos | Composição comparável a definir |
| OTD | Suprimentos | **Existente** em KPI-FICHAS / Overview — universo ainda precisa homologação (P-03); não alterar lógica neste roadmap |
| Divergência na entrada de NF | Suprimentos | Candidato |
| Risco de estoque sem demanda | Suprimentos | Regra a definir (ligado a SUP-008) |
| Status do fechamento | Controladoria | Ver roadmap Controladoria |
| Pendências vencidas | Controladoria | Ver roadmap Controladoria |
| Atividades ainda manuais | Controladoria | Fórmula a definir |
| Correções de centro de custo | Controladoria | Ver roadmap Controladoria |

---

## 6. Ondas (sem datas)

| Onda | Foco | Itens típicos |
|---|---|---|
| **0 — Descoberta** | Processos, regras, planilhas, ACSI, alçadas, fórmula ESTSEG, OTD, NF, similaridade | SUP-012, SUP-007 fórmula, SUP-009, SUP-004, SUP-014 |
| **1 — Visibilidade** | Consultas, contexto, checklist, pendências, tarefas | SUP-001/002 (leitura), CORE-001, SUP-005 |
| **2 — Padronização** | Formulários, validações, classificação, indicadores | SUP-003, SUP-009 homologado |
| **3 — Automação** | Alertas, pré-validação, cálculos homologados | SUP-008, SUP-010, SUP-006 |
| **4 — Inteligência** | IA contextual, similaridade assistida, previsões com governança | CORE-004, SUP-014 |

Roadmap ≠ autorização de implementação.

---

## 7. Matriz estado atual × necessidade

| Capacidade | Estado atual | Evidência | Necessidade | Próximo passo |
|---|---|---|---|---|
| Portal SC/PC (E1–E7 impl.) | Existente (implementação) | `plugins/supplies`, `supplies-api`, README | Manter; evoluir qualidade SC | Homologar SUP-003/004 |
| E8 / WF-06 detalhe PC | IMPLEMENTATION PRESENT / DEPLOYED; GATE INCONCLUSIVE | README GATE-FEATURE WF-06 | Smoke federado live | Não declarar GATE PASS |
| Overview + OTD KPI | Existente | KPI-FICHAS; `/analytics/otd` | Homologar universo OTD | P-03 |
| ESTSEG | Parcial | `plugins/estoque-seguranca`; placeholder Portal | Absorção + fórmula ideal | E11 + homologação |
| Fornecedor 360 / OTD página | Proposto | Placeholder `App.tsx` | Página nativa | Contrato SA2; P-11 |
| Importações / ACSI | Ainda não localizado / Em validação | P-05; ACSI=0 hits | Inventário | Dump Core; ACSI |
| Contexto Vendas→Compras | Proposto | Brief / fonte Transforma+ | SUP-001/002 | Descoberta CRM |
| Similaridade de materiais | Proposto | Fonte Transforma+ 16/09 | SUP-014 | Engenharia + dados |
| Pré-validação NF | Proposto | LNF Existente (app) | SUP-010 | Owner + regras oficiais |
| My tasks Portal | Proposto | Placeholder | CORE-001 | Não copiar Comercial |
| IA Suprimentos | Documentado, não localizado como runtime de agente | DESIGN-IA | CORE-004 + guardrails | Validação técnica |

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
| Prosa E1–E8 concluída vs YAML antigo `e6-s5 pending` / `e7`/`e8` blocked | IMPLEMENTATION-PLAN | Reconciliado em 2026-09-21 (`aa13f1075`): YAML `completed` para a entrega. GATE-FEATURE WF-06 segue `INCONCLUSIVE`; E9 segue bloqueada |
| `/me/routes` vs `/me/apps` | README/instruções oficiais vs Core atual | Contrato vigente = `/me` + `/me/apps`; documentado no README supplies |
| Cutover OTD → `/suppliers/otd` vs placeholder | CUTOVER-RUNBOOK vs código | Target documentado; código ainda não |
| DESIGN-IA “foco SC” vs E8 implementado (gate INCONCLUSIVE) | DESIGN-IA status | Doc de status atrasada |
| KPI-PO-LATE “aguarda E7” | KPI-FICHAS | Em validação pós-E7 |
| Manifest schemaVersion 1.0.0 supplies vs “Manifesto v2” genérico nas instruções oficiais | supplies README vs doc arquiteto | Dual surface documental — não inventar manifest novo aqui |

---

## 11. Garantias

- Nenhum item Proposto foi marcado como Existente sem path de código.
- Nenhuma fórmula ESTSEG/OTD/fiscal inventada.
- Este arquivo **não** autoriza implementação.
