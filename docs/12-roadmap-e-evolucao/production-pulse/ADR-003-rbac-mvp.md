# ADR-003 — RBAC MVP (operador vs supervisor)

**Status:** aceito (set/2026)  
**Contexto:** operador de chão de fábrica não deve ter CRUD; supervisor precisa reset no painel sem rota operador.

**Referências de mercado:** least privilege (OWASP); separação **operator** vs **administrator** em MES/SCADA leve; BFF valida permissão **por rota**, MFE só oculta UI.

---

## Decisão

### Permissões base (manifesto)

| Código | Papel típico |
|--------|----------------|
| `production-pulse.access` | Entrar no plugin (menu) |
| `production-pulse.devices.view` | Supervisor — painel, detalhe, histórico |
| `production-pulse.devices.manage` | TI/manutenção — CRUD, binding, test-probe, poll-all |
| `production-pulse.devices.command` | Supervisor — comandos hardware **no painel admin** |
| `production-pulse.operator` | Operador — hub, picker, superfície, comandos **só na rota operador** |
| `production-pulse.view.filial-XX` | Escopo filial |
| `production-pulse.admin` | Todas filiais |

### Matriz MVP (API — fonte de verdade)

| Ação | `operator` | `devices.view` | `devices.manage` | `devices.command` |
|------|:----------:|:--------------:|:----------------:|:-----------------:|
| `GET /operator/*` | ✓ | — | — | — |
| Comandos `increment/decrement/reset` **via rota operador** | ✓ | — | — | — |
| `GET /devices`, `/summary`, `/readings`, `/live` | — | ✓ | ✓ | ✓ |
| `POST /devices/{id}/poll` (refresh manual) | — | ✓ | ✓ | ✓ |
| `POST /devices/poll-all` | — | — | ✓ | — |
| `POST /devices/test-probe`, `POST /devices/{id}/test` | — | — | ✓ | — |
| CRUD + binding | — | — | ✓ | — |
| Comandos **no detalhe/painel admin** | — | — | ✓ | ✓ |
| `GET /catalog/*` | — | ✓ | ✓ | ✓ |

**Regras fechadas:**

1. **`operator` basta** para +/−/zerar na superfície operador — **não** exige `devices.view` nem `devices.command`.
2. **`devices.command`** habilita comandos nas rotas **admin** (`/devices/{id}/commands/*`).
3. **`devices.manage`** implica comandos admin (supervisor técnico).
4. Toda rota com comando exige **capability do driver** (R18) — permissão sozinha não basta.
5. Filial: gate `branch_access` em **todas** as rotas acima + `view.filial-XX` ou `admin`.

### MFE

- Ocultar ações sem permissão (não `disabled` confuso) — [DESIGN-FRONTEND.md §6](./DESIGN-FRONTEND.md).
- Operador: menu «Operador · Pulso» só com `operator`.
- Link «Painel administrativo» na BrandBar só com `devices.view`.

### Fora do MVP (Fase 4)

- Matriz por filial granular além de `view.filial-XX`.
- Audit export / delegação temporária.

---

## Consequências

- Testes `test_permissions.py`: operador comanda sem `devices.view`; viewer não comanda.
- Manifest [MANIFEST-DRAFT.md](./MANIFEST-DRAFT.md) permanece válido.
