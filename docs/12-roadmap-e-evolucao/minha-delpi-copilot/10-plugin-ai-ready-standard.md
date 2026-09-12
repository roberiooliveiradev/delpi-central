# 10 — Padrão AI-ready para apps e plugins

## 1. Objetivo

Todo novo app da Minha DELPI deve nascer preparado para ser utilizado tanto pela UI quanto pelo Copilot, sem exigir hardcodes no motor central de IA.

## 2. Princípio

```text
Novo app
├─ manifesto
├─ routes
├─ permissions
├─ APIs/use cases
├─ OpenAPI
├─ semantic metadata
├─ Workspace Context adapter
└─ UI capabilities opcionais
        ↓
Minha DELPI Copilot
```

## 3. Requisitos mínimos

### 3.1 Manifesto e rotas

O app deve possuir:

- `appId` estável;
- `basePath`;
- rotas identificáveis;
- labels amigáveis;
- permission por rota quando aplicável;
- metadata suficiente para Portal e Copilot descreverem a função da rota.

### 3.2 Permissões

Toda função protegida deve possuir permission clara.

Não usar apenas visibilidade de botão como autorização.

### 3.3 Business use cases

Operações de negócio devem viver em use cases/API, não dentro de componentes React.

### 3.4 OpenAPI

APIs consumíveis pelo Copilot devem expor OpenAPI de qualidade com:

- `summary` útil;
- `description` semântica;
- operationId estável;
- parâmetros descritos;
- required/type/enum/format corretos;
- request body schema;
- response schemas;
- exemplos quando agregarem valor;
- erros documentados;
- security schemes.

### 3.5 Sensitivity/policy

Actions de escrita precisam de metadata/policy que permita derivar:

```text
readWrite
risk
requiresConfirmation
parallelSafe
```

Sem classificar manualmente tudo como read/low.

## 4. Workspace Context Adapter

O MFE deve implementar um adapter pequeno quando possuir contexto útil.

Exemplos:

- cliente aberto;
- produto selecionado;
- solicitação atual;
- período;
- filial;
- aba;
- dataset visível.

Não publicar estado interno irrelevante.

## 5. UI Capabilities

Registrar somente capacidades visuais que não duplicam business actions.

Permitido:

```text
open entity
select tab
change local view
focus section
apply local view filter
```

Evitar:

```text
createOrder via UI capability
updateCustomer via UI capability
approveRequest via UI capability
```

Essas devem ser Business Actions.

## 6. Entity Deep Links

Apps com entidades relevantes devem declarar como abrir uma entidade sem ensinar URLs ao LLM.

Exemplo conceitual:

```json
{
  "entityType": "customer",
  "routeId": "customer-detail",
  "routeParams": ["customerId"]
}
```

O Shell resolve e valida a navegação.

## 7. Apresentação

A API deve devolver schema/payload suficientemente descritivos para apresentação genérica útil.

Presenter dedicado é melhoria opcional, não requisito para a capability existir.

## 8. Help e descrição

O app deve fornecer linguagem de negócio suficiente para o Copilot explicar:

- o que o app faz;
- principais entidades;
- principais operações;
- significado de campos/indicadores quando não óbvio.

Essa documentação pode alimentar knowledge/RAG e help contextual.

## 9. Matriz de readiness

Cada app deve manter:

| Item | Status |
|---|---|
| Rotas autorizadas deriváveis | |
| Business APIs disponíveis | |
| OpenAPI completo | |
| Permissions alinhadas | |
| Sensitivity correta | |
| Workspace Context | |
| Entity deep links | |
| UI capabilities necessárias | |
| Help/RAG | |
| Evals básicos | |

## 10. Testes mínimos

- app/route visibility por RBAC;
- capability discovery para usuário autorizado;
- ausência para usuário não autorizado;
- read action via Copilot;
- write action com confirmação quando aplicável;
- entity deep link;
- Workspace Context update;
- negative: app novo não exige alteração no core do Copilot.

## 11. Definition of Ready para novo app

Um app é AI-ready quando:

```text
[ ] UI e Copilot usam os mesmos contratos de negócio
[ ] OpenAPI é suficiente para discovery/binding genérico
[ ] nenhuma regra de endpoint foi adicionada ao core da IA
[ ] permissões são reutilizadas pelo Copilot
[ ] contexto visual útil possui adapter
[ ] navegação usa metadata tipada, não URL inventada
[ ] writes possuem sensitivity/confirmation
[ ] smoke de capability passa
```

## 12. Governança

O checklist de criação de novo plugin/MFE deve incorporar este padrão progressivamente. O objetivo é que AI-readiness seja uma propriedade do ecossistema, não um projeto posterior de integração por app.
