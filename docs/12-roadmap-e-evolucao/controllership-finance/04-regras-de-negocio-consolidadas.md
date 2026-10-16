# 04 — Regras de Negócio Consolidadas

## GAP-RULE-01 — SD1 / Centro de Custo

**Estado:** CLOSED_AT_REPORT_LEVEL / PARTIAL_AUTOMATION.

Campos funcionais confirmados:
- competência: `DT Digitação`;
- filtro visual: `Tipo Entrada`;
- `Cod. F` é campo distinto com códigos fiscais de 4 dígitos;
- `Tipo Produto` identifica MP;
- CC original: `C Custo`;
- analítico: `Classificação / Tipo Despesa`.

Valores aceitos na fatia validada:
`001, 003, 016, 018, 019, 020, 028, 030, 080, 083, 085, 204, 318`.

A lista executável completa continua PARTIAL.

Não inferir campos físicos D1*/B1*.

02xx/03xx/04xx = padrão/heurística, não classificador determinístico.

0407/0413 = casos reais; tratamento caso a caso. Não existe target CC universal provado.

Coparticipação pode ficar sem CC conforme natureza/descrição; fornecedor sozinho é insuficiente.

Owner da autoridade de CC: gestor/solicitante.

## GAP-RULE-02 — Kardex 01 / CPV

**Estado:** DETERMINISTIC no nível do relatório.

- Kardex Físico-Financeiro/Estoque;
- armazém 01;
- período da competência;
- filtro `C.F.`;
- valores aceitos: 5101, 6101, 6124;
- TES é distinto;
- totalização `SAIDAS CUST`;
- cálculo por unidade.

Acompanha Custos = pré-requisito PROVEN.

Fechamento do faturamento é necessário para valor final.

Custo Reposição/Refaz Saldos não são pré-requisitos estritos comprovados.

Residual ~R$3,80/R$4,00 = caso específico, não tolerância.

Destino: Fiscal.

## GAP-RULE-03 — Kardex 99 / Inventário

**Estado:** CLOSED_AT_BUSINESS_RULE_LEVEL / INFORMED.

- armazém 99;
- INVENT/INVENTE;
- entradas = sobra/ganho;
- saídas = falta/perda;
- líquido = Entradas Custo - Saídas Custo.

Exemplo ~-R$57 mil não é target.

Acompanha Custos = dependência forte.

Destino: Contábil.

## GAP-RULE-04 — Faturamento × MOD

**Estado:** DETERMINISTIC.

Relatório `Kardex e Faturamento por MOD`.

Campos: Produto, Descrição, Nota, Quantidade, Centro de Trabalho, Valor MOD/Mão de Obra, Valor Total.

Regra:
- considerar linhas válidas de produtos faturados;
- ignorar headers/subtotais;
- `SUM(Valor MOD)` por unidade.

Sem filtro PROVEN `Valor MOD > 0`.

MOD = mão de obra incorporada/faturada no produto, não folha.

Separar de custo-hora anual/PROC-0010.

Destino: Contábil.

## GAP-RULE-05 — Conciliação tripla

Exemplo:
- Entradas/Saídas = R$ 3.890.247,18
- P7 = R$ 3.776.994,69
- H02 = R$ 64.591,71

```text
Divergência = Entradas/Saídas - P7 - H02
```

Calculado: R$ 48.660,78. Verbal: R$ 48.660,77.

Diferença R$0,01 = UNKNOWN_CAUSE.

Não inventar hidden decimals/transcription.

A regra corrente exige **paridade monetária exata até os centavos**:

```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
```

- R$ 0,00 = paridade;
- R$ 0,01 = divergência;
- R$ -0,01 = divergência;
- R$ 0,25 = divergência;
- qualquer valor diferente de R$ 0,00 = divergência.

Não existe tolerância monetária implícita, faixa de arredondamento aceitável ou descarte de centavos.

R$0,25 em Insumos permanece como caso/evidência histórica; **não é valor aceitável de fechamento**.

A implementação não pode introduzir epsilon/tolerância numérica para decidir a paridade monetária. A representação técnica do valor é decisão de implementação, mas o critério de negócio continua sendo igualdade exata em centavos.

Investigação: `total → grupo → item/evidência`.

## GAP-RULE-06 — Cutoff / revalidação / sacramentação

Cutoff = fim dos movimentos que ainda podem alterar estoque/faturamento.

~18h é referência prática, não regra fixa.

Estados:

