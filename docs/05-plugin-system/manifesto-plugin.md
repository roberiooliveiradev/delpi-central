# Minha DELPI — Manifesto de Plugin

> **Arquivo:** `docs/05-plugin-system/manifesto-plugin.md`  
> **Status:** documentação oficial (maio/2026)  

**Exemplos de plugin id no repositório:** `strategic-indicators` (microfrontend), `dash-lmps` (iframe, `basePath` `/dash-lmps`). Trechos genéricos com `dashboard-lmps` ilustram MFE — não confundir com o manifesto atual de LMPs.
> **Produto:** Minha DELPI  
> **Escopo:** contrato JSON de manifesto, validações e regras de domínio do Plugin System

---

## 1. Objetivo

Este documento descreve o contrato de **manifesto de plugin** da Minha DELPI.

**Operação:** [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md) · **Inventário:** [../08-plugins/README.md](../08-plugins/README.md)

O manifesto é o arquivo JSON usado para registrar plugins, microfrontends, iframes e módulos backend-only na Core API.

Ele define:

- identidade do plugin;
- nome e descrição;
- versão;
- tipo;
- base path;
- entry point;
- permissões;
- rotas;
- backend opcional;
- metadados de UI;
- dependências;
- informações de ciclo de vida, segurança e observabilidade.

O manifesto é validado pela Core API antes de qualquer plugin ser registrado ou atualizado.

---

## 2. Papel do manifesto

O manifesto é o contrato entre o plugin e a plataforma.

Ele permite que a Core API saiba:

- qual app deve ser criado;
- quais permissões pertencem ao plugin;
- quais rotas devem aparecer no Portal;
- qual entry point deve ser carregado;
- qual tipo de renderização deve ser usado;
- se o plugin possui backend;
- se existem dependências entre plugins;
- qual versão está sendo registrada.

Sem manifesto válido, o plugin não deve ser registrado na Minha DELPI.

---

## 3. Versão suportada

### 3.1 Schema vigente em produção (`1.0.0`)

```json
{
  "schemaVersion": "1.0.0"
}
```

Qualquer manifesto com outra versão **não listada abaixo** deve ser rejeitado pelo resolvedor de versão.

Regra atual:

```text
schemaVersion = 1.0.0 → v1
```

### 3.2 Evolução planejada (`1.1.0`)

A especificação **1.1.0** formaliza tipos `plugin` / `module`, `routes[].target`, `menuGroup` e `ui.module`. **Ainda não implementada** na Core API nem no Portal.

| Documento | Conteúdo |
|---|---|
| [manifest-schema-1.1.0.md](./manifest-schema-1.1.0.md) | Contrato JSON completo |
| [plugin-vs-module.md](./plugin-vs-module.md) | Visão arquitetural |
| [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md) | Fases de implementação |

Manifests `1.0.0` **não** exigem migração imediata. Aliases `microfrontend` / `iframe` continuam válidos até adoção do 1.1.0.

---

## 4. Tipos de plugin suportados

### 4.1 Tipos em produção (`1.0.0`)

```text
microfrontend
iframe
backend-only
```

| Tipo | Descrição |
|---|---|
| `microfrontend` | Plugin frontend carregado de forma integrada ao Portal |
| `iframe` | Aplicação externa ou interna renderizada via iframe |
| `backend-only` | Plugin sem UI, usado para registrar permissões/backend/integração |

### 4.2 Tipos planejados (`1.1.0`)

| `type` | Descrição |
|---|---|
| `plugin` | App autônomo (substitui semanticamente `microfrontend` / `iframe`) |
| `module` | Shell agregador com `routes[].target` |
| `backend-only` | Inalterado |

Ver [plugin-vs-module.md](./plugin-vs-module.md) §2.

---

## 5. Pipeline de validação

O manifesto passa por um pipeline de validação na Core API.

Fluxo:

```text
Manifesto recebido
  ↓
ManifestNormalizer
  ↓
ManifestVersionResolver
  ↓
JSON Schema Draft 2020-12
  ↓
Strategy por tipo
  ↓
Regras de domínio
  ↓
ValidationResult
```

Etapas:

1. Normalização automática.
2. Resolução da versão do schema.
3. Validação estrutural por JSON Schema.
4. Validação específica por tipo de plugin.
5. Validação semântica de regras de domínio.

---

## 6. Normalização automática

Antes da validação, a Core API normaliza alguns campos.

