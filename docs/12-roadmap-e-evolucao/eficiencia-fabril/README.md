# Eficiência Fabril — plugin Minha DELPI

Dashboard gerencial de apontamentos de produção (eficiência operacional e resultado MOD), consumindo a view TOTVS `dbo.vw_Apontamentos_Eficiencia` via **api-delpi**.

**Status (2026-05-28):** MVP funcional em desenvolvimento — plugin deployável, UI completa, filtros locais e exportação Excel.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ROADMAP.md](./ROADMAP.md) | Fases de implantação, entregas e critérios de pronto |
| [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md) | **Funcionalidades implementadas** (UI, KPIs, gráficos, regras) |
| [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | Contrato da view TOTVS, fórmulas e literais |
| [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md) | Relatório da validação TOTVS (Fase 0) |
| [regras-faixa-eficiencia-producao.md](../../../api-delpi/docs/api/regras-faixa-eficiencia-producao.md) | Faixa válida **0–199%** (alinhada ao OEE) |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Plugin MFE | `plugins/eficiencia-fabril/` |
| Repository TOTVS | `api-delpi/app/infrastructure/persistence/totvs/eficiencia_fabril/` |
| Rotas Produção | `api-delpi/app/interface/http/routes/production/production_router.py` |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |
| Inventário plugins | [08-plugins/README.md](../../08-plugins/README.md) |

---

## Identificação do plugin

| Campo | Valor |
|-------|--------|
| `id` | `eficiencia-fabril` |
| `basePath` | `/apps/eficiencia-fabril` |
| Container Docker | `delpi-eficiencia-fabril` |
| Permissão Portal | `eficiencia-fabril.view` |
| Fonte de dados | `dbo.vw_Apontamentos_Eficiencia` (SQL Server / Protheus) |

### Endpoints API (gateway)

| Método | Caminho | Uso |
|--------|---------|-----|
| `GET` | `/apps/api-delpi/production/eficiencia-fabril/appointments` | Carga bulk do período (MFE atual) |
| `GET` | `/apps/api-delpi/production/eficiencia-fabril/dashboard` | Agregado paginado no SQL (smoke / legado) |

---

## Acesso rápido (dev)

```text
http://localhost/apps/eficiencia-fabril/
```

Rebuild após alterações no plugin: ver [plugins/eficiencia-fabril/README.md](../../../plugins/eficiencia-fabril/README.md).
