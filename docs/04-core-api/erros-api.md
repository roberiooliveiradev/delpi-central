# Minha DELPI — Core API: Padrão de Erros da API

> **Arquivo:** `docs/04-core-api/erros-api.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** formato de erro, status HTTP, códigos e boas práticas de tratamento de erro na Core API

---

## 1. Objetivo

Este documento descreve o padrão de erros usado pela **Core API** da Minha DELPI.

A padronização de erros é importante para:

- manter respostas previsíveis;
- facilitar tratamento no Portal;
- simplificar testes automatizados;
- evitar vazamento de detalhes internos;
- permitir internacionalização futura;
- documentar contratos de API de forma consistente.

---

## 2. Formato padrão

A Core API deve retornar erros no formato:

```json
{
  "errors": [
    {
      "code": "validation_error",
      "message": "Campo obrigatório.",
      "path": "name"
    }
  ]
}
```

A raiz da resposta deve conter:

```text
errors
```

`errors` deve ser uma lista.

Cada item representa um erro específico.

---

## 3. Estrutura de um erro

Campos de cada erro:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `code` | string | Sim | Código estável de erro |
| `message` | string | Sim | Mensagem legível |
| `path` | string | Não | Campo, JSONPath ou `_global` |

Exemplo:

```json
{
  "code": "plugin.not_found",
  "message": "Plugin not found",
  "path": "_global"
}
```

---

## 4. Campo `code`

O campo `code` deve ser estável e previsível.

Regras:

- usar lowercase;
- usar ponto para namespace quando fizer sentido;
- não depender da mensagem textual;
- ser seguro para lógica de frontend;
- evitar acentos e espaços.

Exemplos:

```text
unauthorized
forbidden
validation_error
plugin.not_found
plugin.version_already_exists
plugin.route_structure_change_not_allowed
```

---

## 5. Campo `message`

O campo `message` é uma mensagem legível para humanos.

Regras:

- deve explicar o erro de forma clara;
- não deve expor stack trace;
- não deve expor segredo, token, senha ou query interna;
- pode estar em inglês ou português conforme padronização da API;
- não deve ser usado pelo frontend como identificador lógico.

O frontend deve usar `code` para lógica.

---

## 6. Campo `path`

O campo `path` indica onde ocorreu o erro.

Valores comuns:

```text
_global
$.id
$.version
$.permissions
name
email
```

Uso recomendado:

| Tipo de erro | Path recomendado |
|---|---|
| Erro geral | `_global` |
| Campo simples | `name`, `email`, `active` |
| Campo de manifesto | `$.id`, `$.routes[0].path` |
| Query param | `query.page` |
| Path param | `path.plugin_id` |

---

## 7. Helpers de erro

A Core API possui helpers em:

```text
app/interfaces/http/utils/errors.py
```

Helpers conhecidos:

```text
api_error
error_response
unauthorized
forbidden
not_found
bad_request
unprocessable
conflict
server_error
```

Esses helpers devem ser preferidos em controllers para manter formato consistente.

---

## 8. Status HTTP recomendados

| Status | Uso |
|---:|---|
| `400 Bad Request` | JSON inválido, parâmetros inválidos ou erro de validação simples |
| `401 Unauthorized` | Usuário ausente, token inválido ou sessão expirada |
| `403 Forbidden` | Usuário autenticado sem permissão |
| `404 Not Found` | Recurso inexistente |
| `409 Conflict` | Conflito de estado ou duplicidade |
| `422 Unprocessable Entity` | Entrada semanticamente inválida |
| `500 Internal Server Error` | Erro inesperado |

---

## 9. Erros de autenticação

### 9.1 Token ausente

Quando endpoint protegido é chamado sem usuário autenticado:

```json
{
  "errors": [
    {
      "code": "unauthorized",
      "message": "Authentication required",
      "path": "_global"
    }
  ]
}
```

Status:

```text
401 Unauthorized
```

---

### 9.2 Token inválido

Quando JWT não pode ser validado:

```json
{
  "errors": [
    {
      "code": "invalid_token",
      "message": "Invalid token",
      "path": "_global"
    }
  ]
}
```

Status:

```text
401 Unauthorized
```

Causas possíveis:

- assinatura inválida;
- token expirado;
- issuer inválido;
- audience inválida;
- JWKS indisponível;
- token de outro realm.

---

### 9.3 Claims inválidas

Quando claims obrigatórias estão ausentes:

```json
{
  "errors": [
    {
      "code": "invalid_claims",
      "message": "Token missing required claims",
      "path": "_global"
    }
  ]
}
```

Status:

```text
401 Unauthorized
```

---

### 9.4 `sub` inválido

Quando `sub` não é UUID válido para criação/sincronização local:

```json
{
  "errors": [
    {
      "code": "invalid_uuid",
      "message": "Invalid user identifier",
      "path": "sub"
    }
  ]
}
```

Status:

```text
401 Unauthorized
```

---

## 10. Erros de autorização

### 10.1 Sem permissão

Quando usuário está autenticado, mas não possui permissão exigida:

```json
{
  "errors": [
    {
      "code": "forbidden",
      "message": "Permission denied",
      "path": "_global"
    }
  ]
}
```

Status:

```text
403 Forbidden
```

---

### 10.2 Superadmin exigido

Quando operação exige superadmin:

```json
{
  "errors": [
    {
      "code": "forbidden",
      "message": "Superadmin required",
      "path": "_global"
    }
  ]
}
```

Status:

```text
403 Forbidden
```

---

## 11. Erros de validação

Erros de validação devem apontar o campo problemático.

Exemplo:

```json
{
  "errors": [
    {
      "code": "validation_error",
      "message": "Name is required",
      "path": "name"
    }
  ]
}
```

Status recomendado:

```text
400 Bad Request
```

ou:

```text
422 Unprocessable Entity
```

Quando houver múltiplos erros:

```json
{
  "errors": [
    {
      "code": "validation_error",
      "message": "Name is required",
      "path": "name"
    },
    {
      "code": "validation_error",
      "message": "Email is invalid",
      "path": "email"
    }
  ]
}
```

---

## 12. Erros de Plugin System

### 12.1 Plugin não encontrado

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

Status:

```text
404 Not Found
```

---

### 12.2 Versão duplicada

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

Status recomendado:

```text
409 Conflict
```

ou, se tratado como validação:

```text
400 Bad Request
```

---

### 12.3 Versão histórica não encontrada

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

Status:

```text
404 Not Found
```

---

### 12.4 Manifesto histórico inválido

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

Status:

```text
500 Internal Server Error
```

ou:

```text
422 Unprocessable Entity
```

conforme decisão de API.

---

### 12.5 Plugin possui dependentes

```json
{
  "errors": [
    {
      "code": "plugin.has_dependents",
      "message": "Plugin has dependent plugins",
      "path": "_global"
    }
  ]
}
```

Status:

```text
409 Conflict
```

---

## 13. Erros de atualização de manifesto

### 13.1 ID divergente

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

### 13.2 Alteração de versão não permitida

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

---

### 13.3 Alteração de basePath não permitida

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

---

### 13.4 Alteração de permissões não permitida

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

---

### 13.5 Alteração estrutural de rotas não permitida

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

---

## 14. Erros de validação de manifesto

Códigos comuns:

```text
schema_validation_error
unsupported_plugin_type
invalid_plugin_id
invalid_version
invalid_base_path
invalid_permission_code
duplicate_permission_code_in_manifest
permission_name_required
permission_module_mismatch
entry_required
routes_required
invalid_route_path
route_outside_base_path
duplicate_route_path_in_manifest
route_permission_not_declared
backend_only_cannot_have_routes
backend_only_entry_not_allowed
backend_required
backend_required_must_be_true
backend_missing_issuer
backend_missing_audience
missing_access_permission
invalid_iframe_entry_url
```

Esses erros normalmente retornam:

```text
400 Bad Request
```

com `path` apontando para o campo do manifesto.

---

## 15. Erros de RBAC

Exemplos recomendados:

### 15.1 Role não encontrada

```json
{
  "errors": [
    {
      "code": "role.not_found",
      "message": "Role not found",
      "path": "_global"
    }
  ]
}
```

Status:

```text
404 Not Found
```

---

### 15.2 Grupo não encontrado

```json
{
  "errors": [
    {
      "code": "group.not_found",
      "message": "Group not found",
      "path": "_global"
    }
  ]
}
```

Status:

```text
404 Not Found
```

---

### 15.3 Usuário não encontrado

```json
{
  "errors": [
    {
      "code": "user.not_found",
      "message": "User not found",
      "path": "_global"
    }
  ]
}
```

Status:

```text
404 Not Found
```

---

### 15.4 Último superadmin

```json
{
  "errors": [
    {
      "code": "user.last_superadmin",
      "message": "Cannot remove the last superadmin",
      "path": "is_superadmin"
    }
  ]
}
```

Status:

```text
409 Conflict
```

---

## 16. Erros de favoritos

### 16.1 App não encontrado para favorito

```json
{
  "errors": [
    {
      "code": "app.not_found",
      "message": "App não encontrada",
      "path": "app_id"
    }
  ]
}
```

Status:

```text
404 Not Found
```

ou:

```text
400 Bad Request
```

conforme implementação atual.

---

## 17. Erros de notificações

### 17.1 Notificação não encontrada

```json
{
  "errors": [
    {
      "code": "notification.not_found",
      "message": "Notification not found",
      "path": "notification_id"
    }
  ]
}
```

Status:

```text
404 Not Found
```

---

### 17.2 Notificação de outro usuário

```json
{
  "errors": [
    {
      "code": "forbidden",
      "message": "Permission denied",
      "path": "_global"
    }
  ]
}
```

Status:

```text
403 Forbidden
```

---

## 18. Erro interno

Erros inesperados devem retornar resposta genérica.

```json
{
  "errors": [
    {
      "code": "internal_server_error",
      "message": "Internal server error",
      "path": "_global"
    }
  ]
}
```

Status:

```text
500 Internal Server Error
```

Não retornar:

- stack trace;
- SQL completo;
- variáveis de ambiente;
- token;
- senha;
- segredo;
- detalhes internos sensíveis.

---

## 19. Tratamento no Portal

O Portal deve tratar erros usando `code`, não `message`.

Exemplo:

```typescript
if (error.code === "forbidden") {
  showAccessDenied()
}

