# 04 — Segurança e identidade

> **Status:** decisões `READY_CONFIRMED`; BFF publicado e sessão OAuth `PROVEN` na lista de 21/09/2026
> **Contrato:** [`03-contrato.md`](./03-contrato.md)

## 1. Duas portas

```text
JWT Minha DELPI + helpdesk.access     entra no módulo
token OAuth do GLPI, escopo api       age no chamado
```

Uma não substitui a outra. Ter `helpdesk.access` não cria chamado se o perfil GLPI não deixar. Ter perfil no GLPI não abre o módulo sem a permissão do portal.

## 2. Fluxo de autorização

1. A pessoa já está na Minha DELPI (Keycloak).
2. `GET /auth/glpi/start` só responde se o JWT for válido e tiver `helpdesk.access`.
3. O navegador abre `https://helpdesk.centraldelpi.com.br/?samlIdpId=1&redirect=…`, com a URL de `api.php/authorize` (state, PKCE e `accept=1`) codificada duas vezes.
4. O samlsso dispara o IdP `Minha DELPI` (id 1), o mesmo do botão do helpdesk. Quem já tem sessão no Keycloak entra sem formulário. Quem já existe no GLPI é reconhecido pelo e-mail; quem não existe é criado pelo JIT já ligado nesse IdP. Não há usuário local com senha criado pela helpdesk-api.
5. No retorno, o GLPI segue o `redirect` guardado e emite o código para a redirect URI cadastrada, sem a tela de consentimento.
6. A helpdesk-api troca o código em `POST /api.php/token`, com o segredo do cliente, no servidor.
7. O refresh token fica cifrado, ligado ao `sub` do JWT. Outro usuário não lê essa linha.

O passo 3 é redirect do navegador. A helpdesk-api não chama `authorize` servidor a servidor: o cookie de sessão do GLPI está no browser.

O samlsso grava o `redirect` em `glpi_plugin_samlsso_loginstates.redirect`. A coluna nasceu `varchar(255)` e não cabe a URL de autorização; em produção ela fica `TEXT`. Sem isso o retorno perde o state e o PKCE. O login direto no helpdesk continua com o formulário local, porque `enforce_sso` permanece desligado. Só a entrada vinda da Minha DELPI pede o IdP.

## 3. Cliente OAuth travado

| Item | Valor |
|---|---|
| Nome | `minha-delpi-helpdesk` |
| Concessão | somente `authorization_code` |
| Escopo | somente `api` |
| Redirect | `https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback` |
| IP do cliente | vazio até o BFF chamar o GLPI por um endereço estável e conhecido |
| Segredo | variável da helpdesk-api, nunca no MFE, no Git ou em log |

Não habilitar `password` nem `client_credentials`. Não ligar a API legada.

O refresh token vem junto com o authorization code no GLPI 11.0.5. Não há checkbox separado. Access token: 1 hora.

PKCE S256 é obrigatório no BFF. O cliente é confidencial: o segredo continua só no servidor. PKCE protege o código no navegador; o segredo protege a troca do token.

## 4. O que o cliente não pode pedir

- Solicitante diferente do usuário do token.
- Entidade. Vale a entidade padrão desse usuário no GLPI.
- Escopo além de `api`.
- `Change`, `Problem` ou rota de ativo através deste BFF.

O escopo `api` no GLPI é largo: cobre a HLAPI que o perfil permitir, não só chamado. O recorte “só helpdesk da pessoa” é o perfil GLPI mais as rotas que a helpdesk-api publica. Os perfis de quem só abre chamado são `Self-Service (cópia)` (interface helpdesk) e `Colaborador - Chamados` (interface central). Eles não são reimplementados na Minha DELPI. A HLAPI trata categoria como dropdown, não como campo do formulário: sem `itilcategory` READ o `GET /Dropdowns/ITILCategory` volta 403 mesmo com direito de abrir chamado. Esses perfis ficam com leitura do catálogo; criação e alteração de categoria continuam nos perfis de administração.

## 5. Sessão e saída

- Apagar o vínculo local no logout da Minha DELPI e em `DELETE /auth/glpi/session`.
- Não guardar access token nem refresh token em `localStorage` ou cookie legível pelo MFE.
- Identidade de autor da conversa: id do usuário no GLPI ou e-mail do JWT. Nome de pessoa não entra em nenhum fluxo de decisão.
- Log de integração: sujeito Keycloak, id do chamado, status HTTP, duração. Sem título, descrição, código de autorização, access token, refresh token ou segredo.
- Cifra da sessão com chave própria da helpdesk-api, distinta do segredo OAuth.

## 6. Rede

A helpdesk-api chama o GLPI com timeout. O host público `helpdesk.centraldelpi.com.br` é o mesmo que o navegador usa na autorização, para o cookie e o redirect baterem com o GLPI já publicado. Chamada interna direta ao container só entra se o `Host` e o certificado continuarem coerentes com esse nome; isso não muda o contrato.

## 7. HTML do chamado (alvo, não publicado)

O GLPI grava abertura e acompanhamento em HTML. Hoje o BFF achata isso em texto. Quando o corpo rico for autorizado ([`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md)):

- o BFF é a autoridade da allowlist e do rewrite de `document.send.php`;
- o browser não busca o host do GLPI para imagem ou documento;
- o kit só defende de novo, não substitui o sanitizer;
- o log continua sem o corpo da mensagem.
