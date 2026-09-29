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

## Monitoramento Industrial MVP

A página de monitoramento consulta `/monitoring` a cada 5 segundos em um único fluxo centralizado. O polling pausa com aba oculta ou navegador offline e retoma imediatamente ao voltar. Cronômetros são derivados de `stateStartedAt` com correção pelo `referenceAt` do servidor, sem requests por segundo.

Cada snapshot gera N cards sem fan-out. O detalhe usa os dados do card e consulta uma única timeline, somente ao abrir um run e apenas com `delpi-mes.history.view`. A visão cobre exclusivamente runs ativos; não representa catálogo de máquinas nem saúde/offline da telemetria.

Paradas e Histórico completos continuam nas fases seguintes.
