# Delpi MES — MFE

Microfrontend gerencial do Delpi MES, integrado à Minha DELPI por Module Federation.

## Arquitetura

```text
Portal → plugins/delpi-mes → JWT → delpi-mes-api → S2S → production-control-api
```

O MFE consome exclusivamente `/apps/delpi-mes-api`. Não contém regra industrial, não acessa Production Control/Pulse/cockpit e não armazena token.

## Rotas

- `/apps/delpi-mes` → monitoramento;
- `/apps/delpi-mes/monitoring?branch=01`;
- `/apps/delpi-mes/downtimes?branch=01`;
- `/apps/delpi-mes/history?branch=01`.

A filial permanece na URL: `01 · SC` ou `02 · ES`.

## Permissões

- `delpi-mes.access`;
- `delpi-mes.monitoring.view`;
- `delpi-mes.downtimes.view`;
- `delpi-mes.history.view`;
- `delpi-mes.view.filial-01`;
- `delpi-mes.view.filial-02`.

O frontend usa as permissões apenas para experiência visual; o backend continua sendo a autoridade.

## Desenvolvimento

```bash
npm install
npm run test
npm run typecheck
npm run lint
npm run build
```

Para subir com a infraestrutura canônica:

```bash
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build delpi-mes
```

## Manifesto

`delpi-mes.manifest.json` está pronto para importação manual. Esta entrega não registra o manifesto nem busca token administrativo.

## Escopo da Fase 2

A shell, navegação, permissões, filial, HTTP client e integração federada estão prontas. Monitoramento com dados, paradas e histórico completos pertencem às fases seguintes.
