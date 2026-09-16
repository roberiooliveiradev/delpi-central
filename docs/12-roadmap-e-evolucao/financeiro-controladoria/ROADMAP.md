# Financeiro / Controladoria — Roadmap Transforma+

> **Papel:** consolidar necessidades Transforma+ de fechamento mensal, Contabilidade e custos.  
> **Fonte de descoberta do brief:** EXECUTION BRIEF 2026-09-16.  
> **Playbook** `playbook_transforma_suprimentos_controladoria.md`: **Ainda não localizado** no workspace — itens do brief = Proposto / Em validação, não Existente.  
> **BASE HEAD:** `d9e2fe1a94ab3556119afc0e44a26f72bae5763a`.  
> Roadmap ≠ autorização de implementação.

## 1. Semântica de evidência

| Rótulo | Significado |
|---|---|
| Informado/Observado | Relato da área |
| Hipótese | Precisa validação |
| Proposto | Candidato futuro |
| Existente / Parcial | Provado no monorepo com path |
| Ainda não localizado | Search miss ≠ ausência definitiva; abrir fonte |

Não promover Proposto → Existente sem path. Não inventar código de relatório Protheus, fórmula de mão de obra ou integração bancária.

## 2. O que já existe (não confundir com este roadmap)

| Capacidade | Estado | Evidência |
|---|---|---|
| Portal Financeiro P0 | Existente | [../financial/README.md](../financial/README.md); `plugins/financial`; `financial-api` — billing, delinquency, cost-centers, freight, indicators |
| Despesas por centro de custo | Existente | `/apps/financial/cost-centers` → api-delpi `/financeiro/despesas-centro-custo/*` |
| Planejamento orçamentário + cockpits de aprovação | Existente | [../planejamento-orcamentario/](../planejamento-orcamentario/) — **não** é fechamento contábil mensal |
| Lançamento de notas fiscais | Existente | [../lancamento-notas-fiscais/](../lancamento-notas-fiscais/) |
| Cockpit de fechamento por competência | Ainda não localizado | Sem app/pasta dedicada neste inventário |
| Contabilidade como módulo de consulta | Ainda não localizado | — |
| Custo de mão de obra homologado (produto Controladoria) | Ainda não localizado / Em validação | Custos de produção podem existir em outros domínios SI/produção — **não** reutilizar como fórmula oficial sem homologação |

---

## 3. Temas Transforma+

### 3.1 Fechamento mensal (CTL-001)

**Problema (Informado/Observado — brief):** concentração de conhecimento no fechamento.

**Produto proposto:** COCKPIT DE FECHAMENTO POR COMPETÊNCIA — checklist, status, relatórios, filtros, responsáveis, pendências, prazos, anexos/referências, validação, histórico, disponibilização para Contabilidade.

**Estado:** Proposto. Avaliar primeiro o que já existe (Portal Financeiro, Delpi Reports, orçamento) antes de novo produto.

### 3.2 Relatórios Protheus/TOTVS (CTL-002)

Manter como descoberta: códigos, filtros, parâmetros, sequência, saídas, periodicidade.

**Não inventar códigos.** Estado: Ainda não sabemos / Em validação.

### 3.3 Pendências do fechamento (CTL-003)

Extratos, documentos externos, responsável, data necessária, status, notificação, confirmação de entrega.

**Não assumir** integração bancária. Estado: Proposto.

### 3.4 Contabilidade — acesso (CTL-004)

Perfil/acesso limitado para consultar ou extrair informações preparadas **sem** recompilação manual por outra pessoa.

Seguir RBAC existente. **Não** criar permission nova sem análise material. Estado: Proposto.

### 3.5 Centro de custo e classificação (CTL-005)

Assistência futura considerando material, finalidade, área, direto/indireto, manutenção, consumo, insumo, centro de custo.

Quando regra não estiver localizada: `REQUER HOMOLOGAÇÃO DA CONTROLADORIA`.

**Parcial:** despesas por CC já existem no Portal Financeiro; assistência/classificação inteligente = Proposto.

### 3.6 Custo de mão de obra (CTL-006)

Documentar: fórmula homologada, parâmetros, vigência, memória de cálculo, versionamento, responsável por aprovação.

**Não criar fórmula.** Estado: Proposto · fórmula = Ainda não sabemos.

