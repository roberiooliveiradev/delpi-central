# 20 — Cobertura Transforma+ → Portal Controladoria & Finanças

## Objetivo

Preservar a rastreabilidade das necessidades históricas do roadmap Transforma+ sem transformar discovery em contrato runtime.

Fonte histórica:
- [../financeiro-controladoria/ROADMAP.md](../financeiro-controladoria/ROADMAP.md)

TARGET implementável:
- [README.md](./README.md)
- páginas P1–P6 desta pasta

Nenhum `CTL-*` pode desaparecer silenciosamente.

## Classificação

| Estado | Significado |
|---|---|
| ABSORBED | a necessidade está coberta funcionalmente pelo TARGET atual |
| PARTIALLY_ABSORBED | parte está coberta; parte permanece futura ou dependente de inventário |
| NEEDS_BUSINESS_CONFIRMATION | a necessidade continua válida, mas sua forma/destino de produto não está fechada |
| FUTURE_CAPABILITY_CANDIDATE | não pertence ao primeiro recorte da Central de Fechamento; preservar para evolução |
| SUPERSEDED_BY_TARGET | formulação histórica foi substituída por decisão TARGET explícita |
| OUT_OF_SCOPE | não pertence ao produto atual |

## Matriz CTL-*

| ID | Necessidade Transforma+ | Cobertura no TARGET | Classificação | Dependência / observação |
|---|---|---|---|---|
| CTL-001 | Cockpit de fechamento por competência | P1 Cockpit + P2 documentos + P4 pendências + P5 pacote | ABSORBED | bindings técnicos ainda passam por T01/T05 |
| CTL-002 | Catálogo de relatórios/filtros Protheus | regras consolidadas, P3 e inventário técnico | PARTIALLY_ABSORBED | códigos, endpoints, campos e freshness reais permanecem T01; não inventar códigos físicos |
| CTL-003 | Pendências externas, documentos, responsáveis, data/status/notificação | P1/P2/P4 + notificações | ABSORBED | `DUE_DATE/OVERDUE/SLA` históricos foram SUPERSEDED_BY_TARGET; usar `PENDING_SINCE` até nova decisão |
| CTL-004 | Acesso da Contabilidade ao preparado | acesso/escopo e leitura das superfícies do fechamento | ABSORBED | effective permissions/scopes reais dependem T05; não criar permission por tela |
| CTL-005 | Assistência de CC/classificação | P4 cobre a fatia do fechamento com sugestão + decisão humana | PARTIALLY_ABSORBED | despesas por CC do Portal Financeiro são adjacentes, não a mesma feature; expansão além do fechamento permanece futura |
| CTL-006 | Custo de mão de obra homologado/versionado | não há capability específica fechada na Central | NEEDS_BUSINESS_CONFIRMATION / FUTURE_CAPABILITY_CANDIDATE | não confundir com Fat×MOD do fechamento; fórmula anual/homologada não pode ser inventada |
| CTL-007 | Visão Controladoria de custos de importação | entregáveis de importação podem compor o fechamento | PARTIALLY_ABSORBED / FUTURE_CAPABILITY_CANDIDATE | visão ampla deve preservar fonte/owner de Suprimentos/ACSI; owner técnico continua TO_INVENTORY |

## Capacidades transversais CORE-*

| ID | Cobertura | Estado |
|---|---|---|
| CORE-001 — tarefas vinculadas | P4 modela pendências/ownership para o fechamento | PARTIALLY_ABSORBED; não cria framework genérico de tarefas |
| CORE-002 — comunicação contextual | P5 cobre esclarecimentos ligados ao pacote | PARTIALLY_ABSORBED; não cria canal genérico |
| CORE-003 — notificações | [16-configuracoes-catalogos-e-notificacoes.md](./16-configuracoes-catalogos-e-notificacoes.md) | ABSORBED conceitualmente; binding T02 |
| CORE-004 — IA contextual | P1–P4 + [14-seguranca-rbac-auditoria-e-ia.md](./14-seguranca-rbac-auditoria-e-ia.md) | ABSORBED com IA assistiva e decisão humana |
| CORE-005 — RBAC cross-portal | [14-seguranca-rbac-auditoria-e-ia.md](./14-seguranca-rbac-auditoria-e-ia.md) | ABSORBED conceitualmente; Core/T05 definem binding real |

## Indicadores candidatos do Transforma+

| Indicador histórico | Destino |
|---|---|
| Status do fechamento | ABSORBED por P1; derivado de eixos independentes, não percentual único obrigatório |
| Pendências vencidas | SUPERSEDED_BY_TARGET enquanto `DUE_DATE=NO` e `OVERDUE=NO` |
| Atividades ainda manuais | FUTURE_CAPABILITY_CANDIDATE; fórmula/medição não definida |
| Correções de centro de custo | FUTURE_CAPABILITY_CANDIDATE; ainda não aprovado como KPI |

## Ondas históricas

As ondas 0–4 do Transforma+ permanecem como histórico de discovery.

Elas **não** determinam a ordem de implementação atual. A ordem executável é governada por [18-readiness-e-handoff-de-implementacao.md](./18-readiness-e-handoff-de-implementacao.md), dependências reais, inventories E/T e gates de página.

## Regras de preservação

- roadmap histórico não prova runtime;
- item absorvido não transfere ownership técnico automaticamente;
- item parcialmente absorvido mantém o residual explicitado;
- item futuro não deve ser implementado dentro da Central apenas para "zerar" backlog;
- ausência de binding técnico não reabre decisão de produto já fechada;
- `search miss != ausência`;
- nenhuma classificação deste documento autoriza implementação fora do gate da página.

## Residuais explícitos

- CTL-006: decidir futuramente o destino funcional da capability de custo de mão de obra homologado;
- CTL-007: definir owner/binding da visão ampla de custos de importação sem duplicar Suprimentos/ACSI;
- CTL-005: qualquer expansão de classificação fora da fatia do fechamento exige novo gate de produto;
- indicadores manuais/CC: fórmula, owner e aceite ainda não definidos.
