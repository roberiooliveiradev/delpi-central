# Minha DELPI — Versionamento e Rollback de Plugins

> **Arquivo:** `docs/05-plugin-system/versionamento-e-rollback.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** histórico de versões, registro de nova versão e rollback de plugins

---

## 1. Objetivo

Este documento descreve como funciona o versionamento de plugins na **Minha DELPI** e como a Core API executa rollback para uma versão previamente registrada.

Ele explica:

- onde as versões são armazenadas;
- quando uma nova versão é criada;
- como a versão ativa é definida;
- como rollback restaura manifesto, permissões e rotas;
- quais eventos são emitidos;
- quais cuidados devem ser tomados durante evolução de plugins.

---

## 2. Conceito de versão de plugin

Cada plugin registrado na Minha DELPI possui uma versão declarada no manifesto:

```json
{
  "version": "1.0.0"
}
```

A versão representa um snapshot estrutural do plugin.

Ela deve mudar quando houver alteração estrutural, como:

- adicionar rota;
- remover rota;
- alterar path de rota;
- adicionar permissão;
- remover permissão;
- alterar `basePath`;
- alterar tipo do plugin;
- alterar contrato funcional relevante.

A versão atual do plugin fica em:

```text
apps.version
```

O histórico de versões fica em:

```text
app_versions
```

---

## 3. Formato de versão

O contrato efetivo atual exige SemVer simples:

```text
MAJOR.MINOR.PATCH
```

Exemplos válidos:

```text
1.0.0
1.1.0
2.0.0
```

Exemplos inválidos no contrato efetivo atual:

```text
1.0
v1.0.0
1.0.0-beta
01.0.0
```

Ponto de atenção:

> Embora o JSON Schema aceite sufixo de pré-release, as regras de domínio atuais rejeitam versões fora de `MAJOR.MINOR.PATCH`. Portanto, pré-release não deve ser usado hoje.

---

## 4. Tabela `app_versions`

A tabela `app_versions` armazena o histórico de manifestos registrados.

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | Identificador interno da versão |
| `app_id` | ID do plugin |
| `version` | Versão do manifesto |
| `manifest` | Snapshot JSON completo do manifesto |
| `checksum` | Hash SHA-256 do manifesto |
| `created_at` | Data de criação da versão |
| `updated_at` | Data de atualização do registro |

Constraint única:

```text
app_id + version
```

Isso impede registrar duas vezes a mesma versão para o mesmo plugin.

---

## 5. Diferença entre versão ativa e histórico

A versão ativa fica em:

```text
apps.version
```

O manifesto ativo fica em:

```text
app_manifests.manifest
```

O histórico fica em:

```text
app_versions.manifest
```

Relação:

```text
apps.version
  ↓ aponta conceitualmente para
app_versions.version

app_manifests.manifest
  ↓ representa
manifesto vigente usado pela plataforma
```

Em registro de nova versão, os dois são atualizados.

Em atualização não estrutural de manifesto, `app_manifests` pode ser atualizado sem criar nova linha em `app_versions`.

---

## 6. Quando uma nova versão é criada

Uma nova versão é criada somente pelo fluxo de registro:

```http
POST /admin/apps/register
```

Se o plugin não existe:

- cria `apps`;
- cria `app_manifests`;
- cria primeira linha em `app_versions`;
- cria permissões;
- cria rotas.

Se o plugin já existe:

- verifica se a versão ainda não existe;
- atualiza `apps.version`;
- atualiza `app_manifests`;
- cria nova linha em `app_versions`;
- substitui permissões;
- substitui rotas.

---

## 7. Quando uma nova versão deve ser obrigatória

Criar nova versão quando houver mudança estrutural.

### 7.1 Mudanças em permissões

Exemplos:

```text
Adicionar dashboard-lmps.details
Remover dashboard-lmps.access
Trocar dashboard-lmps.access por dashboard-lmps.view
```

Motivo:

- permissões impactam RBAC;
- roles podem depender delas;
- rotas podem apontar para elas;
- histórico precisa preservar contrato anterior.

---

### 7.2 Mudanças em rotas

Exemplos:

```text
Adicionar /apps/dashboard-lmps/detalhes
Remover /apps/dashboard-lmps
Alterar /apps/dashboard-lmps para /apps/lmps
```

Motivo:

- rotas afetam menu;
- rotas podem afetar favoritos;
- rotas podem afetar links salvos;
- rotas podem afetar gateway e entry points.

---

### 7.3 Mudanças em basePath

Exemplo:

```text
/apps/dashboard-lmps → /apps/lmps
```

Motivo:

- altera a raiz de navegação do plugin;
- pode quebrar rotas existentes;
- pode exigir alteração no gateway;
- pode invalidar favoritos e links.

---

### 7.4 Mudanças em type

Exemplo:

```text
iframe → microfrontend
```

Motivo:

- muda estratégia de renderização;
- muda validações de manifesto;
- muda a forma como o Portal carrega o app.

---

## 8. Quando não é obrigatório criar nova versão

Mudanças não estruturais podem usar atualização de manifesto:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Exemplos:

- alterar nome;
- alterar descrição;
- alterar ícone;
- alterar label de rota;
- alterar ícone de rota;
- alterar ordem de rota;
- alterar `showInMenu`.

Essas mudanças não criam nova linha em `app_versions`.

---

## 9. Registro de nova versão

Fluxo técnico:

```text
POST /admin/apps/register
  ↓