### 3.7 Visão Controladoria de custos de importação (CTL-007)

Evitar duplicidade com Suprimentos ([../supplies/ROADMAP-TRANSFORMA-PLUS.md](../supplies/ROADMAP-TRANSFORMA-PLUS.md) SUP-012/013).

**Princípio:** MESMA FONTE DE DADOS + VISÕES DIFERENTES POR PERFIL. Owner técnico = `TO_INVENTORY` até evidência.

---

## 4. Capacidades transversais

| ID | Tema | Estado | Nota |
|---|---|---|---|
| CORE-001 | Tarefas vinculadas a objetos | Proposto neste domínio | Comercial tem my-tasks (outro BC) |
| CORE-002 | Comunicação contextual (fechamento/pendência) | Proposto | Sem chat genérico por default |
| CORE-003 | Notificações de pendência | Proposto | Canal oficial = Ainda não sabemos |
| CORE-004 | IA contextual | Proposto | Guardrails: permissões; não inventar; fonte; sugestão≠decisão; fiscal/contábil exige validação oficial; sem gravação ERP sem fluxo |
| CORE-005 | RBAC entre portais | Em validação | Reusar Core; sem permission por botão |

---

## 5. Backlog estável (CTL-*)

### CTL-001 — Cockpit de fechamento

| Campo | Conteúdo |
|---|---|
| Problema | Conhecimento concentrado; fechamento pouco rastreável |
| Objetivo | Cockpit por competência |
| Estado | Proposto |
| Dependências | Sequência de fechamento; owners; inventário de relatórios |
| Fonte | Brief Transforma+ |
| Requisito | Checklist + status + responsáveis + histórico |
| Aceite | Competência consultável; Contabilidade acessa preparado |
| Pendências | Sequência oficial; product owner do cockpit |

### CTL-002 — Relatórios / filtros Protheus

| Campo | Conteúdo |
|---|---|
| Problema | Parâmetros na cabeça de poucas pessoas |
| Objetivo | Catálogo homologado de relatórios |
| Estado | Em validação / Ainda não sabemos códigos |
| Dependências | CTL-001 |
| Fonte | Brief |
| Requisito | Não inventar código |
| Aceite | Lista com código+filtro+saída+periodicidade |
| Pendências | Coleta com Controladoria |

### CTL-003 — Pendências externas

| Campo | Conteúdo |
|---|---|
| Problema | Extratos/documentos atrasam fechamento |
| Objetivo | Rastreio de pendências |
| Estado | Proposto |
| Dependências | CTL-001; notificações |
| Fonte | Brief |
| Requisito | Sem assumir open banking |
| Aceite | Status + responsável + data |
| Pendências | Fontes de extrato |

### CTL-004 — Acesso da Contabilidade

| Campo | Conteúdo |
|---|---|
| Problema | Recompilação manual |
| Objetivo | Perfil de consulta/extração |
| Estado | Proposto |
| Dependências | CTL-001; RBAC Core |
| Fonte | Brief |
| Requisito | Sem permission inventada |
| Aceite | Contabilidade lê preparado no escopo |
| Pendências | Matriz de papéis |

### CTL-005 — Assistência CC / classificação

| Campo | Conteúdo |
|---|---|
| Problema | Classificação inconsistente |
| Objetivo | Assistência homologada |
| Estado | Proposto (despesas CC Existentes) |
| Dependências | Regra Controladoria |
| Fonte | Brief |
| Requisito | `REQUER HOMOLOGAÇÃO DA CONTROLADORIA` |
| Aceite | Sugestão ≠ lançamento automático |
| Pendências | Regra oficial |

### CTL-006 — Custo de mão de obra

| Campo | Conteúdo |
|---|---|
| Problema | Fórmula não versionada / não auditável |
| Objetivo | Memória de cálculo homologada |
| Estado | Proposto |
| Dependências | Aprovador oficial |
| Fonte | Brief |
| Requisito | Não inventar fórmula |
| Aceite | Fórmula+vigência+responsável publicados |
| Pendências | Homologação |

### CTL-007 — Visão custos de importação

