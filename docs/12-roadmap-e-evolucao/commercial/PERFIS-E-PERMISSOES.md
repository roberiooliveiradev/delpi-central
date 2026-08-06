# Perfis e permissões — Portal Comercial

> **Objetivo:** criar **papéis** na Minha Delpi (Core RBAC) e atribuí-los a usuários/grupos — sem permissões soltas no usuário e **sem** códigos que nomeiem persona (`commercial.vendedor`, etc.).  
> **Modelo:** [permission-resolver.md](../../03-autenticacao-autorizacao/permission-resolver.md)  
> **Manifest:** [commercial.manifest.json](../../../plugins/commercial/commercial.manifest.json)

## Princípio

```text
Usuário → Papel(éis) Minha Delpi → permission codes (capacidades) → API / MFE
```

| É | Não é |
|---|--------|
| `commercial.accounts.view` (capacidade) | `commercial.vendedor` / `permissao.vendedor` |
| Papel **Comercial — Vendedor** (agrupa codes) | Atribuir 15 codes soltos no usuário |
| Escopo `own\|team` na **API** (carteira) | Permission `commercial.scope.team` |

## Catálogo Wave G (manifest + commercial-api)

| Código | Nome UI | Onde vale |
|--------|---------|-----------|
| `commercial.accounts.view` | Acessar Portal Comercial | App, Início, pedidos, carteira, conta; aliases: `pedidos-venda-abertos.access`, `api-delpi.access` |
| `commercial.worklist.view` | Ver Meu dia / worklist | Menu `/my-day`, `GET /me/worklist`, `GET /tasks` |
| `commercial.followups.manage` | Gerir follow-ups próprios | `POST /tasks`, complete, `POST /activities` |
| `commercial.seller-portfolios.manage` | Administrar carteiras | Admin carteiras; alias: `pedidos-venda-abertos.admin` |
| `commercial.audit.view` | Ver auditoria comercial | `GET /audit` (quando exposto) |

**Home:** usa `commercial.accounts.view` (não há `commercial.home.view` separado na Wave G).

Códigos Wave H+ (pipeline, forecast, samples…) ficam no playbook §9 — **não** ativar no manifest até o MFE/API checarem.

## Papéis sugeridos (criar na Minha Delpi)

| Papel (nome sugerido) | Objetivo | Permission codes |
|-----------------------|----------|------------------|
| **Comercial — Vendedor** | Carteira própria, pedidos, Meu dia, conta 360 | `commercial.accounts.view`, `commercial.worklist.view`, `commercial.followups.manage` |
| **Comercial — Supervisor** | Mesmo que vendedor; visão equipe via escopo API + home gestão | mesmos codes do Vendedor (+ `seller-portfolios.manage` **não** incluído) |
| **Comercial — Admin carteiras** | Configurar vendedores/carteiras | Supervisor + `commercial.seller-portfolios.manage` |
| **Comercial — Auditor (leitura)** | Consulta + audit | `commercial.accounts.view`, `commercial.audit.view` |
| **Comercial — Full (Wave H+)** | Pipeline/forecast futuros | documentar depois; não criar agora |

Supervisor vs Vendedor: a diferença de **dados** (equipe) não é um permission code de persona — é resolução de escopo na commercial-api / api-delpi quando o usuário tem carteiras/equipe. Na Wave G, admin (`seller-portfolios.manage`) já enxerga lista de vendedores no filtro.

## Como criar o papel Vendedor (3 passos)

1. **Admin Minha Delpi → Papéis → Novo**  
   Nome: `Comercial — Vendedor`
2. **Marcar permissões:**
   - [ ] `commercial.accounts.view`
   - [ ] `commercial.worklist.view`
   - [ ] `commercial.followups.manage`
3. **Atribuir** o papel ao usuário ou ao grupo (evitar `user_permissions` diretas salvo exceção auditada).

Repetir para Admin carteiras incluindo `commercial.seller-portfolios.manage`.

## Aliases Portal do Vendedor (até F2c)

| Legado | Equivalente commercial |
|-------|------------------------|
| `pedidos-venda-abertos.access` | leitura (`accounts.view`) |
| `pedidos-venda-abertos.admin` | `seller-portfolios.manage` |

No cutover F2c, migrar papéis para só `commercial.*`.

## O que NÃO fazer

- Inventar permission com nome de cargo/persona.
- Confundir role Keycloak com papel Delpi (resolver Core é a fonte).
- Usar o MFE como única barreira — API revalida codes.
- Dar `seller-portfolios.manage` a todo vendedor “para facilitar”.

## Checklist homologação RBAC

- [ ] Papel Vendedor criado; menu mostra Início, Meu dia, Pedidos, Carteira; **não** Carteiras admin
- [ ] Sem `worklist.view` → `/my-day` oculto / 403 na API
- [ ] Sem `followups.manage` → não cria/completa tarefa (403)
- [ ] Admin carteiras vê `/seller-portfolios`
- [ ] PVA ainda acessível com aliases legados (F2c não aplicado)