Valida manifesto
  ↓
Extrai plugin_id e version
  ↓
Busca plugin existente
  ↓
Se existe, verifica versão duplicada
  ↓
Atualiza apps.version
  ↓
Salva app_manifests
  ↓
Cria app_versions
  ↓
Remove app_routes atuais
  ↓
Remove permissions por module
  ↓
Cria permissions novas
  ↓
Cria app_routes novas
  ↓
Publica plugin_registered
```

---

## 10. Bloqueio de versão duplicada

A Core API rejeita registrar uma versão já existente para o mesmo plugin.

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

Exemplo:

```text
Plugin dashboard-lmps já possui 1.0.0.
Tentar registrar dashboard-lmps 1.0.0 novamente será bloqueado.
```

---

## 11. Listagem de versões

Endpoint:

```http
GET /admin/apps/<plugin_id>/versions
```

Permissão exigida:

```text
apps.view
```

Fluxo:

```text
Busca plugin
  ↓
Se não existir, retorna plugin.not_found
  ↓
Lista app_versions por app_id
  ↓
Ordena por created_at desc
```

Resposta conceitual:

```json
{
  "versions": [
    {
      "version": "1.1.0",
      "checksum": "...",
      "created_at": "2026-03-05T18:21:30"
    },
    {
      "version": "1.0.0",
      "checksum": "...",
      "created_at": "2026-03-01T12:00:00"
    }
  ]
}
```

---

## 12. Rollback de plugin

Rollback restaura um plugin para uma versão já existente no histórico.

Endpoint:

```http
POST /admin/apps/<plugin_id>/rollback
```

Permissão exigida:

```text
apps.manage
```

Body esperado:

```json
{
  "version": "1.0.0"
}
```

Use case:

```text
RollbackPluginVersionUseCase
```

---

## 13. Fluxo de rollback

Fluxo técnico:

```text
Recebe plugin_id e target_version
  ↓
Busca plugin em apps
  ↓
Se não existir, retorna plugin.not_found
  ↓
Busca versão em app_versions
  ↓
Se não existir, retorna plugin.version_not_found
  ↓
Obtém manifest e checksum da versão
  ↓
Valida se manifest é dict
  ↓
Atualiza apps.version
  ↓
Salva app_manifests com manifest/checksum históricos
  ↓
Remove app_routes atuais
  ↓
Remove permissions por module
  ↓
Cria permissions do manifest restaurado
  ↓
Cria app_routes do manifest restaurado
  ↓
