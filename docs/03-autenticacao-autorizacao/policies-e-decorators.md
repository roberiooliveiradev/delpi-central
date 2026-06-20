# Minha DELPI — Policies e Decorators

> **Arquivo:** `docs/03-autenticacao-autorizacao/policies-e-decorators.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** decorators de autenticação/autorização, Policy Engine e padrões de proteção de rotas na Core API

---

## 1. Objetivo

Este documento descreve como a Core API protege endpoints HTTP usando decorators e policies.

A proteção de rotas na Minha DELPI é dividida em duas camadas:

```text
Autenticação → JWT/middleware
Autorização → decorators e policies
```

Decorators resolvem validações diretas, como "usuário autenticado" ou "usuário possui permissão X".

Policies resolvem regras mais complexas, como "usuário possui permissão e não está tentando deletar a si mesmo".

---

## 2. Arquivos principais

Arquivos reais envolvidos:

```text
app/interfaces/http/security/authorization.py
app/interfaces/http/security/policy_engine.py
app/interfaces/http/security/decorators.py
```

Documentos históricos também mencionam:

```text
app/interfaces/http/security/policies.py
```

Esse arquivo deve conter funções de policy registradas com `@register_policy`, quando policies forem usadas para regras complexas.

---

## 3. Separação de responsabilidades

| Componente | Responsabilidade |
|---|---|
| Middleware de autenticação | Validar JWT e preencher `g.current_user` |
| `require_auth` | Exigir usuário autenticado |
| `require_superadmin` | Exigir `is_superadmin=True` |
| `require_permission` | Exigir uma permission code |
| `require_any_permission` | Exigir pelo menos uma permission code |
| `require_all_permissions` | Exigir todas as permission codes |
| `PolicyEngine` | Executar policies registradas |
| `@register_policy` | Registrar função de policy |
| `@policy` | Aplicar policy a endpoint Flask |

---

## 4. Fluxo de uma rota protegida

Fluxo geral:

```text
Request HTTP
  ↓
Middleware valida JWT
  ↓
Core API popula g.current_user
  ↓
Decorator verifica autenticação/autorização
  ↓
Controller executa use case
  ↓
Resposta HTTP
```

Se o usuário não estiver autenticado:

```text
unauthorized
```

Se estiver autenticado, mas sem permissão:

```text
forbidden
```

---

## 5. `g.current_user`

Todos os decorators e o `PolicyEngine` dependem de:

```python
g.current_user
```

Estrutura conceitual:

```text
id
email
name
roles
groups
permissions
is_superadmin
```

Esse objeto é criado pelo middleware de autenticação após validação do JWT e sincronização do usuário local.

---

## 6. `require_auth`

O decorator `require_auth()` exige usuário autenticado.

Uso:

```python
@require_auth()
def get_me():
    ...
```

Regra:

```text
Se g.current_user não existir → unauthorized
Se existir → executa endpoint
```

Usar em endpoints que exigem login, mas não exigem permissão específica.

Exemplos:

```text
GET /me
GET /me/apps
GET /me/notifications
```

---

## 7. `require_superadmin`

O decorator `require_superadmin()` exige usuário autenticado e `is_superadmin=True`.

Uso:

```python
@require_superadmin()
def delete_user(user_id):
    ...
```

Regra:

```text
Sem usuário → unauthorized
Usuário não superadmin → forbidden("Superadmin required")
Superadmin → executa endpoint
```

Usar para operações de autoridade máxima.

---

## 8. `require_permission`

O decorator `require_permission(permission_code)` exige que o usuário tenha uma permission code específica.

Uso:

```python
@require_permission("apps.manage")
def register_plugin():
    ...
```

Regra:

```text
Sem usuário → unauthorized
Superadmin → bypass
Permissão presente em user.permissions → executa endpoint
Permissão ausente → forbidden("Permission denied")
```

Usar para regras simples de autorização.

---

## 9. `require_any_permission`

O decorator `require_any_permission([...])` permite acesso caso o usuário possua pelo menos uma das permissões listadas.

Uso:

```python
@require_any_permission(["users.view", "users.manage"])
def list_users():
    ...
```

Regra lógica:

```text
users.view OR users.manage
```

Superadmin bypassa a validação.

---

## 10. `require_all_permissions`

O decorator `require_all_permissions([...])` exige que o usuário possua todas as permissões listadas.

Uso:

```python
@require_all_permissions(["rbac.manage", "roles.manage"])
def update_role():
    ...
```

Regra lógica:

```text
rbac.manage AND roles.manage
```

Superadmin bypassa a validação.

---

## 11. Ordem dos decorators no Flask

A ordem recomendada é:

```python
@blueprint.get("/path")
@require_permission("apps.view")
def handler():
    ...
```

Ou seja:

```text
1. Decorator de rota Flask
2. Decorator de segurança
3. Função controller
```

Essa ordem mantém a rota registrada no Flask e aplica segurança no wrapper correto.

---

## 12. Decorators em controllers reais

A Core API usa decorators nos controllers administrativos.

Exemplo conceitual:

```python
@admin_apps_bp.get("")
@require_permission("apps.view")
def list_apps():
    ...
```

Exemplo conceitual:

```python
@admin_apps_bp.put("/<plugin_id>")
@require_permission("apps.manage")
def update_app(plugin_id):
    ...
