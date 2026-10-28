# EVA MCP V1 — ChatGPT Connection (guia operacional)

Guia para conectar o Plugin **EVA — Engenharia Virtual Assistida** no
ChatGPT. Segue o runbook transversal
`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`
(FASE E–H) — este documento apenas fixa os valores EVA.

## 1. Identidade do Plugin

| Campo | Valor |
|---|---|
| Name | `EVA — Engenharia Virtual Assistida` |
| Descrição | Especialista de Engenharia do Portal Engenharia DELPI — consulta área de trabalho (tarefas, solicitações, LMPs) e indicadores oficiais (LMP + TRANSFORMA+), somente leitura, com provenance e disponibilidade honestas. |
| Server URL (resource) | `https://minhadelpi.com.br/apps/engineering-api/mcp` |
| Authentication | OAuth |
| OAuth mode | **Cliente OAuth definido pelo usuário** (client governado `mcp-engineering`) |
| Client ID / Secret | do Keycloak (doc 28) — nunca no repositório |
| Token auth | `client_secret_post` |
| Scopes | `openid profile email mcp:tools` (+ `offline_access` always-requested, padrão TÉO) |

**Não** depender de DCR nem tratar aviso de CIMD como bloqueio — o client
governado já carrega audience/scopes/PKCE revisados.

### Redirect URI — regra crítica

1. Criar o Plugin no ChatGPT primeiro.
2. Selecionar **Cliente OAuth definido pelo usuário**.
3. Copiar a **URL de retorno exata** exibida pelo ChatGPT.
4. Colar em Keycloak → `mcp-engineering` → Valid redirect URIs.
5. Prosseguir o fluxo OAuth.

Nunca inventar a redirect; nunca reutilizar callback de TÉO/DAVI/CLARA.

## 2. Ferramentas esperadas (tool discovery)

Exatamente **3 tools** READ/discovery — nenhuma de escrita:

| Tool | Resposta esperada |
|---|---|
| `get_catalog` | catálogo com as 3 tools + `planned_capabilities` `not_implemented` + notas de disponibilidade/metas |
| `get_engineering_home` | payload `/v1/home` do usuário autenticado: sections, attention, tasks, lmps, requests, activity, collaboration + status por fonte |
| `get_engineering_overview` | payload `/v1/overview`: 6 indicadores com valor, unidade, período, escopo, provenance; metas/IDD só em `lmp_on_time` e `transforma_gross_savings` |

Tool count do provider ≠ parâmetro de regressão: comparar **coverage**, não
número com outras superfícies (nota TÉO no runbook).

## 3. Testes de conexão

```text
P0  GET …/.well-known/oauth-protected-resource → 200 + resource EVA
P1  POST /mcp sem token → 401 + WWW-Authenticate (resource_metadata)
P2  POST /mcp token inválido → 401
P3  Plugin criado → login com usuário real DELPI (proibido service account)
P4  initialize + tools/list via ChatGPT → 3 tools
P5  "Quais são minhas demandas de Engenharia?" → get_engineering_home
    com dados do usuário autenticado
P6  "Qual o % de LMPs dentro do prazo este mês?" → get_engineering_overview
    com competence → indicador + meta (se owner a publicou)
P7  Usuário sem engineering.access → resposta forbidden estruturada,
    nunca dados nem 200 silencioso
P8  Fonte downstream indisponível → resposta declara unavailable —
    nunca "você não tem tarefas"
```

Cada prova deve registrar: usuário (sanitizado), tool, status, provenance
(`generated_at`, source) — **sem tokens** em logs/screenshots.

## 4. Critérios de aceite da conexão

- OAuth completa com usuário humano real (paridade user = portal).
- `aud` do token contém `delpi-central` + resource EVA e **não** outros MCPs.
- Respostas carregam dados oficiais com provenance visível.
- Falhas aparecem como erro/disponibilidade honesta (não como sucesso).
- Nenhuma capacidade `not_implemented` é apresentada como funcional.

## 5. Troubleshooting EVA-específico

| Sintoma | Causa provável | Correção |
|---|---|---|
| 401 com `resource_metadata` no challenge | token sem aud EVA ou sem `mcp:tools` | revisar mapper dedicado + scopes (doc 28 §3–4) |
| 401 imediato mesmo com token portal | `aud` tem `delpi-central` mas falta resource exato | conferir `Included Custom Audience` exato (sem `/` final) |
| tools/list vazio no ChatGPT | metadata/conformance — `list_tools` in-process ≠ provider | re-checar discovery do provider; ver `securitySchemes` |
| Resposta 403 estruturada | usuário sem `engineering.access` | grant na Core — não é defeito do MCP |
| "sem tarefas" com fonte down | cliente ignorou status `unavailable` | grounding: reportar indisponibilidade, não ausência |
| ChatGPT insiste em DCR | — | selecionar Cliente OAuth definido pelo usuário |
| aud misturando outro MCP | mapper de resource dentro de `mcp:tools` shared | mover mapper p/ dedicated scope do `mcp-engineering` |

## 6. Rollback

- ChatGPT: desativar/excluir o Plugin (não afeta outros especialistas).
- Keycloak: desabilitar `mcp-engineering` → 401 fail-closed em `/mcp`.
- Código: `git revert` do commit EVA + redeploy `engineering-api` + gateway —
  rotas `/v1` REST e o Portal Engenharia não são impactados.

## 7. Estado esperado após esta entrega

```text
Código+infra+docs:        PROVEN (SHA do commit EVA.MCP.V1)
Endpoint fail-closed:     PROVEN (401 sem token correto)
Client Keycloak:          PENDING_ADMIN (doc 28)
Plugin ChatGPT conectado: PENDING_ADMIN (este guia)
Smoke autenticado e2e:    TEST_NOT_RUN até credencial oficial
```
