# 22 — Handoff de Implementação P1–P6

## Objetivo

Transformar as especificações funcionais P1–P6 em um handoff executável e uniforme, sem substituir os documentos canônicos de cada página.

Fontes primárias:
- [08-p1-cockpit-da-competencia.md](./08-p1-cockpit-da-competencia.md)
- [09-p2-checklist-e-documentos.md](./09-p2-checklist-e-documentos.md)
- [10-p3-estoque-cutoff-e-conciliacao.md](./10-p3-estoque-cutoff-e-conciliacao.md)
- [11-p4-classificacoes-e-pendencias.md](./11-p4-classificacoes-e-pendencias.md)
- [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md)
- [13-p6-administracao-e-configuracao.md](./13-p6-administracao-e-configuracao.md)

Este documento organiza o handoff; em conflito, a regra específica comprovada no documento canônico da página vence.

Reuso frontend obrigatório:
- [30-plugin-ui-reuse-map.md](./30-plugin-ui-reuse-map.md)
- runtime import: `@delpi/plugin-ui/index`
- styles: `@delpi/plugin-ui/styles`

Antes de criar UI reutilizável local, verificar o catálogo do kit.

## Baseline transversal de experiência

Todas as páginas devem tratar, quando aplicável:
- `LOADING`;
- `EMPTY`;
- `PARTIAL`;
- `UNAVAILABLE_SOURCE`;
- `ERROR`;
- `FORBIDDEN` / 403;
- `NOT_FOUND` / 404;
- desktop/mobile;
- claro/escuro;
- teclado e foco visível;
- deep link/F5;
- freshness/proveniência;
- Help contextual;
- nenhuma autorização baseada apenas em UI;
- `@delpi/plugin-ui` first; chrome reutilizável local só quando o kit não oferecer equivalente.

## P1 — Cockpit da Competência

### Objetivo
Responder como está o fechamento, quais eixos estão prontos e o que bloqueia avanço/conclusão.

### Composição lógica

```text
ContextHeader
→ StatusAxes
→ BlockerList
→ PendingItems
→ ClosingHistory
→ ContextualHelp
```

Os nomes acima são lógicos, não contrato de componente React.

### Atores e acesso
- ACCESS consulta cockpit e navega para superfícies operacionais, respeitando resource ownership/business rules quando aplicável;
- MANAGE não recebe poderes adicionais em P1 apenas por ser MANAGE;
- sem ACCESS: FORBIDDEN, sem exposição de dados.

### Owners / sources
P1 compõe estados vindos de P2, P3, P4 e P5. Não se torna owner das regras desses módulos.

Bindings físicos/freshness permanecem T01; effective permissions/ownership permanecem T05 quando aplicável.

### Estados e interações
Eixos independentes:
- Estoque: PRELIMINARY → WAITING_FOR_CUTOFF → REVALIDATION_REQUIRED → READY_TO_CLOSE → STOCK_CLOSED;
- Documentos: derivados de requirement/satisfaction/validation;
- Pacote: PACKAGE_INCOMPLETE → READY_TO_FINALIZE → PACKAGE_FINALIZED → PACKAGE_SENT → WAITING_FOR_CLARIFICATION → MONTHLY_CLOSING_COMPLETED derivado.

P1 não sacramenta, valida evidência nem envia pacote.

### Blockers
- REQUIRED/CONDITIONAL aplicável não satisfeito;
- source obrigatório indisponível;
- P3 sem paridade exata pós-cutoff;
- pacote/destinatário pendente;
- esclarecimento aberto quando aplicável.

### Help
Explicar eixos independentes, preliminary/final, freshness, blockers e diferença entre estoque fechado, pacote enviado e fechamento concluído.

### Dependências / stop
T01 para bindings e T05 para effective permissions/ownership. Falta de source não vira zero nem sucesso.

## P2 — Checklist e Documentos

### Objetivo
Operar entregáveis da competência com snapshot, evidência, validação e histórico auditável.

### Composição lógica

```text
ChecklistFilters
→ ChecklistList
→ ChecklistItemDetail
→ EvidencePanel
→ ValidationPanel
→ ItemHistory
→ ContextualHelp
```

### Atores e acesso
- ACCESS opera itens da competência conforme ownership/business rules aplicáveis;
- validator valida/rejeita quando autorizado;
- MANAGE administra mestre/catálogos/correções estruturais;
- MANAGE_APPROVAL != EVIDENCE_VALIDATION.

