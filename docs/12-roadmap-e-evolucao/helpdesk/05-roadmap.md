# 05 — Roadmap

> **Ordem executável:** [`06-plano-execucao.md`](./06-plano-execucao.md)
> **Este arquivo é a evolução macro. Não marca fase como feita.**

```text
H0  Fundação GLPI                          PROVEN
H1  BFF e sessão OAuth                     PROVEN
H2  Leitura da lista                       PROVEN
H3  Abertura e acompanhamento              PLANNED
H4  Tela nativa no lugar do iframe         PROVEN
H5  Anexo, satisfação, bancada técnica     TARGET
```

## H0 — Fundação GLPI

Já feito em produção e registrado no ledger: versão 11.0.5, API nova ligada, API legada desligada, cliente OAuth do BFF criado. Nenhuma etapa de código reabre essa fundação, salvo drift comprovado.

## H1 — BFF e sessão

`helpdesk-api` sobe na plataforma, completa o authorization code e guarda a sessão cifrada do usuário. Ainda sem tela de chamado.

## H2 — Leitura

Categorias, urgências, lista e detalhe, sempre com o token da pessoa.

## H3 — Escrita

Abrir chamado e incluir acompanhamento, com idempotência e sem retry de POST.

## H4 — Tela

MFE federado substitui o iframe. Ajuda in-app entra junto. O console do técnico no host do GLPI permanece.

## H5 — Depois da primeira entrega

Não entra em `E1…E5`.

| Capacidade | Motivo de ficar para depois |
|---|---|
| Anexo | listar e baixar os arquivos já ligados ao chamado. Enviar arquivo novo continua fora: a API nova do GLPI 11.0.5 não recebe o binário |
| Pesquisa de satisfação | fluxo posterior ao fechamento |
| Fila, atribuição, tarefa, solução, validação | bancada do técnico, continua no GLPI |
| Mudança e problema | outro itemtype |
| Seletor de entidade | a primeira entrega usa a entidade padrão do usuário |
| Restrição de IP no cliente OAuth | só quando o IP que o GLPI vê na chamada do BFF for estável |

H5 só começa com decisão nova. Não é continuação automática de H4.
