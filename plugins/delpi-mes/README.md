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
- `/apps/delpi-mes/history?branch=01`;
- `/apps/delpi-mes/registrations` → hub de Cadastros;
- `/apps/delpi-mes/registrations/downtime-reasons` → catálogo de motivos de parada.

A filial permanece na URL: `01 · SC` ou `02 · ES` — exceto em Cadastros, que é uma área global e não carrega `branch`.

## Permissões

- `delpi-mes.access`;
- `delpi-mes.monitoring.view`;
- `delpi-mes.downtimes.view`;
- `delpi-mes.history.view`;
- `delpi-mes.view.filial-01`;
- `delpi-mes.view.filial-02`;
- `delpi-mes.downtime-reasons.manage` — área Cadastros (criar, editar, ativar e desativar motivos de parada).

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

Cada snapshot gera N cards sem fan-out. O detalhe usa os dados do card e, apenas ao abrir um CT e somente com `delpi-mes.history.view`, consulta o histórico do dia daquele centro (`/work-centers/{workCenter}/timeline?branch=&from=`): todos os estados do dia corrente, inclusive de runs/OPs anteriores, com refetch pontual quando o estado do CT muda — sem polling próprio e sem N+1. A visão cobre exclusivamente runs ativos; não representa catálogo de máquinas nem saúde/offline da telemetria.

Paradas e Histórico completos continuam nas fases seguintes.

## Cadastros — Etapa 3

A área **Cadastros** (`/registrations`) é global: não exige filial, oculta o seletor de filial e exibe a indicação «Cadastro global — as alterações são válidas para todas as filiais». Hoje contém um único cadastro, **Motivos de parada**, que administra o catálogo global via `delpi-mes-api`:

- lista motivos ativos e inativos com busca local (código, descrição, categoria) e filtro de status;
- cria motivo (`code` técnico em lowercase) e edita `label`/`category`/`requiresNote`/`sortOrder` — `code` é somente leitura na edição;
- desativa com confirmação (o histórico é preservado) e reativa sem confirmação;
- trata 409/422 do BFF como conflito funcional (código duplicado; `setup` protegido mantém a mensagem segura do backend);
- não existe DELETE e os campos OEE nunca aparecem na tela nem nos bodies;
- `delpi-mes.downtime-reasons.manage` controla a visibilidade; acesso direto pela URL sem a permissão mostra o estado de acesso insuficiente — o backend continua autoridade.

Auditoria administrativa ainda não foi implementada.
