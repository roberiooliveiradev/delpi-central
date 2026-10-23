# 🔐 Guia Completo — Implementação de Proteção de Rotas na Core API (DELPI Central)

---

# 📌 Objetivo

Este documento descreve de forma detalhada como implementar proteção de rotas na **Core API (Flask)** utilizando:

- JWT validado via Keycloak
- Middleware de autenticação
- Decorators de autorização
- Permissões baseadas em RBAC
- Integração com arquitetura event-driven

Este guia é voltado tanto para iniciantes quanto para desenvolvedores experientes.

---

# 🏗 Arquitetura de Segurança

Fluxo completo de uma requisição protegida:

```
Request HTTP
      ↓
JWT Middleware (valida token)
      ↓
Popula g.current_user
      ↓
Decorator verifica permissão
      ↓
Controller executa UseCase
```

Separação de responsabilidades:

| Camada | Responsabilidade |
|--------|------------------|
| Middleware | Autenticação (validar JWT) |
| Decorators | Autorização (verificar permissão) |
| UseCases | Regra de negócio |
| EventHandler | Sincronização IAM / Cache |

---

# 1️⃣ Middleware de Autenticação

## 🎯 Objetivo

- Validar JWT recebido no header Authorization
- Extrair dados do usuário
- Popular `g.current_user`

---

## ✅ Exemplo de Middleware

```python
# app/interfaces/http/auth_middleware.py

from flask import request, g
from delpi_auth.jwt_validator import validate_token


def authenticate():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        g.current_user = None
        return

    token = auth_header.split(" ", 1)[1]

    try:
        payload = validate_token(token)
    except Exception:
        g.current_user = None
        return

    g.current_user = {
        "id": payload.get("sub"),
        "is_superadmin": payload.get("is_superadmin", False),
        "permissions": payload.get("permissions", []),
    }
```

---

# 2️⃣ Decorators de Autorização

Arquivo:

```
app/interfaces/http/security/authorization.py
```

---

## 🔹 require_superadmin

```python
@require_superadmin()
def route():
    ...
```

Permite acesso apenas a usuários com `is_superadmin=True`.

---

## 🔹 require_permission

```python
@require_permission("rbac.user.manage")
def route():
    ...
```

Valida se a permissão está na lista do usuário.

---

## 🔹 require_any_permission

```python
@require_any_permission(["reports.read", "reports.admin"])
def route():
    ...
```

Permite acesso se o usuário tiver pelo menos uma das permissões.

---

# 3️⃣ Ordem Correta dos Decorators

⚠️ IMPORTANTE: No Flask, a ordem importa.

```python
@bp.route("/admin/users", methods=["POST"])
@require_permission("rbac.user.create")
def create_user():
    ...
```

Sempre:

1. `@route`
2. `@require_permission`

---

# 4️⃣ Exemplo Prático Completo

## 🔹 Rota para substituir roles de usuário

```python
@bp.route("/admin/rbac/users/<user_id>/roles", methods=["PUT"])
@require_permission("rbac.user.manage")
def replace_user_roles(user_id):

    data = request.json
    role_ids = data.get("roleIds", [])

    with SqlAlchemyUnitOfWork() as uow:
        usecase = ReplaceUserRolesUseCase(uow)
        result = usecase.execute(user_id, role_ids)

    return jsonify(result)
```

---

# 5️⃣ Boas Práticas

## ✅ Use constantes para permissões

```python
# app/domain/constants/permissions.py

RBAC_USER_MANAGE = "rbac.user.manage"
```

Uso:

```python
@require_permission(RBAC_USER_MANAGE)
```

Evita erros de digitação.

---

## ✅ Nunca valide permissão dentro do UseCase

❌ Errado:

```python
if not user.has_permission(...):
    raise Exception()
```

✔ Correto:

- Middleware valida identidade
- Decorator valida permissão
- UseCase executa regra pura

---

# 6️⃣ Testando a Proteção

### 🔎 Caso 1 — Usuário sem token

Resultado esperado:

```
401 Unauthorized
```

---

### 🔎 Caso 2 — Usuário sem permissão

Resultado esperado:

```
403 Permission denied
```

---

### 🔎 Caso 3 — Superadmin

Sempre deve permitir acesso.

---

# 7️⃣ Integração com Event-Driven RBAC

Após alteração de roles/permissões:

1. UseCase publica evento
2. EventBus executa handler
3. Cache invalidado
4. IAM sincronizado

Isso garante que o JWT emitido posteriormente já reflita as mudanças.

---

# 8️⃣ Checklist Final

✔ Middleware valida JWT
✔ g.current_user populado
✔ Decorators aplicados nas rotas
✔ UseCases sem lógica de autorização
✔ Permissões centralizadas
✔ Eventos sincronizando IAM

---

# 🏆 Resultado Final

Sua Core API agora possui:

- 🔐 Autenticação baseada em JWT (Keycloak)
- 🎯 Autorização por permissão
- 🧠 Separação clara de responsabilidades
- 🔄 Sincronização automática via eventos
- 🏗 Arquitetura limpa e escalável

---

# 🚀 Próximos Níveis Possíveis

- Policy-based authorization
- Proteção dinâmica por módulo/app
- Integração com OpenAPI Security Schemes
- Auditoria automática por decorator

---

**Documento oficial da DELPI Central — Proteção de Rotas Core API**