Regras atuais:

- `id` é convertido para string, removido espaço e transformado em lowercase;
- se `routes` for `null`, vira lista vazia;
- se `permissions` for `null`, vira lista vazia;
- `entry` global string é trimado; string vazia vira `null`;
- `routes[].entry` string é trimado; string vazia vira `null`;
- `backend.issuer` e `backend.audience` são convertidos para string e trimados.

Exemplo:

```json
{
  "id": " Dashboard-LMPs ",
  "entry": "  "
}
```

Após normalização conceitual:

```json
{
  "id": "dashboard-lmps",
  "entry": null
}
```

---

## 7. Campos obrigatórios globais

O schema exige os seguintes campos:

```json
[
  "schemaVersion",
  "id",
  "name",
  "version",
  "type",
  "basePath",
  "permissions"
]
```

Tabela:

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `schemaVersion` | Sim | Versão do contrato do manifesto |
| `id` | Sim | Identificador único do plugin |
| `name` | Sim | Nome legível do plugin |
| `description` | Não | Descrição do plugin |
| `category` | Não | Categoria de agrupamento |
| `version` | Sim | Versão do plugin |
| `icon` | Não | Ícone exibido no Portal |
| `type` | Sim | Tipo do plugin |
| `basePath` | Sim | Caminho base do plugin |
| `entry` | Depende | Entry point global |
| `healthcheck` | Não | URL/rota de healthcheck |
| `dependencies` | Não | Lista de plugins dependidos |
| `permissions` | Sim | Permissões declaradas pelo plugin |
| `routes` | Depende | Rotas de navegação |
| `backend` | Depende | Configuração de backend |
| `features` | Não | Flags ou recursos opcionais |
| `lifecycle` | Não | Metadados de ciclo de vida |
| `security` | Não | Metadados de segurança |
| `observability` | Não | Metadados de observabilidade |
| `ui` | Depende | Configurações de UI |
| `metadata` | Não | Metadados livres |

O schema não permite propriedades extras no nível raiz.

---

## 8. Campo `id`

O `id` identifica o plugin na plataforma.

Regras:

- obrigatório;
- string;
- mínimo 1 caractere;
- máximo 50 caracteres;
- deve ser lowercase;
- pode conter números;
- pode conter hífen;
- não deve conter espaços;
- não deve conter acentos;
- não deve conter underscore.

Regex de domínio:

```regex
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

Exemplos válidos:

```text
dashboard-lmps
strategic-indicators
qualidade
api-delpi
```

Exemplos inválidos:

```text
DashboardLMPs
 dashboard-lmps
