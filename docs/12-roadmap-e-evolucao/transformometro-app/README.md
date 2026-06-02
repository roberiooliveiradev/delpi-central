# Transformômetro — aplicação Minha Delpi

Documentação de arquitetura e plano de entrega do **Transformômetro** como produto independente no monorepo Delpi Central (API dedicada + plugin microfrontend), no mesmo padrão do [Strategic Indicators](../../../strategic-indicators-api/docs/README.md).

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [OVERVIEW.md](./OVERVIEW.md) | Visão geral, objetivo, componentes, URLs, permissões |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Camadas, domínio, cálculo, banco, integração portal |
| [PLAYBOOK-MODELAGEM.md](./PLAYBOOK-MODELAGEM.md) | Contrato vivo de modelagem, vigência, atividade, investimentos, recursos e cálculo |
| [ROADMAP.md](./ROADMAP.md) | Fases de entrega, dependências, o que reaproveitar do legado |
| [ESPECIFICACAO.md](./ESPECIFICACAO.md) | Especificação funcional completa (origem: planilha + Apps Script) |
| [OPERATIONS.md](./OPERATIONS.md) | Runbook: import, recalcular, planilha, troubleshooting |
| [status-atual.md](./status-atual.md) | Snapshot do que está em produção |
| [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md) | Docker, compose, migrations, checklist |

## Legado hoje no monorepo

| Peça | Situação atual |
|------|----------------|
| Planilha Google Sheets | Fonte operacional (`transforma_mais`) |
| Cálculo | `ProcessSummaryCalculator` em `strategic-indicators-api` e `api-delpi` |
| Leitura HTTP | `GET .../engineering/transforma-mais/processes` (api-delpi) |
| UI parcial | `plugins/dashboard-engineering` (lista/resumo, somente leitura) |

A nova aplicação **substitui o cadastro na planilha** por CRUD na API + Postgres, mantendo as **mesmas regras de cálculo** validadas na análise de maio/2026.

## Referências

- Modelagem e fórmulas: [documentos/documentacao_modelagem_transformometro.md](../../../documentos/documentacao_modelagem_transformometro.md)
- Rotas legado Transforma+: [documentos/Routes/documentacao_rota_transforma_mais.md](../../../documentos/Routes/documentacao_rota_transforma_mais.md)