### Owners / sources
- template/catálogos: produto, com governança P6;
- evidências externas: upload/attachment do item;
- evidências derivadas/internas: source autorizado;
- validator/responsible/recipient: opções autorizadas, binding real inventariado.

### Estados/interações
Cobrir:
- upload != validação;
- ACCEPTED/REJECTED e replacement;
- PER_ATTACHMENT/WHOLE_SET;
- N/A apenas CONDITIONAL;
- CANCELLED != DELETED;
- item excepcional da competência;
- correção estrutural pós-execução por request/review/nova revisão;
- promoção ao mestre somente por MANAGE e sem retroatividade.

### Audit / notifications
Preservar versões rejeitadas, substituições, reversões, N/A, cancelamento, correções e ator/timestamp/reason.

Notificações seguem [16-configuracoes-catalogos-e-notificacoes.md](./16-configuracoes-catalogos-e-notificacoes.md).

### Help
Requirement types, satisfaction rules, upload vs validation, multi-anexo, N/A, rejeição/substituição, cancelamento e correção estrutural.

### Dependências / stop
E05/E06 para seeds; T02 para capability de notificação; T05 para effective permissions/ownership.

## P3 — Estoque, Cutoff e Conciliação

### Objetivo
Expor readiness do estoque, confirmar cutoff, revalidar fontes e provar paridade monetária antes do fechamento canônico.

### Composição lógica

```text
ClosingContext
→ CutoffStatus
→ RevalidationPanel
→ ReconciliationSummary
→ ReconciliationDrilldown
→ SourceFreshness
→ ClosingHistory
→ ContextualHelp
```

### Atores e acesso
- usuário autorizado pode confirmar cutoff/reprocessar;
- V1 não executa escrita ERP;
- owner autorizado continua responsável pela sacramentação real.

### Owners / sources
- P7, Entradas/Saídas e H02: bindings T01;
- STOCK_CLOSED: owner canônico a confirmar em T03;
- não criar fallback manual silencioso para estado canônico ausente.

### Regra monetária
```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
TOLERANCIA_MONETARIA = NONE
```

Qualquer valor não zero bloqueia READY_TO_CLOSE.

### Estados/interações
PRELIMINARY → WAITING_FOR_CUTOFF → REVALIDATION_REQUIRED → READY_TO_CLOSE → STOCK_CLOSED.

Zero pré-cutoff continua preliminar. Alteração de input após revalidação deve invalidar a prontidão aplicável.

### Freshness/proveniência
Exibir source, fetched/calculated_at, competência, unidade, preliminary/final e rule/version.

### Help
Cutoff, revalidação, paridade exata, preliminary/final, source indisponível e diferença entre READY_TO_CLOSE e STOCK_CLOSED.

### Dependências / stop
T03 é stop condition material. Se owner canônico não existir ou for incompatível, EXECUTION_DRIFT.

## P4 — Classificações e Pendências

### Objetivo
Assistir classificação/CC necessária ao fechamento e operar filas de pendências sem automatizar decisão humana.

### Composição lógica

```text
PendencyFilters
→ PendencyQueue
→ ClassificationWorkbench
→ PendencyDetail
→ EvidenceContext
→ OwnershipHistory
→ ContextualHelp
```

### Atores e acesso
- ACCESS opera pendências conforme ownership/business rules aplicáveis;
- usuário/papel autorizado pode claim/reassign/resolve;
- IA sugere; humano confirma;
- V1 não grava ERP.

### Owners / sources
- autoridade de CC: gestor/solicitante quando aplicável;
- dados/evidências: sources autorizados;
- P4 registra decisão do Portal, não se torna owner da regra upstream.

### Estados/interações
OPEN, IN_ANALYSIS, WAITING_EXTERNAL, RESOLVED, DISMISSED.

DISMISSED exige justificativa e não substitui NOT_APPLICABLE nem serve para esconder blocker.

### Boundary
A fatia P4 do fechamento não é a mesma feature que despesas por CC do Portal Financeiro P0. Expansão corporativa fora do fechamento exige novo gate.

### Help
Owner/responsável, estado, evidência, sugestão IA, decisão humana, dismiss e ausência de SLA/overdue.

### Dependências / stop
T01 para source e T05 para effective permissions/ownership. Regra nova de classificação sem homologação não pode ser inventada.

## P5 — Pacote, Finalização e Envio

### Objetivo
Versionar o pacote do fechamento, finalizar, enviar por destinatário, tratar esclarecimentos e derivar conclusão mensal.

### Composição lógica

