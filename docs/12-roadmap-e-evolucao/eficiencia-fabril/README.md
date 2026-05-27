# Eficiência Fabril — plugin Minha DELPI

Dashboard gerencial de apontamentos de produção (eficiência operacional e resultado MOD), consumindo a view TOTVS `dbo.vw_Apontamentos_Eficiencia` via **api-delpi**.

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ROADMAP.md](./ROADMAP.md) | Fases de implantação, entregas, critérios de pronto e dependências |
| [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | Contrato da view TOTVS, fórmulas e literais validados |
| [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md) | Relatório da validação TOTVS (Fase 0) |

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Padrão MFE dashboard | `plugins/dashboard-lmps/` |
| Domínio Produção (api-delpi) | `api-delpi/app/interface/http/routes/production/` |
| Consulta TOTVS (LMPs) | `api-delpi/app/infrastructure/persistence/totvs/lmp_repositories/` |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |
| Contrato manifesto | [manifesto-plugin.md](../../05-plugin-system/manifesto-plugin.md) |

## Identificação do plugin

| Campo | Valor |
|-------|--------|
| `id` | `eficiencia-fabril` |
| `basePath` | `/apps/eficiencia-fabril` |
| Container Docker | `delpi-eficiencia-fabril` |
| API (gateway) | `/apps/api-delpi/production/eficiencia-fabril/*` |
| Fonte de dados | `dbo.vw_Apontamentos_Eficiencia` (SQL Server / Protheus) |