mini_app
app--teste
app teste
```

---

## 9. Campo `name`

Nome legível do plugin.

Regras:

- obrigatório;
- string;
- mínimo 1 caractere;
- máximo 150 caracteres.

Exemplo:

```json
{
  "name": "Dashboard LMPs"
}
```

---

## 10. Campo `description`

Descrição textual do plugin.

Regras:

- opcional;
- string.

Exemplo:

```json
{
  "description": "Painel de acompanhamento de LMPs."
}
```

---

## 11. Campo `version`

Versão do plugin.

Apesar do JSON Schema aceitar SemVer com sufixo pré-release, as regras de domínio atuais restringem o formato para:

```text
MAJOR.MINOR.PATCH
```

Regex efetiva de domínio:

```regex
^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$
```

Exemplos válidos:

```text
1.0.0
2.1.0
10.4.3
```

Exemplos inválidos no contrato efetivo atual:

```text
1.0
1.0.0-beta
v1.0.0
01.0.0
```

Ponto de atenção:

> O JSON Schema permite pré-release, mas as regras de domínio rejeitam. Portanto, o contrato efetivo atual não aceita pré-release.

---

## 12. Campo `type`

Define o tipo do plugin.

Valores aceitos:

```text
microfrontend
iframe
backend-only
```

Regras variam conforme o tipo.

---

## 13. Campo `basePath`

Define o caminho base do plugin na plataforma.

Regras:

- obrigatório;
- deve começar com `/`;
- deve conter apenas letras minúsculas, números, hífen e `/`;
- não pode ser apenas `/`.

Regex de domínio:

```regex
^/[-a-z0-9/]*$
```

Exemplos válidos:

```text
/apps/dashboard-lmps
/apps/strategic-indicators
/apps/api-delpi
```

Exemplos inválidos:

```text
apps/dashboard-lmps
/
/Apps/Dashboard
/apps/dashboard_lmps
/apps/dashboard lmps
```

---

## 14. Campo `entry`

Define o entry point global do plugin.

A obrigatoriedade depende do tipo.

| Tipo | `entry` |
|---|---|
| `microfrontend` | Obrigatório no contrato efetivo atual |
| `iframe` | Obrigatório no contrato efetivo atual |
| `backend-only` | Não permitido; deve ser `null` ou ausente |

Observação:

> Algumas strategies aceitam entry global ou `routes[].entry`, mas as regras de domínio atuais exigem `entry` global para `microfrontend` e `iframe`. Portanto, o contrato efetivo deve considerar `entry` global obrigatório para plugins visuais.

---

## 15. Campo `ui.renderMode`

Define o modo de renderização.

Valores globais do schema:

```text
embedded
external
federated
```

Mas os valores permitidos dependem do tipo.

| Tipo | Valores permitidos |
|---|---|
| `iframe` | `embedded`, `external` |
| `microfrontend` | `embedded`, `federated` |
| `backend-only` | `ui` não permitido |

Exemplo microfrontend federado:

```json
{
  "ui": {
    "renderMode": "federated"
  }
}
```

Exemplo iframe externo:

```json
{
  "ui": {
    "renderMode": "external"
  }
}
```

---

## 16. Permissões

O campo `permissions` declara permissões pertencentes ao plugin.

Regras do schema:

- obrigatório;
- array;
- mínimo 1 item;
- cada item deve ter `code`, `name` e `module`.

Estrutura:

```json
{
  "code": "dashboard-lmps.access",
  "name": "Acessar Dashboard LMPs",
  "description": "Permite acessar o dashboard de LMPs.",
  "module": "dashboard-lmps"
}
```

---

## 17. Regras de permission code

Regex de domínio:

```regex
^[a-z][a-z0-9-]*\.[a-z0-9-]+(?:\.[a-z0-9-]+)*$
```

Formato recomendado:

```text
<module>.<resource>.<action>
```

Ou, para acesso simples:

```text
<module>.access
```

Exemplos válidos:

```text
dashboard-lmps.access
crm.leads.read
crm.leads.write
qualidade.relatorio.view
```

Exemplos inválidos:

```text
Dashboard.access
access
module_access
module..access
1module.access
```

---

## 18. Regra de `permissions[].module`

As regras de domínio exigem que `permissions[].module` seja igual ao `id` do plugin.

Exemplo válido:

```json
{
  "id": "dashboard-lmps",
  "permissions": [
    {
      "code": "dashboard-lmps.access",
      "name": "Acessar Dashboard LMPs",
      "module": "dashboard-lmps"
    }
  ]
}
```

Exemplo inválido:

```json
{
  "id": "dashboard-lmps",
  "permissions": [
    {
      "code": "dashboard-lmps.access",
      "name": "Acessar Dashboard LMPs",
      "module": "system"
    }
  ]
}
```

Erro esperado:

```text
permission_module_mismatch
```

---

## 19. Rotas

O campo `routes` declara rotas navegáveis do plugin.

Para `microfrontend` e `iframe`, rotas são obrigatórias.

Para `backend-only`, rotas não são permitidas.

Estrutura de rota:

```json
{
  "path": "/apps/dashboard-lmps",
  "label": "Dashboard LMPs",
  "icon": "bar-chart3",
  "entry": null,
  "permission": "dashboard-lmps.access",
  "showInMenu": true,
  "order": 1,
  "menuGroup": "Dashboards"
}
```

Campos:

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `path` | Sim | Caminho da rota |
| `label` | Sim | Nome exibido no menu |
| `icon` | Não | Ícone da rota |
| `entry` | Não | Entry específico da rota |
| `permission` | Sim | Permissão exigida |
| `showInMenu` | Não | Indica se aparece no menu |
| `order` | Não | Ordem de exibição |
| `menuGroup` | Não | Agrupamento visual |

---

## 20. Regras de rota

Regras de domínio:

- `path` deve começar com `/`;
- `path` deve conter apenas letras minúsculas, números, hífen e `/`;
- `path` deve iniciar com `basePath`;
- não pode haver rotas duplicadas no manifesto;
- se a rota declarar `permission`, ela precisa existir em `permissions[].code`.

Exemplo válido:

```json
{
  "basePath": "/apps/dashboard-lmps",
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "permission": "dashboard-lmps.access"
    }
  ]
}
```

Exemplo inválido:

```json
{
  "basePath": "/apps/dashboard-lmps",
  "routes": [
    {
      "path": "/dashboard-lmps",
      "label": "Dashboard LMPs",
      "permission": "dashboard-lmps.access"
    }
  ]
}
```

Erro esperado:

```text
route_outside_base_path
```

---

## 21. Backend

O campo `backend` descreve backend associado ao plugin.

Estrutura:

```json
{
  "backend": {
    "required": true,
    "serviceName": "api-delpi",
    "baseUrl": "/apps/api-delpi",
    "validateJwt": true,
    "audience": "delpi-central",
    "issuer": "http://localhost/auth/realms/delpi",
    "requiredPermissionsHeader": "X-Required-Permissions"
  }
}
```

Campos:

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `required` | Sim | Indica se backend é obrigatório |
| `serviceName` | Não | Nome lógico do serviço |
| `baseUrl` | Não | URL base do backend |
| `validateJwt` | Sim | Indica se backend valida JWT |
| `audience` | Condicional | Audience esperada pelo backend |
| `issuer` | Condicional | Issuer esperado pelo backend |
| `requiredPermissionsHeader` | Não | Header usado para permissões exigidas |

---

## 22. Regras para `backend-only`

Para plugin `backend-only`:

- `backend` é obrigatório;
- `backend.required` deve ser `true`;
- `routes` não são permitidas;
- `entry` não é permitido;
- `ui` não é permitido pelo schema;
- se `backend.validateJwt` for `true`, `issuer` e `audience` são obrigatórios.

Também há recomendação forte de declarar permissão:

```text
<plugin-id>.access
```

Exemplo:

```json
{
  "schemaVersion": "1.0.0",
  "id": "api-relatorios",
  "name": "API de Relatórios",
  "version": "1.0.0",
  "type": "backend-only",
  "basePath": "/apps/api-relatorios",
  "entry": null,
  "permissions": [
    {
      "code": "api-relatorios.access",
      "name": "Acessar API de Relatórios",
      "module": "api-relatorios"
    }
  ],
  "routes": [],
  "backend": {
    "required": true,
    "validateJwt": true,
    "issuer": "http://localhost/auth/realms/delpi",
    "audience": "delpi-central"
  }
}
```

---

## 23. Regras para `microfrontend`

Para plugin `microfrontend`:

- `entry` é obrigatório no contrato efetivo atual;
- `routes` é obrigatório e deve ter ao menos uma rota;
- `ui.renderMode` pode ser `embedded` ou `federated`;
- rotas devem iniciar com `basePath`;
- permissões usadas nas rotas devem estar declaradas em `permissions`.

Exemplo:

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs",
  "description": "Painel de acompanhamento de LMPs.",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/apps/dashboard-lmps",
  "entry": "/apps/dashboard-lmps/assets/remoteEntry.js",
  "icon": "bar-chart3",
  "ui": {
    "renderMode": "federated"
  },
  "permissions": [
    {
      "code": "dashboard-lmps.access",
      "name": "Acessar Dashboard LMPs",
      "description": "Permite acessar o dashboard de LMPs.",
      "module": "dashboard-lmps"
    }
  ],
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "icon": "bar-chart3",
      "permission": "dashboard-lmps.access",
      "showInMenu": true,
      "order": 1
    }
  ]
}
```