```text
PackageSummary
→ RecipientPackages
→ FinalizationPanel
→ DeliveryStatus
→ ClarificationPanel
→ VersionHistory
→ ContextualHelp
```

### Atores e acesso
Ações dependem de ACCESS + resource ownership quando aplicável + business rule. Envio exige capability real; UI não autoriza sozinha.

### Estados/interações
```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED
→ PACKAGE_SENT
→ WAITING_FOR_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

Finalizar != Enviar.

Pacotes por destinatário avançam independentemente. PACKAGE_SENT é imutável; correção pós-envio cria complemento/nova versão ligada ao histórico.

### Canal
A finalização/versionamento está especificada.

O slice de envio permanece bloqueado por:
- E04 — canal real;
- T04 — capability corporativa.

Não assumir e-mail, pasta, Teams ou mecanismo próprio.

### Help
Finalizar vs Enviar, versionamento, envio parcial, imutabilidade, esclarecimentos e critério de conclusão.

### Dependências / stop
Q22/E04/T04 bloqueiam implementação do envio real, não a modelagem de pacote/finalização.

## P6 — Administração e Configuração

### Objetivo
Administrar templates, catálogos, vigências e regras futuras sem alterar snapshots históricos.

### Composição lógica

```text
AdministrationNavigation
→ TemplateVersions
→ CatalogManagement
→ EffectiveDatePanel
→ PublicationPanel
→ AuditHistory
→ ContextualHelp
```

### Atores e acesso
- ACCESS usa opções vigentes;
- MANAGE cria/administra/publica mestre e catálogos;
- sem permission por botão/CRUD.

### Estados/interações
DRAFT → REVIEW → PUBLISH → EFFECTIVE_FROM.

ACTIVE → INACTIVE_FROM(date), sem delete físico.

Publicação futura não altera competência já aberta nem pacote histórico.

### Catálogos
Governar:
- bancos/contas;
- checklist items;
- requirement;
- origin;
- recipients;
- operational responsible;
- validator;
- satisfaction rule;
- validation scope;
- notification targets;
- attachment roles;
- extensões de motivos;
- vigência.

`CONFIGURABLE != FREE_FORM_EVERYWHERE`.

### Audit
Registrar draft/update/publish/inactivation e mudanças de catálogo com ator, motivo e vigência.

### Help
Draft vs publicado, effective_from, snapshot, inativação, ACCESS vs MANAGE e impacto prospectivo.

### Dependências / stop
E01/E05/E06 para seeds; T02 para notificações; T05 para effective permissions/ownership.

## Deep links

Cada página deve preservar contexto relevante — competência, unidade, item, destinatário ou filtro — no mecanismo de navegação definido durante arquitetura técnica.

Não definir route pattern antes do inventário de plugin/basePath. O contrato de deep link deve ser provado no HEAD e testado com F5 sem bypass de AuthZ.

## Matriz de completude

| Página | Produto/regra | UX states | Security | Audit | Help | Source/owner | RQ/AC | Estado documental |
|---|---|---|---|---|---|---|---|---|
| P1 | coberto | coberto transversalmente | coberto | histórico coberto | definido acima | composição + T01/T05 | ledger 23 | READY_FOR_IMPLEMENTATION_INVENTORY |
| P2 | coberto | coberto transversalmente | coberto | coberto | definido acima | produto + sources autorizados | ledger 23 | READY_FOR_IMPLEMENTATION_INVENTORY |
| P3 | coberto | coberto transversalmente | coberto | coberto | definido acima | T01/T03 | ledger 23 + 15.1 | READY_WITH_STOP_CONDITION_ON_T03 |
| P4 | coberto | coberto transversalmente | coberto | coberto | definido acima | owner CC + T01/T05 | ledger 23 | READY_FOR_IMPLEMENTATION_INVENTORY |
| P5 | finalização coberta; envio condicionado | coberto transversalmente | coberto | coberto | definido acima | E04/T04 para envio | ledger 23 | PARTIALLY_READY |
| P6 | coberto | coberto transversalmente | coberto | coberto | definido acima | E/T aplicáveis | ledger 23 | READY_FOR_IMPLEMENTATION_INVENTORY |

## Regra de execução

Este handoff fecha a **documentação funcional** necessária para começar inventário técnico por página.

Não define:
- plugin id;
- BFF;
- basePath;
- schema físico;
- migrations;
- endpoints;
- names de services.

Esses itens devem ser provados no HEAD antes do primeiro diff técnico.
