# 🔐 DELPI Central — Documentação Oficial de Segurança

## 1. Visão Geral

A arquitetura de segurança da **DELPI Central** foi projetada para fornecer um modelo robusto, escalável e auditável de controle de acesso para aplicações corporativas.

Ela é baseada em três camadas principais:

Authentication (JWT / Keycloak)
↓
RBAC (Roles, Groups, Permissions)
↓
Policy Engine (Regras de autorização avançadas)

Esse modelo permite separar claramente:

- **Quem é o usuário** (autenticação)
- **Quais permissões ele possui** (RBAC)
- **Quais ações ele pode executar** (Policies)

Essa abordagem segue padrões utilizados por plataformas modernas como:

- GitHub
- AWS IAM
- Laravel Policies
- Django Permissions

---

# 2. Authentication (Autenticação)

A autenticação da plataforma utiliza **JWT emitido pelo Keycloak**.

Toda requisição autenticada deve incluir o header:

Authorization: Bearer <token>

## Fluxo de autenticação

1. Requisição chega na API
2. Middleware valida o JWT
3. Claims são extraídas
4. Usuário é sincronizado no banco
5. RBAC é carregado
6. `g.current_user` é preenchido

Middleware responsável:

`auth_middleware.authenticate()`

---

## Estrutura de g.current_user

Após autenticação, o contexto da requisição passa a conter:

```python
{
    id: str
    email: str
    name: str
    roles: list[str]
    groups: list[str]
    permissions: list[str]
    is_superadmin: bool
}
```

Esse objeto é utilizado por **todos os mecanismos de autorização**.

---

# 3. RBAC — Role Based Access Control

A DELPI Central utiliza um modelo RBAC hierárquico.

## Estrutura

Permissions
↓
Roles
↓
Groups
↓
Users

## Relações

- Permissions são atribuídas a Roles
- Roles são atribuídas a Groups
- Groups são atribuídos a Users
- Users também podem receber roles diretamente

---

## Exemplo prático

Permissions:

- users.read
- users.manage

Role:

admin

permissions:

- users.read
- users.manage

Group:

IT

roles:

- admin

User:

João

Groups:

- IT

Resultado:

João possui automaticamente:

- users.read
- users.manage

---

# 4. Decorators de RBAC

O RBAC é aplicado através de decorators definidos em:

`security/authorization.py`

Esses decorators permitem validar permissões diretamente nas rotas.

---

## require_superadmin

Permite acesso apenas para usuários com privilégios de superadmin.

```python
@require_superadmin()
def reset_platform():
```

Validação:

user.is_superadmin == True

---

## require_permission

Exige que o usuário possua uma permissão específica.

```python
@require_permission("users.manage")
def create_user():
```

Validação:

permission ∈ user.permissions

Superadmins ignoram essa validação.

---

## require_any_permission

Permite acesso caso o usuário possua **qualquer uma das permissões listadas**.

```python
@require_any_permission([
    "users.read",
    "users.manage"
])
def list_users():
```

Validação lógica:

users.read OR users.manage

---

## require_all_permissions

Exige que o usuário possua **todas as permissões especificadas**.

```python
@require_all_permissions([
    "apps.manage",
    "routes.manage"
])
def update_route():
```

Validação lógica:

apps.manage AND routes.manage

---

# 5. Policy Engine

RBAC resolve apenas **regras simples de autorização**.

Exemplo:

"usuário possui permissão X?"

Entretanto, muitas regras de negócio são mais complexas.

Exemplo:

"pode deletar usuário MAS não pode deletar a si mesmo"

Para lidar com essas regras foi criado o **Policy Engine**.

Arquivo:

`security/policy_engine.py`

Responsabilidades:

- registrar policies
- executar policies
- aplicar bypass de superadmin
- retornar erros padronizados

---

## Fluxo de execução

Controller
↓
@policy decorator
↓
PolicyEngine.evaluate()
↓
Policy Function
↓
Controller executa

---

# 6. Registry Automático de Policies

Policies são registradas automaticamente através do decorator:

`@register_policy()`

Arquivo:

`security/decorators.py`

Exemplo:

```python
@register_policy()
def can_manage_users(user):
    return "users.manage" in user.permissions
```

Quando o módulo é carregado, a policy é automaticamente registrada no `PolicyEngine`.

---

# 7. Decorator @policy

O decorator `@policy` é utilizado para aplicar policies nos controllers.

Exemplo:

```python
@policy("can_delete_user")
def delete_user(user_id):
```

Funcionamento:

1. Obtém `g.current_user`
2. Executa policy
3. Se falhar retorna HTTP 403
4. Se passar executa o controller

---

# 8. Definição de Policies

Arquivo:

`security/policies.py`

Policies representam **regras de autorização mais complexas**.

---

## Exemplo: deletar usuário

```python
@register_policy()
def can_delete_user(user, user_id=None):

    if "users.manage" not in user.permissions:
        return False

    if str(user.id) == str(user_id):
        return False

    return True
```

Regras:

- usuário precisa da permissão users.manage
- usuário não pode deletar a si mesmo

---

## Exemplo: gerenciar RBAC

```python
@register_policy()
def can_manage_rbac(user):
    return "rbac.manage" in user.permissions
```

---

# 9. Criando uma Nova Policy

## Passo 1 — Definir função

```python
@register_policy()
def can_create_app(user):

    if "apps.manage" not in user.permissions:
        return False

    return True
```

---

## Passo 2 — Aplicar no controller

```python
@policy("can_create_app")
def create_app():
```

---

## Passo 3 — Garantir import

No startup da aplicação:

```python
import app.interfaces.http.security.policies
```

Sem isso as policies não são registradas.

---

# 10. Passando Parâmetros para Policies

Policies podem receber parâmetros vindos da rota.

Exemplo de rota:

DELETE /users/<user_id>

Controller:

```python
@policy("can_delete_user")
def delete_user(user_id):
```

Policy:

```python
def can_delete_user(user, user_id):
```

---

# 11. Bypass de Superadmin

Superadmins ignoram todas as policies.

Implementação:

```python
if user.is_superadmin:
    return True
```

Isso garante que administradores possam recuperar o sistema em cenários críticos.

---

# 12. Estrutura de Diretórios

```
security
 ├ authorization.py
 ├ policy_engine.py
 ├ decorators.py
 └ policies.py
```

---

# 13. Boas Práticas

## Use RBAC para regras simples

Exemplo:

GET endpoints

```
@require_permission("users.read")
```

---

## Use Policy para regras complexas

Exemplo:

```
@policy("can_delete_user")
```

---

# 14. Padrão Recomendado

GET endpoints → require_permission

POST endpoints → policy

PUT endpoints → policy

DELETE endpoints → policy

Exemplo:

GET /users → users.read

POST /users → policy(can_create_user)

DELETE /users → policy(can_delete_user)

---

# 15. Vantagens da Arquitetura

- Controllers limpos
- Lógica de segurança centralizada
- Regras reutilizáveis
- Fácil auditoria
- Fácil teste
- Escalabilidade

---

# 16. Possíveis Evoluções

A arquitetura permite evoluir para:

## Resource Based Policies

```
@policy("group.update")
```

## Policies baseadas em recurso

- owner
- tenant
- estado do recurso

## Audit Log de segurança

Registro de:

- usuário
- policy executada
- resultado
- timestamp

---

# Conclusão

O sistema de segurança da DELPI Central combina:

JWT Authentication
+
RBAC
+
Policy Engine

Esse modelo fornece um controle de acesso **flexível, escalável e seguro**, suportando tanto regras simples quanto validações complexas de negócio.