```text
PRELIMINARY
→ WAITING_FOR_CUTOFF
→ REVALIDATION_REQUIRED
→ READY_TO_CLOSE
→ STOCK_CLOSED
```

Pós-cutoff:
- P7;
- Entradas/Saídas;
- H02;
- conciliação tripla.

`READY_TO_CLOSE = cutoff + revalidação aplicável + divergência zero`.

MATA280 = INFORMED / INFERRED / TO_INVENTORY.

## GAP-RULE-07 — Pacote / completude

Processo inicia no primeiro dia e termina após envio + esclarecimentos.

XML/SPED não deve virar upload obrigatório sem mudança formal.

Dennis = dependência específica XP.

Estados:

```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ REVIEW_PENDING / REVIEW_IN_PROGRESS
→ REVIEW_ACCEPTED | CHANGES_REQUESTED
→ [MONTHLY_CLOSING_COMPLETED per D-P5-REVIEW-COMPLETION]
```

## Regras adicionais

### FINR190
- primeiro ao último dia;
- pagos por DATA e NATUREZA;
- Receber altera "Da Carteira?";
- procedimento cita empresas 01,03,04.

### Extratos
Conta aplicável sem movimento ainda requer extrato.

`NO_MOVEMENT != NOT_APPLICABLE`.

### P7 / consumo
- P7 = MATR460;
- consumo/Relação por OP = MATR860;
- `MATR860 != P7`.

### Vocabulário fiscal
Inclui Alimentação, Amostra MP, Assistência Médica, Ativo, Combustível, Consumo Geral, Embalagem, EPI, Frete, Informática, Insumo, Limpeza, Manutenção, Material de Expediente, MP, Segurança/Vigilância.

Não inferir campo físico do Protheus a partir desse vocabulário.


## Regras TARGET transversais — Gate V2

As regras GAP-RULE acima preservam evidência específica de relatórios/fontes. As regras abaixo consolidam o comportamento TARGET do produto e não substituem a provenance original.

### RULE-T01 — Competência e snapshot

```text
COMPETENCE OPEN
→ SNAPSHOT(template version + effective configuration)
```

Nova publicação não altera competência já aberta.

### RULE-T02 — Requirement / satisfaction

```text
REQUIRED
CONDITIONAL
OPTIONAL
```

- REQUIRED nunca vira N/A;
- CONDITIONAL pode N/A somente quando regra permitir, com justificativa;
- OPTIONAL ausente não bloqueia;
- `ATTACHED != VALIDATED`;
- `NO_MOVEMENT != NOT_APPLICABLE`.

### RULE-T03 — Evidência e validação

- versões históricas não são sobrescritas;
- PER_ATTACHMENT valida cada arquivo;
- WHOLE_SET valida o conjunto;
- rejeição preserva motivo/histórico;
- replacement não herda aceite automaticamente;
- reversão é governada e bloqueada quando nova versão já existe.

### RULE-T04 — Item excepcional / correção estrutural

- item excepcional pertence à competência, não altera mestre;
- pré-execução permite edição governada;
- cancelamento é `CANCELLED`, não delete;
- pós-execução usa request → MANAGE review → nova revisão;
- MANAGE pode autoaprovar mantendo request/approval auditados separadamente;
- promoção ao mestre é prospectiva.

### RULE-T05 — Source / completeness

```text
SOURCE_UNAVAILABLE != ZERO
SOURCE_UNAVAILABLE != EMPTY
PRELIMINARY != FINAL
```

Source/freshness/proveniência devem permanecer visíveis quando materiais.

### RULE-T06 — Cutoff / paridade / STOCK_CLOSED

```text
PRELIMINARY
→ WAITING_FOR_CUTOFF
→ REVALIDATION_REQUIRED
→ READY_TO_CLOSE
→ STOCK_CLOSED
```

```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
TOLERANCIA_MONETARIA = NONE
```

Decisão E02 aprovada em 09/10/2026:

```text
STOCK_CLOSED
= terminal no lifecycle P3 do Portal V1
```

O Portal V1:
- não reabre;
- não desfaz sacramentação;
- não retifica localmente `STOCK_CLOSED`;
- preserva histórico;
- deixa correções posteriores no owner canônico/ERP.

T03 continua necessário para provar o owner/state canônico.

### RULE-T07 — Classificação e pendências

```text
AI_SUGGESTION != HUMAN_DECISION
PENDING_SINCE != SLA
DISMISSED != NOT_APPLICABLE
```

Estados:
- OPEN;
- IN_ANALYSIS;
- WAITING_EXTERNAL;
- RESOLVED;
- DISMISSED.

