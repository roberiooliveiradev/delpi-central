# SUPPLIES-ENRICHMENT-01 — P0.1 code inventory (HEAD)
 
> **Estado: PARTIAL / EVIDENCE-DRIVEN; não implementação.** Inspeção de arquivos reais na branch default do GitHub em 2026-10-21, HEAD observado no início: `ddc6dccaf9454d9f138985a943d8e2b9afc07e34`. Não foi possível obter `git status` local, executar testes ou inspeção recursiva integral do monorepo via conector; esses passos permanecem `TO_INVENTORY`, não `PASS`. Branch de docs PR #106, sem alteração de código.

## 1. Evidência direta do HEAD — arquivos abertos

| Path | Fato comprovado |
|---|---|
| `supplies-api/app/composition/root_composer.py` | Registra `suppliers_bp` no Flask; há outros blueprints de home, inventory, pedidos, compras, analytics, usuários |
| `supplies-api/app/interfaces/http/routes/suppliers_routes.py` | Implementa GET list/detail, catalogs, CEP, operation; POST e PUT encaminhados à api-delpi via S2S |
| `supplies-api/app/application/services/suppliers_dto.py` | Allowlist, projeção LGPD de CPF, normalização do ID e sanitização POST/PUT |
| `supplies-api/app/application/security/supplies_permissions.py` | Capabilities `supplies.access` e `supplies.manage`; `can_use_operations` exige `supplies.access` |
| `supplies-api/app/interfaces/http/auth_middleware.py` | Bearer/JWT Keycloak e `AuthorizationService.resolve_effective_user` via Core |
| `supplies-api/app/interfaces/http/auth_decorators.py` | Decorators `require_policy`, `require_unit`, `require_units`; uso real no enrichment ainda precisa ser desenhado |
| `supplies-api/app/application/services/authorization_service.py` | Busca usuário Core `/me`; permission efetiva e lista fixa `OPERATIONAL_UNITS` 01/02 para filtro (necessária validação contra resource scope de fornecedor) |
| `supplies-api/app/infrastructure/gateways/delpi_s2s_gateway.py` | Token client credentials individual, S2S fail-closed, propagação Bearer de usuário, sem fallback a shared token |
| `supplies-api/app/infrastructure/gateways/delpi_api_gateway.py` | HTTP GET/POST/PUT, timeout, request-id e single attempt de escrita; nenhum retry cego |
| `supplies-api/app/infrastructure/config/settings.py` | S2S configurável, PostgreSQL plugins DB, `RUN_MIGRATIONS_ON_STARTUP`; não contém configuração específica CNPJ provider |
| `supplies-api/tests/test_suppliers_routes.py` | Testes de rotas supplier, 401/403, CPF mascarado/CNPJ exibido, gateway upstream e cenários via mocks; suíte não executada aqui |
| `api-delpi/docs/integrations/supplier-write-provenance-contract.md` | Contrato implementado v1 de provenance e modo por campo, com `GOVERNMENT_API`/third-party/suggestion bloqueados até evidência verificável |

## 2. Rotas supplier efetivamente presentes

| Método | Path Flask | Operação | Owner downstream |
|---|---|---|---|
| GET | `/suppliers` | lista paginada por query/state/blocked/page/page_size/sort | `/supplies/suppliers` na api-delpi |
| GET | `/suppliers/catalogs/<catalog>` | allowlist de 8 catálogos TOTVS | `/supplies/supplier-catalogs/{kind}` |
| GET | `/suppliers/postal-codes/<postal_code>` | proxy lookup CEP com source/IBGE | `/addresses/postal-codes/{postal_code}` |
| GET | `/suppliers/<code>/<store>` | ficha de fornecedor | `/integrations/protheus/suppliers/{supplier_id}` |
| GET | `/suppliers/operations/<operation_id>` | status, ACK vs persistência | `/integrations/operations/{id}` |
| POST | `/suppliers` | create supplier gated | `POST /integrations/protheus/suppliers` |
| PUT | `/suppliers/<code>/<store>` | edição allowlisted gated | `PUT /integrations/protheus/suppliers/{supplier_id}` |

**Não há endpoints de enrichment/reviews declarados no `suppliers_routes.py` inspecionado**; não é prova absoluta de inexistência em módulos não inspecionados. O `root_composer.py` registra `suppliers_bp`, não um blueprint separado de enrichment. Para contract freeze, executar residual search no HEAD.

## 3. Drift real identificado — POST/PUT e escrita com proveniência

