# GPT Builder — checklist go-live (Custom GPT Transformômetro)

Valores prontos para colar no ChatGPT GPT Editor. O **client secret** fica só no Keycloak → Credentials — **nunca** no Git.

## Pré-requisitos já feitos no ambiente

| Item | Estado |
|------|--------|
| API com `gpt-actions/v1` | Deploy + OpenAPI público |
| Client Keycloak `chatgpt-transformometro` | Confidential, Standard flow, Direct access **Off** |
| Audience mapper | scope `audience-delpi` → `aud` inclui `delpi-central` |
| Redirect URIs (wildcard até fechar o `g-...`) | `https://chatgpt.com/*`, `https://chat.openai.com/*` (+ callbacks `aip/*/oauth/callback`) |
| Web origins | `https://chatgpt.com`, `https://chat.openai.com` |

## 1. Create GPT → Actions

Import URL (substituir host se não for localhost):

```text
http://localhost/apps/transformometro-api/transformometro/gpt-actions/v1/openapi.json
```

Produção:

```text
https://<host-publico>/apps/transformometro-api/transformometro/gpt-actions/v1/openapi.json
```

Alternativa: colar `docs/openapi-gpt-actions.json`.

Esperado: **11** operations (`gpt_analyze`, `gpt_get_catalog`, …). O GET `openapi.json` não aparece como Action.

O ChatGPT **rejeita** `servers.url` relativo (`/apps/transformometro-api`). Se aparecer
«Não foi possível encontrar uma URL válida em `servers`», altere no editor para:

```json
"servers": [
  {
    "url": "https://minhadelpi.com.br/apps/transformometro-api",
    "description": "Minha DELPI gateway"
  }
]
```

Depois: Autenticação → **OAuth** (não «Nenhum»).

## 2. Authentication → OAuth (não API Key)

| Campo | Valor (dev) |
|-------|-------------|
| Client ID | `chatgpt-transformometro` |
| Client secret | Keycloak → Clients → `chatgpt-transformometro` → Credentials |
| Authorization URL | `http://localhost/auth/realms/delpi/protocol/openid-connect/auth` |
| Token URL | `http://localhost/auth/realms/delpi/protocol/openid-connect/token` |
| Scope | `openid email profile` |

Produção: trocar `http://localhost` pelo `PUBLIC_BASE_URL` / host público do realm.

## 3. Instructions

```text
Você é o assistente do Transformômetro DELPI.
Antes de cadastrar, chame gpt_get_catalog.
Para KPIs use gpt_analyze (view=summary|processes|instances|rows).
Cadastro segue: unidade/departamento → processo → melhoria (instance) → revisão → medição/investimento.
Confirme writes destrutivos (delete, activate, cancel ata) com o usuário.
Não invente UUIDs: busque com gpt_search_records / gpt_get_record.
Assinatura manuscrita de atas e uploads binários ficam na UI Minha DELPI.
```

## 4. Fechar redirects com o GPT ID real

Após salvar o GPT, copiar o `g-...` da URL e (opcional, se wildcards forem rejeitados pela OpenAI/Keycloak) restringir no Keycloak:

```text
https://chatgpt.com/aip/g-YOUR-GPT-ID/oauth/callback
https://chat.openai.com/aip/g-YOUR-GPT-ID/oauth/callback
```

## 5. Pronto quando

- GPT lista as 11 actions
- Pede **Sign in** (OAuth Keycloak)
- Após login, `gpt_analyze` / `gpt_get_catalog` respondem sem `invalid_token` / `Invalid redirect URI`

Detalhes: [`chatgpt-custom-gpt-actions.md`](./chatgpt-custom-gpt-actions.md).
