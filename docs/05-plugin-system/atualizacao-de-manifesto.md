# Minha DELPI — Atualização de Manifesto de Plugin

> **Arquivo:** `docs/05-plugin-system/atualizacao-de-manifesto.md`  
> **Status:** documentação oficial (maio/2026)  

URLs de admin usam o `id` do manifesto (ex.: `PUT /core-api/admin/apps/dash-lmps/manifest`). Exemplos com `dashboard-lmps` podem ser legado MFE — ver manifesto atual em `plugins/dashboard-lmps/dash-lmps.manifest.json`.
> **Produto:** Minha DELPI  
> **Escopo:** atualização não estrutural de manifesto de plugin

---

## 1. Objetivo

Este documento descreve como funciona a atualização de manifesto de plugin na **Minha DELPI**.

A atualização de manifesto permite alterar metadados e propriedades visuais de um plugin sem registrar uma nova versão estrutural.

Ela é diferente do registro de plugin.

Regra central:

> Atualização de manifesto é usada apenas para mudanças não estruturais. Mudanças estruturais exigem nova versão via `POST /admin/apps/register`.

---

## 2. Endpoint

Endpoint:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Controller:

```text
app/interfaces/http/apps_controller.py
```

Use case:

```text
app/application/use_cases/update_plugin_manifest_use_case.py
```

Permissão exigida:

```text
apps.manage
```

---

## 3. Quando usar este endpoint

Usar atualização de manifesto quando for necessário alterar apenas informações não estruturais, como:

- nome exibido do plugin;
- descrição;
- ícone;
- label de rotas;
- ícone de rotas;
- ordem de rotas;
- visibilidade de rotas no menu.

Exemplos:

```text
Alterar "Dashboard LMPs" para "Painel de LMPs"
Alterar ícone do menu
Reordenar rotas
Ocultar rota do menu mantendo rota ativa
Atualizar descrição do app
```

---

## 4. Quando não usar este endpoint

Não usar atualização de manifesto para mudanças estruturais.

Mudanças estruturais exigem nova versão via registro.

Exemplos de mudanças estruturais:

- alterar `id`;
- alterar `version`;
- alterar `basePath`;
- alterar `type`;
- adicionar rota;
- remover rota;
- alterar conjunto de rotas;
- adicionar permissão;
- remover permissão;
- alterar conjunto de permissões;
- mudar o contrato funcional do plugin.

Nesses casos, usar:

```http
POST /admin/apps/register
```

com uma nova versão.

---

## 5. Fluxo geral

Fluxo da atualização:

```text
Recebe plugin_id e manifesto
  ↓
Valida manifesto completo
  ↓
Confere se manifest.id == plugin_id
  ↓
Busca plugin existente
  ↓
Bloqueia alteração de version
  ↓
Bloqueia alteração de basePath
  ↓
Bloqueia alteração de permissões
  ↓
Bloqueia alteração estrutural de rotas
  ↓
Atualiza metadata do plugin
  ↓
Salva manifesto vigente com novo checksum
  ↓
Atualiza propriedades não estruturais das rotas
  ↓
Publica evento plugin_manifest_updated
```

---

## 6. Validação do manifesto

Mesmo sendo uma atualização não estrutural, o manifesto enviado passa pelo `ManifestValidator` completo.

Pipeline:

```text
ManifestNormalizer
  ↓
ManifestVersionResolver
  ↓
JSON Schema
  ↓
Strategy por tipo
  ↓
Regras de domínio
```

Isso significa que o manifesto enviado deve continuar sendo um manifesto completo e válido.

Não é um PATCH parcial.

A requisição deve enviar o manifesto inteiro atualizado.

---

## 7. Validação de ID

O campo `id` do manifesto deve ser igual ao `plugin_id` da URL.

Exemplo correto:

```http
PUT /admin/apps/dashboard-lmps/manifest
```

Body:

```json
{
  "id": "dashboard-lmps"
}
```

Se houver divergência:

```json
{
  "errors": [
    {
      "code": "plugin.id_mismatch",
      "message": "manifest.id deve ser igual ao plugin_id",
      "path": "$.id"
    }
  ]
}
```

---

## 8. Validação de existência do plugin

A Core API verifica se o plugin existe em `apps`.

Se não existir:

```json
{
  "errors": [
    {
      "code": "plugin.not_found",
      "message": "Plugin not found",
      "path": "_global"
    }
  ]
}
```

---

## 9. Bloqueio de alteração de versão

A atualização de manifesto não permite alterar `version`.

Regra:

```text
manifest.version deve ser igual a apps.version
```

Se for diferente:

```json
{
  "errors": [
    {
      "code": "plugin.version_change_not_allowed",
      "message": "Alterar 'version' requer novo register do plugin.",
      "path": "$.version"
    }
  ]
}
```

Motivo:

> Uma nova versão deve gerar histórico em `app_versions`. Atualizar manifesto sem nova versão não pode modificar o versionamento do plugin.