Publica plugin_version_rolled_back
```

---

## 14. O que o rollback altera

Rollback altera:

| Tabela | Alteração |
|---|---|
| `apps` | atualiza `version` |
| `app_manifests` | salva manifesto/checksum restaurado |
| `permissions` | remove por module e recria |
| `app_routes` | remove por app e recria |

Rollback não cria nova linha em:

```text
app_versions
```

Ele usa uma versão histórica existente.

---

## 15. Erros de rollback

### 15.1 Plugin inexistente

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

### 15.2 Versão inexistente

```json
{
  "errors": [
    {
      "code": "plugin.version_not_found",
      "message": "Target version not found in history",
      "path": "version"
    }
  ]
}
```

---

### 15.3 Manifesto histórico inválido

```json
{
  "errors": [
    {
      "code": "plugin.invalid_version_manifest",
      "message": "Stored manifest is invalid",
      "path": "_global"
    }
  ]
}
```

---

## 16. Evento de rollback

Ao final do rollback, a Core API coleta evento:

```python
AdminChangedEvent(
    entity="plugins",
    action="plugin_version_rolled_back",
    payload={
        "pluginId": plugin_id,
        "version": target_version,
    },
    target_user_id=None,
)
```

Esse evento é broadcast.

O Portal pode usar o evento para recarregar apps, rotas e menus.

---

## 17. Efeito do rollback no Portal

Após rollback:

1. O manifesto vigente muda.
2. A versão ativa muda.
3. Rotas podem mudar.
4. Permissões podem mudar.
5. Apps retornados por `/me/apps` podem mudar.
6. Menus podem mudar.
7. Usuários podem ganhar ou perder acesso a rotas conforme permissões restauradas.

O Portal deve recarregar a visão autorizada da Core API.

---

## 18. Efeito do rollback no RBAC

Rollback remove e recria permissões do módulo.

Isso pode impactar roles existentes.

Exemplo:

```text
Versão 1.1.0 adicionou dashboard-lmps.details.
Role Analista recebeu dashboard-lmps.details.
Rollback para 1.0.0 remove essa permissão do cadastro.
```

Pontos de atenção:

- roles podem perder vínculo com permissões removidas;
- rotas podem deixar de exigir permissões novas;
- usuários podem perder acesso a funcionalidades;
- deve-se validar impacto antes do rollback.

---

## 19. Ordem de remoção e recriação

Tanto no registro de nova versão quanto no rollback, a ordem é importante.

```text
1. Remover rotas atuais
2. Remover permissões atuais por module
3. Criar permissões do manifesto alvo
4. Criar rotas do manifesto alvo
```

Motivo:

- rotas referenciam permissões;
- permissões antigas não devem permanecer se não existem no manifesto alvo;
- rotas precisam resolver `permission_id` a partir de `permission` code.

---

## 20. Rollback versus register

| Aspecto | Register nova versão | Rollback |
|---|---|---|
| Endpoint | `POST /admin/apps/register` | `POST /admin/apps/<id>/rollback` |
| Fonte do manifesto | Body da requisição | `app_versions` |
| Cria versão histórica | Sim | Não |
| Atualiza `apps.version` | Sim | Sim |
| Atualiza `app_manifests` | Sim | Sim |
| Recria permissões | Sim | Sim |
| Recria rotas | Sim | Sim |
| Valida manifesto recebido | Sim | Não necessariamente revalida completo |
| Evento | `plugin_registered` | `plugin_version_rolled_back` |

---

## 21. Rollback versus update de manifesto

| Aspecto | Update Manifest | Rollback |
|---|---|---|
| Endpoint | `PUT /admin/apps/<id>/manifest` | `POST /admin/apps/<id>/rollback` |
| Altera versão ativa | Não | Sim |
| Fonte do manifesto | Body da requisição | Histórico |
| Pode alterar estrutura | Não | Sim, para estrutura da versão alvo |
| Cria versão histórica | Não | Não |
| Recria permissões | Não | Sim |
| Recria rotas | Não | Sim |
| Evento | `plugin_manifest_updated` | `plugin_version_rolled_back` |

---

## 22. Exemplo de linha do tempo

```text
1.0.0 registrada
  ↓
app_versions: [1.0.0]
apps.version: 1.0.0

1.1.0 registrada
  ↓
app_versions: [1.0.0, 1.1.0]
apps.version: 1.1.0

Rollback para 1.0.0
  ↓
app_versions: [1.0.0, 1.1.0]
apps.version: 1.0.0
app_manifests: manifesto da 1.0.0
```

---

## 23. Checklist antes de registrar nova versão

- [ ] A versão segue `MAJOR.MINOR.PATCH`.
- [ ] A versão ainda não existe para o plugin.
- [ ] O manifesto completo é válido.
- [ ] Mudanças estruturais são intencionais.
- [ ] Permissões novas foram planejadas.
- [ ] Roles que precisam das novas permissões serão atualizadas.
- [ ] Rotas novas estão dentro do `basePath`.
- [ ] Gateway já serve os assets necessários.
- [ ] O plugin foi testado antes do registro.
- [ ] Existe plano de rollback.

---

## 24. Checklist antes de executar rollback

- [ ] A versão alvo existe em `app_versions`.
- [ ] O impacto em permissões foi avaliado.
- [ ] O impacto em rotas e menu foi avaliado.
- [ ] O plugin/asset da versão alvo ainda está compatível com o gateway.
- [ ] Usuários afetados foram considerados.
- [ ] O rollback foi comunicado quando necessário.
- [ ] O usuário executor possui `apps.manage`.

---

## 25. Pontos de atenção

1. Não é permitido registrar versão duplicada para o mesmo plugin.
2. Rollback não cria nova versão; ele restaura uma versão existente.
3. Update de manifesto não cria snapshot em `app_versions`.
4. Rollback pode remover permissões usadas em roles.
5. Rollback pode alterar rotas retornadas pelo `/me/apps`.
6. O manifesto histórico precisa estar íntegro.
7. O gateway/assets precisam continuar compatíveis com a versão restaurada.
8. Permissões são removidas por `module = plugin_id`.
9. Rotas são removidas por `app_id = plugin_id`.
10. Eventos devem ser usados pelo Portal para recarregar estado.

---

## 26. Documentos relacionados

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/04-core-api/visao-geral-core-api.md
docs/03-autenticacao-autorizacao/rbac.md
```

