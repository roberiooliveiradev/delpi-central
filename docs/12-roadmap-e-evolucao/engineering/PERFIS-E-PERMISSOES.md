# Portal de Engenharia — perfis e permissões

> **Status:** proposta de RBAC mínimo para planejamento.  
> **Regra:** códigos finais devem ser confrontados com o catálogo Core e ADRs vigentes antes do provisionamento.

## 1. Princípio

O Portal usa RBAC central da Minha DELPI. JWT autentica e identifica; permissions efetivas são resolvidas pelo Core e aplicadas no backend.

Não criar permission por tela, aba, botão ou verbo CRUD sem necessidade real de segregação de risco.

## 2. Capabilities alvo mínimas

Catálogo P0 proposto:

```text
engineering.access
engineering.analytics.access
engineering.lmps.access
engineering.products.access
engineering.documents.access
engineering.nonconformities.write
engineering.costs.view
engineering.administration.manage   # somente se/ quando existir superfície admin real
```

### O que NÃO precisa nascer como permission P0

Sala e Minhas tarefas podem usar `engineering.access` + resource/self scope enquanto não houver requisito de segregação adicional.

Não criar automaticamente:

```text
engineering.rooms.view
engineering.rooms.create
engineering.rooms.write
engineering.rooms.react
engineering.tasks.view
engineering.tasks.update
```

Se uma ação exigir segregação comprovada, documentar a ameaça/risco e evoluir o catálogo por ADR.

## 3. Permissions legadas relevantes

```text
dashboard-engineering.view
dashboard-lmps.view
dashboard-lmps.nc.write
```

Mapeamento conceitual para coexistência:

| Legado | Alvo provável | Observação |
|---|---|---|
| `dashboard-engineering.view` | `engineering.access` + `engineering.analytics.access` | confirmar personas antes do cutover |
| `dashboard-lmps.view` | `engineering.access` + `engineering.lmps.access` | preservar acesso equivalente |
| `dashboard-lmps.nc.write` | `engineering.nonconformities.write` | não ampliar leitura/escrita por acidente |

Não remover alias/permission legado até o `GATE-PARITY` e o plano de cutover autorizarem.

## 4. Perfis funcionais

Perfis são composições administrativas de capabilities, não condicionais hardcoded no código.

### Engenharia — Consulta

Pode abrir Portal, Sala, Minhas tarefas próprias e ferramentas gerais liberadas; acesso a LMP/Produtos/Documentos depende das capabilities correspondentes.

### Engenharia — Operacional

Exemplo de composição:

```text
engineering.access
engineering.lmps.access
engineering.products.access
engineering.documents.access
```

Escrita de NC só se atribuída separadamente.

### Engenharia — Gestor

Exemplo:

```text
engineering.access
engineering.analytics.access
engineering.lmps.access
engineering.products.access
engineering.documents.access
```

Visão de equipe ou administração só entra se existir contrato e permission específicos.

### Engenharia — Administrador

`engineering.administration.manage` apenas para funções reais de configuração do Portal. Não usar “admin” como bypass universal de resource scope sem trilha auditável.

## 5. Navegação por capability

TopBar base:

| Item | Regra |
|---|---|
| Início | `engineering.access` |
| Visão geral | `engineering.analytics.access` |
| Sala de interação | `engineering.access` + room resource scope |
| Minhas tarefas | `engineering.access` + self scope |
| LMPs | `engineering.lmps.access` |
| Ajuda | `engineering.access` |

A ordem relativa permanece a mesma quando um item condicional é omitido.

## 6. Ferramentas por capability

| Ferramenta | Regra alvo |
|---|---|
| Produtos | `engineering.products.access` |
| Biblioteca de desenhos | `engineering.products.access` ou `engineering.documents.access`, decisão a fechar conforme owner |
| Documentos técnicos | `engineering.documents.access` |
| Controle de MP | exige acesso Portal + acesso real no `my-requests`/owner |
| Não conformidades — leitura | `engineering.lmps.access` |
| Não conformidades — escrita | `engineering.nonconformities.write` |
| TRANSFORMA+ | acesso Portal + permissão real do Transformômetro quando drill externo exigir |
| Custos/preços de Produto | `engineering.costs.view` + demais scopes do recurso |

O Portal não concede acesso indireto a um sistema integrado. Um card/deep link só aparece/funciona quando a combinação de capabilities locais e do owner estiver resolvida com segurança.

## 7. Resource scopes

### Sala

Conhecer `room_id` não autoriza leitura. Backend valida:

```text
engineering.access
AND sala existe/ativa
AND membership/policy permite acesso
AND contexto vinculado continua autorizado, quando a policy exigir
```

### LMP

A permission de LMP autoriza a capacidade, mas o backend deve preservar qualquer regra de escopo já existente no owner da LMP.

### Produto

Preço/custo pode possuir escopo mais restrito que os demais metadados.

### Documento

```text
engineering.documents.access
AND library_id autorizada
AND document_id resolve dentro da raiz allowlisted
AND policy de download/preview
```

## 8. Escopo por unidade/filial

Não criar `engineering.unit.*` apenas por simetria com outros portais. Primeiro provar que o domínio Engenharia possui visibilidade segregada por filial e que os providers suportam essa semântica.

Além disso, indicadores estratégicos de Engenharia são atualmente consolidados; isso não impede filtros operacionais de LMP quando o owner os sustentar, mas proíbe inventar score estratégico por filial.

Se o E0 confirmar necessidade real, criar ADR específico para unit scope.

## 9. Core-first e fail-closed

Falha ao resolver autorização efetiva do Core:

- não assumir acesso pelo JWT;
- não usar permission cache sem política/freshness comprovada;
- responder erro apropriado/fail-closed;
- não degradar 403 para dado parcial.

## 10. Testes de autorização

Cada rota protegida deve incluir no mínimo:

- positive: capability + resource scope válidos;
- sibling: capability válida em recurso permitido diferente;
- negative: sem capability;
- negative: IDOR/recurso fora do escopo;
- Core indisponível quando resolução for necessária;
- permission sensível de custo/NC;
- usuário desativado/removido da sala quando aplicável.

## 11. Provisionamento e cutover

Antes de trocar menu/redirect do legado:

1. mapear usuários/grupos/roles com permissions legadas;
2. provisionar capabilities novas no Core;
3. comparar população autorizada;
4. testar persona comum, gestor e escrita de NC;
5. somente então promover o Portal como caminho principal.

Nunca usar a remoção do legado como mecanismo para “forçar” o RBAC novo sem migração comprovada.
