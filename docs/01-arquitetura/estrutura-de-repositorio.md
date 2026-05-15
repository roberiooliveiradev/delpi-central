# Minha DELPI — Estrutura de Repositório

> **Arquivo:** `docs/01-arquitetura/estrutura-de-repositorio.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** organização do monorepo, responsabilidades por pasta e relação entre aplicações

---

## 1. Objetivo

Este documento descreve a estrutura de repositório da **Minha DELPI**.

A plataforma é organizada como um conjunto de aplicações e serviços independentes, orquestrados pela pasta `infra`, com separação clara entre:

- **Core API**: governança central da plataforma;
- **Portal**: shell frontend principal;
- **API DELPI**: backend operacional/domínios;
- **Plugins**: aplicações plugáveis;
- **Gateway**: reverse proxy;
- **Infraestrutura**: Docker Compose, bancos e Keycloak.

---

## 2. Estrutura macro esperada

Estrutura de alto nível:

```text
delpi-central/          # monorepo (nome legado do repositório)
  api-delpi/
  core-api/
  minha-delpi-ai-api/
  gateway/
  infra/
  plugins/
  portal/
  docs/
```

Responsabilidade por pasta:

| Pasta | Responsabilidade |
|---|---|
| `core-api/` | API Flask de governança: usuários, RBAC, apps, plugins, manifestos, favoritos, notificações e eventos |
| `portal/` | Frontend React/Vite principal, autenticação SSO, menu dinâmico e carregamento de plugins |
| `api-delpi/` | API operacional para domínios, integrações, TOTVS, Portal RH e dados de plugins |
| `minha-delpi-ai-api/` | Chat, agentes, RAG; FastAPI + pgvector |
| `plugins/` | Microfrontends e aplicações plugáveis |
| `gateway/` | Nginx/reverse proxy e entrada HTTP única |
| `infra/` | Docker Compose, inicialização de bancos, Keycloak themes e configuração local |
| `docs/` | Documentação oficial centralizada |

---

## 3. Pasta `infra/`

A pasta `infra` é o ponto de execução da stack Docker.

Estrutura esperada:

```text
infra/
  docker-compose.yml
  docker-compose.dev.yml
  docker/
    postgres/
      init.sql
      plugins-init.sql
  keycloak/
    themes/
```

Responsabilidades:

- subir `postgres-core`;
- subir `keycloak-db`;
- subir `keycloak`;
- subir `core-api`;
- subir `portal`;
- subir plugins;
- subir `postgres-plugins`;
- subir `api-delpi`;
- subir `minha-delpi-ai-api` e `ollama`;
- subir `gateway`;
- manter scripts de inicialização dos bancos;
- manter temas customizados do Keycloak.

Regra:

> Os caminhos do Compose partem da pasta `infra`, usando `..` para acessar `core-api`, `portal`, `api-delpi`, `gateway` e `plugins`.

---

## 4. Pasta `core-api/`

A `core-api` é a API de governança central da Minha DELPI.

Estrutura conceitual:

```text
core-api/
  app/
    application/
    domain/
    extensions/
    infrastructure/
    interfaces/
    create_app.py
    main.py
  migrations/
  Dockerfile.dev
  Dockerfile.prod
```

Responsabilidades:

- autenticar requisições via JWT validado contra Keycloak;
- sincronizar usuário local;
- resolver RBAC;
- gerenciar apps/plugins;
- gerenciar rotas;
- persistir manifestos;
- versionar plugins;
- emitir eventos administrativos;
- servir dados do usuário atual para o Portal;
- servir `/me/apps` para menu e autorização de apps.

---

## 5. Estrutura interna da `core-api/app`

### 5.1 `domain/`

Camada de domínio.

Contém:

- eventos de domínio;
- ports/contratos;
- abstrações usadas pelos use cases;
- regras que não devem depender de Flask, SQLAlchemy ou Socket.IO.

Exemplo conceitual:

```text
app/domain/
  events/
  ports/
```

Regra:

> `domain` não deve depender de infraestrutura.

---

### 5.2 `application/`

Camada de aplicação.

Contém:

- use cases;
- event bus;
- event handlers;
- serviços de aplicação;
- contrato do Unit of Work.

Exemplo conceitual:

```text
app/application/
  use_cases/
  event_bus.py
  event_handlers/
  unit_of_work.py
```

Responsabilidade:

```text
Orquestrar regra de aplicação usando ports/repositories via Unit of Work.
```

---

### 5.3 `interfaces/`

Camada de entrada/adapters.

Contém:

- controllers HTTP;
- middleware de autenticação;
- policies/decorators;
- handlers Socket.IO.

Exemplo:

```text
app/interfaces/
  http/
    health_controller.py
    me_controller.py
    apps_controller.py
    rbac_controller.py
    auth_middleware.py
    security/
  socket/
    socket_handlers.py
```

Responsabilidade:

```text
Adaptar HTTP/Socket para use cases.
```

Controllers devem ser finos e não concentrar regra de negócio.

---

### 5.4 `infrastructure/`

Camada de infraestrutura.

Contém:

- configuração;
- models SQLAlchemy;
- repositories concretos;
- cache;
- socket dispatcher;
- seeds;
- adapters técnicos.

Exemplo:

```text
app/infrastructure/
  config/
  db/
    models/
  persistence/
    sqlalchemy/
  cache/
  seeds/
  socket/
```

Responsabilidade:

```text
Implementar detalhes técnicos usados pelas camadas internas.
```

---

### 5.5 `extensions/`

Contém extensões Flask inicializadas no bootstrap:

```text
app/extensions/
  db.py
  migrate.py
  socket.py
