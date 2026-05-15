# Minha DELPI — Autorização no Portal (UX)

> **Arquivo:** `docs/06-portal-frontend/app-authorization.md`  
> **Status:** documentação oficial  
> **Implementação:** `portal/src/routes/ProtectedRoute.tsx`

---

## 1. Camadas de autorização

| Camada | Responsável | Finalidade |
|---|---|---|
| Core API / API DELPI | Backend | **Segurança real** — decorators, use cases |
| `/me/apps` | Core API | Menu e rotas já filtrados |
| `ProtectedRoute` | Portal | Bloqueio de navegação React (UX) |
| Sidebar / Admin link | Portal | Ocultar links sem permissão |

---

## 2. `ProtectedRoute`

```tsx
export const ProtectedRoute = ({ permission, children }) => {
  const { user, coreLoaded } = useContext(AuthContext);

  if (!coreLoaded) return <Loader />;
  if (!user) return <Navigate to="/unauthorized" />;

  if (user.is_superadmin) return children;
  if (!permission) return children;

  if (!user.permissions.includes(permission))
    return <Navigate to="/unauthorized" />;

  return children;
};
```

Regras:

- **Superadmin** passa em qualquer rota com `permission` definida
- Sem `permission` prop → apenas exige usuário carregado
- Aguarda `coreLoaded` para evitar flash de unauthorized

---

## 3. Permissões por rota de plugin

Cada rota do manifesto pode declarar `permission`. O Portal repassa para `ProtectedRoute`.

A Core API **já não retorna** rotas sem permissão — o guard é defesa em profundidade se o usuário acessar URL direta antes de reload.

---

## 4. Área admin

```tsx
<ProtectedRoute permission="rbac.manage">
  <AdminPage />
</ProtectedRoute>
```

Operações dentro do admin (apps, roles) exigem permissões adicionais no backend (`apps.manage`, etc.). A aba pode carregar e falhar com 403 se o usuário só tiver `rbac.manage` parcial — tratar erros HTTP no `adminApi`.

---

## 5. Uso de `user.permissions`

Vindas de `GET /me`:

```json
{
  "permissions": ["api-delpi.access", "dash-lmps.access"],
  "is_superadmin": false
}
```

Usar para:

- mostrar link Admin
- condicionar botões na Home

Não usar para:

- substituir validação server-side
- decidir acesso a dados em API DELPI sem checar no backend

---

## 6. Documentos relacionados

- [autenticacao-frontend.md](./autenticacao-frontend.md)
- [../03-autenticacao-autorizacao/rbac.md](../03-autenticacao-autorizacao/rbac.md)
- [../03-autenticacao-autorizacao/permission-resolver.md](../03-autenticacao-autorizacao/permission-resolver.md)
