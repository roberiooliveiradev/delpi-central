# 09 — Testes e aceite

> **Requisitos:** [`07-requisitos.md`](./07-requisitos.md)
> **Pronto:** [`08-definition-of-done.md`](./08-definition-of-done.md)

## 1. Classe do problema

Integração em nome do usuário com um helpdesk externo que já é a fonte do chamado.

| Varia | Permanece |
|---|---|
| título, descrição, categoria, urgência, texto do acompanhamento | solicitante = usuário do token; entidade = padrão desse usuário; dono = GLPI |
| pessoa e perfil | portão `helpdesk.access` + perfil GLPI, sem regra duplicada na tela |

Contraexemplo que não pode passar: criar chamado com solicitante escolhido na tela, ou criar chamado sem sessão OAuth.

## 2. Casos

| Caso | Entrada | Esperado |
|---|---|---|
| Positive | JWT com `helpdesk.access`, sessão GLPI, POST válido | 201, um chamado no GLPI, solicitante = essa pessoa |
| Irmão | mesmo usuário, POST de acompanhamento nesse chamado | 201, texto na timeline |
| Irmão de leitura | GET /tickets depois do POST | o chamado aparece |
| Negativo de portão | JWT sem `helpdesk.access` | 403 antes do GLPI |
| Negativo de vínculo | JWT ok, sem sessão GLPI | 409 `glpi_link_required`, nenhum POST ao GLPI |
| Negativo de direito | sessão GLPI cujo perfil não cria chamado | 403 `glpi_forbidden`, nenhum chamado |
| Negativo de vazamento | GET do id de chamado que o perfil não vê | 403 ou 404, sem descrição |
| Negativo de duplicata | dois POST com a mesma Idempotency-Key | um id |
| Negativo de retry | falha de rede no POST | o cliente HTTP não dispara segundo POST sozinho |
| F5 | abrir `/apps/helpdesk/tickets/{id}` de novo | o mesmo detalhe |
| Invariante | fila no host do GLPI | técnico continua operando lá |

Teste de unidade da helpdesk-api usa GLPI falso. Teste do adapter pode usar o contrato gravado de `/api.php/doc.json`. Homologação `E5.S2` usa o GLPI de produção com um chamado marcado como teste.

Prova de formatação, XSS e imagem no corpo **não** entra nesta lista até haver autorização de código. Os casos estão em [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) §16.

Prova da grade (data absoluta, resolução, busca no conteúdo) está em [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md) §14 e também só depois de autorização.

Prova da página e dos sete status está em [`14-pagina-e-estados-do-chamado.md`](./14-pagina-e-estados-do-chamado.md) §11.

## 2.1 H12 — upload / colar / resize (já PROVEN live)

| Caso | Entrada | Esperado |
|---|---|---|
| Positive | multipart + `Idempotency-Key` + flag on | 201 `{ document_id, filename, mime }`; Document+Ticket no GLPI |
| Irmão | colar print (Snipping Tool / data: / clipboard.read) no compositor | **P0 urgente** — deve usar `RichTextEditor.onPasteImages` (paridade sala); ledger STALE até re-provar |
| Irmão | redimensionar imagem no editor | `width`/`height` HTML persistem após sanitizer |
| Negativo | flag off / token ausente | 503 `glpi_feature_disabled` |
| Negativo | CSS `width` no `style` | removido pelo sanitizer; atributos HTML ok |
| Preview | `<img src="/apps/helpdesk-api/.../attachments/N">` no editor | `blob:` via fetch Bearer; no envio, `normalizeInlineAttachmentSrcs` |

Evidência: ledger `H12.upload.*` / `H12.paste.snipping` / `H12.resize` / `H12.preview.blob`.

A matriz do restante do GLPI Assistência está em [`15-capacidades-glpi.md`](./15-capacidades-glpi.md) e não tem prova de produto até uma linha deixar de ser CONSOLE/HIPOTESE.

## 3. Homologação E5.S2

```text
[ ] Colaborador abre chamado pela Minha DELPI
[ ] O número existe no GLPI em nome desse colaborador
[ ] Acompanhamento feito na Minha DELPI aparece na timeline
[ ] Usuário sem direito de chamado vê acesso negado
[ ] Usuário sem helpdesk.access não abre o módulo
[ ] Técnico segue atendendo em helpdesk.centraldelpi.com.br
[ ] Log da helpdesk-api não contém segredo, token nem texto do chamado
```

O ledger só marca `PROVEN` com data e quem executou essa lista.
