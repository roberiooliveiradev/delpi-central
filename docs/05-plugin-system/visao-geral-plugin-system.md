# Minha DELPI — Visão Geral do Plugin System

> **Arquivo:** `docs/05-plugin-system/visao-geral-plugin-system.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** visão geral do sistema de plugins, manifesto, registro, persistência, autorização e consumo pelo Portal

---

## 1. Objetivo

Este documento apresenta a visão geral do **Plugin System** da Minha DELPI.

O Plugin System é o mecanismo que permite registrar módulos plugáveis na plataforma por meio de manifesto declarativo. Ele conecta:

- Core API;
- Portal Frontend;
- RBAC;
- banco `postgres-core`;
- Gateway;
- microfrontends;
- iframes;
- backends governados pela plataforma.

Este documento é uma visão panorâmica. Detalhes específicos estão nos documentos individuais da pasta `docs/05-plugin-system`.

**Evolução jun/2026:** distinção formal **plugin** (app autônomo) vs **módulo** (shell agregador) — ver [plugin-vs-module.md](./plugin-vs-module.md) e [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md).

---

## 2. Conceito

Um plugin é um módulo registrado na Minha DELPI por meio de um manifesto JSON.

Esse manifesto declara:

- identidade do plugin;
- versão;
- tipo de integração;
- path base;
- entry point;
- permissões;
- rotas;
- backend opcional;
- dependências;
- metadados.

Depois de registrado, o plugin passa a fazer parte da governança da plataforma.

Isso significa que ele pode:

- aparecer no menu do Portal;
- ter rotas filtradas por permissão;
- declarar permissões próprias;
- ser ativado ou desativado;
- possuir versões históricas;
- sofrer rollback;
- ser consumido por usuários conforme RBAC.

---

## 3. Fonte de verdade

O contrato oficial do plugin é o manifesto validado pela Core API.

A verdade operacional é composta por:

```text
delpi.manifest.schema.json
normalizers
version resolver
manifest validator
strategies por tipo
regras de domínio
use cases de registro/versionamento
tabelas apps/app_routes/app_manifests/app_versions/permissions
```

Documentações antigas que mencionem contrato incompatível com o schema atual não devem ser usadas como referência final.

---

## 4. Versão oficial do manifesto

A versão oficial do contrato vigente é:

```json
{
  "schemaVersion": "1.0.0"
}
```

Versões diferentes devem ser rejeitadas pelo pipeline atual de validação.

---

## 5. Tipos de plugin suportados

A Minha DELPI suporta três tipos principais de plugin:

```text
microfrontend
iframe
backend-only
```

| Tipo | Possui UI | Uso principal |
|---|---:|---|
| `microfrontend` | Sim | Módulo frontend integrado ao Portal |
| `iframe` | Sim | Sistema externo ou legado renderizado por URL |
| `backend-only` | Não | API, integração ou serviço backend governado |

---

## 6. Microfrontend

Um plugin `microfrontend` representa uma aplicação frontend integrada ao shell do Portal.

Uso típico:

- dashboards internos;
- módulos React/Vite;
- aplicações plugáveis novas;
- módulos com experiência integrada.

Características:

- possui rotas;
- declara permissões;
- possui entry point;
- pode usar `renderMode` `embedded` ou `federated`;
- depende do Gateway para servir assets;
- é carregado pelo Portal com base em `/me/apps`.

---

## 7. Iframe

Um plugin `iframe` representa uma aplicação carregada por URL.

Uso típico:

- sistemas legados;
- sistemas externos;
- ferramentas SaaS;
- integrações rápidas;
- aplicações que não foram convertidas para microfrontend.

Características:

- possui rotas;
- declara permissões;
- `entry` deve ser URL absoluta `http://` ou `https://`;
- pode usar `renderMode` `embedded` ou `external`;
- depende de headers compatíveis para ser embutido.

---

## 8. Backend-only

Um plugin `backend-only` representa um serviço sem interface visual.

Uso típico:

- APIs internas;
- integrações com ERP;
- serviços auxiliares de plugins;
- backends governados por RBAC;
- serviços que precisam declarar permissões e dependências.

Características:

- não deve ter UI;
- `entry` deve ser `null`;
- `routes` deve ser array vazio;
- `backend` é obrigatório;
- `backend.required` deve ser `true`;
- se validar JWT, deve declarar issuer e audience;
- não aparece como rota navegável no Portal.

---

## 9. Fluxo geral do Plugin System

Fluxo simplificado:

```text
Plugin é desenvolvido
  ↓
Plugin publica assets/backend
  ↓
Manifesto é escrito
  ↓
Administrador registra manifesto na Core API
  ↓
Core API valida schema, strategy e regras de domínio
  ↓
Core API persiste app, manifesto, versão, permissões e rotas
  ↓
Usuários recebem permissões via RBAC
  ↓
Portal chama /me/apps
  ↓
Core API retorna apps/rotas autorizados
  ↓
Portal monta menu e carrega plugin
```

---

## 10. Registro do plugin

Endpoint administrativo:

```http
POST /admin/apps/register
```

