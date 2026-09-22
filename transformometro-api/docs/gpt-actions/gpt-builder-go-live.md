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

Esperado: **18** operations importáveis (V2), incluindo `gpt_get_methodology_guide`, `gpt_prepare_record_change`, `gpt_commit_proposal` (`gpt_get_my_context`, `gpt_get_process_context`, `gpt_analyze`, `gpt_get_catalog`, `gpt_validate_improvement_package`, `gpt_list_evidence`, `gpt_manage_evidence`, `gpt_get_process_timeline`, `gpt_adjust_shared_resource_cost`, `gpt_meeting_minute_manage`, …). Sem `gpt_commit_improvement_package` no schema (commit via `gpt_commit_proposal`). O GET `openapi.json` não aparece como Action. Inventários de 20/21 operations são HISTORICAL.

O ChatGPT **rejeita** `servers.url` relativo (`/apps/transformometro-api`). Se aparecer «Não foi possível encontrar uma URL válida em `servers`», altere no editor para:

```json
"servers": [{"url": "https://minhadelpi.com.br/apps/transformometro-api", "description": "Minha DELPI gateway"}]
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

O Builder limita **Instructions a 8.000 caracteres**. O repositório impõe meta mais conservadora de **<= 7.000 caracteres** para o bloco canônico.

1. Colar **somente** o bloco `Instructions (colar no GPT Builder)` de [`specialist-instructions.md`](./specialist-instructions.md). Não colar cabeçalhos/notas do arquivo inteiro.
2. Adicionar [`teo-method-playbooks.md`](./teo-method-playbooks.md) como Knowledge File do GPT. Detalhes de SIPOC/Lean/Ishikawa/CTP/TDR/KPI/SWOT ficam no Knowledge, não duplicados em Instructions.
3. Se o Builder mostrar erro de tamanho, **não cortar manualmente**: corrigir a fonte canônica e o teste de budget no repositório.

Resumo operacional:

- Problem-first e entrevista adaptativa.
- Method Router escolhe o menor método suficiente; `INFERRED != FACT`; `PROPOSED != SAVED`.
- `gpt_get_catalog` + `registration_guide.entity_schemas` antes de qualquer gravação.
- Schema canônico da entidade prevalece sobre a assinatura genérica da Action; não empacotar campos em `conteudo` (exceto documentos).
- Envelope nested (`process` + `instance` + `scenario.revision`) → `gpt_validate_improvement_package` → `ready=true` → mostrar → confirmar → `gpt_commit_proposal`.
- Diagramas/WBS: draft = PROPOSED; persistência governada com validators, manage AuthZ e read-back.
- Após write rejeitado: read-back antes de retry; evitar duplicata.
- Evidência: links/metadados via `gpt_list_evidence` / `gpt_manage_evidence`; upload/download binário permanece UI-only / BLOCKED_BY_PLATFORM.
- Assinatura manuscrita PNG/PDF/magic-link público: UI-only / NOT_EXPOSED_BY_DESIGN.
- Timeline de processo, reajuste canônico de custo e extras de ata: Actions semânticas dedicadas (não proxy genérico).
- REIMPORT OpenAPI quando o schema mudar. No código, o contrato importável tem **18** operationIds (`GPT_ACTIONS_OPERATION_IDS`, lifecycle `GOVERNED_PREPARE_COMMIT_V2`). **20/21** são HISTORICAL. Este checklist não prova que o Builder já foi reimportado.
- `gpt_get_my_context` = contexto pessoal (nome/cargo), não permissões.

## 4. Fechar redirects com o GPT ID real

Após salvar o GPT, copiar o `g-...` da URL e, se necessário, restringir no Keycloak:

```text
https://chatgpt.com/aip/g-YOUR-GPT-ID/oauth/callback
https://chat.openai.com/aip/g-YOUR-GPT-ID/oauth/callback
```

## 5. Pronto quando

- Name = **TÉO — Especialista em Transformação Digital**
- Instructions aceitas sem erro de 8.000 caracteres
- `teo-method-playbooks.md` presente em Knowledge
- GPT lista as **18** Actions do contrato no código, depois de reimport manual. Critérios antigos de **20/21** são HISTORICAL. Reimport no Builder = TEST_NOT_RUN neste documento
- OAuth pede **Sign in**
- `gpt_analyze` / `gpt_get_catalog` / `gpt_get_process_context` respondem sem erro de token/redirect
- `gpt_get_catalog` devolve `registration_guide`
- Builder evals M01–M10 executados na configuração documentada

Detalhes: [`custom-gpt-actions.md`](./custom-gpt-actions.md).
