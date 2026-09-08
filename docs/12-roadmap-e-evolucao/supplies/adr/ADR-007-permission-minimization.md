# ADR-007 — Minimização do catálogo de permissões

| Campo | Valor |
|-------|-------|
| Status | Aceito (PO, 2026-09-08) |
| Contexto | Portal Suprimentos precisa de RBAC seguro sem explosão de permission codes |
| Relacionados | [PERFIS-E-PERMISSOES.md](../PERFIS-E-PERMISSOES.md), [ADR-006](./ADR-006-unit-permissions.md), [MANIFEST-DRAFT.md](../MANIFEST-DRAFT.md) |

---

## Contexto

Granularidade máxima não equivale a segurança máxima. Modelar cada verbo CRUD como uma permission (`view`, `create`, `edit`, `complete`, `cancel`) aumenta o catálogo, o custo de administração e o risco de papéis incoerentes sem necessariamente criar uma fronteira real de segurança.

O Portal Suprimentos já possui um segundo eixo ortogonal para unidade TOTVS e possui regras de ownership/escopo de recurso. Essas dimensões devem ser usadas antes de criar novos codes.

## Decisão

Permission representa **capacidade material de negócio, segurança ou governança**, não botão, endpoint ou verbo HTTP.

Modelo canônico:

```text
capability
  AND unit scope quando houver dado TOTVS
  AND resource scope / ownership
  AND business rule
  → ação autorizada
```

O catálogo novo deve ser o **menor conjunto suficiente** para preservar segurança, segregação de função e auditabilidade.

### Permission separada só é justificada quando houver pelo menos uma diferença material

- público autorizado diferente;
- risco significativamente maior;
- administração/configuração global;
- aprovação/rejeição ou outra segregação de função;
- acesso transversal de escopo;
- exposição/exportação sensível;
- operação em massa;
- impacto financeiro/material;
- necessidade real de delegação independente.

A existência de `GET`, `POST`, `PATCH` ou `DELETE` distintos **não** justifica sozinha permission separada.

## Aplicação no Portal Suprimentos

Catálogo alvo mínimo:

| Permission | Papel |
|------------|-------|
| `supplies.portal.access` | Entrar no Portal, usar Home, Ajuda, busca e preferências próprias |
| `supplies.purchase-requests.access` | Jornada de Solicitações de Compras, preservando escopo CC fail-closed |
| `supplies.operations.access` | Jornada operacional do comprador: pedidos, entregas, fornecedores, produtos e estoques relacionados |
| `supplies.analytics.access` | Overview, KPIs e análises gerenciais |
| `supplies.administration.manage` | Administração, mappings, scopes e settings homologados |
| `supplies.purchase-requests.view-all` | Exceção de escopo: bypass de centro de custo dentro das unidades autorizadas |
| `supplies.purchase-requests.export` | Mantida separada enquanto houver necessidade de controlar e auditar saída de dados em massa |
| `supplies.unit.filial-{TOTVS}` | Eixo B de unidade; não é capability funcional |

`supplies.approvals.manage` só poderá nascer se a futura jornada de alçadas realmente executar aprovação/rejeição. Consultar informação de alçada, por si só, não cria essa permission.

### Tasks / follow-ups

Não criar `tasks.view`, `tasks.create`, `tasks.complete` etc. na P0.

- listar tarefas próprias: `supplies.portal.access`;
- criar/editar/concluir follow-up: exige `supplies.portal.access` + acesso ao recurso referenciado + unidade autorizada + ownership/regra de equipe;
- operação sobre recurso que o usuário não pode acessar continua negada mesmo que a task seja dele.

Se no futuro houver usuário que possa consultar tasks sem operá-las, ou operar tasks de terceiros/equipe, reavaliar com evidência.

### Notas de fornecedor

Não criar `suppliers.notes.write` na P0 por padrão. A nota interna faz parte da jornada operacional do fornecedor e exige:

```text
supplies.operations.access
AND unidade autorizada
AND fornecedor dentro do escopo
```

A separação entre consultar fornecedor e escrever nota só será criada se E1/homologação provar públicos ou riscos distintos.

### Settings

Administração tem risco materialmente diferente. Por isso `supplies.administration.manage` permanece separada.

## Matriz obrigatória para qualquer permission nova

| Capability candidata | Operações | Mesmo público? | Mesmo risco? | Ownership resolve? | Unit scope resolve? | Permission nova? | Justificativa |
|---|---|---:|---:|---:|---:|---:|---|

Se a resposta indicar que capability existente + scope + ownership preserva a segurança, **não criar** novo code.

## O que é proibido

- espelhar CRUD no catálogo de permissions;
- criar permission porque nasceu um botão, modal, rota ou método HTTP;
- criar `{feature}.{action}.filial-*` para resolver unidade;
- usar minimização para eliminar segregação de função comprovadamente necessária;
- usar frontend ou ownership sem validação backend como substituto de RBAC.

## Consequências

- papéis mais simples e previsíveis;
- menor risco de combinações impossíveis de manter;
- unidade continua independente pelo ADR-006;
- segurança fina fica em capability + unidade + ownership + regra de negócio;
- permissions adicionais exigem justificativa explícita e rastreável.