Permissão esperada:

```text
apps.manage
```

Responsabilidade:

- registrar plugin novo;
- registrar nova versão de plugin existente;
- validar manifesto;
- criar ou atualizar app;
- salvar manifesto vigente;
- criar versão histórica;
- criar permissões;
- criar rotas;
- emitir evento administrativo.

---

## 11. Persistência no banco

O Plugin System usa tabelas do `postgres-core`.

Tabelas principais:

```text
apps
app_routes
app_manifests
app_versions
permissions
```

Relacionamento conceitual:

```text
apps
  ├── app_routes
  ├── app_manifests
  └── app_versions

app_routes
  └── permissions
```

---

## 12. Tabela `apps`

A tabela `apps` guarda a identidade principal do plugin.

Campos relevantes:

```text
id
name
description
base_path
icon
type
version
active
created_at
updated_at
```

O `id` é string e deve ser estável ao longo da vida do plugin.

---

## 13. Tabela `app_routes`

A tabela `app_routes` guarda as rotas navegáveis do plugin.

Campos relevantes:

```text
app_id
path
label
icon
order
show_in_menu
active
permission_id
```

Essas rotas são usadas pela Core API para montar a resposta de `/me/apps`.

---

## 14. Tabela `app_manifests`

A tabela `app_manifests` guarda o manifesto vigente completo.

Campos:

```text
app_id
manifest
checksum
created_at
updated_at
```

Ela permite que a Core API mantenha o contrato completo do plugin, mesmo quando parte dele também é normalizada em tabelas relacionais.

---

## 15. Tabela `app_versions`

A tabela `app_versions` guarda o histórico versionado dos manifestos.

Campos relevantes:

```text
app_id
version
manifest
checksum
created_at
updated_at
```

Ela é usada para:

- listar versões;
- impedir versão duplicada;
- executar rollback;
- manter histórico estrutural.

---

## 16. Permissões de plugin

Permissões declaradas no manifesto são persistidas em `permissions`.

Cada permissão deve possuir:

```text
code
name
module
```

`description` é opcional.

Regra crítica:

```text
permissions.module = plugin_id
```

Essa regra permite que register, rollback e unregister saibam quais permissões pertencem a cada plugin.

---

## 17. Rotas e permissões

Uma rota pode declarar uma permissão por código no manifesto.

Exemplo:

```json
{
  "path": "/apps/dashboard-lmps",
  "label": "Dashboard LMPs",
  "permission": "dashboard-lmps.access"
}
```

Durante o registro, a Core API resolve o código de permissão para o `permission_id` da tabela `app_routes`.

Em runtime, a resposta de `/me/apps` expõe a permissão como código, não como UUID.

---

## 18. Manifesto vigente versus dados normalizados

O Plugin System mantém dois formatos de persistência ao mesmo tempo:

| Origem | Destino |
|---|---|
| `manifest.id`, `name`, `version`, `type`, `basePath`, `icon` | `apps` |
| `manifest.routes[]` | `app_routes` |
| `manifest.permissions[]` | `permissions` |
| manifesto completo | `app_manifests` |
| snapshot versionado | `app_versions` |

Isso garante consultas eficientes e preservação integral do contrato.

---

## 19. Validação de manifesto

A validação ocorre em camadas:

```text
normalização
  ↓
resolução de schemaVersion
  ↓
JSON Schema
  ↓
strategy por tipo
  ↓
regras de domínio
```

A normalização ajusta valores simples antes da validação, como `id`, `routes`, `permissions`, `entry`, `backend.issuer` e `backend.audience`.

---

## 20. Regras por tipo

### 20.1 Microfrontend

Regras principais:

- precisa de rotas;
- precisa de `entry` global ou `routes[].entry`;
- `ui.renderMode` pode ser `embedded` ou `federated`.

### 20.2 Iframe

Regras principais:

- precisa de rotas;
- precisa de `entry` global ou `routes[].entry`;
- toda entry usada deve começar com `http://` ou `https://`;
- `ui.renderMode` pode ser `embedded` ou `external`.

### 20.3 Backend-only

Regras principais:

- `entry` deve ser `null`;
- `routes` deve ser `[]`;
- `backend` é obrigatório;
- `backend.required` deve ser `true`;
- se `validateJwt=true`, `issuer` e `audience` são obrigatórios;
- `ui` não é permitida.

---

## 21. Atualização de manifesto

Há dois tipos de alteração.

### 21.1 Atualização não estrutural

Endpoint:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Uso:

- alterar nome;
- alterar descrição;
- alterar ícone;
- alterar label de rota;
- alterar ícone de rota;
- alterar ordem;
- alterar `showInMenu`.

Não deve alterar versão, basePath, permissões ou conjunto de rotas.

### 21.2 Nova versão

Endpoint:

```http
POST /admin/apps/register
```

Uso:

- alterar rotas;
- alterar permissões;
- alterar basePath;
- alterar contrato do backend;
- alterar estrutura do plugin;
- publicar nova versão SemVer.

---

## 22. Rollback

Endpoint:

