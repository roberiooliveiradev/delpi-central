# 04 — Segurança e identidade

> **Status:** decisões `READY_CONFIRMED` na fundação GLPI; runtime do BFF `PLANNED`
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
3. O navegador abre `https://helpdesk.centraldelpi.com.br/api.php/authorize`.
4. O GLPI vê a sessão SAML. Se não houver sessão, o samlsso manda ao Keycloak e volta.
5. O GLPI devolve o código para a redirect URI cadastrada.
6. A helpdesk-api troca o código em `POST /api.php/token`, com o segredo do cliente, no servidor.
7. O refresh token fica cifrado, ligado ao `sub` do JWT. Outro usuário não lê essa linha.

O passo 3 é redirect do navegador. A helpdesk-api não chama `authorize` servidor a servidor: o cookie de sessão do GLPI está no browser.

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

O escopo `api` no GLPI é largo: cobre a HLAPI que o perfil permitir, não só chamado. O recorte “só helpdesk da pessoa” é o perfil GLPI mais as rotas que a helpdesk-api publica. Os perfis de quem só abre chamado são `Self-Service (cópia)` (interface helpdesk) e `Colaborador - Chamados` (interface central). Eles não são reimplementados na Minha DELPI.

## 5. Sessão e saída

- Apagar o vínculo local no logout da Minha DELPI e em `DELETE /auth/glpi/session`.
- Não guardar access token nem refresh token em `localStorage` ou cookie legível pelo MFE.
- Log de integração: sujeito Keycloak, id do chamado, status HTTP, duração. Sem título, descrição, código de autorização, access token, refresh token ou segredo.
- Cifra da sessão com chave própria da helpdesk-api, distinta do segredo OAuth.

## 6. Rede

A helpdesk-api chama o GLPI com timeout. O host público `helpdesk.centraldelpi.com.br` é o mesmo que o navegador usa na autorização, para o cookie e o redirect baterem com o GLPI já publicado. Chamada interna direta ao container só entra se o `Host` e o certificado continuarem coerentes com esse nome; isso não muda o contrato.
