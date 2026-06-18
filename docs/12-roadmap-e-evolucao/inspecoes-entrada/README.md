# Inspeções de Entrada — plugin Minha DELPI

Painel operacional de **inspeções de recebimento** (entrada de materiais), consumindo views TOTVS via **api-delpi**.

**Status (2026-06-18):** MVP em branch `feature/inspecoes-entrada` — backend completo (7 rotas), MFE com dashboard + histórico + detalhe/certificado.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ROADMAP.md](./ROADMAP.md) | Fases de implantação, entregas e critérios de pronto |
| [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md) | Funcionalidades implementadas (UI, abas, regras) |
| [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | Contrato das views TOTVS e mapeamento de colunas |
| [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md) | Procedimento de validação TOTVS (Fase 0) |
| [status-atual.md](./status-atual.md) | Snapshot do que funciona e pendências |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Plugin MFE | `plugins/inspecoes-entrada/` |
| Repository TOTVS | `api-delpi/app/infrastructure/persistence/totvs/inspecoes_entrada/` |
| Rotas HTTP | `api-delpi/app/interface/http/routes/inspecoes_entrada/` |
| Doc API | `api-delpi/docs/api/inspecoes-entrada.md` |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |
| Inventário plugins | [08-plugins/README.md](../../08-plugins/README.md) |

---

## Identificação do plugin

| Campo | Valor |
|-------|--------|
| `id` | `inspecoes-entrada` |
| `basePath` | `/apps/inspecoes-entrada` |
| Container Docker | `delpi-inspecoes-entrada` |
| Permissões Portal | `inspecoes-entrada.view.filial-01`, `.filial-02`, `.view` |
| Fonte de dados | Views `dbo.vw_minha_delpi_inspecoes_entrada_*` + `QER010` (detalhe ensaios) |

### Endpoints API (gateway)

| Método | Caminho | Uso no MFE v0.1 |
|--------|---------|-----------------|
| `GET` | `/apps/api-delpi/inspecoes-entrada/resumo` | Dashboard — KPIs |
| `GET` | `/apps/api-delpi/inspecoes-entrada/pendentes` | Dashboard — tabela pendências |
| `GET` | `/apps/api-delpi/inspecoes-entrada/pendentes-fornecedor` | Dashboard — gargalos |
| `GET` | `/apps/api-delpi/inspecoes-entrada/rejeitadas-produto` | Dashboard — rejeitadas |
| `GET` | `/apps/api-delpi/inspecoes-entrada/rejeitadas-ensaiador` | Reservado (API pronta) |
| `GET` | `/apps/api-delpi/inspecoes-entrada/historico` | Aba Histórico |
| `GET` | `/apps/api-delpi/inspecoes-entrada/historico/detalhe` | Modal detalhe + certificado |

---

## Acesso rápido (dev)

```text
http://localhost/apps/inspecoes-entrada/filial-01
http://localhost/apps/inspecoes-entrada/filial-02?tab=historico
```

Rebuild após alterações: [plugins/inspecoes-entrada/README.md](../../../plugins/inspecoes-entrada/README.md).
