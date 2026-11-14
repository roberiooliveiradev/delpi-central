# ADR-003 — Auditoria de entradas na BFF

| Campo | Valor |
|---|---|
| Status | **ACCEPTED** |
| Data | 2026-11-14 |
| Decisor | owner do produto (trilha aprovada em 2026-11-13) |
| Contexto | Auditoria de entradas Protheus × XML de NF-e e CT-e |
| Relacionados | [plan.md](../entry-audit/plan.md) · [backend](../entry-audit/backend/README.md) · [trilha](../entry-audit/track.md) · [ADR-001](./ADR-001-hospedagem-lancamento-notas-fiscais.md) |

O contrato (payloads, `V023`, chave estável, ids de regra, flag) está no backend §6. Este ADR registra a decisão e o que ficou de fora.

## Decisão

A auditoria roda na `controllership-finance-api`. O motor é domínio puro. O Protheus é lido pela api-delpi e o XML pela financial-api. O resultado fica no schema `controllership_finance`. A CLARA usa as seis tools que já existem.

| Id | Decisão |
|---|---|
| D1 | Motor na BFF, domain sem framework, HTTP, banco ou SDK. Fontes por adapters. |
| D2 | Dados automáticos. Sem upload. A T0 mostrou que o Questor filtra emissão. |
| D3 | Front-end com `@delpi/plugin-ui`. Fora deste ADR até a T10. |
| D4 | Tudo com `controllership-finance.access`. `manage` herda. Sem permission nova. |
| D5 | Página própria, com atalho no Fechamento mensal. Fora deste ADR até a T11. |
| D6 | CLARA audita num comando. `run`, `rerun`, `resolve` e `reopen` são diretos. As seis tools não mudam. |
| D7 | Worker no `lifespan` da BFF. Uma análise por filtros; uma execução por filial. |
| D8 | Filtros da execução: período De/Até pela data de recebimento, tipo NF-e/CT-e, filiais. |
| D9 | Primitivos novos nascem no plugin-ui. Fora deste ADR até a T10. |
| D10 | Sob demanda. Sem agendamento. |
| D11 | XML pela chave para toda nota da SF1; listagem por emissão só para achar o que não foi lançado; «só no XML» com solicitação aberta no LNF fica «Em lançamento (LNF)». |
| D12 | TES 004, CFOP 352, folga de 30 dias, graça de 3 dias e tolerância de R$ 0,05 em variáveis. Cada análise grava a configuração. |
| D13 | `ENTRY_AUDIT_ENABLED` (padrão `false`) controla rotas `/entry-audit/*`, worker e entradas da CLARA. Rotas de leitura da api-delpi e da financial-api não usam a flag. |
| D14 | Fichas AE-00 a AE-15 no domínio `controllership` do corpus. |

Completam a decisão, pela evidência da T0:

- a rota `branches` lê `SYS_COMPANY` com `M0_CODIGO = '01'`;
- a contagem da listagem de NF-e do Questor é o número de linhas, não o total informado pelo portal;
- a solicitação do LNF é achada pelo número e pelo fornecedor; a chave só existe quando há DANFE anexado;
- a auditoria não escreve no Protheus, no Questor nem no LNF.

Dívida registrada na revisão de T0–T3: a api-delpi aceita a BFF nas leituras `/financeiro/entry-audit/*` pelo escopo S2S `stock-inventory.read`, reaproveitado para não criar permissão nem escopo novo. O escopo descreve outro conjunto de dados. A troca por um escopo próprio da auditoria fica para quando o Keycloak puder ser provisionado sem 403.

O rework da T5 tira o bearer do usuário do worker. Quem pede a análise continua sendo um usuário com `controllership-finance.access` (ou a CLARA em nome dele). A execução, inclusive a retomada depois de um reinício, lê o Protheus e o XML com a credencial de serviço da BFF (`ClientCredentialsTokenProvider`, cliente `controllership-finance-api`). A api-delpi aceita essa credencial sozinha nas rotas `/financeiro/entry-audit/*`, no mesmo guard S2S das outras leituras financeiras e sem bearer delegado. A financial-api aceita o mesmo cliente e o mesmo escopo nas rotas de leitura de notas recebidas, além do token interno que já existia. Não há permission nova de usuário.

## Alternativas rejeitadas

- Motor na skill, com planilha no meio: a SF4 fica velha e o resolvido não é da equipe.
- Upload do ZIP como caminho normal: a listagem por data existe.
- Permission nova ou tool MCP nova: as seis tools e o `access` já cobrem.
- SQL do Protheus na BFF: o owner do TOTVS é a api-delpi.
