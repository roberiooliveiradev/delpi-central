# Minha DELPI — Clean Architecture

> **Arquivo:** `docs/01-arquitetura/clean-architecture.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** aplicação de Clean Architecture na Core API, API DELPI, Portal e plugins

---

## 1. Objetivo

Este documento descreve como a **Minha DELPI** aplica Clean Architecture.

A arquitetura busca separar regras de negócio de detalhes técnicos, garantindo que Flask, SQLAlchemy, Socket.IO, Keycloak, bancos, Gateway e bibliotecas frontend não sejam o centro da regra de negócio.

---

## 2. Princípio central

Regra fundamental:

```text
Dependências apontam para dentro.
```

Modelo conceitual:

```text
Interfaces / Infrastructure → Application → Domain
```

Isso significa:

- `domain` não conhece Flask;
- `domain` não conhece SQLAlchemy;
- `application` orquestra casos de uso;
- `interfaces` adapta HTTP/Socket para aplicação;
- `infrastructure` implementa banco, cache, socket e providers externos.

---

## 3. Camadas backend

### 3.1 Domain

Responsabilidade:

```text
Conter contratos, eventos e regras independentes de tecnologia.
```

Na Core API, inclui:

```text
app/domain/
  events/
  ports/
```

Deve conter:

- ports de repositories;
- ports de cache;
- ports de dispatcher;
- eventos de domínio/aplicação;
- entidades ou value objects quando existirem regras próprias.

Não deve conter:

- Flask;
- SQLAlchemy;
- `request`;
- `jsonify`;
- Socket.IO;
- código de banco;
- chamada HTTP externa concreta.

---

### 3.2 Application

Responsabilidade:

```text
Orquestrar casos de uso.
```

Na Core API, inclui:

```text
app/application/
  use_cases/
  event_handlers/
  event_bus.py
  unit_of_work.py
```

Deve conter:

- use cases;
- regra de aplicação;
- orquestração de repositories via Unit of Work;
- coleta de eventos;
- handlers de eventos;
- contratos transacionais.

Não deve conter:

- routes Flask;
- SQLAlchemy models diretamente;
- detalhes de Nginx/Gateway;
- renderização frontend.

---

### 3.3 Interfaces

Responsabilidade:

```text
Adaptar protocolos externos para use cases.
```

Na Core API, inclui:

```text
app/interfaces/
  http/
  socket/
```

Contém:

- controllers;
- blueprints;
- middleware;
- decorators/policies;
- socket handlers.

Controllers devem:

- validar entrada básica;
- extrair parâmetros;
- chamar use case;
- traduzir resultado para HTTP;
- traduzir exceções para erros padronizados.

Controllers não devem:

- conter regra extensa;
- acessar models diretamente;
- manipular múltiplos repositories;
- publicar Socket.IO diretamente.

---

### 3.4 Infrastructure

Responsabilidade:

```text
Implementar detalhes técnicos.
```

Na Core API, inclui:

```text
app/infrastructure/
  config/
  db/
  persistence/
  cache/
  socket/
  seeds/
```

Contém:

- models SQLAlchemy;
- repositories concretos;
- adapters de cache;
- dispatcher Socket.IO;
- configuração;
- seeds;
- integração com banco.

---

## 4. Fluxo ideal de uma rota

```text
HTTP Request
  ↓
Controller
  ↓
Use Case
  ↓
Port
  ↓
Repository concreto
  ↓
Banco / Provider externo
```

Exemplo com Unit of Work:

```text
Controller
  ↓
SqlAlchemyUnitOfWork
  ↓
UseCase.execute()
  ↓
uow.repositories
  ↓
uow.collect_event()
  ↓
commit
  ↓
EventBus
```

---

## 5. Exemplo aplicado: registrar plugin

```text
apps_controller.py
  ↓
RegisterPluginUseCase
  ↓
Manifest validator / regras de aplicação
  ↓
uow.plugins
uow.plugin_manifests
uow.plugin_versions
uow.plugin_permissions
uow.plugin_routes
  ↓
AdminChangedEvent(plugin_registered)
  ↓
commit
  ↓
EventBus
  ↓
Socket.IO
```

Pontos de separação:

- controller não sabe como persistir manifesto;
- use case não sabe detalhes HTTP;
- repositories não publicam eventos;
- dispatcher Socket.IO fica na infraestrutura.

---

## 6. Exemplo aplicado: `/me/apps`

```text
me_controller.py
  ↓
ListUserAppsUseCase
  ↓
uow.app_queries
  ↓
AppAuthorizationService
  ↓
DTO para Portal
```

Regras:

- autorização final é calculada no backend;
- Portal recebe somente apps/rotas autorizados;
- frontend não recalcula RBAC completo.

---

## 7. Unit of Work como fronteira transacional

O Unit of Work agrupa repositories e controla transação.

Responsabilidades:

- fornecer repositories;
- compartilhar sessão;
- controlar commit;
- controlar rollback;
- coletar eventos;
- publicar eventos após commit.

Fluxo:

```text
with uow:
  use_case.execute()
  ↓
  collect_event()
saída do contexto
  ↓
commit
  ↓
