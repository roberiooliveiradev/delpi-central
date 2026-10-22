# Relatório Metalográfico — chamado #1400

Origem: Helpdesk **#1400**, aberto em 21/10/2026. HTML de referência não versionado; SHA-256 `13ba5eb7033afa616bf542ac6f7a6df5c67a0d318d2ea898caa4fb368220b820`.

## Estado

| Capacidade | Estado |
|---|---|
| CRUD, filtros, cópia, exclusão lógica, imagens e PDF na `api-delpi` | Implementado e coberto por testes automatizados. Contrato: [engineering-metallographic-reports.md](../../../api-delpi/docs/api/engineering-metallographic-reports.md) |
| Paridade visual do PDF com o HTML recebido | Não validada — o arquivo não está neste ambiente |
| MFE Metalografia DELPI, manifesto e Ajuda | Implementado em `plugins/metalography`. O registro no Core ocorre no deploy, com `apps.manage`. As permissões do manifesto não são atribuídas automaticamente aos usuários |
| Paridade visual do PDF e da tela com o HTML recebido | Não validada — o arquivo não está neste ambiente |
| Portal de Engenharia | TARGET. Não há segundo app nem segunda API |
| Deploy da API e do MFE | Não executado nesta entrega |

## Aceites desta etapa de API

- Relatório persistido no PostgreSQL de plugins, número único no servidor, UUID estável.
- Cinco medições e duas micrografias fazem round-trip; a imagem continua disponível para outra instância de storage no mesmo volume.
- `Idempotency-Key` idêntica não gera segundo relatório; conteúdo diferente com a mesma chave conflita.
- `If-Match` ausente ou velho não sobrescreve edição.
- Sem JWT a operação é 401; sem a permissão específica, 403, inclusive em imagem e PDF.
- Exclusão lógica some da lista e da consulta; a cópia não altera o original.
- PDF A4 sai do snapshot salvo, sem mudar versão nem revisão, com as seções documentadas. A fidelidade ao HTML permanece pendente do arquivo original.

## Tema da tela

A interface do MFE acompanha `data-theme` do Portal em todas as superfícies de tela. As cores ficam nos tokens `--mg-*` de `plugins/metalography/src/styles/screen-theme.css`, mapeados para os tokens do Portal. A folha na tela muda só a cor. A impressão isolada e o PDF permanecem na paleta do HTML (`#fff`, `#0b3a5d`, `#00a4ce`, `#25465f`). O HTML de referência não entra nessa alteração.
