# Minha DELPI — Arquitetura Geral

> **Arquivo:** `docs/01-arquitetura/arquitetura-geral.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** arquitetura técnica macro da plataforma

---

## 1. Objetivo

Este documento descreve a arquitetura geral da **Minha DELPI**, explicando como os serviços se organizam, como se comunicam, quais responsabilidades pertencem a cada camada e quais decisões técnicas sustentam a plataforma.

A intenção é fornecer uma visão técnica clara para desenvolvimento, manutenção, operação e evolução da plataforma.

---

## 2. Visão arquitetural resumida

A Minha DELPI é uma plataforma corporativa modular composta por:

- Gateway Nginx;
- Portal React/Vite;
- Core API Flask;
- Keycloak;
- API DELPI (operacional / TOTVS);
- Minha DELPI AI API (chat, RAG, agentes);
- Ollama (LLM local em dev);
- Plugins/microfrontends;
- PostgreSQL Core, Keycloak e Plugins (pgvector).

Visão macro:

```text
                 ┌────────────────────┐
                 │      Usuário       │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │      Gateway       │
                 │       Nginx        │
                 └─────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌────────────────┐  ┌────────────────┐
│    Portal     │  │    Core API    │  │    Keycloak    │
│ React + Vite  │  │ Flask + RBAC   │  │ OIDC Provider  │
└───────┬───────┘  └───────┬────────┘  └───────┬────────┘
        │                  │                   │
        │                  ▼                   ▼
        │          ┌────────────────┐  ┌────────────────┐
        │          │ postgres-core  │  │  keycloak-db   │
        │          └────────────────┘  └────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                 Plugins / Microfrontends                │
│ dashboard-delpi, strategic-indicators, dashboard-lmps... │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   API DELPI   │
                    │ Domínios/TOTVS│
                    └───────┬───────┘
                            ▼
                    ┌──────────────────┐
                    │ postgres-plugins │
                    └──────────────────┘
```

---

## 3. Princípio central da arquitetura

A arquitetura da Minha DELPI segue uma separação forte entre **governança da plataforma** e **domínios de negócio**.

```text
Core API  → governa a plataforma
API DELPI → atende dados e regras operacionais
Portal    → entrega a experiência visual
Plugins   → implementam módulos funcionais
Gateway   → expõe e roteia os serviços
Keycloak  → autentica usuários
```

Essa separação evita que regras de negócio operacionais contaminem a governança da plataforma e evita que o Portal precise conhecer detalhes de autorização, banco ou infraestrutura.

---

## 4. Camadas da plataforma

A arquitetura pode ser entendida em camadas.

```text
Edge Layer
  Gateway Nginx

Identity Layer
  Keycloak

Experience Layer
  Portal React
  Plugins / Microfrontends

Governance Layer
  Core API

Business/API Layer
  API DELPI

Data Layer
  postgres-core
  keycloak-db
  postgres-plugins