---

## 24. Regras para `iframe`

Para plugin `iframe`:

- `entry` é obrigatório no contrato efetivo atual;
- `entry` deve iniciar com `http://` ou `https://`;
- `routes` é obrigatório e deve ter ao menos uma rota;
- se usar `routes[].entry`, cada entry de rota também deve iniciar com `http://` ou `https://`;
- `ui.renderMode` pode ser `embedded` ou `external`;
- rotas devem iniciar com `basePath`.

Exemplo:

```json
{
  "schemaVersion": "1.0.0",
  "id": "sistema-externo",
  "name": "Sistema Externo",
  "version": "1.0.0",
  "type": "iframe",
  "basePath": "/apps/sistema-externo",
  "entry": "https://sistema.exemplo.com",
  "ui": {
    "renderMode": "embedded"
  },
  "permissions": [
    {
      "code": "sistema-externo.access",
      "name": "Acessar Sistema Externo",
      "module": "sistema-externo"
    }
  ],
  "routes": [
    {
      "path": "/apps/sistema-externo",
      "label": "Sistema Externo",
      "permission": "sistema-externo.access",
      "showInMenu": true,
      "order": 10
    }
  ]
}
```

---

## 25. Dependências

O campo `dependencies` permite declarar dependência de outros plugins.

Exemplo:

