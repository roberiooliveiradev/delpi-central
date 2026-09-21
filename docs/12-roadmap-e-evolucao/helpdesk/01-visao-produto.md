# 01 — Visão de produto

> **Status:** `PROVEN` na lista publicada em 21/09/2026
> **North star e authorities:** [`README.md`](./README.md)

## 1. Para quem

Colaborador que já entra na Minha DELPI e hoje precisaria ir ao GLPI para abrir ou acompanhar um chamado.

O técnico, o supervisor e o administrador do parque continuam no GLPI. Esta entrega não substitui a bancada deles.

## 2. O que a primeira entrega faz

| Ação | Resultado perceptível |
|---|---|
| Abrir Meus Chamados de TI | Tela da Minha DELPI, não um iframe do GLPI |
| Primeira vez | O navegador autoriza o cliente OAuth no GLPI e volta para a Minha DELPI |
| Ver chamados | Lista só os chamados que o perfil da pessoa enxerga |
| Abrir chamado | Título, descrição, categoria e urgência; o solicitante é a própria pessoa |
| Ver detalhe | Status, datas e linha do tempo |
| Incluir acompanhamento | Texto no chamado que ela pode ver |

Estados obrigatórios em cada tela: carregando, vazio, erro, acesso negado.

## 3. Wireframe

O desenho fechado das telas, dos componentes do kit e do claro/escuro está em [`WIREFRAMES.md`](./WIREFRAMES.md). A visão resumida:

```text
/apps/helpdesk                  tabela + filtros
/apps/helpdesk/tickets/new      esquerda: título e descrição; direita: categoria e urgência
/apps/helpdesk/tickets/{id}     cartão (status, categoria, urgência) + conversa + responder
```

Deep link do detalhe fica na URL do MFE (`/apps/helpdesk/tickets/{id}`), para sobreviver a atualizar a página.

## 4. O que não muda para a pessoa que opera a fila

`https://helpdesk.centraldelpi.com.br` continua o console do GLPI. Chamado criado na Minha DELPI aparece lá como chamado daquela pessoa, na entidade padrão dela no GLPI. O BFF não escolhe outra entidade e não aceita solicitante vindo da tela.

## 5. Ajuda

A ajuda in-app (manual do produto e textos de campo) entra na mesma entrega da tela, em [`06-plano-execucao.md`](./06-plano-execucao.md) `E4.S3`. Não descreve path de API nem nome de tabela.
