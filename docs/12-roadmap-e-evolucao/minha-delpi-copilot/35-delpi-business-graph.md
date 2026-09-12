# Minha DELPI Copilot — DELPI Business Graph

**Status:** arquitetura proposta  
**Objetivo:** fornecer contexto semântico transversal entre entidades, sistemas e processos sem duplicar bancos operacionais.

## 1. Problema

APIs isoladas permitem consultar dados, mas não representam explicitamente como as entidades da empresa se relacionam.

Exemplo:

```text
Reclamação
→ Produto
→ Lote
→ Ordem de Produção
→ Matéria-prima
→ Fornecedor
→ Inspeção
→ Não Conformidade
→ Plano de Ação
```

Para investigações empresariais, o Copilot precisa navegar por relações, não apenas fazer buscas independentes.

## 2. Princípio

O Business Graph é **grafo de referências e semântica**, não um data warehouse que duplica todos os dados.

Os dados de negócio continuam nas APIs e bancos owners.

```text
Business Graph
→ identifica entidades e relações
→ aponta source system / sourceRef
→ orienta retrieval/planning
→ API owner fornece o dado atual
```

## 3. Modelo mínimo

### EntityRef

```json
{
  "entityType": "product",
  "entityId": "90264238",
  "sourceSystem": "api-delpi",
  "label": "Produto 90264238",
  "attributes": {},
  "provenance": {}
}
```

### RelationshipRef

```json
{
  "from": {"type": "complaint", "id": "RNC-123"},
  "relation": "affects_product",
  "to": {"type": "product", "id": "90264238"},
  "source": "customer-experience",
  "confidence": "authoritative"
}
```

## 4. Relações iniciais candidatas

- cliente → pedidos;
- cliente → reclamações;
- pedido → itens;
- item → produto;
- produto → desenhos/revisões;
- produto → roteiro/processo;
- produto → materiais;
- produto → fornecedores;
- produto → inspeções;
- produto → não conformidades;
- OP → produto/lote/operações;
- compra → fornecedor/material;
- reclamação → produto/lote/cliente;
- NC → produto/processo/causa/plano;
- plano de ação → responsáveis/prazos/evidências;
- documento → entidade relacionada.

C0 deve provar entidades/IDs owners antes de materializar relações.

## 5. Fontes do grafo

Preferência:

1. relacionamentos expostos por APIs/contratos canônicos;
2. eventos de domínio;
3. views/materializações controladas;
4. metadata declarativa governada;
5. inferência apenas como hipótese, nunca como relação authoritative sem confirmação.

## 6. Segurança

O Graph não pode virar canal de bypass.

```text
existência da relação ≠ permissão para ler o nó
```

Toda expansão do grafo deve ser filtrada por capabilities/permissões efetivas e políticas das fontes.

## 7. Uso pelo Copilot

Exemplo:

> “Essa reclamação pode estar relacionada ao fornecedor?”

```text
complaint
→ product
→ lot/production order
→ material
→ supplier
→ receiving inspection
→ quality history
→ grounded comparison
```

O planner usa o grafo para propor a trajetória; as APIs autorizadas fornecem fatos atuais.

## 8. Provenance

Toda relação deve carregar, quando aplicável:

```text
sourceSystem
sourceRef
observedAt
relationshipType
authority/confidence
```

Relação inferida deve ser marcada explicitamente como `inferred`.

## 9. Implementação incremental

### BG0
- inventário de entity types/IDs/deep links;
- canonical `EntityRef`.

### BG1
- mapa de relações prioritárias de Comercial, Suprimentos, Produção, Qualidade e Engenharia.

### BG2
- repository/query port de graph traversal;
- permission filtering.

### BG3
- index/materialization quando necessária para performance.

### BG4
- relationship discovery assistido + governança.

## 10. Não fazer

- duplicar datasets completos;
- criar IDs paralelos quando source owner já possui ID estável;
- usar relação inferida como fato;
- usar graph traversal para ignorar RBAC;
- embutir regras de negócio no graph repository;
- transformar path/endpoint em semântica de domínio.

## 11. Gate

O primeiro release só precisa provar que o Copilot consegue atravessar uma cadeia multi-domínio usando `EntityRef`/relações canônicas e buscar os fatos atuais nos owners corretos.