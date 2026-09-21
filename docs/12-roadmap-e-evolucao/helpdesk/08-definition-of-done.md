# 08 — Definição de pronto

> **Ordem:** [`06-plano-execucao.md`](./06-plano-execucao.md)
> **Provas:** [`09-testes-e-aceite.md`](./09-testes-e-aceite.md)

Uma etapa só fecha quando o aceite dela no plano de execução e os itens abaixo que a etapa toca estão verdes. Documentação desta pasta, sozinha, não fecha H1–H4.

## Sempre

```text
[ ] GLPI continua dono do chamado
[ ] api-delpi não é chamada por este módulo
[ ] enable_api do GLPI permanece desligado
[ ] cliente OAuth permanece authorization_code + escopo api
[ ] segredo e tokens fora do MFE, do Git e do log
[ ] helpdesk.access é o portão do portal; o perfil GLPI é o direito do chamado
[ ] POST de chamado e de acompanhamento não tem retry automático
```

## E1

```text
[ ] helpdesk-api sobe com health
[ ] domain sem framework e sem cliente GLPI
[ ] callback grava sessão só para o sub do JWT que iniciou o fluxo
[ ] state inválido ou expirado não grava token
[ ] DELETE da sessão remove o vínculo local
[ ] gateway expõe /apps/helpdesk-api
```

## E2

```text
[ ] categoria e urgência saem do GLPI
[ ] lista vazia é 200
[ ] chamado fora da visão do token não devolve corpo
[ ] timeout do cliente HTTP está explícito
```

## E3

```text
[ ] chamado criado aparece no GLPI com o solicitante do token
[ ] payload não aceita solicitante nem entidade
[ ] mesma Idempotency-Key devolve o mesmo id
[ ] acompanhamento cai na timeline daquele chamado
[ ] acompanhamento em chamado invisível não grava
```

## E4

```text
[x] /apps/helpdesk é MFE, não iframe
[x] loading, vazio, erro e proibido visíveis
[x] F5 no detalhe reabre o mesmo chamado
[x] ajuda in-app publicada com a tela
[x] uma única entrada no menu, com o nome Meus Chamados de TI
[ ] desktop e largura estreita utilizáveis
```

## E5

```text
[ ] positive, irmão e negativo descritos em 09 passaram
[ ] homologação com usuário real registrada no ledger
[ ] console do técnico em helpdesk.centraldelpi.com.br inalterado
```

A lista em produção, em 21/09/2026, fecha a leitura e a tela. A abertura e o acompanhamento ao vivo ainda precisam entrar no ledger para H3 deixar de ser `NOT_STARTED`.
