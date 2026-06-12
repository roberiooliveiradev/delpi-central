# Transformômetro — aplicação Minha Delpi

Documentação de arquitetura e plano de entrega do **Transformômetro** como produto independente no monorepo Delpi Central (API dedicada + plugin microfrontend), no mesmo padrão do [Strategic Indicators](../../../strategic-indicators-api/docs/README.md).

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [OVERVIEW.md](./OVERVIEW.md) | Visão geral, objetivo, componentes, URLs, permissões |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Camadas, domínio, cálculo, banco, integração portal |
| [PLAYBOOK-MODELAGEM.md](./PLAYBOOK-MODELAGEM.md) | Contrato vivo de modelagem, vigência, atividade, investimentos, recursos e cálculo |
| [PLAYBOOK-18-instancias-filial-setor-escopo.md](./PLAYBOOK-18-instancias-filial-setor-escopo.md) | Refatoração: instâncias operacionais, filiais/setores UUID, escopo híbrido de recursos, visões consolidado/filial/dept |
| [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md) | Status técnico S1–S10 + MFE §9 (API) |
| [regras-de-calculo.md](../../../transformometro-api/docs/regras-de-calculo.md) | Fórmulas oficiais + escopo de recurso e visões |
| [status-atual.md](./status-atual.md) | Snapshot do que está em produção / deploy |
| [ROADMAP.md](./ROADMAP.md) | Fases de entrega e Playbook 18 |
| [ESPECIFICACAO.md](./ESPECIFICACAO.md) | Especificação funcional (planilha + Apps Script) |
| [OPERATIONS.md](./OPERATIONS.md) | Runbook operacional e deploy Playbook 18 |
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
