# 02 — Arquitetura

> **Status do alvo:** publicado; lista `PROVEN` em 21/09/2026
> **Status do GLPI de produção:** `PROVEN` em 21/09/2026
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Estado no repositório

```text
Portal
  → plugins/helpdesk (type: microfrontend, permissão helpdesk.access)
      entry /apps/helpdesk/assets/remoteEntry.js
  → helpdesk-api /apps/helpdesk-api
      → GLPI HLAPI 2.2 em nome do usuário
```

O iframe antigo apontava para `https://centraldelpi.com.br/helpdesk/`, que não é o host do GLPI. O manifesto vigente é o microfrontend em `/apps/helpdesk`. O portal publicado já serve essa tela. O path `/helpdesk` redireciona para `/apps/helpdesk`.

GLPI de produção, lido no container `inventario-ti-glpi-1`:

| Fato | Valor |
|---|---|
| Imagem | `glpi/glpi:latest` |
| Versão | 11.0.5 |
| API nova | `enable_hlapi = 1` |
| Versão da API | 2.2.0 |
| API legada | `enable_api = 0` |
| Cliente OAuth | `minha-delpi-helpdesk`, ativo |
| Concessão | `authorization_code` |
| Escopo | `api` |
| Redirect gravado | `https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback` |
| SSO | plugin `samlsso` (Keycloak) |
| Chaves OAuth do GLPI | `oauth.pem` / `oauth.pub` já existem no container |

Não há cliente OAuth além desse. A API legada permanece desligada.

## 2. Estado alvo

```text
Portal / MFE  plugins/helpdesk
    HTTP /apps/helpdesk-api
helpdesk-api
    domain ← application ← adapters
    HTTP interno, timeout explícito
GLPI HLAPI
    https://helpdesk.centraldelpi.com.br/api.php/v2.2
```

| Peça | Dono |
|---|---|
| Chamado, categoria, urgência, acompanhamento, perfil | GLPI |
| Identidade da Minha DELPI | Keycloak |
| App, rota, `helpdesk.access` | Core API |
| Sessão OAuth do GLPI ligada ao sujeito Keycloak | helpdesk-api |
| Contrato JSON consumido pelo MFE | helpdesk-api |
| Tela | `plugins/helpdesk` |
| Banco de chamado | GLPI. A helpdesk-api não cria tabela de chamado |

A helpdesk-api persiste só o vínculo de sessão OAuth (refresh e access token cifrados, sujeito Keycloak, validade). Schema próprio, migration própria. Não lê nem escreve o MySQL do GLPI.

## 3. Camadas da helpdesk-api

```text
domain          Ticket, FollowUp, Category, Urgency — sem Flask, HTTP ou GLPI SDK
application     casos de uso: listar, abrir, detalhar, acompanhar, iniciar OAuth
adapters        HTTP do GLPI, repositório de sessão, JWT da plataforma
```

O MFE fala apenas com a helpdesk-api. Não usa `api-delpi`, não guarda App-Token e não monta URL do GLPI.

## 4. Mapa de integração

| Superfície | Caminho |
|---|---|
| UI | `/apps/helpdesk` |
| Detalhe | `/apps/helpdesk/tickets/{id}` |
| BFF | `/apps/helpdesk-api` |
| Callback OAuth | `https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback` |
| Autorização GLPI | `https://helpdesk.centraldelpi.com.br/api.php/authorize` |
| Token GLPI | `https://helpdesk.centraldelpi.com.br/api.php/token` |
| Recursos GLPI | `https://helpdesk.centraldelpi.com.br/api.php/v2.2/Assistance/Ticket` |

`authorize` e `token` estão no controller de sessão da HLAPI, fora do prefixo `/v2.2`. O recurso de chamado está em `/Assistance/Ticket`, com `itemtype` limitado a `Ticket`, `Change` e `Problem`. Este módulo usa somente `Ticket`.

Acompanhamento no GLPI: `POST /Assistance/Ticket/{id}/Timeline/Followup`.

## 5. Hipóteses descartadas

| Hipótese | Por que não |
|---|---|
| Iframe com o host certo | Não entrega a tela nativa pedida |
| Browser chama a HLAPI | Expõe cliente OAuth e foge do BFF da plataforma |
| API legada + App-Token + conta técnica | API legada está desligada; o chamado não ficaria em nome do usuário |
| Token do Keycloak aceito pelo GLPI | O GLPI 11.0.5 emite o token dele; o Keycloak entra pela sessão SAML já configurada |
| Chamado gravado na Minha DELPI | Segunda fonte de verdade |

## 6. Invariantes

- GLPI em `helpdesk.centraldelpi.com.br` continua no ar para quem opera a fila.
- `enable_api` permanece 0.
- O cliente OAuth não ganha concessão `password` nem `client_credentials`.
- O escopo do cliente permanece `api`.
- A redirect URI do cliente permanece exatamente a URL da tabela acima.