| Campo | Conteúdo |
|---|---|
| Problema | Risco de segunda fonte vs Suprimentos |
| Objetivo | Visão Controladoria sobre fonte única |
| Estado | Proposto · owner TO_INVENTORY |
| Dependências | SUP-012/013; ACSI |
| Fonte | Brief; roadmap supplies |
| Requisito | Mesma fonte · perfil diferente |
| Aceite | Matriz de ownership cruzada |
| Pendências | Owner técnico |

---

## 6. Ondas (sem datas)

| Onda | Foco | Itens |
|---|---|---|
| **0 — Descoberta** | Sequência fechamento, relatórios, extratos, fórmulas, ACSI | CTL-002, CTL-006, CTL-007 inventário |
| **1 — Visibilidade** | Checklist, pendências, acesso Contabilidade | CTL-001 (MVP leitura), CTL-003, CTL-004 |
| **2 — Padronização** | Classificação CC, indicadores de fechamento | CTL-005 |
| **3 — Automação** | Alertas de pendência, cálculos homologados | CTL-003 notif, CTL-006 |
| **4 — Inteligência** | IA contextual com guardrails | CORE-004 |

---

## 7. Matriz estado × necessidade

| Capacidade | Estado atual | Evidência | Necessidade | Próximo passo |
|---|---|---|---|---|
| Portal Financeiro P0 | Existente | financial README | Manter; não reinventar billing/CC | Linkar no cockpit se útil |
| Orçamento / aprovações | Existente | planejamento-orcamentario | Separar de fechamento contábil | Onda 0 |
| Cockpit fechamento | Ainda não localizado | inventário 2026-09-16 | CTL-001 | Descoberta processo |
| Relatórios Protheus | Ainda não sabemos | — | CTL-002 | Coletar códigos |
| Pendências externas | Proposto | Brief | CTL-003 | Definir objetos |
| Acesso Contabilidade | Proposto | Brief | CTL-004 | Matriz RBAC |
| Classificação CC | Parcial | despesas CC Existentes | CTL-005 | Homologação |
| Mão de obra | Proposto | Brief | CTL-006 | Homologar fórmula |
| Custos importação | Proposto | SUP-013 | CTL-007 | Owner + ACSI |

---

## 8. Matriz de integrações (resumo)

| Origem | Destino | Informação | Direção | Estado | Necessidade |
|---|---|---|---|---|---|
| TOTVS/Protheus | api-delpi / Portal Financeiro | ROL, inadimplência, despesas CC | consulta | Existente (parcial) | Manter |
| Extratos externos | Cockpit fechamento | Pendências | preparação | Proposto | Sem banco automático |
| Contabilidade | Cockpit | Leitura preparado | consulta | Proposto | CTL-004 |
| Portal Suprimentos | Controladoria | Custos importação | consulta compartilhada | Proposto | CTL-007 |
| Helpdesk | Roadmap | Tickets | descoberta | Ainda não localizado | Mapear |
| Minha DELPI | TOTVS | Gravação | — | Não assumida | Fluxo autorizado só após decisão |

---

## 9. Questões em aberto

- Sequência oficial de fechamento; códigos/filtros Protheus  
- Fontes de extratos; perfil Contabilidade  
- Regra centro de custo; fórmula mão de obra; planilhas prioritárias  
- APIs de gravação; sincronização; cache; eventos; notificações  

---

## 10. Review cruzado com Suprimentos

| Tema | Fonte principal | Link |
|---|---|---|
| Importações / ACSI | Suprimentos SUP-012 | [../supplies/ROADMAP-TRANSFORMA-PLUS.md](../supplies/ROADMAP-TRANSFORMA-PLUS.md) |
| Custos importação | Compartilhado SUP-013 + CTL-007 | mesma fonte |
| NF / fiscal | LNF app + SUP-010 (pré-validação) | [../lancamento-notas-fiscais/](../lancamento-notas-fiscais/) |
| Tarefas / notif / IA | CORE-* alinhados | não duplicar canal |
| Despesas CC operacionais | Portal Financeiro | [../financial/README.md](../financial/README.md) |

Sem requisito contraditório: Controladoria **não** redefine OTD/ESTSEG; Suprimentos **não** redefine fórmula de mão de obra.

---

## 11. Garantias

- Nada marcado como implementado sem path.  
- Nenhuma hipótese promovida a fato.  
- Nenhuma regra fiscal/contábil/mão de obra inventada.  
- Nenhum código/migration/permission alterado por este documento.
