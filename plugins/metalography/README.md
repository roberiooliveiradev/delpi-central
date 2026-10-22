# Metalografia DELPI

Relatórios de análise metalográfica no Minha DELPI. O MFE consulta, cria, edita, duplica, exclui, recebe micrografias e baixa o PDF pela API DELPI já existente. Não há API, banco nem gerador de PDF próprios.

```text
Portal → /apps/metalography/assets/remoteEntry.js
      → MFE metalography
      → /apps/api-delpi/engineering/metallographic-reports
```

A futura inclusão no Portal de Engenharia é apenas destino. Este plugin permanece o mesmo MFE e a mesma API.

## Rotas da interface

| Caminho | Tela |
|---|---|
| `/apps/metalography` | Lista, filtros e ações |
| `/apps/metalography/new` | Novo relatório |
| `/apps/metalography/{id}` | Editor |
| `/apps/metalography/{id}/view` | Consulta sem edição |

## API

Base: `/apps/api-delpi/engineering/metallographic-reports`.

Contrato: [engineering-metallographic-reports.md](../../api-delpi/docs/api/engineering-metallographic-reports.md).

O cliente envia `X-Delpi-Caller-App: metalography`, `Idempotency-Key` na criação e na cópia, e `If-Match` na edição, exclusão e mutação de imagem. PDF e imagens vêm em binário; o navegador não gera o PDF.

## Permissões

`metalography.view`, `metalography.create`, `metalography.edit`, `metalography.delete`, `metalography.export`.

O manifesto registra os códigos no Core. Isso não atribui a permissão aos usuários.

## Referência visual

A referência visual é `docs/12-roadmap-e-evolucao/quality/reference/Modelo_Relatorio_Metalografico_Delpi_Editavel.html` (SHA-256 `13ba5eb7033afa616bf542ac6f7a6df5c67a0d318d2ea898caa4fb368220b820`). A folha do editor reutiliza o CSS, a fonte, o logotipo e o esquema desse arquivo. A comparação no Chrome, folha vazia e folha preenchida, não teve pixel diferente na região da folha. O PDF continua sendo o da API DELPI, na mesma composição em milímetros, com a marca RASCUNHO apenas em rascunho.

## Imprimir e exportar

**Imprimir** abre o diálogo do navegador com somente a folha A4 que está na tela, inclusive alteração ainda não salva. O documento vai para um iframe oculto do `@delpi/plugin-ui` (`printDelpiDocumentHtml`), com o CSS, a fonte, o logotipo e o esquema da folha. A navegação do Portal não entra nessa impressão.

**Exportar PDF** continua baixando o snapshot já gravado na API DELPI. Não substitui a impressão e não lê o rascunho local.

Os diálogos de exclusão, cópia, saída sem salvar e recorte usam a caixa visível do `@delpi/plugin-ui` (`useContainedModalViewportStyle`). Eles permanecem abertos até Cancelar ou Confirmar. O atalho CSS `inset` não é aplicado, porque ele solta o modal da posição fixa.

## Tema

A tela acompanha o `data-theme` que o Portal grava em `<html>`. Não há seletor próprio. As cores de tela passam pelos tokens `--mg-*` em `screen-theme.css`, mapeados para `--surface`, `--surface-2`, `--app-canvas`, `--text`, `--primary`, `--secundary`, `--control-bg`, `--danger` e `--success`. No escuro, título e faixa não usam `--secundary` cru, porque o Portal não clareia esse token.

A impressão isolada e o PDF não mudam. Em `@media print` os tokens `--mg-*` voltam à paleta documental (`#fff`, `#0b3a5d`, `#00a4ce`, `#25465f`). O esquema técnico não é recolorido. No tema escuro, a marca Delpi da tela usa a logo cadastrada para fundo escuro (`logoDelpiOnDark`). A impressão volta à logo documental de fundo claro.

## Desenvolvimento

```bash
cd plugins/plugin-ui && npm install && npm run dev
cd plugins/metalography && npm install && VITE_PLUGIN_UI_DEV=1 npm run dev
npm test
npm run build
```

Compose, perfil `plugins`:

```bash
docker compose -f infra/docker-compose.dev.yml --profile plugins up -d plugin-ui metalography
```

Registro no Core, com token de quem tem `apps.manage`:

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/metalography/scripts/register-manifest.sh
```

## Smoke

```bash
curl -sI http://localhost/apps/metalography/assets/remoteEntry.js | head -3
curl -sI http://localhost/apps/plugin-ui/assets/remoteEntry.js | head -3
```

## Publicação

O gateway já encaminha `/apps/{id}/assets/*` para o container `delpi-metalography`. A API DELPI desta coleção ainda precisa estar publicada, com a migration `V010__metallographic_reports.sql` aplicada e o volume `metallographic-images` montado, antes do uso real.

```bash
./infra/scripts/up-prod-sequential.sh --fase mfe --build metalography
```

Rollback: voltar o commit anterior e repetir o build do serviço `metalography`. Não há migration neste plugin.
