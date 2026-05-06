# Minha DELPI — Registro de Plugin

> **Arquivo:** `docs/05-plugin-system/registro-de-plugin.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** fluxo técnico de registro de plugins na Core API

---

## 1. Objetivo

Este documento descreve como funciona o registro de plugins na **Minha DELPI**.

O registro de plugin é o processo pelo qual a Core API recebe um manifesto JSON, valida seu contrato, cria ou atualiza o app correspondente, registra permissões, cria rotas, salva o manifesto vigente e mantém histórico versionado.

Este documento complementa:

```text
docs/05-plugin-system/manifesto-plugin.md
```

---

## 2. Visão geral

Um plugin só passa a existir na plataforma depois de ser registrado na Core API.

O registro transforma um manifesto em dados persistidos nas tabelas centrais:

```text
apps
app_manifests
app_versions
permissions
app_routes
```

Fluxo macro:

```text
Manifesto JSON
  ↓
POST /admin/apps/register
  ↓
ManifestValidator
  ↓
Checksum SHA-256
  ↓
Cria ou atualiza plugin
  ↓
Cria versão histórica
  ↓
Cria permissões
  ↓
Cria rotas
  ↓
Publica evento plugin_registered
```

---

## 3. Endpoint

Endpoint de registro:

```http
POST /admin/apps/register
```

Blueprint:

```text
admin_apps_bp
```

Prefixo:

```text
/admin/apps
```

Controller:

```text
app/interfaces/http/apps_controller.py
```

Use case:

```text
app/application/use_cases/register_plugin_use_case.py
```

Permissão exigida:

```text
apps.manage
```

---

## 4. Contrato da requisição

O body da requisição deve ser um JSON válido contendo o manifesto do plugin.

Exemplo mínimo para microfrontend:

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

Se o body não for um objeto JSON, a API deve retornar erro de validação.

---

## 5. Resposta de sucesso

Quando o registro é concluído com sucesso:

```json
{
  "ok": true
}
```

Status HTTP:

```text
201 Created
```

---

## 6. Resposta de erro

Se a validação falhar:

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

Status HTTP:

```text
400 Bad Request
```

Se a versão já existir para o plugin:

```json
{
  "errors": [
    {
      "code": "plugin.version_already_exists",
      "message": "This version is already registered",
      "path": "$.version"
    }
  ]
}
```

---

## 7. Validações executadas

O registro usa o `ManifestValidator`.

Pipeline:

```text
ManifestNormalizer
  ↓
ManifestVersionResolver
  ↓
JSON Schema Draft 2020-12
  ↓
Strategy por tipo
  ↓
validate_manifest_rules
```

Validações principais:

- `schemaVersion` deve ser suportado;
- `id` deve seguir padrão de plugin id;
- `version` deve seguir SemVer efetivo;
- `type` deve ser suportado;
- `basePath` deve ser válido;
- `permissions` deve existir e ser coerente;
- `permissions[].module` deve ser igual ao `id`;
- rotas devem iniciar com `basePath`;
- permissões usadas nas rotas devem estar declaradas;
- regras específicas por tipo devem ser cumpridas.

---

## 8. Cálculo de checksum

Após validação, o use case calcula um checksum SHA-256 do manifesto.

Lógica conceitual:

```python
hashlib.sha256(
    json.dumps(manifest, sort_keys=True).encode("utf-8")
).hexdigest()
```

Esse checksum é salvo em:

```text
app_manifests.checksum
app_versions.checksum
```

Finalidades:

- identificar conteúdo exato do manifesto registrado;
- permitir comparação entre versões;
- manter histórico auditável;
- apoiar rollback e diagnóstico.

---

## 9. Cenário 1 — Plugin novo

Quando o plugin ainda não existe em `apps`, o registro cria todos os dados iniciais.

Fluxo:

```text
Plugin não existe
  ↓
Cria registro em apps
  ↓
Salva manifesto vigente em app_manifests
  ↓
Cria versão em app_versions
  ↓
Cria permissões em permissions
  ↓
Cria rotas em app_routes
  ↓
