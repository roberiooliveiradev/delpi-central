# Controle de Retrabalhos — plugin Minha DELPI

Dashboard de horas improdutivas de retrabalho (motivo `RT`) por filial, consumindo view TOTVS via **api-delpi**.

**Status (2026-07):** MVP entregue — MFE + 7 rotas HTTP + RBAC por filial.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | View TOTVS, filtros SQL, validação Fase 0 |
| [Plugin README](../../../plugins/controle-retrabalhos/README.md) | Dev, smoke, permissões, estrutura |
| [API controle-retrabalhos.md](../../../api-delpi/docs/api/controle-retrabalhos.md) | Contrato HTTP completo |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Plugin MFE | `plugins/controle-retrabalhos/` |
| SQL / repository | `api-delpi/app/infrastructure/persistence/totvs/retrabalho/` |
| Rotas HTTP | `api-delpi/app/interface/http/routes/retrabalho/` |
| RBAC filial | `retrabalho_branch_access.py` |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |
| Inventário plugins | [08-plugins/README.md](../../08-plugins/README.md) |

---

## Identificação

| Campo | Valor |
|-------|--------|
| `id` | `controle-retrabalhos` |
| `basePath` | `/apps/controle-retrabalhos` |
| Container Docker | `delpi-controle-retrabalhos` |
| Permissões | `.view.filial-sc`, `.view.filial-es`, `.view`, `.access`, `.export` |
| View TOTVS | `dbo.VW_BI_RT_HORAS_IMPRODUTIVAS` |

---

## Acesso rápido (dev)

```text
http://localhost/apps/controle-retrabalhos/sc
http://localhost/apps/controle-retrabalhos/es
```