```http
POST /admin/apps/<plugin_id>/rollback
```

O rollback restaura uma versão histórica em `app_versions`.

Efeitos esperados:

- atualiza `apps.version`;
- restaura `app_manifests`;
- remove rotas atuais;
- remove permissões do módulo;
- recria permissões;
- recria rotas;
- publica evento administrativo.

Atenção:

> Rollback restaura o contrato da Core API, mas não garante que assets antigos ainda estejam disponíveis no Gateway.

---

## 23. Ativação e desativação

Plugins possuem campo:

```text
apps.active
```

Quando `active=false`, o app não deve aparecer no fluxo comum de `/me/apps`.

A ativação/desativação permite remover um plugin da experiência do usuário sem apagar histórico, manifesto ou versões.

---

## 24. Unregister

A remoção completa de plugin deve remover:

- versões;
- rotas;
- permissões do módulo;
- manifesto;
- app.

Antes de remover, a Core API deve verificar dependências declaradas em outros manifestos.

Se houver dependentes, a remoção deve ser bloqueada.

---

## 25. Dependências entre plugins

O manifesto pode declarar:

```json
{
  "dependencies": ["api-delpi"]
}
```

Isso permite que a plataforma saiba que um plugin depende de outro.

Uso:

- impedir unregister de plugin usado por outro;
- documentar acoplamentos;
- apoiar evolução futura de healthchecks e orquestração.

---

## 26. Integração com RBAC

Plugins declaram permissões, mas não concedem acesso automaticamente a usuários.

Fluxo:

```text
Plugin declara permissions
  ↓
Core API cria permissions
  ↓
Administrador associa permissions a roles/grupos
  ↓
PermissionResolver calcula permissões efetivas
  ↓
AppAuthorizationService filtra rotas
  ↓
Portal mostra apenas apps autorizados
```

---

## 27. Integração com Portal

O Portal consome plugins por:

```http
GET /me/apps
```

A Core API retorna apenas apps e rotas autorizados.

O Portal usa:

```text
app.type
app.entryUrl
app.renderMode
route.path
route.entry
route.showInMenu
route.order
```

para montar menu e renderizar o plugin.

---

## 28. Integração com Gateway

O registro de um plugin na Core API não publica assets automaticamente.

O Gateway precisa estar configurado para servir o `basePath` e o `entry` do plugin.

Exemplo conceitual:

```text
/apps/dashboard-lmps/* → dashboard-lmps
/apps/api-delpi/*      → api-delpi
```

Se o Gateway não expuser o path correto, o plugin pode aparecer no menu, mas falhar ao carregar.

---

## 29. Eventos administrativos

Operações do Plugin System devem emitir eventos administrativos.

Eventos comuns:

```text
plugin_registered
plugin_manifest_updated
plugin_version_rolled_back
plugin_unregistered
plugin_activated
plugin_deactivated
route_created
route_updated
route_deleted
```

O Portal pode reagir a esses eventos recarregando `/me/apps`.

---

## 30. Boas práticas

1. Manter `id` estável.
2. Usar `schemaVersion: "1.0.0"`.
3. Versionar com SemVer.
4. Usar `module = plugin_id` nas permissões.
5. Declarar permissão de acesso principal.
6. Manter rotas dentro de `basePath`.
7. Não usar campos fora do schema.
8. Usar `backend-only` para serviços sem UI.
9. Usar `microfrontend` para módulos integrados novos.
10. Usar `iframe` para sistemas externos ou legados.
11. Validar JWT em backends protegidos.
12. Garantir que o Gateway publique os paths necessários.
13. Não conceder acesso diretamente pelo frontend.
14. Usar RBAC para governar acesso.
15. Testar `/me/apps` após registro.

---

## 31. Checklist para novo plugin

Manifesto e registro:

- [ ] Manifesto usa `schemaVersion: "1.0.0"`.
- [ ] `id` está em lowercase e é estável.
- [ ] `version` segue SemVer.
- [ ] `type` é suportado.
- [ ] `basePath` começa com `/`.
- [ ] `permissions` possui ao menos uma permissão.
- [ ] Cada permissão tem `code`, `name` e `module`.
- [ ] `module` é igual ao `plugin_id`.
- [ ] Rotas declaram permissões existentes.
- [ ] Gateway serve o path do plugin.
- [ ] Plugin foi registrado via Core API.
- [ ] Permissões foram atribuídas a roles/grupos.
- [ ] `/me/apps` retorna o plugin para usuário autorizado.
- [ ] Portal carrega o plugin sem erro.

**Microfrontend (`type: microfrontend`):** checklist técnico adicional em [novo-plugin-mfe-checklist.md](./novo-plugin-mfe-checklist.md) — Module Federation, `preparePluginUiRemote()`, Dockerfile sem `COPY plugin-ui`, compose `plugin-ui-federated`.

---

## 32. Documentos relacionados

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/novo-plugin-mfe-checklist.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/05-plugin-system/microfrontends.md
docs/05-plugin-system/backend-only.md
docs/05-plugin-system/iframe.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/09-banco-de-dados/modelo-plugin-system.md
```
