# ADR-009 — Acesso de produto e escopo operacional de dados

| Campo | Valor |
|-------|--------|
| Status | Aceito — contrato vigente do Portal Suprimentos |
| Contexto | Manifest 0.4.0 e runtime já usam só `supplies.access` e `supplies.manage` |
| Supersede | [ADR-006](./ADR-006-unit-permissions.md) por completo; trechos de unidade e `view-all` do Portal em [ADR-008](./ADR-008-access-manage-rbac.md) |
| Relacionados | ADR-001, ADR-002, ADR-007 (histórico), ADR-008 |

## Decisão

O catálogo do **novo Portal Suprimentos** é somente:

- `supplies.access` — uso normal do produto
- `supplies.manage` — administração do Portal

`manage` não implica `access`. Quem administra e usa o produto recebe os dois grants. Não há permission por página, unidade, exportação, endpoint ou CRUD.

A Core API continua a authority das capabilities efetivas. O JWT identifica o usuário. Claim de permission no JWT não autoriza.

## Escopo de dados, não grant de filial

O universo operacional atual do produto é fixo:

- `01` — Santa Catarina
- `02` — Espírito Santo

`supplies.access` habilita esse universo. A seleção Todas | Santa Catarina | Espírito Santo é filtro de dados. «Todas» significa `01`+`02`, nunca todas as filiais existentes no TOTVS. Filial desconhecida é erro de contrato. Filial nova exige decisão de produto, não permission nova.

Não existem `supplies.unit.*`.

## Solicitações

A tela de Solicitações do Portal é acompanhamento global dentro de `01`/`02`. Não há recorte de centro de custo nessa jornada e não existe `supplies.purchase-requests.view-all`.

O módulo standalone `purchase-requests` mantém o próprio RBAC (`purchase-requests.access`, `admin`, `view-all`, `export`, `unit.*`). `supplies.access` no token do usuário, sozinho, não ativa o acompanhamento global.

Esse contexto só atravessa para `purchase-requests-api` quando a chamada é da `supplies-api` com service token interno válido. Caller falso, token inválido ou token ausente não são confiáveis.

`supplies.manage` não concede `purchase-requests.admin`.

## Fronteiras

O MFE chama somente `supplies-api`.

`supplies-api` → `api-delpi` e `supplies-api` → `purchase-requests-api` usam identidade S2S (`X-Delpi-Caller-App: supplies-api` + `X-Delpi-Service-Token`). A api-delpi não refaz a autorização do Portal já tomada pela BFF nessa chamada confiável. Chamada direta continua no contrato do downstream.

`purchase-requests-api` → `api-delpi` para linhas de SC usa a identidade `purchase-requests-api` + service token. `supplies.access` no usuário não é grant direto na api-delpi.

E9, quando for autorizada, usa `supplies.access` e o mesmo escopo de dados. Não cria permission de entregas.

## Consequências

Papel de uso normal = `supplies.access`. Papel admin = `supplies.manage`, com `access` se também usa o produto. Unidades deixam de ser atribuídas no Core para este Portal.