```json
{
  "dependencies": [
    "api-delpi",
    "dashboard-commercial"
  ]
}
```

Uso atual conhecido:

- o unregister de plugin verifica se outros manifestos dependem do plugin alvo;
- se houver dependentes, a remoção é bloqueada.

Erro esperado:

```text
plugin.has_dependents
```

---

## 26. Features, lifecycle, security, observability e metadata

O schema permite objetos livres para metadados:

```json
{
  "features": {},
  "lifecycle": {},
  "security": {},
  "observability": {},
  "metadata": {}
}
```

Esses campos são opcionais e podem ser usados para evolução futura.

Regra recomendada:

> Campos livres devem ser documentados pelo plugin quando usados. Não devem carregar regras críticas que a Core API não valida.

---

## 27. Erros de validação

A validação retorna erros no padrão:

```json
{
  "errors": [
    {
      "code": "invalid_plugin_id",
      "message": "Campo 'id' deve ser lowercase...",
      "path": "$.id"
    }
  ]
}
```

Códigos comuns:

| Código | Situação |
|---|---|
| `schema_validation_error` | Erro estrutural no JSON Schema |
| `unsupported_plugin_type` | Tipo de plugin inválido |
| `invalid_plugin_id` | ID fora do padrão |
| `invalid_version` | Versão fora do SemVer efetivo |
| `invalid_base_path` | Base path inválido |
| `invalid_permission_code` | Permission code inválido |
| `duplicate_permission_code_in_manifest` | Permissão duplicada |
| `permission_name_required` | Permission sem name |
| `permission_module_mismatch` | Module diferente do plugin id |
| `entry_required` | Entry obrigatório ausente |
| `routes_required` | Rotas obrigatórias ausentes |
| `invalid_route_path` | Path de rota inválido |
| `route_outside_base_path` | Rota fora do basePath |
| `duplicate_route_path_in_manifest` | Rota duplicada |
| `route_permission_not_declared` | Permissão da rota não declarada |
| `backend_only_cannot_have_routes` | Backend-only com rotas |
| `backend_only_entry_not_allowed` | Backend-only com entry |
| `backend_required` | Backend-only sem backend |
| `backend_required_must_be_true` | backend.required diferente de true |
| `backend_missing_issuer` | JWT backend sem issuer |
| `backend_missing_audience` | JWT backend sem audience |
| `missing_access_permission` | Backend-only sem `<id>.access` |

---

## 28. Registro de manifesto

Endpoint:

```http
POST /admin/apps/register
```

Permissão exigida:

```text
apps.manage
```

Fluxo:

```text
Recebe manifesto
  ↓
Valida manifesto
  ↓
Calcula checksum SHA-256
  ↓
Se plugin não existe:
    cria app
    salva manifesto vigente
    cria versão histórica
    cria permissões
    cria rotas
  ↓
Se plugin existe:
    verifica versão duplicada
    atualiza versão ativa
    salva novo manifesto
    cria versão histórica
    remove permissões e rotas antigas
    recria permissões e rotas
  ↓
Publica evento plugin_registered
```

---

## 29. Atualização de manifesto

Endpoint:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Permissão exigida:

```text
apps.manage
```

A atualização de manifesto é não estrutural.

Pode alterar:

- `name`;
- `description`;
- `icon`;
- `routes[].label`;
- `routes[].icon`;
- `routes[].order`;
- `routes[].showInMenu`.

Não pode alterar:

- `id`;
- `version`;
- `basePath`;
- conjunto de permissões;
- conjunto de rotas.

Mudança estrutural deve ser feita por novo registro de versão.

---

## 30. Versionamento

Cada registro de nova versão cria entrada em:

```text
app_versions
```

Campos principais:

```text
app_id
version
manifest
checksum
created_at
updated_at
```

Há constraint única:

```text
app_id + version
```

Portanto, não é permitido registrar duas vezes a mesma versão para o mesmo plugin.

---

## 31. Rollback

Endpoint:

```http
POST /admin/apps/<plugin_id>/rollback
```

Body:

```json
{
  "version": "1.0.0"
}
```

Fluxo:

```text
Busca plugin
  ↓
Busca versão histórica
  ↓
Obtém manifesto e checksum
  ↓
Atualiza versão ativa
  ↓
Salva manifesto restaurado
  ↓
Remove permissões e rotas atuais
  ↓
Recria permissões e rotas do manifesto restaurado
  ↓
Publica plugin_version_rolled_back
```

---

## 32. Unregister

Endpoint:

```http
DELETE /admin/apps/<plugin_id>
```

Fluxo:

```text
Verifica se plugin existe
  ↓
Verifica dependentes em manifests salvos
  ↓
Se houver dependentes, bloqueia
  ↓
Remove versões
  ↓
Remove rotas
  ↓
Remove permissões por module
  ↓
Remove manifesto
  ↓
Remove app
  ↓
Publica plugin_unregistered
```

---

## 33. Como o manifesto vira dados internos

Quando um manifesto é registrado, a Core API popula tabelas internas.

| Campo do manifesto | Tabela / campo interno |
|---|---|
| `id` | `apps.id` |
| `name` | `apps.name` |
| `description` | `apps.description` |
| `basePath` | `apps.base_path` |
| `icon` | `apps.icon` |
| `type` | `apps.type` |
| `version` | `apps.version` e `app_versions.version` |
| manifesto inteiro | `app_manifests.manifest` e `app_versions.manifest` |
| checksum | `app_manifests.checksum` e `app_versions.checksum` |
| `permissions[]` | `permissions` |
| `routes[]` | `app_routes` |

---

## 34. Como o Portal consome o manifesto

O Portal não consome diretamente o manifesto bruto.

Fluxo real:

```text
Manifesto registrado
  ↓
Core API salva app, rotas e manifesto
  ↓
Portal chama /me/apps
  ↓
Core API lista apps ativos com rotas
  ↓
Core API lê manifesto para entry/renderMode/routes[].entry
  ↓
Core API filtra por permissão
  ↓
Portal recebe DTO normalizado
```

Resposta conceitual:

```json
{
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs",
  "basePath": "/apps/dashboard-lmps",
  "icon": "bar-chart3",
  "type": "microfrontend",
  "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
  "renderMode": "federated",
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "permission": "dashboard-lmps.access",
      "label": "Dashboard LMPs",
      "showInMenu": true,
      "order": 1,
      "entry": null
    }
  ]
}
```

---

## 35. Checklist para criar novo plugin

Antes de registrar um plugin, verificar:

- [ ] `schemaVersion` é `1.0.0`.
- [ ] `id` está em lowercase e usa hífen se necessário.
- [ ] `version` segue `MAJOR.MINOR.PATCH`.
- [ ] `type` é `microfrontend`, `iframe` ou `backend-only`.
- [ ] `basePath` começa com `/` e não é `/`.
- [ ] `permissions` possui ao menos uma permissão.
- [ ] Cada permissão possui `code`, `name` e `module`.
- [ ] `module` das permissões é igual ao `id` do plugin.
- [ ] Rotas começam com `basePath`.
- [ ] Rotas não estão duplicadas.
- [ ] Permissões usadas nas rotas estão declaradas em `permissions`.
- [ ] `entry` está coerente com o tipo.
- [ ] `ui.renderMode` está coerente com o tipo.
- [ ] `backend-only` não declara rotas nem UI.
- [ ] Dependências, se existirem, usam IDs de plugins válidos.

---

## 36. Pontos de atenção

1. O contrato efetivo aceita apenas `schemaVersion: 1.0.0`.
2. O schema e as regras de domínio não são idênticos; as regras de domínio podem ser mais restritivas.
3. Pré-release em `version` não é aceito no contrato efetivo atual.
4. `permissions[].module` deve ser igual ao `id` do plugin.
5. Rotas devem iniciar com `basePath`.
6. Backend-only não pode ter rotas nem entry.
7. Atualização de manifesto não deve alterar estrutura.
8. Mudanças estruturais exigem nova versão via register.
9. Unregister bloqueia remoção se houver plugins dependentes.
10. O Portal recebe DTO normalizado, não o manifesto bruto.

---

## 37. Documentos relacionados

```text
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/05-plugin-system/microfrontends.md
docs/05-plugin-system/backend-only.md
docs/05-plugin-system/iframe.md
docs/04-core-api/visao-geral-core-api.md
docs/03-autenticacao-autorizacao/rbac.md
```