```

---

## 5. Edge Layer — Gateway

O Gateway é a borda HTTP da plataforma.

Ele deve ser o único serviço exposto diretamente para o usuário em ambiente normal.

Responsabilidades:

- receber requisições HTTP;
- rotear para serviços internos;
- servir como ponto único de entrada;
- simplificar URLs públicas;
- esconder portas internas;
- centralizar proxy reverso;
- permitir publicação por path.

Serviço Docker:

```text
gateway
```

Implementação:

```text
Nginx
```

Paths esperados (dev):

```text
/                              → portal
/core-api/*                    → core-api
/auth/*                        → keycloak
/socket.io/*                   → core-api (WebSocket)
/apps/api-delpi/*              → api-delpi
/apps/minha-delpi-ai/api/*     → minha-delpi-ai-api
/apps/<plugin-id>/*            → container do plugin (assets MFE)
```

Detalhe: [../02-infraestrutura/gateway-nginx.md](../02-infraestrutura/gateway-nginx.md).

A documentação detalhada do gateway deve ficar em:

```text
docs/02-infraestrutura/gateway-nginx.md
```

---

## 6. Identity Layer — Keycloak

O Keycloak é responsável por autenticação.

Responsabilidades:

- autenticar usuários;
- manter realm;
- manter client OIDC do Portal;
- emitir access token JWT;
- expor JWKS;
- permitir SSO;
- suportar integrações externas quando necessário.

Serviços Docker:

```text
keycloak
keycloak-db
```

Banco:

```text
keycloak-db
```

O Keycloak não é a fonte final de permissões da Minha DELPI.

A autorização é resolvida pela Core API.

---

## 7. Experience Layer — Portal

O Portal é o frontend principal da plataforma.

Responsabilidades:

- renderizar a interface principal;
- iniciar login via Keycloak;
- receber e usar access token;
- chamar a Core API;
- montar menu dinâmico;
- listar apps autorizados;
- gerenciar favoritos;
- consumir notificações;
- conectar no Socket.IO;
- carregar plugins conforme `entryUrl`, `renderMode` e rotas retornadas pela Core API.

Serviço Docker:

```text
portal
```

Tecnologias:

```text
React
Vite
```

O Portal não deve:

- resolver permissões diretamente;
- acessar banco;
- registrar plugins;
- conter lista fixa definitiva de apps;
- duplicar regras de RBAC.

---

## 8. Experience Layer — Plugins e microfrontends

Plugins são módulos plugáveis da plataforma.

Serviços identificados na stack atual:

```text
strategic-indicators
minha-delpi-chat
dashboard-delpi
dashboard-lmps
```

Inventário: [../08-plugins/README.md](../08-plugins/README.md).

Tipos de plugin suportados pelo contrato de manifesto:

```text
microfrontend
iframe
backend-only
```

Um plugin visual normalmente é publicado sob:

```text
/apps/<plugin>
```

O Portal só deve exibir um plugin se a Core API retornar esse app/rota como autorizado para o usuário.

---

## 9. Governance Layer — Core API

A Core API é a camada de governança central.

Serviço Docker:

```text
core-api
```

Tecnologias principais:

```text
Python
Flask
SQLAlchemy
Flask-Migrate / Alembic
Socket.IO
PostgreSQL
```

Responsabilidades:

- validar JWT recebido;
- sincronizar usuário local;
- manter usuários;
- manter roles;
- manter groups;
- manter permissions;
- calcular permissões efetivas;
- aplicar RBAC em endpoints administrativos;
- gerenciar apps;
- gerenciar rotas;
- registrar e versionar plugins;
- armazenar manifestos;
- gerenciar favoritos;
- gerenciar notificações;
- publicar eventos administrativos;
- manter auditoria.

Banco:

```text
postgres-core
```

A Core API segue Clean Architecture de forma pragmática:

```text
interfaces/http → application/use_cases → domain/ports → infrastructure/repositories
```

---

## 10. Business/API Layer — API DELPI

A API DELPI é a API operacional e de integrações.

Serviço Docker:

```text
api-delpi
```

Responsabilidades:

- expor rotas de negócio;
- consultar TOTVS;
- atender módulos operacionais;
- usar datasource SQL Server/TOTVS quando necessário;
- usar `postgres-plugins` para persistência de módulos novos;
- funcionar como backend de plugins quando aplicável.

A API DELPI não deve ser confundida com a Core API.

```text
Core API  → identidade interna, RBAC, apps e plugins
API DELPI → operação, TOTVS, módulos e dados de negócio
```

---

## 10.1 AI Layer — Minha DELPI AI API

Serviços Docker (dev):

```text
minha-delpi-ai-api
ollama
```

Responsabilidades:

- chat e agentes com LLM (Ollama em dev, vLLM em prod opcional);
- embeddings e base de conhecimento (pgvector em `postgres-plugins`);
- validação JWT Keycloak (mesmo padrão issuer/JWKS);
- integração com Core API para contexto de usuário.

O plugin **minha-delpi-chat** consome esta API em `/apps/minha-delpi-ai/api/*`, não a Core API.

Documentação: `minha-delpi-ai-api/docs/api/`.

---

## 11. Data Layer — Bancos

A arquitetura usa bancos separados.

### 11.1 postgres-core

Serviço:

```text
postgres-core
```

Responsável por dados de governança:

- users;
- roles;
- groups;
- permissions;
- user_roles;
- user_groups;
- role_permissions;
- group_roles;
- user_permissions;
- apps;
- app_routes;
- app_manifests;
- app_versions;
- user_favorite_apps;
- notifications;
- audit_logs.

---

### 11.2 keycloak-db

Serviço:

```text
keycloak-db
```

Responsável exclusivamente pelos dados internos do Keycloak.

A aplicação não deve acessar esse banco diretamente para regras de negócio.

---

### 11.3 postgres-plugins

Serviço:

```text
postgres-plugins
```

Responsável por persistência de módulos/plugins/domínios que não pertencem ao banco core.

Consumido por:

- **API DELPI** (`PLUGINS_DB_*`) — módulos operacionais;
- **Minha DELPI AI API** (`DATABASE_URL`) — schema RAG/pgvector.

---

## 12. Fluxo de requisição HTTP

Fluxo típico de acesso ao Portal:

```text
Usuário
  ↓
Gateway :80
  ↓
Portal
```

Fluxo típico de chamada protegida:

```text
Portal
  ↓ Authorization: Bearer <token>
Gateway
  ↓
Core API
  ↓
Auth middleware
  ↓
JWT validator
  ↓
Controller
  ↓
Use case
  ↓
Repository
  ↓
Postgres Core
```

Fluxo típico de módulo operacional:

```text
Portal ou Plugin
  ↓
Gateway
  ↓
API DELPI
  ↓
TOTVS / postgres-plugins / outro datasource
```

---

## 13. Fluxo de autenticação

A autenticação acontece via Keycloak.

```text
Portal
  ↓
Keycloak
  ↓
Login
  ↓
Access Token JWT
  ↓
Portal
```

Depois do login, o Portal envia o token para a Core API.

A Core API valida:

- assinatura;
- issuer;
- audience;
- expiração;
- claims essenciais.

Depois disso, sincroniza o usuário localmente se necessário.

---

## 14. Fluxo de autorização

A autorização acontece na Core API.

Fluxo lógico:

```text
Usuário autenticado
  ↓
Roles diretas
  ↓
Grupos
  ↓
Roles via grupos
  ↓
Permissões das roles
  ↓
Overrides individuais
  ↓
Permissões efetivas
  ↓
Apps e rotas filtrados
```

A resolução efetiva é responsabilidade do domínio da Core API.

O Portal recebe uma visão já autorizada.

---

## 15. Fluxo de plugins

Registro de plugin:

```text
Manifesto JSON
  ↓
Core API /admin/apps/register
  ↓
ManifestValidator
  ↓
JSON Schema
  ↓
Strategy por tipo
  ↓
Regras de domínio
  ↓
Criação/atualização de app
  ↓
Criação/atualização de manifesto
  ↓
Criação de versão
  ↓
Criação de permissões
  ↓
Criação de rotas
  ↓
Evento admin.changed
```

Consumo de plugin:

```text
Portal chama /me/apps
  ↓
Core API filtra apps e rotas
  ↓
Portal recebe entryUrl/renderMode/routes
  ↓
Portal carrega plugin
```

---

## 16. Fluxo de eventos administrativos

A plataforma usa eventos para refletir mudanças administrativas.

Fluxo:

```text
Controller
  ↓
Use case
  ↓
Unit of Work coleta evento
  ↓
Commit
  ↓
EventBus
  ↓
RbacEventHandler / SocketIOEventDispatcher
  ↓
Portal recebe admin.changed
```

Eventos podem ser:

- globais;
- direcionados a um usuário.

Exemplos:

```text
plugin_registered
plugin_unregistered
plugin_activated
plugin_deactivated
route_created
route_updated
route_deleted
role_created
role_updated
roles_replaced
permissions_replaced
favorite_added
favorite_removed
```

---

## 17. Organização da Core API

Estrutura conceitual da Core API:

```text
core-api/
  app/
    application/
      services/
      use_cases/
      validators/
      event_handlers/
      event_bus.py
      unit_of_work.py

    domain/
      dto/
      events/
      plugins/
      ports/
      services/

    infrastructure/
      cache/
      config/
      db/
      persistence/
      plugins/
      security/
      seeds/
      socket/

    interfaces/
      http/
      socket/

    extensions/
      db.py
      migrate.py
      socket.py

    create_app.py
    main.py
```

Camadas:

| Camada | Responsabilidade |
|---|---|
| `interfaces` | Controllers HTTP, middlewares, socket handlers |
| `application` | Use cases, validators, event bus, serviços de aplicação |
| `domain` | Ports, eventos, DTOs, serviços de domínio e regras centrais |
| `infrastructure` | SQLAlchemy, cache, socket, config, schemas e integrações |
| `extensions` | Instâncias Flask de db, migrate e socket |

---

## 18. Clean Architecture na Core API

A Core API usa um desenho inspirado em Clean Architecture.

Regra geral de dependência:

```text
Interfaces → Application → Domain
Infrastructure → Domain/Application
```

O domínio define contratos por ports.

A infraestrutura implementa esses ports usando SQLAlchemy, cache, socket e outros detalhes técnicos.

Exemplo:

```text
UseCase
  ↓ depende de
UnitOfWork / Port
  ↓ implementado por
SqlAlchemyRepository
  ↓ acessa
PostgreSQL
```

Essa estrutura permite:

- testar regras sem depender diretamente do Flask;
- trocar detalhes de persistência com menor impacto;
- manter controllers mais finos;
- separar regra de negócio de banco e HTTP.

---

## 19. Unit of Work

O Unit of Work é o ponto de composição transacional da Core API.

Responsabilidades:

- expor repositories;
- controlar commit;
- controlar rollback;
- coletar eventos de domínio;
- publicar eventos após commit;
- manter aliases de compatibilidade para código antigo.

Fluxo esperado:

```text
with SqlAlchemyUnitOfWork() as uow:
    use_case = SomeUseCase(uow)
    result = use_case.execute(...)

# __exit__ executa commit e publica eventos
```

Regra recomendada:

> Use cases não devem chamar commit diretamente, salvo casos legados já existentes. O padrão preferencial é deixar o Unit of Work controlar a transação no contexto externo.

---

## 20. Segurança arquitetural

A segurança da plataforma é baseada em quatro pilares:

1. **Autenticação via Keycloak**  
   Usuário prova identidade no Identity Provider.

2. **Validação JWT na Core API e serviços protegidos**  
   O token é validado antes de acesso a endpoints protegidos.

3. **Autorização por RBAC na Core API**  
   Permissões são calculadas internamente.

4. **Filtro de apps e rotas por permissão**  
   O Portal só recebe o que o usuário pode acessar.

---

## 21. Decisões arquiteturais atuais

| Decisão | Estado |
|---|---|
| Gateway como entrada única | Vigente |
| Keycloak como Identity Provider | Vigente |
| Core API como governança central | Vigente |
| API DELPI separada para operação | Vigente |
| PostgreSQL separado para Core, Keycloak e Plugins | Vigente |
| Plugin System por manifesto JSON | Vigente |
| Manifesto versão `1.0.0` | Vigente |
| Autorização resolvida internamente pela Core API | Vigente |
| Portal com menu dinâmico por `/me/apps` | Vigente |
| Eventos via Socket.IO | Vigente |

---

## 22. Pontos de atenção arquitetural

Durante a análise do código atual, foram identificados pontos que devem ser acompanhados:

1. **Nomenclatura antiga**  
   Ainda existem referências a DELPI Central em código e configurações.

2. **Ports possivelmente incompletos**  
   Algumas implementações expõem métodos não declarados nos ports correspondentes.

3. **Controle transacional inconsistente em alguns use cases**  
   A maioria depende do Unit of Work externo, mas alguns use cases administrativos fazem commit/rollback diretamente.

4. **Notificações**  
   Há use case que chama método `get` no repository de notificações; é necessário confirmar a implementação final desse método.

5. **SemVer do manifesto**  
   O JSON Schema permite pré-release, mas as regras de domínio restringem SemVer para `MAJOR.MINOR.PATCH` sem sufixo.

6. **Keycloak não é autorização final**  
   Qualquer documentação que diga que permissões completas vêm do Keycloak deve ser considerada desatualizada.

---

## 23. Relação com outros documentos

Este documento é uma visão macro.

Detalhes específicos devem ser documentados em:

```text
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/gateway-nginx.md
docs/03-autenticacao-autorizacao/rbac.md
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/modelos-de-banco.md
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/06-portal-frontend/visao-geral-portal.md
docs/07-api-delpi/visao-geral-api-delpi.md
```

