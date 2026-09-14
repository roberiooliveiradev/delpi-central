# GPT Builder — checklist go-live (TÉO · Custom GPT Transformômetro)

> Padrão transversal (outros produtos): [padrao-custom-gpt-actions-oauth.md](../../../docs/11-padroes-de-desenvolvimento/padrao-custom-gpt-actions-oauth.md)

Valores prontos para colar no ChatGPT GPT Editor. O **client secret** fica só no Keycloak → Credentials — **nunca** no Git.

## Identidade do GPT (manual no Builder)

`MANUAL_CONFIGURATION_REQUIRED` — Name / Description / Conversation starters só existem na UI do ChatGPT.

| Campo (GPT Builder) | Valor |
|---------------------|--------|
| **Name** | `TÉO — Especialista em Transformação Digital` |
| **Description** | Transforme problemas em processos melhores. TÉO analisa processos, identifica gargalos, desenha melhorias, propõe indicadores e ajuda a registrar resultados no Transformômetro. |
| **Tagline** | Transforme problemas em processos melhores. |
| **Acrônimo** | TÉO = Transformação · Eficiência · Otimização |

Conversation starters sugeridos:

```text
Quero melhorar um processo
Quero mapear os macroprocessos da empresa
Me ajude a desenhar o AS-IS e o TO-BE
Quero descobrir a causa de um problema operacional
Quero criar indicadores para medir uma transformação
Quero fazer uma análise SWOT
```

Produto = **Transformômetro**. Persona/especialista = **TÉO**. Não renomear o produto.

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

Alternativa: colar `docs/gpt-actions/openapi-gpt-actions.json`.

Esperado: **13** operations (`gpt_get_process_context`, `gpt_analyze`, `gpt_get_catalog`, `gpt_commit_improvement_package`, …). O GET `openapi.json` não aparece como Action.

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

## 3. Instructions + Knowledge

1. Colar o bloco *Instructions* de [`specialist-instructions.md`](./specialist-instructions.md) (**REPLACE INSTRUCTIONS** — persona **TÉO** + Method Router).
2. Adicionar [`teo-method-playbooks.md`](./teo-method-playbooks.md) como Knowledge File do GPT (**ADD/UPDATE KNOWLEDGE**). O arquivo é metodologia/reasoning; não cria Action, AuthZ nem persistência.

Resumo operacional:

- Problem-first: diagnóstico via `gpt_get_process_context` antes de cadastro, salvo QUICK REGISTRATION.
- Method playbooks: menor método suficiente; entrevista adaptativa; INFERRED ≠ FACT; PROPOSED ≠ SAVED.
- Chamar `gpt_get_catalog` e ler `registration_guide` antes de cadastrar.
- Preferir `gpt_commit_improvement_package` com `dry_run=true` → confirmar → commit.
- Listar revisões de uma melhoria com `instance_id`.
- Diagramas/WBS: draft Mermaid = PROPOSED; persistência governada (validators canônicos + confirmação + read-back).
- Evidências/assinatura → UI Minha DELPI.
- REIMPORT OpenAPI somente se o schema mudou (esperado estável: **13** actions).

## 4. Fechar redirects com o GPT ID real

Após salvar o GPT, copiar o `g-...` da URL e (opcional, se wildcards forem rejeitados pela OpenAI/Keycloak) restringir no Keycloak:

```text
https://chatgpt.com/aip/g-YOUR-GPT-ID/oauth/callback
https://chat.openai.com/aip/g-YOUR-GPT-ID/oauth/callback
```

## 5. Pronto quando

- Name do GPT = **TÉO — Especialista em Transformação Digital**
- GPT lista as **13** actions
- Pede **Sign in** (OAuth Keycloak)
- Após login, `gpt_analyze` / `gpt_get_catalog` / `gpt_get_process_context` respondem sem `invalid_token` / `Invalid redirect URI`
- `gpt_get_catalog` devolve `registration_guide`; dry_run do pacote lista `missing` quando incompleto

Detalhes: [`custom-gpt-actions.md`](./custom-gpt-actions.md).