IA explica/sugere; humano autorizado confirma. V1 não grava correção ERP.

### RULE-T08 — Pacote / finalização / envio

```text
READY_TO_FINALIZE
!= PACKAGE_FINALIZED
!= PACKAGE_SUBMITTED_FOR_REVIEW
!= REVIEW_ACCEPTED
!= MONTHLY_CLOSING_COMPLETED
```

- finalizar cria versão/snapshot e não submete;
- recipient packages avançam independentemente;
- reabertura antes da submissão cria nova working/version;
- PACKAGE_SUBMITTED_FOR_REVIEW é histórico e não é editado in-place;
- correção após submissão cria complemento/nova versão;
- reviewer autenticado continua o processo dentro da Minha DELPI;
- e-mail é notification side effect, nunca transport do package;
- monthly completion depende de D-P5-REVIEW-COMPLETION.

Envio para análise:

```text
PACKAGE_STAYS_IN_MINHA_DELPI = YES
PACKAGE_TRANSPORT_BY_EMAIL = NO
PACKAGE_SUBMITTED_FOR_REVIEW = BUSINESS_STATE
NOTIFICATION_DISPATCHED != PACKAGE_SUBMITTED_FOR_REVIEW
EMAIL_SENT != PACKAGE_SUBMITTED_FOR_REVIEW
```

### RULE-T09 — Administração / configuração

```text
DRAFT
→ REVIEW
→ PUBLISH
→ EFFECTIVE_FROM
```

- save != publish;
- um MANAGE pode publicar com auditoria;
- no hard delete;
- effective dating prospectivo;
- catálogos tipados;
- identities permanecem Core references.

### RULE-T10 — Notifications

Core Notification capability é PROVEN no HEAD revalidado em 09/10/2026.

```text
POST /integrations/notifications
= platform notification capability

NOTIFICATION_FAILURE != BUSINESS_STATE_CHANGE
NOTIFICATION_DISPATCHED != PACKAGE_SUBMITTED_FOR_REVIEW
EMAIL_SENT != PACKAGE_SUBMITTED_FOR_REVIEW
```

O produto ainda define adapters/event payloads/recipients; não cria SMTP/preferences paralelos.

### RULE-T11 — AuthZ

```text
JWT = identity/context
Core PermissionResolver = effective permission authority

ALLOW
= capability
AND resource_scope / ownership
AND business_rule
```

Permission codes do produto:
- `controllership-finance.access`;
- `controllership-finance.manage`.

`ACCESS != MANAGE`.

Unidade/filial é dimensão de dado/contexto, não permission code.

### RULE-T12 — Colaboração / tarefas

```text
MESSAGE != BUSINESS_DECISION
ROOM_MEMBER != AUTHORIZATION_GRANT
CHAT_ATTACHMENT != P2_EVIDENCE
TASK_PROJECTION != TASK_ENTITY
BLOCKER != MY_TASK
MENTION != MY_TASK
```

Minhas tarefas é self-only e abre o owner. A Sala não cria task genérica na V1.

### RULE-T13 — Temporalidade

```text
FORMAL_SLA = NO
DUE_DATE = NO
OVERDUE = NO
SLA_BREACH = NO
TIME_BASED_ESCALATION = NO
PENDING_SINCE = YES
```

Exceção: prazo só existe quando owner específico possuir due formal real.

### RULE-T14 — Help

```text
USER_FACING_CHANGE
→ HELP_SYNC
→ FEATURE ACCEPTANCE
```

Help runtime só publica capability implementada/autorizada.

### RULE-T15 — Documented vs implemented

```text
DOCUMENTED != IMPLEMENTED
READY_FOR_IMPLEMENTATION_BRIEF != IMPLEMENTATION_AUTHORIZED
```

FASE A não cria runtime.


## Decisões PO P5-F a P5-J — consolidação contratual vigente (16/10/2026)

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este adendo é superveniente aos registros de perguntas abertas P5-F..J e prevalece quando notas históricas anteriores conflitarem. C2, D-P5-02..05 e P5-A..E permanecem válidas nos termos abaixo. A antiga unanimidade de *pessoas* em D-P5-01 foi substituída pela unanimidade das *áreas obrigatórias* em P5-A.