---

## 10. Bloqueio de alteração de basePath

A atualização de manifesto não permite alterar `basePath`.

Regra:

```text
manifest.basePath deve ser igual a apps.base_path
```

Se for diferente:

```json
{
  "errors": [
    {
      "code": "plugin.base_path_change_not_allowed",
      "message": "Alterar basePath requer nova versão do plugin.",
      "path": "$.basePath"
    }
  ]
}
```

Motivo:

> `basePath` define estrutura de navegação e publicação. Alterá-lo pode quebrar rotas, gateway, favoritos e links existentes.

---

## 11. Bloqueio de alteração de permissões

A atualização de manifesto não permite alterar o conjunto de permissões.

A Core API compara:

```text
Permissões existentes no banco por module = plugin_id
```

com:

```text
permissions[].code do manifesto enviado
```

Se os conjuntos forem diferentes:

```json
{
  "errors": [
    {
      "code": "plugin.permission_change_not_allowed",
      "message": "Alterar permissões requer nova versão do plugin.",
      "path": "$.permissions"
    }
  ]
}
```

Mudanças bloqueadas:

- adicionar permissão;
- remover permissão;
- trocar código de permissão;
- substituir conjunto de permissões.

Observação:

> Alterar textos como `name` ou `description` de permissões também deve ser tratado com cuidado. O bloqueio atual compara conjunto de códigos, não necessariamente todos os metadados.

---

## 12. Bloqueio de alteração estrutural de rotas

A atualização de manifesto não permite adicionar ou remover rotas.

A Core API compara:

```text
Rotas existentes em app_routes por app_id = plugin_id
```

com:

```text
routes[].path do manifesto enviado
```

Se os conjuntos forem diferentes:

```json
{
  "errors": [
    {
      "code": "plugin.route_structure_change_not_allowed",
      "message": "Adicionar/remover rotas requer nova versão do plugin.",
      "path": "$.routes"
    }
  ]
}
```

Mudanças bloqueadas:

- adicionar rota;
- remover rota;
- trocar path de rota;
- substituir estrutura de navegação.

---

## 13. Alterações permitidas no plugin

A atualização pode alterar metadata do plugin.

Campos atualizados em `apps`:

| Manifesto | Campo interno |
|---|---|
| `name` | `apps.name` |
| `description` | `apps.description` |
| `icon` | `apps.icon` |

Essas alterações afetam como o plugin aparece no Portal.

---

## 14. Alterações permitidas nas rotas

A atualização pode alterar propriedades não estruturais de rotas existentes.

Campos permitidos:

| Manifesto | Campo interno |
|---|---|
| `routes[].label` | `app_routes.label` |
| `routes[].icon` | `app_routes.icon` |
| `routes[].order` | `app_routes.order` |
| `routes[].showInMenu` | `app_routes.show_in_menu` |

Não é permitido alterar `routes[].path` como mudança de rota existente. Alteração de path é tratada como remoção de uma rota e criação de outra, portanto exige nova versão.

---

## 15. Salvamento do manifesto atualizado

Após passar nas validações, a Core API calcula novo checksum do manifesto e salva em:

```text
app_manifests
```

Campos atualizados:

```text
manifest
checksum
updated_at
```

Importante:

> A atualização de manifesto atualiza o manifesto vigente, mas não cria nova linha em `app_versions`.

---

## 16. Versionamento na atualização de manifesto

A atualização de manifesto não altera:

```text
apps.version
app_versions
```

Isso significa que:

- o plugin continua na mesma versão;
- o histórico versionado não recebe nova entrada;
- o manifesto vigente pode ficar diferente do manifesto histórico daquela versão.

Ponto de atenção:

> Como o update não cria nova versão em `app_versions`, alterações não estruturais ficam refletidas no manifesto vigente, mas podem não estar preservadas como novo snapshot histórico. Caso seja necessário auditar cada mudança de metadata, deve-se evoluir o mecanismo de auditoria ou criar política de versionamento também para mudanças não estruturais.

---

## 17. Evento publicado

Ao final da atualização, a Core API coleta evento:

```python
AdminChangedEvent(
    entity="plugins",
    action="plugin_manifest_updated",
    payload={
        "pluginId": plugin_id,
    },
    target_user_id=None,
)
```

Como `target_user_id` é `None`, o evento é broadcast.

O Portal pode usar esse evento para recarregar apps, menus ou metadados.

---

## 18. Resposta de sucesso

Resposta esperada:

```json
{
  "ok": true
}
```

ou resposta equivalente baseada no result do use case.

Status esperado:

```text
200 OK
```

---

## 19. Exemplo de atualização válida

Cenário: alterar nome, descrição, ícone e ordem da rota.

Antes:

```json
{
  "name": "Dashboard LMPs",
  "description": "Painel de LMPs.",
  "icon": "bar-chart3",
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "icon": "bar-chart3",
      "permission": "dashboard-lmps.access",
      "showInMenu": true,
      "order": 10
    }
  ]
}
```

