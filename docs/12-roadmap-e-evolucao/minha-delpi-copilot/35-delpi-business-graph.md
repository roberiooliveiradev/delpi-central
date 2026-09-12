# Minha DELPI Copilot — DELPI Business Graph

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Contracts:** `EntityRef` e `RelationshipRef` vêm da foundation C0.

## 1. Objetivo

Fornecer contexto semântico transversal entre entidades/sistemas/processos sem duplicar bancos operacionais.

```text
Reclamação
→ Produto
→ Revisão/Desenho
→ Lote/OP
→ Matéria-prima
→ Fornecedor
→ Inspeção
→ Não Conformidade
→ Plano de Ação
```

## 2. Princípio

O Graph é **grafo de referências/relacionamentos**.

```text
Graph
→ identifica EntityRefs e RelationshipRefs
→ preserva source/provenance
→ aplica permission-aware traversal
→ source API fornece dado atual
```

Não é data warehouse nem system of record das entidades.

## 3. EntityRef

Usar o primitive compartilhado C0. Exemplo conceitual:

```json
{
  "entityType":"product",
  "entityId":"90264238",
  "sourceSystem":"api-delpi",
  "label":"Produto 90264238"
}
```

Não adicionar `attributes` arbitrários ao EntityRef para transformar ref em snapshot de negócio. Dados adicionais vêm da source API ou refs/evidence adequados.

## 4. RelationshipRef

Usar o primitive compartilhado:

```json
{
  "from":{"entityType":"complaint","entityId":"RNC-123","sourceSystem":"customer-experience"},
  "relationshipType":"affects_product",
  "to":{"entityType":"product","entityId":"90264238","sourceSystem":"api-delpi"},
  "authority":"domain",
  "sourceRef":"...",
  "confidence":1.0
}
```

Relações inferidas precisam ser explicitamente marcadas como `inferred`/não-authoritative conforme contract final.

## 5. Relações candidatas

- cliente → pedidos/reclamações;
- pedido → itens/produto;
- produto → desenho/revisão;
- produto → roteiro/processo;
- produto → materiais/fornecedores;
- produto → inspeções/NCs;
- OP → produto/lote/operações;
- compra → fornecedor/material;
- reclamação → produto/lote/cliente;
- NC → produto/processo/causa/plano;
- plano → responsáveis/prazos/evidências;
- documento → entidade relacionada.

C0.S0 comprova IDs/owners antes de registrar relação.

## 6. Fontes de relações

Ordem de confiança:

1. relação explicitada por domain API/contract;
2. domain event;
3. materialização/view governada;
4. metadata declarativa governada;
5. inferred relationship, sempre rotulada e nunca promovida silenciosamente a fato.

## 7. Traversal

```text
start EntityRef
→ lookup authorized relationships
→ apply depth/cycle/budget
→ filter by permission/policy
→ return related EntityRefs/SourceRefs
→ fetch current facts from source APIs
→ normalize Evidence/Outcome
```

Planner não precisa conhecer tables/endpoints do Graph.

## 8. Security

```text
relation exists ≠ user may read target
```

Obrigatório:

- permission-aware traversal;
- source permission revalidation;
- graph cache não vira bypass;
- hidden node não vaza por label/count indevido;
- inferred relation não é FACT.

## 9. Provenance

Cada relação material precisa, quando aplicável:

```text
relationshipType
authority/inference status
sourceRef
observedAt/version
confidence quando metodologicamente válida
```

## 10. Performance

Começar com query/adapters simples. Criar index/materialization somente quando métricas provarem necessidade.

Caching precisa invalidation/freshness semantics.

## 11. Implementation mapping

Não executar fases `BG*` independentes.

```text
C0 → inventory + Entity/Relationship contracts + ports
C3 → relationship registry/query runtime + permission traversal + pilot
C6/C7 → coverage/performance/governance refinements se necessários
```

## 12. Piloto recomendado

```text
complaint
→ product
→ lot/production order
→ material
→ supplier
→ inspection/quality history
```

O piloto deve demonstrar source fetch real e evidence, não dados copiados para o Graph.

## 13. Anti-patterns

- copiar datasets completos;
- inventar IDs paralelos;
- usar path/endpoint como domain semantics;
- inferred relation como authoritative;
- graph repository com business rules;
- Graph-specific EntityRef/Evidence contract;
- planner branch por relationship type.

## 14. Gate

C3 Graph só passa com:

- authorized traversal;
- sibling/unknown relation onboarding sem planner patch;
- source fetch real;
- provenance;
- depth/cycle budget;
- no RBAC leakage;
- no duplicate domain data authority.