| ID | Resultado aprovado | Invariante |
|---|---|---|
| **P5-F = A** | Substituição de responsável mantém válido o aceite já realizado para a mesma área e PackageVersion; a autoria permanece a do executor original. Substituto assume somente ações futuras. | REASSIGNMENT != INVALIDATE_PRIOR_ACCEPTANCE |
| **P5-G = A** | Aceite P5 não é reversível/alterável pela UI V1. Eventual erro exige processo excepcional separado, formal, auditado e **não autorizado enquanto seu contrato não for aprovado**. | NO_P5_ACCEPTANCE_REVERSAL_IN_V1 |
| **P5-H = A** | P6 configura por tipo de pacote as áreas/especialidades obrigatórias em versão governada; P5 congela a configuração aplicável na submissão. Core fornece identidade, effective permissions e atributos de grupo/função conforme contrato a inventariar. | REVIEW_AREA_SET_SNAPSHOTTED_ON_SUBMISSION |
| **P5-I = B** | Reviewer elegível registra rejeição do pacote em nome da área; uma **autoridade operacional formalmente definida**, distinta da simples permission MANAGE, confirma com justificativa e auditoria a rejeição terminal da competência. | AREA_PACKAGE_REJECTION != TERMINAL_COMPETENCE_REJECTION |
| **P5-J = A** | Após confirmação da rejeição terminal, a competência fica rejeitada e todas as projeções/tarefas de revisão ainda acionáveis deixam de sê-lo; histórico, decisões e autoria permanecem consultáveis conforme AuthZ. | REJECTED_COMPETENCE != MONTHLY_CLOSING_COMPLETED |

### Compatibilidade com regras anteriores

- **C2:** competência concluída somente se TODOS os pacotes aplicáveis foram submetidos, TODAS as áreas obrigatórias aceitaram a PackageVersion vigente e NÃO há esclarecimento aberto. Competência rejeitada nunca satisfaz `MONTHLY_CLOSING_COMPLETED`.
- **P5-A / D-P5-01:** quorum de um aceite por área obrigatória, executado por qualquer usuário elegível; não por indivíduo. Dois elegíveis na mesma área não criam dois aceites necessários.
- **P5-B / D-P5-03 / P5-G:** ninguém sobrescreve aceites; nem o autor pode revertê-los pela UI V1. A referência antiga a “autor pode alterar” é **superseded para aceite P5 na V1**. Reatribuição formal não autoriza mutação de decisões anteriores.
- **P5-C / D-P5-04:** ACCESS efetivo + grupo/função corporativa elegível + escopo do recurso + regra da ação; avaliação server-side fail-closed; reviewer assignment nunca se torna novo permission code.
- **D-P5-02 / P5-E:** esclarecer sem alterar conteúdo preserva versão; qualquer alteração de conteúdo cria nova PackageVersion e **exige novos aceites de todas as áreas obrigatórias**; histórico de versões anteriores preservado.
- **D-P5-05 / P5-D / P5-I:** `CHANGES_REQUESTED` não é `REVIEW_REJECTED`; rejeição da área/pacote não encerra competência automaticamente; só confirmação por autoridade operacional a leva ao estado terminal rejeitado.
- **P5-F / P5-H:** reatribuir elegível não altera aceite já registrado, nem o snapshot de áreas obrigatórias da submissão; edição futura do catálogo P6 não altera snapshots abertos.
- **P5-J:** `TaskProjection != TaskEntity`; P5 continua owner do lifecycle; revisão terminal rejeitada remove acionabilidade, sem hard delete nem apagamento de evidências.

### Trilha de auditoria obrigatória

Preservar identidade Core do ator, data/hora, ação, contexto competência/recipient package, versão, área obrigatória, elegibilidade/scope verificados, motivo/justificativa quando exigidos, estado anterior/posterior, autor original do aceite, referência a reatribuições, confirmação formal da rejeição e correlação da projeção/notificação. Histórico é append-only no nível semântico; **schema físico não definido**.

### Pendências reais — sem aprovação presumida

1. **DECISION_REQUIRED:** quem é a autoridade operacional de confirmação de rejeição terminal; como é designada e substituída, e se a confirmação pode ser negada (e qual estado fica então). Não equiparar automaticamente a `manage`.
2. **DECISION_REQUIRED:** procedimento excepcional de correção de aceite P5 fora da UI V1 (owner, autorização, efeitos na conclusão mensal e revalidação), se for implementado nesta versão; na ausência de decisão, **capability não existe na V1**.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **CONTRACT_PENDING:** mapa versionado tipo de pacote → áreas obrigatórias em P6; regras de publicação/vigência/snapshot, defaults inválidos, configuração ausente e concorrência; não inventar tabelas/migrations.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.