if (error.code === "plugin.version_already_exists") {
  showFieldError("version", error.message)
}
```

Regras:

- `401`: renovar token ou redirecionar login;
- `403`: mostrar acesso negado;
- `404`: mostrar recurso inexistente;
- `409`: mostrar conflito;
- `422/400`: mostrar erros de formulário;
- `500`: mostrar erro genérico.

---

## 20. Boas práticas para controllers

Controllers devem:

1. Usar helpers de erro.
2. Retornar `{ errors: [...] }` em todos os erros conhecidos.
3. Mapear exceções de regra para status adequado.
4. Não vazar exceções internas.
5. Não retornar HTML em erro de API.
6. Validar JSON antes de passar ao use case.
7. Manter mensagens claras.
8. Usar códigos estáveis.
9. Usar `path` quando o erro for de campo.
10. Logar detalhes internos apenas no servidor, não na resposta.

---

## 21. Boas práticas para use cases

Use cases devem:

- lançar exceções de domínio/aplicação quando houver erro de regra;
- retornar resultado simples em sucesso;
- não retornar `jsonify`;
- não criar resposta HTTP diretamente;
- diferenciar recurso não encontrado de conflito;
- evitar capturar exceções técnicas sem necessidade;
- não transformar todo erro em `Exception` genérica.

---

## 22. Checklist de novo endpoint

Ao criar novo endpoint:

- [ ] Definir respostas de sucesso.
- [ ] Definir possíveis erros.
- [ ] Definir códigos estáveis.
- [ ] Definir status HTTP correto.
- [ ] Definir `path` para erros de campo.
- [ ] Usar helpers de erro.
- [ ] Não vazar stack trace.
- [ ] Documentar erros no arquivo da rota.
- [ ] Testar erro de autenticação.
- [ ] Testar erro de autorização.
- [ ] Testar validação de entrada.
- [ ] Testar recurso inexistente.

---

## 23. Pontos de atenção

1. O frontend deve usar `code`, não `message`, para lógica.
2. `message` pode mudar sem quebrar contrato.
3. `path` ajuda formulários e validação de manifesto.
4. `401` não é o mesmo que `403`.
5. Erro de validação de manifesto deve apontar JSONPath quando possível.
6. Conflitos de versão devem usar código específico.
7. Erro interno não deve expor detalhes.
8. Controllers devem centralizar tradução de exceções para HTTP.
9. Use cases não devem conhecer `jsonify`.
10. Padronizar códigos reduz bugs no Portal.

---

## 24. Documentos relacionados

```text
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/use-cases.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/manifesto-plugin.md
docs/06-portal-frontend/autenticacao-frontend.md
```

