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
→ PACKAGE_SENT
→ WAITING_FOR_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
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
