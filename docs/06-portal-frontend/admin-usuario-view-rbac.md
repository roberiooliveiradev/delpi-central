# Portal — Usuário admin view-first + árvores RBAC

> **Código:** `portal/src/ui/admin/rbac/`  
> **API:** `GET /core-api/admin/rbac/users/{id}/access-profile` (`rbac.manage`)

Página de detalhe do usuário no Admin com **modo visualização por padrão** e edição explícita. Três árvores de acesso (Resumo unificada, Papéis, Grupos) consomem um único endpoint de perfil.

---

## Fluxos

| Fluxo | URL / ação |
|-------|------------|
| Ver usuário (lista) | `/admin/users/:id` ou clique no card |
| Editar | botão **Editar** → `?mode=edit` |
| Cancelar | remove `mode=edit`, descarta draft |
| Salvar | `PUT /admin/rbac/users/:id` → volta ao view + refresh access-profile |
| Deep link aba | `?tab=roles|groups|usage|summary` |
| Deep link edição | `?mode=edit&tab=roles` |

---

## Modos

### View (default)

- Título: `Usuário — {email}`
- Ações: **Voltar**, **Editar**
- **Resumo:** identidade read-only + árvore **unificada** (`variant="unified"`)
- **Papéis:** árvore só de papéis efetivos com badge de origem (`variant="roles"`)
- **Grupos:** árvore só de membership (`variant="groups"`)
- **Uso:** analytics (herda [meu-uso-perfil-e-admin.md](./meu-uso-perfil-e-admin.md))

### Edit (`?mode=edit`)

- Título: `Editar usuário — {email}`
- Ações: **Voltar**, **Cancelar**, **Salvar**
- **Resumo:** data de nascimento + toggle superadmin (sem árvore)
- **Papéis diretos / Grupos:** `RelationshipPicker` (dual-list)

---

## Hierarquia da árvore

```text
Papel ou Grupo
└─ App
   └─ Permissões (badges)
```

Permissões sem app/rota correspondente → nó **Outras permissões**.

Util canônico: `portal/src/ui/admin/rbac/rbacAccessTree.ts`  
Componente: `RbacAccessTree.tsx` (variants `unified` | `roles` | `groups`)

---

## Módulos principais

| Arquivo | Responsabilidade |
|---------|------------------|
| `UserEditPage.tsx` | Shell, tabs, save/cancel |
| `useUserPageMode.ts` | `mode=edit`, `tab=` na URL |
| `useAdminUserAccessProfile.ts` | Fetch access-profile |
| `UserSummaryTab.tsx` | Resumo view/edit |
| `UserRolesViewTab.tsx` / `UserGroupsViewTab.tsx` | Abas view |
| `UserRolesEditTab.tsx` / `UserGroupsEditTab.tsx` | Abas edit |
| `userAccessProfileTypes.ts` | Contrato TypeScript |

---

## Backend

Use case canônico: `GetUserAccessProfileUseCase`  
Wrapper titular: `GetMyAccessProfileUseCase` → `GET /me/access-profile`  
Admin: `GET /admin/rbac/users/{userId}/access-profile`

Payload: `roles[]` (com `sources`, `permissions`, `apps`), `groups[]`, `effectivePermissions`, `effectiveApps`, `isSuperadmin`.

---

## Relacionados

- [rbac.md](../03-autenticacao-autorizacao/rbac.md) — modelo RBAC
- [meu-uso-perfil-e-admin.md](./meu-uso-perfil-e-admin.md) — aba Uso
