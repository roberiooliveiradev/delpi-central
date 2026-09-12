# 03 — Modelo de Capabilities

## 1. Conceito

Uma **Capability** representa algo que a plataforma consegue fazer em nome do usuário ou para auxiliá-lo. É a unidade semântica usada pelo Copilot para descobrir possibilidades, planejar tarefas e executar ações.

Capability não é sinônimo de endpoint. Um endpoint pode sustentar uma capability de negócio; uma capability de navegação pode não ter endpoint algum.

## 2. Categorias

### `business.read`

Consulta dados corporativos sem alteração de estado.

Exemplos:

- consultar estoque;
- consultar pedidos;
- consultar fornecedor;
- consultar indicador;
- consultar solicitação.

### `business.write`

Cria ou altera estado de negócio.

Exemplos:

- criar solicitação;
- atualizar cadastro;
- registrar comentário;
- alterar responsável.

### `business.destructive`

Ação com maior impacto ou irreversibilidade.

Exemplos:

- cancelar;
- excluir;
- rejeitar definitivamente;
- encerrar processo.

### `platform.navigation`

Ações de navegação da plataforma.

Exemplos:

- abrir app;
- abrir rota;
- abrir entidade;
- voltar;
- abrir área administrativa autorizada.

### `platform.view`

Ações de experiência visual.

Exemplos:

- mudar aba;
- aplicar filtro local;
- mudar período visual;
- selecionar modo tabela/gráfico;
- destacar entidade.

### `knowledge`

Recuperação de conhecimento autorizado.

Exemplos:

- pesquisar procedimento;
- localizar norma;
- responder com base em documentos;
- recuperar contexto histórico.

### `analysis`

Combina e interpreta evidências já obtidas.

Exemplos:

- comparar períodos;
- calcular variação;
- encontrar anomalias;
- cruzar múltiplas fontes;
- resumir causas.

### `artifact`

Produz saída reutilizável.

Exemplos:

- relatório;
- e-mail;
- resumo executivo;
- apresentação;
- documento.

### `workflow`

Orquestra várias capabilities em um objetivo de negócio.

## 3. Contrato conceitual

Exemplo de capability materializada:

```json
{
  "capabilityId": "purchase-request.create",
  "name": "Criar solicitação de compra",
  "description": "Cria uma solicitação de compra para o usuário autorizado.",
  "category": "business.write",
  "source": "openapi",
  "actionId": "api-delpi:createPurchaseRequest",
  "inputSchema": {},
  "outputSchema": {},
  "permissions": ["purchase-requests.create"],
  "sensitivity": "write",
  "requiresConfirmation": true,
  "parallelSafe": false,
  "idempotency": "supported",
  "tags": ["compras", "solicitação"]
}
```

Exemplo de capability de plataforma:

```json
{
  "capabilityId": "portal.open-app",
  "name": "Abrir aplicativo",
  "category": "platform.navigation",
  "source": "portal",
  "inputSchema": {
    "appId": "string"
  },
  "sensitivity": "read",
  "requiresConfirmation": false,
  "parallelSafe": true
}
```

## 4. Capability Catalog

O catálogo lógico agrega capabilities de várias fontes:

```text
OpenAPI Action Catalog
        +
Portal Capability Catalog
        +
Knowledge Tools
        +
Internal Platform Tools
        +
Artifact/Analysis Capabilities
        ↓
Authorized Capability View
```

A visão entregue ao planner deve ser filtrada por usuário, agente, contexto e policy.

## 5. Descoberta

```text
user goal
→ authorized capability pool
→ lexical/vector/schema retrieval
→ top-K candidates
→ structured planner
```

O planner nunca pode inventar capabilityId fora dos candidates autorizados.

## 6. Semântica mínima recomendada

Cada capability deve possuir, quando aplicável:

- `capabilityId` estável;
- nome e descrição;
- categoria;
- fonte;
- input/output schema;
- required permissions;
- sensitivity;
- confirmation policy;
- read/write semantics;
- parallel safety;
- idempotency;
- tags/semantic descriptions;
- availability status;
- app/entity associations;
- observability metadata.

## 7. Derivação, não duplicação

Para Business Actions, dados técnicos como method/path/parameters/schema devem vir de OpenAPI/Action Catalog. Não duplicar isso em JSON manual do Copilot.

Para Platform Actions, apps e rotas devem ser derivados dos contratos do Core/Portal, não mantidos em lista hardcoded no chat.

## 8. Capabilities compostas

Uma workflow capability pode declarar intenção de alto nível sem congelar uma sequência rígida de endpoints.

Exemplo:

```text
investigate_delivery_delay
```

pode sugerir goals como estoque, carteira, produção e compras, mas a seleção concreta deve ocorrer pelo catálogo autorizado atual.

## 9. Estado e disponibilidade

Uma capability pode estar:

```text
AVAILABLE
UNAVAILABLE_PROVIDER
UNAUTHORIZED
REQUIRES_CONTEXT
REQUIRES_CONFIRMATION
DEGRADED
```

O usuário deve receber explicação clara quando o Copilot não puder executar algo.

## 10. Anti-padrões

Não criar:

- capability por path hardcoded;
- capabilityId derivado de texto instável do endpoint;
- catálogo duplicado de operationIds;
- capability que concede acesso por si só;
- `isAdmin=true` como substituto genérico de permission policy;
- action de escrita classificada como read apenas para simplificar planner.