Publica evento plugin_registered
```

---

## 10. Criação do app

A tabela `apps` recebe os dados principais do plugin.

Mapeamento:

| Manifesto | Tabela `apps` |
|---|---|
| `id` | `id` |
| `name` | `name` |
| `description` | `description` |
| `basePath` | `base_path` |
| `icon` | `icon` |
| `type` | `type` |
| `version` | `version` |
| — | `active = true` |

Exemplo conceitual:

```python
plugins.create({
    "id": plugin_id,
    "name": manifest["name"],
    "description": manifest.get("description"),
    "base_path": base_path,
    "icon": manifest.get("icon"),
    "type": manifest.get("type"),
    "version": version,
    "active": True,
})
```

---

## 11. Salvamento do manifesto vigente

O manifesto vigente é salvo em:

```text
app_manifests
```

Campos:

| Campo | Valor |
|---|---|
| `app_id` | ID do plugin |
| `manifest` | JSON completo do manifesto |
| `checksum` | SHA-256 do manifesto |

Esse registro representa a versão atualmente ativa do manifesto.

---

## 12. Criação da versão histórica

Toda versão registrada é persistida em:

```text
app_versions
```

Campos:

| Campo | Valor |
|---|---|
| `app_id` | ID do plugin |
| `version` | Versão do manifesto |
| `manifest` | JSON completo |
| `checksum` | SHA-256 |

Existe constraint única:

```text
app_id + version
```

---

## 13. Criação de permissões

As permissões declaradas no manifesto são criadas na tabela:

```text
permissions
```

Cada item de `permissions[]` deve conter:

```json
{
  "code": "dashboard-lmps.access",
  "name": "Acessar Dashboard LMPs",
  "description": "Permite acessar o dashboard de LMPs.",
  "module": "dashboard-lmps"
}
```

Mapeamento:

| Manifesto | Tabela `permissions` |
|---|---|
| `code` | `code` |
| `name` | `name` |
| `description` | `description` |
| `module` | `module` |

Regra:

> Em plugins, `module` deve ser igual ao `id` do plugin.

---

## 14. Criação de rotas

As rotas declaradas no manifesto são criadas em:

```text
app_routes
```

Mapeamento:

| Manifesto | Tabela `app_routes` |
|---|---|
| `app_id` | ID do plugin |
| `path` | `path` |
| `label` | `label` |
| `icon` | `icon` |
| `permission` | resolvido para `permission_id` |
| `order` | `order` |
| `showInMenu` | `show_in_menu` |
| — | `active = true` |

A permissão da rota é declarada por código no manifesto.

Exemplo:

```json
{
  "permission": "dashboard-lmps.access"
}
```

Durante a persistência, esse código é resolvido para o ID da permissão cadastrada.

---

## 15. Ordem de criação

A ordem correta é importante.

Para plugin novo:

```text
1. apps
2. app_manifests
3. app_versions
4. permissions
5. app_routes
```

Permissões precisam ser criadas antes das rotas para que `app_routes.permission_id` possa ser resolvido.

---

## 16. Cenário 2 — Plugin existente com nova versão

Quando o plugin já existe, o registro representa uma nova versão.

Fluxo:

```text
Plugin existe
  ↓
Verifica se version já existe
  ↓
Se version existe, bloqueia
  ↓
Atualiza apps.version
  ↓
Salva manifesto vigente
  ↓
Cria nova linha em app_versions
  ↓
Remove rotas antigas
  ↓
Remove permissões antigas do módulo
  ↓
Cria permissões novas
  ↓
Cria rotas novas
  ↓
Publica evento plugin_registered
```

---

## 17. Bloqueio de versão duplicada

Se `app_versions` já possuir a combinação:

```text
plugin_id + version
```

A operação é recusada.

Erro:

```json
{
  "errors": [
    {
      "code": "plugin.version_already_exists",
      "message": "This version is already registered",
      "path": "$.version"
    }
  ]
}
```

---

## 18. Atualização da versão ativa

Para plugin existente, o campo `apps.version` é atualizado para a nova versão.

Exemplo:

```text
apps.version = "1.1.0"
```

Isso indica qual versão está ativa na plataforma.

---

## 19. Substituição de rotas e permissões

Em nova versão, a Core API remove permissões e rotas antigas antes de recriar.

Ordem:

```text
1. delete app_routes by app_id
2. delete permissions by module
3. create permissions from manifest
4. create app_routes from manifest
```

Essa ordem evita rotas apontando para permissões inexistentes.

A remoção de permissões usa:

```text
module = plugin_id
```

Portanto, é essencial que permissões de plugin tenham `module` igual ao ID do plugin.

---

## 20. Evento publicado

Ao final do registro, a Core API coleta evento:

```python
AdminChangedEvent(
    entity="plugins",
    action="plugin_registered",
    payload={
        "pluginId": plugin_id,
        "version": version,
    },
    target_user_id=None,
)
```

Esse evento é publicado após commit pelo Unit of Work.

Como `target_user_id` é `None`, o evento é broadcast.

---

## 21. Efeitos esperados no Portal

Depois que o plugin é registrado:

1. O evento `admin.changed` pode ser recebido pelo Portal.
2. O Portal pode recarregar lista de apps/rotas.
3. Usuários com permissão passam a ver o plugin.
4. Usuários sem permissão não veem o plugin.
5. Se `active = true`, o app é elegível para aparecer.
6. O menu depende das rotas autorizadas e `showInMenu`.

---

## 22. Como o app aparece para o usuário

O plugin só aparece para o usuário quando todas as condições forem verdadeiras:

- app está ativo;
- app possui rotas ativas;
- usuário tem permissão para ao menos uma rota;
- ou a rota não possui permissão associada;
- ou usuário é superadmin.

Fluxo:

```text
Plugin registrado
  ↓