Depois:

```json
{
  "name": "Painel de LMPs",
  "description": "Painel consolidado de acompanhamento de LMPs.",
  "icon": "activity",
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Painel de LMPs",
      "icon": "activity",
      "permission": "dashboard-lmps.access",
      "showInMenu": true,
      "order": 2
    }
  ]
}
```

Essa alteração é válida desde que o manifesto completo mantenha:

- mesmo `id`;
- mesma `version`;
- mesmo `basePath`;
- mesmo conjunto de permissões;
- mesmo conjunto de paths de rotas.

---

## 20. Exemplo de atualização inválida — nova rota

Alteração inválida:

```json
{
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "permission": "dashboard-lmps.access"
    },
    {
      "path": "/apps/dashboard-lmps/detalhes",
      "label": "Detalhes",
      "permission": "dashboard-lmps.details"
    }
  ]
}
```

Motivo:

```text
Foi adicionada nova rota.
```

Erro esperado:

```text
plugin.route_structure_change_not_allowed
```

Como corrigir:

- criar nova versão do manifesto;
- registrar via `POST /admin/apps/register`.

---

## 21. Exemplo de atualização inválida — nova permissão

Alteração inválida:

```json
{
  "permissions": [
    {
      "code": "dashboard-lmps.access",
      "name": "Acessar Dashboard LMPs",
      "module": "dashboard-lmps"
    },
    {
      "code": "dashboard-lmps.details",
      "name": "Acessar detalhes de LMPs",
      "module": "dashboard-lmps"
    }
  ]
}
```

Motivo:

```text
Foi adicionada nova permissão.
```

Erro esperado:

```text
plugin.permission_change_not_allowed
```

Como corrigir:

- criar nova versão do manifesto;
- registrar via `POST /admin/apps/register`.

---

## 22. Exemplo de atualização inválida — alteração de version

Alteração inválida:

```json
{
  "version": "1.1.0"
}
```

Erro esperado:

```text
plugin.version_change_not_allowed
```

Como corrigir:

- usar `POST /admin/apps/register` para registrar a versão `1.1.0`.

---

## 23. Exemplo de cURL

```bash
curl -X PUT "http://localhost/core-api/admin/apps/dashboard-lmps/manifest" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d @manifest-atualizado.json
```

---

## 24. Diferença entre update e register

| Aspecto | Update Manifest | Register Plugin |
|---|---|---|
| Endpoint | `PUT /admin/apps/<id>/manifest` | `POST /admin/apps/register` |
| Cria plugin novo | Não | Sim |
| Registra nova versão | Não | Sim |
| Altera `version` | Não | Sim |
| Altera `basePath` | Não | Sim, se nova versão válida |
| Adiciona permissões | Não | Sim |
| Remove permissões | Não | Sim |
| Adiciona rotas | Não | Sim |
| Remove rotas | Não | Sim |
| Atualiza metadata | Sim | Sim |
| Atualiza labels/ícones/ordem | Sim | Sim |
| Cria linha em `app_versions` | Não | Sim |

---

## 25. Tabelas afetadas

Durante update de manifesto:

| Tabela | Operação |
|---|---|
| `apps` | update de `name`, `description`, `icon` |
| `app_manifests` | update de `manifest`, `checksum` |
| `app_routes` | update de `label`, `icon`, `order`, `show_in_menu` |

Tabelas não alteradas estruturalmente:

| Tabela | Observação |
|---|---|
| `app_versions` | não recebe nova versão |
| `permissions` | conjunto de permissões não muda |
| `apps.version` | não muda |
| `apps.base_path` | não muda |

---

## 26. Checklist antes de atualizar

- [ ] O manifesto enviado está completo.
- [ ] `manifest.id` é igual ao `plugin_id` da URL.
- [ ] `version` não mudou.
- [ ] `basePath` não mudou.
- [ ] O conjunto de `permissions[].code` não mudou.
- [ ] O conjunto de `routes[].path` não mudou.
- [ ] Apenas metadata e propriedades visuais foram alteradas.
- [ ] O usuário possui `apps.manage`.
- [ ] O plugin já existe.

---

## 27. Pontos de atenção

1. O update de manifesto não é PATCH parcial; deve enviar manifesto completo.
2. O update valida o manifesto completo antes de aplicar alterações.
3. `version` não pode mudar.
4. `basePath` não pode mudar.
5. Permissões não podem ser adicionadas/removidas.
6. Rotas não podem ser adicionadas/removidas.
7. O update não cria registro em `app_versions`.
8. O manifesto vigente pode divergir do snapshot histórico da versão em `app_versions`.
9. Alterações estruturais devem usar novo register.
10. O evento publicado é `plugin_manifest_updated`.

---

## 28. Documentos relacionados

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/04-core-api/visao-geral-core-api.md
docs/03-autenticacao-autorizacao/rbac.md
```

