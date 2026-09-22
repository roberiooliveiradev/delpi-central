# M-23 — GET /users 403 no create (@micha)

**Data:** 2026-09-22  
**Sintoma:** menu «Nenhum usuário encontrado»; Network `GET /users?q=micha` → 403.

## Cadeia

```text
@micha → listUsers → BFF GET /users
  → HLAPI GET /Administration/User
  → 403 ERROR_RIGHT_MISSING
```

## Causas (duas, independentes)

| # | Causa | Evidência | Correção |
|---|---|---|---|
| 1 | Perfil `Colaborador - Chamados` (id=1) tinha `glpi_profilerights.name=user` **rights=0** | user_id 69 (sessão portal); Technician rights=1055 → 206 | `UPDATE … SET rights=1` (READ) no GLPI |
| 2 | `=like=` case-sensitive: `@micha` ≠ `Michael` | pós-direito: `micha`→`[]`, `Micha`→id 8 | `build_user_search_filter` OR de variantes de caixa |

## Pós-correção (user 69, token OAuth vivo)

- `Administration/User` público + interno → **206**
- busca `micha` com variantes → encontra Michael (id 8) após deploy do filtro

## Nota E0

G-A4 Colaborador «206» assumia catálogo legível; no runtime o perfil 1 estava com `user=0`. Drift de direito GLPI, não bug do MFE M-23.
