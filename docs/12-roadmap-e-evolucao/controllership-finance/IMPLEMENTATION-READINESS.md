# Implementation Readiness — Portal Controladoria & Finanças

> **Status:** NOT_STARTED  
> **Base:** TÉO PROC-0072 consolidado até 2026-10-05

| Superfície | Estado | Observação |
|---|---|---|
| P1 — Cockpit | READY_FOR_IMPLEMENTATION_INVENTORY | depende de P2/P3/P5, freshness e scopes |
| P2 — Checklist e Documentos | READY_FOR_IMPLEMENTATION_INVENTORY | seeds/catálogos e notificações serão inventariados |
| P3 — Estoque e Conciliação | READY_WITH_STOP_CONDITION | T03 deve provar estado canônico cutoff/STOCK_CLOSED |
| P4 — Classificações/Pendências | READY_FOR_IMPLEMENTATION_INVENTORY | V1 sem escrita ERP |
| P5 — Pacote/Envio | PARTIALLY_READY | Q22 depende E04 + T04 |
| P6 — Administração | READY_FOR_IMPLEMENTATION_INVENTORY | catálogos e RBAC a inventariar |

## PENDING_IMPLEMENTATION_CONFIRMATION

- E01 — seed/owner da lista bancária configurável
- E02 — correção real pós-sacramentação
- E03 — executor/permissões da sacramentação
- E04 — canal operacional real de envio
- E05 — attachment roles reais/seed
- E06 — cobertura do catálogo inicial de motivos

## TO_INVENTORY

- T01 — bindings DAVI / api-delpi
- T02 — notificações Minha DELPI
- T03 — cutoff / STOCK_CLOSED canônico
- T04 — capability corporativa de envio
- T05 — ACCESS / MANAGE / scopes no Core

## Configurabilidade já fechada

Bancos/contas, checklist items, requirement/origin type, recipients, operational responsible, validator, satisfaction rule, validation scope, notification targets, attachment roles, extensões de motivos e vigência de templates são configuráveis.

`CONFIGURABLE != FREE_FORM_EVERYWHERE`: ACCESS usa opções existentes; MANAGE administra catálogos/versões.

## Stop conditions

`EXECUTION_DRIFT` e STOP quando:
- T03 contradizer o modelo de STOCK_CLOSED;
- E04/T04 não suportarem o desenho de envio;
- T05 contradizer ACCESS/MANAGE;
- E02 contradizer state model pós-fechamento;
- evidência nova invalidar owner/regra/contrato TARGET.

## Execução

Antes da feature: revalidar HEAD, authorities, owners, contratos, AuthZ, testes, Help e gate. Documento/rota futura não autoriza implementação por si só.
