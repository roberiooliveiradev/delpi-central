# DÉLIA — DELPI Business Graph

**Status:** `TARGET` — thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Evidence rule:** `EntityRef`, `RelationshipRef`, graph store/index e runtime só são `PROVEN` quando C0/C4 evidence provar owner, contract e implementation.

## 1. Objetivo

Fornecer contexto relacional transversal entre entidades/sistemas/processos sem duplicar bancos operacionais.

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

O Graph é **target de projeção relacional da DÉLIA**, condicionado ao owner/contrato congelado em C0:

```text
source/domain relationships
→ normalized refs/provenance
→ permission-aware traversal
→ current facts fetched from authoritative owners
```

Graph não é data warehouse, Semantic Layer nem system of record.

## 3. EntityRef / RelationshipRef

Se C0 congelar primitives compartilhados, reutilizá-los. Não adicionar snapshots arbitrários nem criar IDs paralelos.

Relações materialmente usadas precisam source/provenance, authority/inference status, timestamps/version quando aplicável e confidence somente quando metodologicamente válida.

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

São candidates. C0/C4 deve provar IDs, owners, contracts e consumers antes de materializar qualquer registry/index.

## 5. Fontes

Preferência conceitual:

1. Domain API/contract explícito;
2. domain/integration event real;
3. materialização/view governada;
4. metadata declarativa;
5. inferred relationship rotulada.

## 6. Traversal

Target:

```text
start EntityRef
→ resolve authorized relationships
→ depth/cycle/budget
→ permission/policy filter
→ related refs
→ fetch current facts from authoritative source
→ Evidence/Outcome
```

Planner não conhece tables/endpoints internos do Graph.

## 7. Security

```text
relation exists != user may read target
```

- permission-aware traversal;
- source permission revalidation;
- cache/index não vira bypass;
- hidden node não vaza por label/count;
- inferred relation não é FACT;
- graph metadata não concede Core/domain/provider permission.

## 8. Provenance/performance

Começar pelo padrão mais simples que satisfaça consumers reais. Materialization/index/cache/graph database só com necessidade comprovada e Abstraction Gate aprovado.

## 9. Phase mapping

```text
C0 → inventory + owner/source/consumer/contracts
C3 → entity/capability semantics foundations when proven
C4 → relationship query/traversal pilot when unlocked
C6/C7 → coverage/performance/governance refinements only if justified
```

## 10. Piloto candidato

```text
complaint
→ product
→ lot/production order
→ material
→ supplier
→ inspection/quality history
```

Piloto só é válido com source fetch real + Evidence e sem copiar masters para o Graph.

## 11. Independence

Graph target pertence à DÉLIA apenas no escopo de projeção/inteligência que C0 atribuir a ela. Domain owners continuam authorities dos dados/regras. Não usar Chat graph/session/tool runtime.

## 12. Anti-patterns

- copiar datasets completos;
- inventar IDs paralelos;
- path/endpoint como domain semantics;
- inferred relation como authoritative;
- graph repository com business rules alheias;
- Graph-specific EntityRef/Evidence incompatível;
- planner branch por relationship type;
- Graph virar Semantic Layer;
- Chat API como proxy.

## 13. Gate C4

PASS só com runtime/evidence para o SHA/config avaliado, incluindo authorized traversal, source fetch real, provenance, depth/cycle budget, no RBAC leakage e no duplicate domain authority.
