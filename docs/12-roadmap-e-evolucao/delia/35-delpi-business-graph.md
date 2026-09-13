# Minha DELPI Copilot — DELPI Business Graph

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Contracts:** `EntityRef` e `RelationshipRef` vêm da foundation C0; runtime do Graph entra em C4.

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

O Graph é projeção da **Copilot API** sobre referências/relacionamentos dos domain owners:

```text
Graph
→ EntityRefs/RelationshipRefs
→ source/provenance
→ permission-aware traversal
→ Domain API fornece dado atual
```

Não é data warehouse nem system of record.

## 3. EntityRef / RelationshipRef

Usar primitives C0. Não adicionar snapshots arbitrários ao `EntityRef` nem criar IDs paralelos.

Relações carregam from/to refs, relationshipType, authority/sourceRef, provenance e confidence quando metodologicamente válida. Relação inferida permanece explicitamente `inferred`/não-authoritative.

## 4. Relações candidatas

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

## 5. Fontes

Ordem de confiança:

1. Domain API/contract explícito;
2. domain/integration event;
3. materialização/view governada;
4. metadata declarativa;
5. inferred relationship rotulada.

## 6. Traversal

```text
start EntityRef
→ lookup authorized relationships
→ depth/cycle/budget
→ permission/policy filter
→ related EntityRefs/SourceRefs
→ fetch current facts from Domain APIs
→ Outcome/Evidence
```

Planner não conhece tables/endpoints do Graph.

## 7. Security

```text
relation exists ≠ user may read target
```

- permission-aware traversal;
- source permission revalidation;
- cache não vira bypass;
- hidden node não vaza por label/count;
- inferred relation não é FACT.

## 8. Provenance/performance

Toda relação material deve carregar relationshipType, authority/inference status, sourceRef e version/observedAt quando aplicável.

Começar com adapters/query simples. Materialization/index só com necessidade comprovada; cache precisa freshness/invalidation.

## 9. Phase mapping

```text
C0 → inventory + Entity/Relationship contracts + ports
C3 → Intelligence Core understands entity/capability semantics
C4 → relationship registry/query runtime + permission traversal + pilot
C6/C7 → coverage/performance/governance refinements when justified
```

## 10. Piloto recomendado

```text
complaint
→ product
→ lot/production order
→ material
→ supplier
→ inspection/quality history
```

O piloto prova source fetch real + Evidence, não dados copiados para o Graph.

## 11. Independence

Graph pertence à Copilot API e consulta Domain APIs diretamente. Não usa Chat graph/session/tool runtime.

## 12. Anti-patterns

- copiar datasets completos;
- inventar IDs paralelos;
- path/endpoint como domain semantics;
- inferred relation como authoritative;
- graph repository com business rules;
- Graph-specific EntityRef/Evidence;
- planner branch por relationship type;
- Chat API como proxy de relações/dados.

## 13. Gate C4

- authorized traversal;
- sibling/unknown relation onboarding sem planner patch;
- source fetch real;
- provenance;
- depth/cycle budget;
- no RBAC leakage;
- no duplicate domain data authority.