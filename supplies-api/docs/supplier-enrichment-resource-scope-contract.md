# SUPPLIER_RESOURCE_SCOPE_CONTRACT — GATE-A (S2)

> **Estado: EVIDENCE-DRIVEN.** Contrato de escopo de acesso para revisões de
> enriquecimento cadastral de fornecedores na `supplies-api`.
> Fórmula exigida: `capability AND unit_scope AND resource_scope/ownership AND business_rule`.

## Evidências do HEAD

| Dimensão | Evidência | Fonte |
|---|---|---|
| capability | `supplies.access` resolvida do Core `/me` (effective permissions); middleware fail-closed (Core down → 503; nunca JWT como autoridade) | `app/interfaces/http/auth_middleware.py`, `authorization_service.py` |
| unit_scope | Core `/me` **não retorna** unidades/filiais por usuário — não existe grant de unidade por usuário na plataforma | `core-api/app/interfaces/http/me_controller.py` |
| unit_scope | `OPERATIONAL_UNITS = ("01","02")` é catálogo fixo; `allowed_units` devolve todos para qualquer `supplies.access` — usado apenas em recursos dimensionados por `branch` (pedidos/SC) | `supplies_permissions.py` |
| supplier↔unit | Fornecedores SA2 são **master data global** — nenhuma rota supplier (GET/POST/PUT) possui dimensão de unidade; api-delpi não filtra fornecedor por filial | `suppliers_routes.py`, `protheus_router.py` |
| resource_scope | Nenhum recurso de revisão existia; modelo novo definido por este contrato | — |

## Modelo adotado (S2)

```text
access = capability(supplies.access, Core)
       AND resource_scope(actor ownership)
       AND business_rule(J-only, CNPJ identity, review window)
```

- **capability**: `can_use_operations` (=`supplies.access`) — mesmo nível das rotas supplier existentes. Zero novas permissions.
- **unit_scope**: **não aplicável a fornecedores** — SA2 é master data global em todos os contratos vigentes; nenhuma correspondência `code/store ↔ unidade` existe e **não foi inventada**. `unit_context` na tabela permanece `NULL` até existir contrato Core canônico.
- **resource_scope/ownership**: **review é propriedade do ator criador.** `actor_subject` é derivado server-side de `EffectiveUser.id` (Core); leitura, listagem, decisão e prepare exigem `review.actor_subject == user.id` — acesso cruzado → 403. Escopo mais estrito que o próprio dado de fornecedor (qualquer `supplies.access` lê qualquer fornecedor).
- **business_rule**: fornecedor `person_type == "J"`; identidade externa ≡ CNPJ; revisão dentro de `expires_at`.

## Validação por operação

| Operação | Checagem |
|---|---|
| create review | capability + supplier legível via GET canônico (404 propaga) + person_type J |
| get/list review | capability + `actor_subject` bound |
| decisions | capability + ownership + status/revision/expiry |
| prepare-update | capability + ownership + baseline fingerprint |

## Residual (declarado, não mascarado)

- **Unit scope de fornecedores não existe na plataforma** — condição pré-existente idêntica a todas as rotas supplier atuais. Se o Core criar atribuição fornecedor↔unidade, reviews devem revalidar esse escopo antes de exibir/decidir.
- Reviews são **individuais por ator** (fail-closed). Visibilidade compartilhada/equipe requer contrato de escopo futuro (PR #106 B-09, pendente PO).

**Verdict: GATE-A = `PASS_WITH_RESIDUAL`** — modelo de escopo implementável e comprovável para revisões ator-scoped; dimensão de unidade é ausência documentada da plataforma, não invenção.
