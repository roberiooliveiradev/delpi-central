# Minha DELPI — Guia Operacional: Registrar Plugin

> **Arquivo:** `docs/10-guias-operacionais/registrar-plugin.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** registro operacional de plugins na Core API

---

## 1. Objetivo

Este guia descreve como registrar um plugin na Minha DELPI.

O registro de plugin é feito na Core API a partir de um manifesto JSON válido. Após o registro, a plataforma persiste app, manifesto, versão, permissões e rotas.

---

## 2. Pré-requisitos

Antes de registrar um plugin, confirme:

- Core API está rodando;
- banco `postgres-core` está migrado;
- Keycloak está configurado;
- usuário autenticado possui permissão administrativa;
- manifesto segue o schema oficial;
- Gateway serve os assets/backend do plugin;
- plugin foi buildado/deployado quando aplicável.

---

## 3. Manifesto oficial

O arquivo esperado é:

```text
delpi.manifest.json
```

O contrato vigente exige:

```json
{
  "schemaVersion": "1.0.0"
}
```

Tipos suportados:

```text
microfrontend
iframe
backend-only
```

---

## 4. Validar campos principais

Antes de registrar, validar:

```text
id
name
version
type
basePath
permissions
routes
entry
ui.renderMode
backend
```

Regras importantes:

- `id` deve ser estável;
- `version` deve seguir SemVer;
- `permissions` deve ter ao menos uma permissão;
- cada permissão precisa de `code`, `name` e `module`;
- `module` deve ser igual ao plugin;
- rotas devem declarar permissões existentes;
- microfrontend precisa de entry global ou entry por rota;
- backend-only não pode ter UI nem rotas.

---

## 5. Endpoint de registro

Endpoint administrativo atual:

```http
POST /admin/apps/register
```

Dependendo do Gateway, o path público pode ser:

```text
/core-api/admin/apps/register
```

Permissão esperada:

```text
apps.manage
```

---

## 6. Exemplo de chamada

```bash
curl -X POST http://localhost/core-api/admin/apps/register \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @delpi.manifest.json
```

Substituir `<token>` por access token de usuário autorizado.

---

## 7. O que acontece no registro

Fluxo interno:

```text
Recebe manifesto
  ↓
Normaliza manifesto
  ↓
Resolve schemaVersion
  ↓
Valida JSON Schema
  ↓
Aplica strategy por type
  ↓
Aplica regras de domínio
  ↓
Calcula checksum
  ↓
Cria/atualiza app
  ↓
Salva manifesto vigente
  ↓
Cria versão histórica
  ↓
Cria permissões
  ↓
Cria rotas
  ↓
Emite evento plugin_registered
```

---

## 8. Plugin novo

Se o plugin ainda não existe:

```text
apps insert
app_manifests insert
app_versions insert
permissions insert
app_routes insert
```

Depois do commit, o Portal pode atualizar `/me/apps` e passar a exibir o plugin para usuários autorizados.

---

## 9. Nova versão de plugin existente

Se o plugin já existe com outra versão:

```text
Verifica versão duplicada
  ↓
Atualiza apps.version
  ↓
Atualiza app_manifests
  ↓
Insere app_versions
  ↓
Remove rotas antigas
  ↓
Remove permissões do módulo
  ↓
Recria permissões
  ↓
Recria rotas
```

Usar nova versão quando houver alteração estrutural.

---

## 10. Não usar register para alteração visual simples

Para alterações não estruturais, usar o fluxo de atualização de manifesto.

Exemplos de alteração não estrutural:

- nome;
- descrição;
- ícone;
- label de rota;
- ícone de rota;
- ordem;
- `showInMenu`.

Não alterar por esse fluxo:

- version;
- basePath;
- conjunto de permissões;
- conjunto de rotas.

---

## 11. Associar permissões a roles

Registrar o plugin cria permissões, mas não concede acesso automaticamente.

Depois do registro:

1. Acesse administração RBAC.
2. Associe a permissão do plugin a uma role.
3. Associe role ao usuário ou grupo.
4. Recarregue `/me` e `/me/apps`.

Fluxo:

```text
manifesto cria permission
  ↓
role recebe permission
  ↓
usuário recebe role
  ↓
PermissionResolver calcula acesso
  ↓
/me/apps retorna plugin
```

---

## 12. Validar no Portal

Após registro e RBAC:

1. Faça login no Portal.
2. Chame `/me`.
3. Chame `/me/apps`.
4. Confirme se o plugin aparece.
5. Clique no menu.
6. Confirme carregamento do plugin.

Para microfrontend, testar diretamente:

```text
http://localhost/apps/<plugin>/assets/remoteEntry.js
```

Deve retornar JavaScript, não HTML.

---

## 13. Erros comuns

### 13.1 `schema_validation_error`

Manifesto não respeita o schema.

Ação:

- revisar campos obrigatórios;
- revisar tipos;
- revisar `additionalProperties`;
- revisar `ui`;
- revisar `backend`.

---

### 13.2 `plugin.version_already_exists`

A versão já foi registrada.

Ação:

- alterar `version`;
- ou usar atualização não estrutural;
- ou executar rollback para versão existente, se esse for o objetivo.

---

### 13.3 Rota não aparece no menu

Verificar:

- app está ativo;
- rota está ativa;
- `showInMenu=true`;
- usuário possui permissão;
- permissão foi associada à role;
- cache RBAC foi invalidado;
- Portal recarregou `/me/apps`.

---

### 13.4 Plugin aparece mas não carrega

Verificar:

- Gateway serve `entry`;
- `remoteEntry.js` retorna JavaScript;
- base pública do build está correta;
- assets existem;
- CORS/headers;
- Module Federation exporta `mount`/`unmount`.

---

## 14. Checklist de registro

- [ ] Manifesto existe.
- [ ] `schemaVersion` é `1.0.0`.
- [ ] `id` está correto.
- [ ] `version` está correta.
- [ ] `type` é suportado.
- [ ] `basePath` está correto.
- [ ] `entry` está correto.
- [ ] Permissões possuem `code`, `name` e `module`.
- [ ] Rotas apontam para permissões declaradas.
- [ ] Gateway serve o plugin.
- [ ] Usuário tem `apps.manage`.
- [ ] Registro retorna sucesso.
- [ ] Permissões foram atribuídas via RBAC.
- [ ] `/me/apps` retorna o plugin.
- [ ] Portal carrega o plugin.

---

## 15. Pontos de atenção

1. Manifesto é fonte de verdade do contrato.
2. Registro não concede acesso automaticamente.
3. Permissões precisam ser atribuídas no RBAC.
4. Gateway precisa publicar o plugin.
5. Rollback não garante assets antigos disponíveis.
6. `module` da permissão deve bater com plugin.
7. Não registrar campos fora do schema.
8. Não usar version antiga já registrada.
9. Não hardcodar plugin no Portal.
10. Backend do plugin deve validar JWT quando aplicável.

---

## 16. Documentos relacionados

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/03-autenticacao-autorizacao/rbac.md
```
