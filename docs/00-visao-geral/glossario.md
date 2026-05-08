# Minha DELPI — Glossário

> **Arquivo:** `docs/00-visao-geral/glossario.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** termos técnicos, funcionais e arquiteturais usados na plataforma

---

## 1. Objetivo

Este glossário centraliza os principais termos usados na documentação da **Minha DELPI**.

Ele deve ser usado como referência comum por pessoas de produto, desenvolvimento, operação, suporte e administração da plataforma.

A plataforma aparece em documentos legados como **DELPI Central**. Na documentação atual, o nome oficial do produto deve ser **Minha DELPI**.

---

## 2. Termos gerais da plataforma

### Minha DELPI

Portal corporativo da DELPI responsável por centralizar autenticação, autorização, acesso a aplicações, módulos operacionais e plugins.

A Minha DELPI funciona como uma plataforma unificada composta por Gateway, Keycloak, Core API, Portal frontend, API DELPI, bancos de dados e aplicações plugáveis.

---

### DELPI Central

Nome anterior ou legado usado em documentos técnicos, registros de fase e especificações iniciais.

Quando documentos antigos mencionarem **DELPI Central**, interpretar como a mesma plataforma que hoje se chama **Minha DELPI**, salvo quando o contexto indicar histórico ou nomenclatura antiga.

---

### Plataforma

Conjunto integrado de serviços que compõem a Minha DELPI.

Inclui, no mínimo:

- Gateway;
- Portal frontend;
- Core API;
- Keycloak;
- PostgreSQL Core;
- API DELPI;
- PostgreSQL Plugins;
- plugins e microfrontends.

---

### Portal

Frontend principal da Minha DELPI.

Também pode ser chamado de **Portal frontend**, **Portal React** ou **shell da aplicação**.

Responsabilidades principais:

- iniciar login via Keycloak;
- consumir `/me` e `/me/apps` na Core API;
- montar menu dinâmico;
- exibir favoritos e notificações;
- carregar plugins autorizados;
- oferecer experiência visual unificada.

---

### Shell

Aplicação frontend principal que hospeda a experiência da plataforma.

Na Minha DELPI, o shell é o Portal.

O shell não deve conter as regras de negócio centrais. Ele renderiza a interface, consome APIs e carrega plugins conforme a autorização retornada pela Core API.

---

### Gateway

Camada de entrada HTTP da plataforma.

Na stack atual, é implementado por Nginx no serviço `gateway`.

Responsabilidades:

- expor a porta pública da plataforma;
- rotear `/` para o Portal;
- rotear `/core-api/*` para a Core API;
- rotear `/auth/*` para o Keycloak;
- rotear `/apps/*` para aplicações e plugins;
- concentrar políticas de borda, como headers, CORS, logs e futura proteção adicional.

---

### Core API

Backend de governança central da Minha DELPI.

Responsável por:

- usuário local;
- RBAC;
- roles, groups e permissions;
- apps e rotas;
- Plugin System;
- manifestos;
- favoritos;
- notificações;
- eventos administrativos;
- auditoria;
- resolução de permissões efetivas.

A Core API não deve concentrar regras operacionais de domínio que pertencem à API DELPI ou aos módulos específicos.

---

### API DELPI

Backend operacional da Minha DELPI.

É separado da Core API.

Responsabilidades esperadas:

- expor rotas operacionais;
- integrar com TOTVS;
- integrar com banco de plugins;
- integrar com Portal RH, quando configurado;
- servir dados para plugins, dashboards e módulos de domínio.

---

### Plugin

Módulo registrado na plataforma por manifesto.

Um plugin pode representar:

- microfrontend;
- iframe;
- backend-only;
- módulo operacional governado pela Core API.

Plugins são registrados pela Core API e podem criar permissões, rotas e manifesto vigente.

---

### App

Representação persistida de uma aplicação ou plugin dentro da Core API.

No banco `postgres-core`, apps ficam na tabela `apps`.

Um app pode ter rotas, permissões, manifesto vigente, versões históricas e favoritos de usuário.

---

### Aplicação plugável

Aplicação que não faz parte fixa do Portal, mas é integrada à Minha DELPI por manifesto e governança da Core API.

Pode ser carregada como microfrontend, iframe ou representada como backend-only.

---

## 3. Autenticação e autorização

### Keycloak

Identity Provider oficial usado pela Minha DELPI para autenticação SSO.

Responsável por:

- login;
- sessão SSO;
- emissão de tokens JWT;
- exposição de JWKS;
- integração OIDC;
- suporte a clients técnicos, quando necessário.

O Keycloak autentica o usuário. A Core API autoriza o acesso funcional dentro da plataforma.

---

### SSO

Single Sign-On.

Mecanismo que permite ao usuário autenticar uma vez no Keycloak e acessar a plataforma ou aplicações compatíveis sem múltiplos logins independentes.

---

### OIDC

OpenID Connect.

Protocolo de identidade usado sobre OAuth2.

Na Minha DELPI, é usado pelo Portal para autenticar usuários via Keycloak e obter tokens JWT.

---

### OAuth2

Protocolo de autorização usado como base para fluxos de autenticação e emissão de tokens.

Na Minha DELPI, aparece principalmente no fluxo com Keycloak.

---

### Authorization Code + PKCE

Fluxo recomendado para autenticação de aplicações frontend públicas.

O Portal deve usar esse fluxo com Keycloak para evitar uso de client secret no frontend.

---

### JWT

JSON Web Token.

Token emitido pelo Keycloak e enviado pelo Portal para APIs protegidas no header:

```http
Authorization: Bearer <access_token>
```

Na Minha DELPI, o JWT identifica o usuário, mas não deve carregar a lista completa de permissões nem a estrutura do menu.

---

### JWKS

JSON Web Key Set.

Endpoint exposto pelo Keycloak contendo chaves públicas usadas pela Core API e outros backends para validar a assinatura do JWT.

---

### Issuer

Claim `iss` do JWT.

Representa quem emitiu o token.

A Core API deve validar se o issuer do token corresponde ao valor configurado em `KEYCLOAK_ISSUER`.

---

### Audience

Claim `aud` do JWT.

Representa para quem o token foi emitido.

A Core API e a API DELPI devem validar se o token contém a audience esperada.

---

### RBAC

Role-Based Access Control.

Modelo de autorização baseado em papéis.

Na Minha DELPI, o RBAC usa:

- users;
- roles;
- groups;
- permissions;
- user_roles;
- user_groups;
- group_roles;
- role_permissions;
- user_permissions.

---

### User

Usuário local da plataforma, persistido na tabela `users` da Core API.

O usuário é sincronizado a partir do JWT emitido pelo Keycloak.

---

### Role

Papel que agrupa permissões.

Exemplo conceitual:

- Administrador de Apps;
- Gestor de Usuários;
- Analista de Qualidade.

---

### Group

Grupo de usuários.

Usuários podem herdar roles por meio de grupos.

---

### Permission

Permissão granular usada para autorizar ações, rotas e funcionalidades.

Exemplos:

```text
apps.view
apps.manage
routes.manage
dashboard-lmps.access
```

---

### Permission Code

Código textual estável de uma permissão.

Deve ser usado em regras de backend, rotas, manifestos e UI como identificador lógico.

---

### Permission Resolver

Componente da Core API responsável por calcular permissões efetivas do usuário.

Considera:

- superadmin;
- roles diretas;
- roles herdadas por grupos;
- overrides individuais;
- cache de permissões.

---

### Permissões efetivas

Conjunto final de permissões que um usuário possui depois de aplicar roles diretas, grupos e overrides.

É esse conjunto que deve orientar `/me`, `/me/apps`, decorators de backend e visibilidade de apps no Portal.

---

### Override de permissão

Regra individual em `user_permissions` que pode conceder ou remover uma permissão específica de um usuário.

`granted=true` concede.

`granted=false` remove.

---

### Superadmin

Usuário com flag administrativa especial na Core API.

Possui bypass para permissões comuns e recebe acesso administrativo amplo.

A plataforma deve impedir a remoção do último superadmin.

---

### Policy

Regra reutilizável de autorização aplicada no backend.

Policies evitam espalhar validações manuais por controllers.

---

### Decorator

Função aplicada sobre rotas HTTP para exigir autenticação ou permissão.

Exemplos conceituais:

```python
@require_auth
@require_permission("apps.manage")
```

---

## 4. Plugin System

### Plugin System

Sistema oficial de registro e governança de plugins da Minha DELPI.

Responsável por:

- validar manifestos;
- criar apps;
- criar permissões;
- criar rotas;
- armazenar manifesto vigente;
- armazenar versões históricas;
- permitir rollback;
- permitir ativação/desativação;
- controlar exposição no Portal.

---

### Manifesto

Arquivo JSON que declara um plugin.

Define identidade, versão, tipo, basePath, entry, permissões, rotas, UI e backend.

---

### `delpi.manifest.json`

Nome convencional do manifesto de um plugin.

Deve obedecer ao schema oficial da plataforma.

---

### Schema do manifesto

Contrato JSON que define campos obrigatórios, tipos aceitos e regras estruturais do manifesto.

A versão atual usada nos documentos recentes é `schemaVersion: "1.0.0"`.

---

### Plugin ID

Identificador único do plugin.

É usado como:

- `manifest.id`;
- `apps.id`;
- `permissions.module`;
- referência de dependência;
- base para permission codes.

---

### Versionamento SemVer

Padrão de versão `MAJOR.MINOR.PATCH`.

Usado para controlar versões registradas de plugins.

---

### Checksum

Hash calculado sobre o manifesto.

É persistido junto ao manifesto vigente e às versões históricas para rastreabilidade.

---

### Microfrontend

Plugin frontend integrado ao Portal.

Pode ser carregado por estratégia federada ou embutida, conforme `renderMode` e `entry`.

---

### Module Federation

Estratégia de carregamento de microfrontends em que uma aplicação remota expõe módulos para o shell.

Na Minha DELPI, é a estratégia preferida para escala de microfrontends.

---

### Remote Entry

Arquivo JavaScript exposto por um microfrontend federado.

Normalmente aparece como:

```text
remoteEntry.js
```

---

### Iframe

Tipo de plugin visual que carrega uma aplicação por URL HTTP/HTTPS dentro ou fora do Portal.

É útil para integrações legadas ou sistemas externos.

---

### Backend-only

Tipo de plugin sem interface visual.

Usado para representar serviços backend, APIs ou módulos sem tela própria, mas que precisam participar da governança de permissões e dependências.

---

### Base Path

Caminho base do app/plugin.

Exemplo:

```text
/apps/dashboard-lmps
```

Rotas do plugin devem iniciar com esse caminho.

---

### Entry

Ponto de entrada de um plugin.

Em microfrontends, pode apontar para um bundle ou remote entry.

Em iframes, deve apontar para uma URL HTTP/HTTPS.

---

### Render Mode

Modo de renderização declarado no manifesto.

Valores comuns:

- `embedded`;
- `federated`;
- `external`.

O conjunto permitido depende do tipo de plugin.

---

### Rota de plugin

Rota navegável associada a um app/plugin.

É persistida em `app_routes` e usada pelo Portal para menu e roteamento.

---

### `showInMenu`

Campo da rota que indica se ela deve aparecer no menu do Portal.

Uma rota pode existir e ser autorizada mesmo com `showInMenu=false`.

---

### `order`

Campo de ordenação usado pelo Portal para organizar itens de menu.

---

### Rollback de plugin

Operação que restaura um plugin para uma versão já registrada no histórico.

Restaura manifesto, versão ativa, permissões e rotas conforme a versão alvo.

---

## 5. Frontend e experiência do usuário

### Menu dinâmico

Menu montado pelo Portal a partir de `/me/apps`.

A Core API retorna apenas apps e rotas autorizados para o usuário atual.

---

### App Authorization

Processo de filtrar apps e rotas conforme permissões efetivas do usuário.

Na Core API, essa filtragem é feita pelo `AppAuthorizationService`.

---

### Favorito

App marcado por um usuário para acesso rápido no Portal.

É persistido por usuário na tabela `user_favorite_apps`.

---

### Notificação

Mensagem persistida para um usuário.

Pode ser listada pelo Portal e marcada como lida.

---

### Socket.IO

Canal de comunicação em tempo real usado pela Core API para enviar eventos ao Portal.

É usado para refletir mudanças administrativas, favoritos, notificações e alterações de RBAC sem depender apenas de reload manual.

---

### Evento administrativo

Evento emitido pela Core API após uma alteração relevante.

Exemplos:

- plugin registrado;
- role alterada;
- favorito adicionado;
- permissão substituída;
- rota removida.

---

## 6. Banco de dados e persistência

### PostgreSQL Core

Banco principal da Core API.

Serviço Docker: `postgres-core`.

Armazena governança da plataforma.

---

### PostgreSQL Plugins

Banco usado para plugins e domínios operacionais.

Serviço Docker: `postgres-plugins`.

Consumidor principal: API DELPI.

---

### Keycloak DB

Banco interno do Keycloak.

Serviço Docker: `keycloak-db`.

Não deve ser acessado diretamente pela aplicação para regras de negócio.

---

### Migration

Arquivo que versiona alterações de schema do banco.

Na Core API, migrations são feitas com Flask-Migrate/Alembic.

---

### Seed

Carga inicial controlada pela aplicação.

Na Core API, usado para permissões base do sistema.

---

### Auditoria

Registro de ações relevantes da plataforma.

Deve ser usada especialmente para ações administrativas, alterações de RBAC, plugins e operações sensíveis.

---

## 7. Infraestrutura e operação

### Docker Compose

Ferramenta usada para subir a stack local e a stack de produção descrita nos arquivos `infra/docker-compose*.yml`.

---

### Container

Unidade de execução isolada de cada serviço.

Exemplos:

- `delpi-core-api`;
- `delpi-portal`;
- `delpi-keycloak`;
- `delpi-gateway`.

---

### Volume

Armazenamento persistente usado por containers.

Exemplos:

- `postgres_core_data`;
- `keycloak_data`;
- `postgres_plugins_data`.

---

### Rede Docker

Rede interna usada para comunicação entre containers.

Na Minha DELPI, a rede principal é `delpi-network`.

---

### Ambiente DEV

Ambiente de desenvolvimento local.

Usa Docker Compose dev, volumes de código e serviços acessíveis localmente.

---

### Ambiente PROD

Ambiente de produção ou execução próxima de produção.

Usa Dockerfiles de produção, menos volumes de código e serviços atrás do Gateway.

---

### Variável de ambiente

Configuração externa usada por containers e aplicações.

Exemplos:

- `KEYCLOAK_ISSUER`;
- `KEYCLOAK_AUDIENCE`;
- `DB_HOST`;
- `VITE_KC_URL`.

---

## 8. Desenvolvimento e arquitetura

### Clean Architecture

Organização do código em camadas com responsabilidades separadas.

Na Core API:

- `domain`;
- `application`;
- `interfaces`;
- `infrastructure`.

---

### Domain

Camada de regras de negócio puras.

Não deve depender de Flask, SQLAlchemy ou detalhes de infraestrutura.

---

### Application

Camada de casos de uso.

Orquestra regras, repositories, services e eventos.

---

### Interfaces

Camada de entrada e adaptação.

Inclui controllers HTTP, handlers Socket.IO e outras interfaces externas.

---

### Infrastructure

Camada de detalhes técnicos.

Inclui banco, SQLAlchemy, configurações, JWT, providers e integrações.

---

### Use Case

Caso de uso da aplicação.

Representa uma ação de negócio, como registrar plugin, listar apps, adicionar role a usuário ou marcar notificação como lida.

---

### Repository

Componente responsável por acessar dados.

Use cases devem acessá-los via Unit of Work, não diretamente por SQLAlchemy.

---

### Unit of Work

Fronteira transacional da Core API.

Agrupa repositories, controla commit/rollback e publica eventos após commit.

---

### DTO

Data Transfer Object.

Estrutura usada para transportar dados entre camadas ou para resposta de API.

---

## 9. Termos de domínio operacional

### TOTVS

Sistema corporativo externo integrado pela API DELPI.

As variáveis `TOTVS_DB_*` configuram conexão da API DELPI com esse datasource.

---

### Portal RH

Banco ou sistema corporativo de RH integrado pela API DELPI, quando configurado.

As variáveis `PORTAL_RH_DB_*` indicam essa integração.

---

### Qualidade

Domínio/plugin operacional relacionado a processos de qualidade.

A documentação oficial possui especificações para módulos de qualidade, como não conformidade externa.

---

## 10. Convenções de nomenclatura

| Termo preferido | Evitar / legado | Observação |
|---|---|---|
| Minha DELPI | DELPI Central | DELPI Central aparece em documentos legados |
| Core API | core, backend central | Usar Core API para governança |
| API DELPI | api operacional | Usar API DELPI para backend operacional |
| Portal | frontend, shell | Portal é o shell React |
| Plugin System | registry de apps | Sistema oficial de manifestos |
| Permission code | permissão string | Código estável da permissão |
| App | plugin registrado | Entidade persistida em `apps` |

---

## 11. Documentos relacionados

```text
docs/00-visao-geral/minha-delpi-visao-geral.md
docs/00-visao-geral/mapa-da-plataforma.md
docs/01-arquitetura/arquitetura-geral.md
docs/02-infraestrutura/docker-compose.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/manifesto-plugin.md
```
