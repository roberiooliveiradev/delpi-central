# Perfis e permissões — Portal Suprimentos

> Contrato vigente: [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md).  
> ADR-006 está superseded. ADR-008 permanece só para `access` / `manage`.  
> ADR-007 e as seções abaixo de **Histórico** não autorizam o runtime.

## Modelo vigente

| Persona | Grants |
|---|---|
| Uso normal | `supplies.access` |
| Administração | `supplies.manage` |
| Uso + administração | `supplies.access` e `supplies.manage` |

`manage` não abre leitura operacional.

Unidade não é permission. Com `supplies.access`, o filtro de dados é o universo do produto: `01` Santa Catarina e `02` Espírito Santo. «Todas» = `01`+`02`.

A tela de Solicitações do Portal acompanha as SC desse universo, sem recorte de centro de custo. O módulo standalone de Solicitações mantém `purchase-requests.access`, `admin`, `view-all`, `export` e `unit.*`.

O JWT identifica. A Core resolve `access` / `manage`. A supplies-api aplica o escopo. O MFE não autoriza.

## Histórico / SUPERSEDED

Até ADR-009, o desenho ensinava eixo de unidade `supplies.unit.filial-*`, capabilities fragmentadas (`portal`, `operations`, `analytics`, `purchase-requests`, `administration`) e `supplies.purchase-requests.view-all`. Esse modelo não é o catálogo do manifest 0.4.0. Evidência e papéis da época ficam em ADR-006, ADR-007 e no histórico do Git deste arquivo. Não recriar esses códigos no Portal.