/me/apps
  ↓
AppQueryRepository lista apps ativos
  ↓
AppAuthorizationService filtra rotas
  ↓
Portal recebe app autorizado
```

---

## 23. Interação com permissões

Ao registrar um plugin, as permissões declaradas passam a existir no RBAC.

Depois disso, administradores podem:

- adicionar permissão a roles;
- criar roles específicas para o plugin;
- atribuir roles a usuários;
- atribuir roles a grupos;
- usar a permissão para controlar visibilidade da rota.

Exemplo:

```text
dashboard-lmps.access
```

Pode ser associada a:

```text
Role: Analista LMP
Group: Operações
```

---

## 24. Registro versus atualização de manifesto

Existem duas operações diferentes:

| Operação | Endpoint | Quando usar |
|---|---|---|
| Registrar plugin | `POST /admin/apps/register` | Criar plugin novo ou registrar nova versão |
| Atualizar manifesto | `PUT /admin/apps/<plugin_id>/manifest` | Alterar metadata ou propriedades não estruturais sem mudar versão |

Mudanças estruturais exigem novo registro.

Exemplos de mudanças estruturais:

- alterar `version`;
- alterar `basePath`;
- adicionar/remover rota;
- adicionar/remover permissão;
- alterar tipo do plugin.

---

## 25. Registro versus rollback

Registro cria nova versão.

Rollback restaura versão já existente no histórico.

| Operação | Efeito |
|---|---|
| Register com versão nova | Cria nova linha em `app_versions` |
| Rollback | Usa manifesto já existente em `app_versions` |

Rollback não cria nova versão histórica por si só; ele restaura uma versão previamente registrada.

---

## 26. Pré-requisitos para registrar plugin

Antes de registrar:

- plugin deve ter build/publicação disponível no gateway;
- `entry` deve apontar para asset acessível quando visual;
- `basePath` deve estar coerente com o gateway;
- permissões devem estar bem nomeadas;
- rotas devem estar dentro do `basePath`;
- versão deve ser nova quando plugin já existe;
- dependências devem existir ou ser planejadas;
- manifesto deve seguir `schemaVersion: 1.0.0`.

---

## 27. Checklist operacional

Checklist antes de chamar o endpoint:

- [ ] O JSON é válido.
- [ ] `schemaVersion` é `1.0.0`.
- [ ] `id` está correto e em lowercase.
- [ ] `version` é nova para o plugin.
- [ ] `type` está correto.
- [ ] `basePath` corresponde ao path servido pelo gateway.
- [ ] `entry` está acessível.
- [ ] `permissions[].module` é igual ao `id`.
- [ ] Rotas começam com `basePath`.
- [ ] Permissões de rotas existem em `permissions`.
- [ ] O plugin está buildado e acessível.
- [ ] O usuário que fará o registro possui `apps.manage`.

---

## 28. Exemplo de cURL

Exemplo conceitual:

```bash
curl -X POST "http://localhost/core-api/admin/apps/register" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d @manifest.json
```

Resposta esperada:

```json
{
  "ok": true
}
```

---

## 29. Tabelas afetadas

| Tabela | Operação em plugin novo | Operação em nova versão |
|---|---|---|
| `apps` | insert | update `version` |
| `app_manifests` | insert | update |
| `app_versions` | insert | insert |
| `permissions` | insert | delete by module + insert |
| `app_routes` | insert | delete by app + insert |

---

## 30. Pontos de atenção

1. Registrar plugin existente com mesma versão é bloqueado.
2. Permissões antigas são removidas por `module = plugin_id`.
3. Rotas antigas são removidas por `app_id = plugin_id`.
4. Permissões devem ser criadas antes das rotas.
5. O manifesto vigente fica em `app_manifests`.
6. O histórico fica em `app_versions`.
7. O checksum é calculado sobre o JSON ordenado por chave.
8. O evento `plugin_registered` é broadcast.
9. O Portal não consome o manifesto bruto; ele consome `/me/apps`.
10. Alterações estruturais devem ser nova versão, não update simples de manifesto.

---

## 31. Documentos relacionados

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/05-plugin-system/microfrontends.md
docs/04-core-api/visao-geral-core-api.md
docs/03-autenticacao-autorizacao/rbac.md
```