- A `api-delpi` atual aceita `change_context` como objeto irmão de `fornecedor`, mas **BFF POST/PUT transmite somente `{"fornecedor": fornecedor}`**. Logo alterações pelo Portal ainda são classificadas como `UNKNOWN_LEGACY`, mesmo quando entrada é manual.
- `sanitize_post_body` retém apenas campos conhecidos, `sanitize_put_body` rejeita campos proibidos e desconhecidos, mas não manipula contexto de proveniência. O envio deve derivar origem do fluxo confiável (formulário/review), não permitir claims arbitrários do navegador.
- `PUT_SUPPLIER_FIELDS` do BFF inclui campos cadastrais além de nomes, excluindo tax_id e store; isso **não prova** que MATA020 homologa PUT de todos esses campos; aplicar gates upstream separados.
- `mask_tax_id` mascara CPF (11), exibe CNPJ (14). A consulta externa deve bloquear CPF e conferir pessoa jurídica/estabelecimento.
- `project_detail` retorna seções identificação/endereço/contato/fiscal/compras; o enrichment deve usar a projeção existente, sem reconsultar SA2 por SQL.
- O GET de proveniência `api-delpi` não está exposto como proxy de leitura em `suppliers_routes.py` hoje; necessário se a UI mostrar origem persistida pós-write.

## 4. AuthZ / resource scope gap

Rota supplier utiliza `@require_policy(can_use_operations)` e permission efetiva `supplies.access`. Isso **comprova capability**, mas a rota não declara `@require_unit` nem verificação explícita de `supplier resource scope`. `supplier code/store` por si só não é unidade. Enrichment precisa garantir `capability AND unit_scope AND resource_scope/ownership AND business_rule`, server-side, fail-closed, sem criar permission por campo/botão/CRUD. Verificar eventual enforcement no downstream `api-delpi`; **não assumir que a capability resolve sozinha o escopo**.

O `AuthorizationService.allowed_units` retorna lista fixa 01/02 para usuários `supplies.access`; a validade dessa regra para o recurso de fornecedor, inclusive filial/empresa, permanece `TO_INVENTORY`.

## 5. Persistência e migration

`Settings` expõe PostgreSQL plugins DB e startup migrations, então a infraestrutura geral existe. **Não foi comprovado neste inventário o repositório/tabela/migration específica para reviews e decisões.** Code tree e migrações precisam ser inventariadas pelo Cursor no worktree com status limpo, sem criar tabela até gate ROPA/retention. Não espelhar SA2 nem salvar response bruta do provider por padrão.

## 6. P0.1 follow-up necessário

1. `git rev-parse HEAD`, `git status --short`, `origin/main`, branch PR #106, authorities e regras `.cursor` do escopo.
2. `find supplies-api -type f` dirigido a routes/composition/application/domain/infrastructure/migrations/tests; grep por `enrichment|supplier|provenance|migration|unit_scope|resource_scope`.
3. Verificar migrações reais e onde adicionar tabelas `reviews/proposals/decisions/events`, transaction boundaries, idempotency/revision, TTL e cleanup.
4. Confirmar Core API effective permission, relação fornecedor/filial/unidade e RBAC; testes positive/sibling/negative.
5. Inspecionar testes existentes e executar comandos atuais; observar falhas pré-existentes vs regressões.
6. Contrato de provider comercial Serpro autorizado, manual/Payload real, legal terms e quota; nenhuma consulta externa antes disso.
7. Definir contrato de evidence v2 entre BFF e api-delpi antes de liberar GOVERNMENT_API e sugestões por PUT.
8. Inventariar MFE existing Supplier 360, Help e kit antes de construir páginas.
9. Validar ROPA/retention para reviews/decisions especificamente (política LGPD institucional já PROVEN).
10. Checar Core/manifest e deploy gates atuais antes de novo código/runtime.

## 7. Recomendações e gates

- **GO possível apenas para design de domain/read-only comparison com fixtures**, após inventário completo e autoridade; **NO GO** para provider externo real, migration pessoal sem retenção, provenance gov write ou PUT Protheus.
- Acrescentar `source_id`, `source_retrieved_at`, `evidence_id` e `change_mode` por campo somente depois de fonte autorizada e contrato cross-consumer de verificação.
- Falha ou ausência de acesso comercial não deve ser contornada por scraping REDESIM.
- Mantenha `supplies-api` como dono da revisão/decisão; `api-delpi` dono da escrita/confirmed provenance.
- Nenhum teste foi rodado e nenhum smoke autenticado foi realizado durante este inventário. `TESTS = TEST_NOT_RUN`, `RUNTIME = INCONCLUSIVE`.

**Classificação final:** `P0.1 = PARTIAL / CODE INSPECTED`; `NEW_ENRICHMENT_ROUTES = NOT PROVEN`; `COMPLETE_REPO_TREE = TO_INVENTORY`; `EVIDENCE_V2 = PENDING`; `PROVIDER = PENDING`; `IMPLEMENTATION = NOT_AUTHORIZED`.