```

Uso:

- SQLAlchemy;
- Flask-Migrate/Alembic;
- Flask-SocketIO.

---

## 6. Bootstrap da Core API

Arquivo principal:

```text
core-api/app/create_app.py
```

Responsabilidades:

- criar instância Flask;
- carregar configuração;
- inicializar `db`;
- inicializar `migrate`;
- inicializar `socketio`;
- registrar middleware de autenticação;
- registrar blueprints;
- importar models;
- executar seed de permissões base fora do modo de teste.

Arquivo de execução:

```text
core-api/app/main.py
```

Responsabilidade:

```text
Executar a aplicação com Socket.IO.
```

---

## 7. Pasta `portal/`

A pasta `portal` contém o frontend principal.

Responsabilidades:

- autenticar usuário via Keycloak;
- obter token;
- consumir `/me`;
- consumir `/me/apps`;
- montar menu dinâmico;
- exibir favoritos;
- exibir notificações;
- conectar Socket.IO;
- carregar microfrontends/iframes.

Estrutura interna exata deve ser documentada a partir do código real do Portal.

Padrão arquitetural esperado:

```text
portal/
  src/
    ui/
    state/
    data/
    routes/
    plugins/
```

Regra:

> Regras de negócio e autorização final não devem ficar no frontend. O Portal renderiza a experiência autorizada pela Core API.

---

## 8. Pasta `api-delpi/`

A `api-delpi` é o backend operacional da plataforma.

Responsabilidades:

- integrar TOTVS;
- integrar Portal RH;
- usar `postgres-plugins`;
- atender plugins e módulos de domínio;
- expor endpoints operacionais;
- validar JWT em endpoints protegidos;
- aplicar permissões quando necessário.

Estrutura desejada em Clean Architecture:

```text
api-delpi/
  app/
    domain/
    application/
    infrastructure/
    interfaces/
```

Observação:

> A documentação detalhada dessa pasta depende da análise dos arquivos reais da `api-delpi`.

---

## 9. Pasta `plugins/`

Contém aplicações plugáveis.

Plugins atuais conhecidos pela stack:

```text
plugins/
  dashboard-delpi/
  strategic-indicators/
  dashboard-lmps/
```

Cada plugin deve possuir, quando aplicável:

- Dockerfile;
- build frontend;
- manifesto;
- basePath;
- permissões;
- rotas;
- entry compatível com Gateway/Portal.

Plugins podem ser:

```text
microfrontend
iframe
backend-only
```

---

## 10. Pasta `gateway/`

Contém a configuração e o build do Gateway Nginx.

Responsabilidades:

- expor a plataforma pela porta HTTP principal;
- rotear `/` para o Portal;
- rotear Core API;
- rotear Keycloak;
- rotear API DELPI;
- rotear plugins;
- aplicar headers e políticas de segurança conforme evolução.

Arquivos esperados:

```text
gateway/
  Dockerfile.dev
  Dockerfile.prod
  nginx.dev.conf
  nginx.conf
```

---

## 11. Pasta `docs/`

Contém a documentação oficial da Minha DELPI.

Estrutura oficial:

```text
docs/
  00-visao-geral/
  01-arquitetura/
  02-infraestrutura/
  03-autenticacao-autorizacao/
  04-core-api/
  05-plugin-system/
  06-portal-frontend/
  07-api-delpi/
  08-plugins/
  09-banco-de-dados/
  10-guias-operacionais/
  11-padroes-de-desenvolvimento/
  12-roadmap-e-evolucao/
```

Regra:

> Documentos devem ser pequenos, navegáveis e orientados por camada/público, evitando um único documento gigante.

---

## 12. Convenções de responsabilidade

| Camada | Pode conhecer | Não deve conhecer |
|---|---|---|
| Domain | regras e contratos | Flask, SQLAlchemy, Socket.IO |
| Application | domain, ports, use cases | detalhes de HTTP e banco concreto |
| Interfaces | HTTP, Socket, use cases | SQL direto e regra de negócio extensa |
| Infrastructure | banco, cache, adapters | decisões de UI |
| Portal | DTOs da Core API, UX | cálculo final de RBAC |
| Plugins | contexto do shell e APIs | governança central interna |
| Gateway | roteamento | regras de negócio |

---

## 13. Regras para novos diretórios

Ao criar nova pasta ou módulo:

1. Verificar se pertence a Core API, API DELPI, Portal ou plugin.
2. Evitar misturar governança central com regra operacional.
3. Manter use cases fora de controllers.
4. Manter repositories concretos fora da camada de domínio.
5. Documentar nova pasta se introduzir responsabilidade relevante.
6. Atualizar `docs/00-visao-geral/mapa-da-plataforma.md` quando o módulo for estrutural.

---

## 14. Pontos de atenção

1. `infra/` é o ponto de execução do Compose.
2. `core-api/` governa a plataforma.
3. `api-delpi/` atende domínios operacionais.
4. `portal/` é shell frontend, não motor de autorização.
5. `plugins/` contém módulos plugáveis.
6. `gateway/` é a entrada HTTP.
7. `docs/` é a fonte oficial de documentação.
8. Separar domínio, aplicação, interfaces e infraestrutura é regra do projeto.
9. O nome atual do produto é **Minha DELPI**.
10. Referências antigas a DELPI Central devem ser tratadas como legado histórico.

---

## 15. Documentos relacionados

```text
docs/01-arquitetura/arquitetura-geral.md
docs/01-arquitetura/clean-architecture.md
docs/01-arquitetura/fluxo-de-requisicao.md
docs/02-infraestrutura/docker-compose.md
docs/04-core-api/visao-geral-core-api.md
docs/07-api-delpi/visao-geral-api-delpi.md
```
