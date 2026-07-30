# Filiais Protheus (sites Delpi)

Parte da [biblioteca de padrões TOTVS](./README.md).

---

## Códigos de filial

| Código | Site | Uso típico |
|--------|------|------------|
| **`01`** | **SC** (Santa Catarina) | Filial padrão em muitos dashboards e defaults de TV |
| **`02`** | **ES** (Espírito Santo) | Segunda unidade |

Campos comuns: `B2_FILIAL`, `BC_FILIAL`, `C2_FILIAL`, `D3_FILIAL`, etc. — sempre `LTRIM(RTRIM(...))` ao comparar.

---

## O que fazer

1. Tratar filial e armazém como eixos **independentes** (`B2_FILIAL` ≠ `B2_LOCAL`). Ver [armazem-custo.md](./armazem-custo.md).
2. Em plugins multi-filial: permissões granulares `.view.filial-sc` / `.view.filial-es` + gate na API (`branch_access_error`).
3. Documentar se a rota exige filial obrigatória ou consolida `01`+`02` quando omitida (ex.: alguns KPIs de refugo/% scrap).
4. Default UX de TV (`"01"`) só em catálogo TV — não forçar no `Query` se consolidado = vazio for a regra de negócio.

### O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| Usar `B2_LOCAL = '01'` quando a intenção era filial SC | Confunde almoxarifado com site |
| Confiar só no MFE para bloquear filial | Segurança fica na API (RBAC) |
| Hardcodar filial sem constante/domínio quando o módulo já tem conjunto válido | Ex.: `VALID_REFUGOS_BRANCHES` |

---

## Referências

- Checklist RBAC multi-filial: `.cursor/rules/new-api-route-checklist.mdc` (§ Dashboard MFE)
- Refugos: [scrap-monitoring.md](../scrap-monitoring.md)
- Estoque de segurança: [estoque-seguranca.md](../estoque-seguranca.md)