publish events
```

Regra:

> Use cases não devem abrir sessão própria nem publicar eventos diretamente.

---

## 8. Ports

Ports são contratos que isolam a aplicação da infraestrutura.

Exemplos:

```text
UserRepositoryPort
RoleRepositoryPort
PermissionRepositoryPort
PluginRepositoryPort
PluginManifestRepositoryPort
EventDispatcherPort
PermissionCachePort
```

Vantagens:

- testabilidade;
- baixo acoplamento;
- troca de implementação sem alterar use case;
- mocks em testes unitários.

---

## 9. Repositories

Repositories concretos pertencem à infraestrutura.

Exemplo:

```text
SqlAlchemyUserRepository
SqlAlchemyPluginRepository
SqlAlchemyNotificationRepository
```

Eles devem:

- consultar banco;
- criar registros;
- atualizar registros;
- remover registros;
- retornar entidades ou DTOs internos.

Eles não devem:

- publicar eventos;
- retornar `jsonify`;
- acessar `request`;
- decidir regra de autorização complexa;
- executar commit fora do Unit of Work.

---

## 10. Event-driven interno

A Core API usa eventos para separar ação de efeitos colaterais.

Exemplo:

```text
Use case altera RBAC
  ↓
coleta AdminChangedEvent
  ↓
commit
  ↓
RbacEventHandler invalida cache
  ↓
SocketIOEventDispatcher notifica Portal
```

Isso evita que controllers e use cases dependam diretamente de Socket.IO.

---

## 11. Aplicação no Portal

No frontend, o princípio também vale.

Separação esperada:

```text
ui/
  components e pages

state/
  hooks, contextos, stores

data/
  api clients, adapters e DTO mapping
```

Regras:

- UI não calcula autorização final;
- UI não contém regra de negócio de domínio;
- chamadas HTTP ficam em camada `data`;
- estado global fica em `state`;
- componentes renderizam estado e disparam ações.

---

## 12. Aplicação na API DELPI

A API DELPI deve seguir o mesmo padrão para domínios operacionais.

Fluxo desejado:

```text
Route
  ↓
Composer
  ↓
UseCase
  ↓
Port
  ↓
Repository concreto
  ↓
TOTVS / postgres-plugins / outro datasource
```

A API DELPI deve evitar:

- rota acessando banco diretamente;
- service gigante concentrando tudo;
- regra operacional dentro de repository;
- acoplamento da regra ao banco TOTVS;
- duplicação de regra no frontend.

---

## 13. Aplicação em plugins

Plugins frontend devem separar:

```text
ui
state
data
```

Plugins backend-only ou módulos da API DELPI devem separar:

```text
domain
application
infrastructure
interfaces
```

Manifesto do plugin deve declarar:

- identidade;
- tipo;
- basePath;
- entry;
- permissões;
- rotas;
- backend quando aplicável.

---

## 14. O que pertence a cada lugar

| Responsabilidade | Lugar correto |
|---|---|
| Regra de autorização HTTP | decorators/policies |
| Cálculo de permissões efetivas | PermissionResolver/Core API |
| Filtro de apps por permissão | AppAuthorizationService |
| Registro de plugin | RegisterPluginUseCase |
| Persistência de plugin | repositories SQLAlchemy |
| Emissão Socket.IO | infraestrutura socket |
| Login SSO | Portal + Keycloak |
| Dados operacionais TOTVS | API DELPI |
| Menu dinâmico | Portal consumindo `/me/apps` |

---

## 15. Anti-padrões proibidos

Evitar:

```text
Controller com regra de negócio extensa.
Use case importando Flask request.
Repository chamando Socket.IO.
Frontend decidindo permissão final.
Plugin aparecendo sem /me/apps.
JWT carregando lista completa de permissões.
Commit espalhado em repositories.
SQL direto em controllers.
Hardcode de secrets.
Duplicar regra de domínio no frontend.
```

---

## 16. Checklist para nova feature backend

- [ ] Existe use case claro.
- [ ] Controller é fino.
- [ ] A regra não depende de Flask.
- [ ] Repository concreto está na infraestrutura.
- [ ] Port/contrato existe quando necessário.
- [ ] Unit of Work controla commit/rollback.
- [ ] Erros seguem padrão `{ errors: [...] }`.
- [ ] Eventos são coletados, não publicados diretamente.
- [ ] Teste unitário pode rodar sem servidor HTTP.
- [ ] Não há segredo hardcoded.

---

## 17. Checklist para nova feature frontend

- [ ] UI apenas renderiza e dispara ações.
- [ ] Chamadas HTTP estão em `data`.
- [ ] Estado está em hook/context/store.
- [ ] Não há regra de autorização final no componente.
- [ ] Permissões vêm de `/me` e apps de `/me/apps`.
- [ ] Erros da API são tratados por `code`.
- [ ] Token não é passado por query string.
- [ ] Não há segredo no frontend.

---

## 18. Pontos de atenção

1. Clean Architecture é regra obrigatória da Minha DELPI.
2. O centro do sistema é domínio/aplicação, não framework.
3. Controllers adaptam protocolo, não concentram regra.
4. Repositories acessam dados, não decidem fluxo de negócio.
5. Unit of Work é a fronteira transacional.
6. Eventos desacoplam persistência de efeitos.
7. Portal não é fonte final de autorização.
8. API DELPI deve aplicar a mesma arquitetura em domínios operacionais.
9. Plugins devem respeitar a governança central.
10. Refatorações devem ser incrementais e testáveis.

---

## 19. Documentos relacionados

```text
docs/01-arquitetura/estrutura-de-repositorio.md
docs/01-arquitetura/fluxo-de-requisicao.md
docs/01-arquitetura/event-driven-e-socket.md
docs/04-core-api/use-cases.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/repositories.md
docs/11-padroes-de-desenvolvimento/padrao-de-use-case.md
```
