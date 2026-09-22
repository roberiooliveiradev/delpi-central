# Meus Chamados de TI

> **Status:** primeira entrega + paridade do solicitante **publicadas** (E1–E13 + E14 menção leitura + **H12 upload live**). Ledger 21/09/2026.
> **Fundação GLPI:** `PROVEN` em produção (21/09/2026)
> **Produto:** Meus Chamados de TI — abertura e acompanhamento de chamados dentro da Minha DELPI, com o GLPI como dono do chamado
> **Requisitos:** `HD-001…HD-027` em [`07-requisitos.md`](./07-requisitos.md)
> **Paridade:** [`16-plano-paridade.md`](./16-plano-paridade.md) `E6…E13` **concluído**; menção leitura [`evidence/e14-mentions.md`](./evidence/e14-mentions.md)
> **Ordem histórica:** [`06-plano-execucao.md`](./06-plano-execucao.md) `E1…E5` · [`16-plano-paridade.md`](./16-plano-paridade.md) `E6…E13`
> **Ondas:** [`05-roadmap.md`](./05-roadmap.md)
> **Estado de execução:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

Esta pasta decide o produto. Não autoriza implementação sozinha e não prova runtime da Minha DELPI. O GLPI em produção já está no estado descrito em [`02-arquitetura.md`](./02-arquitetura.md).

## 1. Decisão fundamental

Meus Chamados de TI não é um segundo sistema de chamados e não é um conserto do iframe atual.

```text
Hoje, publicado                              Ainda aberto / parque / urgente
-------------------------------------------  --------------------------------
MFE /apps/helpdesk + HTML + builder AND      **P0** colar + F5 imagem (DRIFT H12 UX)
helpdesk-api OAuth + contrato ADDITIVE       M-23 @ escrita (BLOQUEADO)
H12 Document upload BFF live                 H10 ciclo write (CONSOLE)
GLPI dono do chamado                         bancada / Change / HD-011 (FORA)
E14 chips de menção na bolha
```

```text
MFE helpdesk
  → helpdesk-api
      → GLPI HLAPI 2.2, em nome do usuário
      → (H12) apirest Document + App-Token + User-Token técnico, só upload
```

O navegador não chama o GLPI. A api-delpi não entra neste fluxo. O GLPI continua a fonte dos chamados, categorias, filas, acompanhamentos e perfis. A API legada fica **desligada para o resto**; a exceção H12 é só `Document` gated por `GLPI_LEGACY_UPLOAD_ENABLED`.

## 2. North Star

> **A pessoa abre e acompanha o próprio chamado na Minha DELPI, com a mesma identidade do Keycloak e com o direito que o perfil dela já tem no GLPI.**

```text
entrar na Minha DELPI
→ abrir Meus Chamados de TI
→ autorizar uma vez no GLPI (sessão SAML já existente)
→ ver os meus chamados
→ abrir um chamado
→ acompanhar e incluir follow-up
```

A fila do técnico, o inventário e a administração continuam no GLPI em `https://helpdesk.centraldelpi.com.br`. Quem tem `helpdesk.console` vê no menu **Console do helpdesk**, que abre esse endereço já pela sessão da Minha DELPI.

## 3. Authorities

```text
Keycloak           = identidade / SSO da Minha DELPI
GLPI + SAML        = sessão do helpdesk e perfil do chamado
GLPI HLAPI OAuth   = token em nome do usuário
Core API           = app, rota, permissão helpdesk.access
helpdesk-api       = BFF, sessão OAuth, contrato do MFE
Portal / MFE       = navegação e renderização
GLPI               = fonte do chamado
```

E:

```text
permissão do portal  !=  direito de abrir chamado
escopo OAuth api     !=  recorte só de chamado
token do BFF         !=  token no browser
iframe               !=  produto alvo
API legada           !=  caminho geral do módulo (exceção H12 Document-only)
```

O portão da Minha DELPI é `helpdesk.access`. O que a pessoa pode criar ou ver é o perfil GLPI aplicado ao token dela. Se o GLPI responder 403, a tela mostra acesso negado. O MFE não reimplementa essa regra.

## 4. Identidade

O nome segue o mesmo corte de Minhas Solicitações: o que a pessoa lê é português e possessivo; o id técnico permanece inglês.

| Superfície | Valor |
|---|---|
| Nome no menu, título da tela, ajuda e manifest `name` | **Meus Chamados de TI** |
| Nome da permissão | Acessar Meus Chamados de TI |
| Id do app, pasta, permissão e API | `helpdesk`, `helpdesk.access`, `helpdesk-api` |
| Caminhos | `/apps/helpdesk` e `/apps/helpdesk-api` |

O id não muda. O plugin iframe já é `helpdesk`, e o cliente OAuth de produção já tem a redirect em `/apps/helpdesk-api/auth/glpi/callback`. Renomear o path agora exigiria outro cliente no GLPI sem mudar o que a pessoa vê.

## 5. Como ler

| Pergunta | Documento |
|---|---|
| Como a tela é composta? | [`WIREFRAMES.md`](./WIREFRAMES.md) |
| Como fica a conversa do chamado? | [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md); a tela publicada está em [`WIREFRAMES.md`](./WIREFRAMES.md) |
| O que ainda falta na experiência? | [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md) — inventário, não é etapa de código |
| O que a mensagem deve mostrar (HTML, imagem, formatação)? | [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) — inventário, não é etapa de código |
| O que a listagem deve mostrar (colunas, filtros, datas)? | [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md) — inventário, não é etapa de código |
| O que a página do chamado e os estados devem mostrar? | [`14-pagina-e-estados-do-chamado.md`](./14-pagina-e-estados-do-chamado.md) — inventário, não é etapa de código |
| O que o GLPI Assistência tem e ainda não estava fatiado? | [`15-capacidades-glpi.md`](./15-capacidades-glpi.md) |
| Qual é a ordem da paridade? | [`16-plano-paridade.md`](./16-plano-paridade.md) |
| O que a pessoa faz? | [`01-visao-produto.md`](./01-visao-produto.md) |
| Quem é dono e o que já existe? | [`02-arquitetura.md`](./02-arquitetura.md) |
| Qual é o contrato? | [`03-contrato.md`](./03-contrato.md) |
| Como a identidade funciona? | [`04-seguranca.md`](./04-seguranca.md) |
| Em que ondas o produto cresce? | [`05-roadmap.md`](./05-roadmap.md) |
| Qual é a próxima etapa executável? | **P0 urgente:** colar imagem + F5 preview no compositor (alinhar à sala de interação). Depois: M-23 `@`, H10 write se HLAPI. Ledger: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) · roadmap [`05`](./05-roadmap.md) §Próximo código |
| Qual é a onda? | [`05-roadmap.md`](./05-roadmap.md) |
| Qual requisito isso cobre? | [`07-requisitos.md`](./07-requisitos.md) |
| Quando uma etapa está pronta? | [`08-definition-of-done.md`](./08-definition-of-done.md) |
| Como provar? | [`09-testes-e-aceite.md`](./09-testes-e-aceite.md) |
| O que já foi provado? | [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) |
| Menção leitura / park `@`? | [`evidence/e14-mentions.md`](./evidence/e14-mentions.md) |

Mapa curto: [`INDEX.md`](./INDEX.md).

## 6. Fora da primeira entrega / ainda parque

Pesquisa de satisfação, fila do técnico, mudança, problema, inventário, banco de chamado na Minha DELPI, e **qualquer uso da API legada além do Document H12**. Baixar e **enviar** anexo estão publicados (H12). Matriz completa em [`15-capacidades-glpi.md`](./15-capacidades-glpi.md).