```

Esse padrão deve ser repetido em novos endpoints.

---

## 13. Policy Engine

O `PolicyEngine` existe para regras que não cabem bem em uma simples permission code.

Exemplo de regra simples:

```text
Usuário possui users.manage?
```

Isso cabe em `require_permission`.

Exemplo de regra complexa:

```text
Usuário possui users.manage E não está tentando deletar a si mesmo?
```

Isso é melhor como policy.

---

## 14. Estrutura do `PolicyEngine`

O `PolicyEngine` mantém um registry interno:

```python
_registry: dict[str, callable]
```

Métodos principais:

```text
register(name, fn)
get(name)
list_policies()
evaluate(name, **context)
```

A avaliação usa `g.current_user`.

---

## 15. Fluxo do `PolicyEngine.evaluate`

Fluxo:

```text
Recebe nome da policy
  ↓
Obtém g.current_user
  ↓
Se não houver usuário, retorna unauthorized
  ↓
Se superadmin, retorna True
  ↓
Busca policy no registry
  ↓
Se não existir, lança RuntimeError
  ↓
Executa policy com user e contexto
  ↓
Se retorno falso, retorna forbidden
  ↓
Se retorno true, permite execução
```

---

## 16. `register_policy`

O decorator `register_policy` registra uma função no `PolicyEngine`.

Uso:

```python
@register_policy()
def can_manage_users(user):
    return "users.manage" in user.permissions
```

Nome padrão:

```text
nome da função
```

Também é possível registrar com nome explícito:

```python
@register_policy("users.delete")
def can_delete_user(user, user_id):
    ...
```

---

## 17. `policy`

O decorator `policy(name)` aplica uma policy registrada a um endpoint Flask.

Uso:

```python
@policy("can_delete_user")
def delete_user(user_id):
    ...
```

Fluxo:

```text
PolicyEngine.evaluate(name, **kwargs)
  ↓
Se retornar True, controller executa
  ↓
Se retornar resposta de erro, ela é retornada ao cliente
```

---

## 18. Exemplo de policy para deletar usuário

Exemplo conceitual:

```python
@register_policy()
def can_delete_user(user, user_id=None):
    if "users.manage" not in user.permissions:
        return False

    if str(user.id) == str(user_id):
        return False

    return True
```

Regras aplicadas:

- exige permissão `users.manage`;
- impede deletar a si mesmo;
- superadmin bypassa pela engine antes de executar a policy.

---

## 19. Quando usar decorator simples

Usar decorators simples quando a regra for apenas permissão/autenticação.

Exemplos:

```text
GET /admin/apps → require_permission("apps.view")
POST /admin/apps/register → require_permission("apps.manage")
GET /me → require_auth()
```

---

## 20. Quando usar policy

Usar policy quando a regra depender de contexto.

Exemplos:

- impedir usuário deletar a si mesmo;
- impedir remover último superadmin;
- validar ownership de recurso;
- validar estado do recurso;
- validar relação entre usuário, grupo, app ou plugin;
- aplicar regra composta com múltiplas condições.

---

## 21. Cuidados com policies

1. Policy deve ser função pequena e testável.
2. Policy deve receber `user` e parâmetros de contexto.
3. Policy não deve executar regra de negócio principal do use case.
4. Policy não deve abrir transação complexa.
5. Policy não deve retornar `jsonify`; deve retornar boolean quando possível.
6. Regras com consulta de banco devem ser bem justificadas.
7. Superadmin já é tratado pela engine.
8. Policies precisam ser importadas no bootstrap para registro.

---

## 22. Import obrigatório das policies

Policies registradas por decorator só entram no registry se o módulo for importado.

Se existir arquivo:

```text
app/interfaces/http/security/policies.py
```

ele deve ser importado no bootstrap da aplicação.

Sem import:

```text
Policy não registrada
PolicyEngine.evaluate → RuntimeError
```

---

## 23. Erros retornados

Decorators e policies usam helpers padronizados de erro.

Erros comuns:

```text
unauthorized
forbidden
```

Formato esperado:

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

---

## 24. Relação com RBAC

Decorators leem permissões efetivas em:

```text
g.current_user.permissions
```

Essas permissões são calculadas antes pelo Permission Resolver, a partir de:

- roles diretas;
- roles via grupos;
- overrides individuais;
- superadmin.

Portanto, decorators não devem recalcular RBAC.

---

## 25. Relação com o Portal

O Portal pode ocultar botões com base em `/me.permissions`, mas isso é apenas UX.

A segurança final está nos decorators e policies da Core API.

Exemplo:

```text
Botão Registrar Plugin oculto no Portal
  ↓
Endpoint POST /admin/apps/register continua protegido por apps.manage
```

---

## 26. Boas práticas

1. Toda rota sensível deve ter decorator de segurança.
2. Use `require_auth` para rotas autenticadas sem permissão específica.
3. Use `require_permission` para autorização simples.
4. Use `require_any_permission` quando houver permissão alternativa.
5. Use `require_all_permissions` para exigência composta simples.
6. Use `require_superadmin` para operações de autoridade máxima.
7. Use policies para regras com contexto.
8. Não duplicar regra de autorização no frontend.
9. Não acessar banco diretamente em decorators simples.
10. Testar endpoints com usuário sem permissão e com superadmin.

---

## 27. Checklist de nova rota protegida

- [ ] A rota exige autenticação?
- [ ] A rota exige uma permission code?
- [ ] A rota exige superadmin?
- [ ] A regra depende de contexto do recurso?
- [ ] Decorator correto foi aplicado?
- [ ] Se for policy, ela está registrada/importada?
- [ ] Superadmin deve bypassar essa regra?
- [ ] Erro 401 foi testado?
- [ ] Erro 403 foi testado?
- [ ] O Portal não é a única barreira?

---

## 28. Documentos relacionados

```text
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/permission-resolver.md
docs/03-autenticacao-autorizacao/superadmin.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/erros-api.md
```
