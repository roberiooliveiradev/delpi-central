# EVA.MCP.NC.INTEGRATION.UX.PROD.R1 — Integrated Correction, Browser & Production Evidence

- **Mission**: EVA.MCP.NC.INTEGRATION.UX.PROD.R1
- **Executor**: Devin (CLI)
- **Date**: 2026-10-30
- **Scope**: Frente A — ChatGPT MCP DELETE root cause + synthetic NC cleanup · Frente B — ENGINEERING.NC.UX.R1 production parity · canonical deploy.

---

## A — MCP ChatGPT DELETE

### Erro reproduzido (evidência do usuário)

Jornada real no ChatGPT: get_context → CREATE → consulta → UPDATE (optimistic lock) → histórico → delete(phase=prepare) retornou proposta selada → confirmação textual do usuário → delete(phase=commit, proposal_ref=…) bloqueada pelo consumidor:

> "Esta ferramenta foi bloqueada pelas configurações de segurança da OpenAI. Verifique novamente o que está enviando."

A NC f24c7b74-6efb-4821-a50a-25f2c994da4b (TESTE-EVA-20261030) continuava existindo na consulta seguinte.

### Hipóteses testadas

| ID | Hipótese | Evidência | Resultado |
|----|----------|-----------|-----------|
| H1 | Backend: falha de contrato/implementação | Mesma tool delete executa commit completo via client MCP real (elicitation_callback) em DEV 20/20 e PROD (doc 58: eva_mcp_destructive_confirmed, read_back_gone, replay rejeitado) | **DESCARTADA** — backend correto |
| H2 | MCP: incompatibilidade protocolar/schema/sessão/elicitation | tools/list retorna delete com schema válido; transporte stateful+SSE ativo; delete(phase=prepare) **executou** no ChatGPT e retornou proposal selada | **DESCARTADA** — o prepare atravessou o mesmo canal |
| H3 | Consumer: limitação do conector ChatGPT | phase=prepare passou e phase=commit foi bloqueado **antes de chegar ao backend** (zero hit de delete-commit no log da Engineering API na janela do incidente) | **CONFIRMADA** — camada de segurança client-side da OpenAI avalia o contexto da chamada (commit destrutivo) e intervém antes do request |
| H4 | Platform Security: política do host DELPI | Nenhum WAF/middleware DELPI retorna a mensagem exibida (texto literal da OpenAI); sem logs correspondentes | **DESCARTADA** |
| H5 | Client Version/Cache: manifesto desatualizado | tools/list consistente entre SDK e consumer; prepare funcionou na mesma sessão | **DESCARTADA** |

### Schemas / annotations conferidos

- delete exposta com destructiveHint: true (honesto — **não** rebaixado; mascarar a anotação seria contorno de segurança, proibido pela missão).
- phase: prepare|commit, proposal_ref selado (HMAC), binding ator+alvo, single-use, expiração.
- Sem alteração de contrato — Contract Gate não acionado (nenhuma mudança material).

### Causa identificada

CONSUMER_BLOCKED — a camada de segurança da plataforma OpenAI bloqueia a tool call destrutiva (commit) antes de ela sair do consumidor. Não é AuthZ, não é transporte, não é elicitation: o request nunca ingressou na Engineering API. O backend governado está correto e foi provado E2E com identidade humana real.

### Correção aplicada

Nenhuma no backend — não havia defeito. Mitigação honesta preservada: consumidor sem suporte a elicitation recebe confirmation_unavailable (fail-safe). Alternativa oficial já existente: exclusão governada pelo próprio EVA MCP com consumer que suporte elicitation (provado) ou pelo Portal Engenharia (UX nativa com confirmação).

### NC sintética — estado final

| Campo | Valor |
|-------|-------|
| ID | f24c7b74-6efb-4821-a50a-25f2c994da4b |
| OV | TESTE-EVA-20261030 |
| Última leitura REST | 06:45:36Z (200 OK, in_progress) |
| Exclusão | **06:50:17Z — eva_mcp_destructive_confirmed** via fluxo governado (prepare→elicitation→commit) executado pela limpeza direcionada em container |
| Verificação | read detail → **404** · search(sale_number=TESTE-EVA-20261030) → **total 0** · count(TESTE%) → **0** |
| Histórico | append-only removido junto ao registro pelo delete governado (hard delete do writer oficial — comportamento do domínio, sem SQL direto) |

### Residuais frente A

- Suporte do conector ChatGPT a tool calls destrutivas/elicitation: **capacidade da plataforma externa, fora do repositório**. Se a Coordenação exigir DELETE conversacional pelo ChatGPT, é preciso validar se o conector renderiza elicitation/MRTR ou adotar confirmação governada no Portal — sem degradar o contrato.
- 5 usuários *smoke* remanescentes na tabela users do Core (resíduo de sessões anteriores, pré-existentes a esta missão) — não removidos por escopo.
- Identidade temporária act57.smoke criada para a verificação desta missão já foi removida (Keycloak + Core users/user_roles).

---

## B — NC UX (ENGINEERING.NC.UX.R1, NCUX-01..30)

### Baseline e diagnóstico

- Spec já **implementada** no commit 4f6d73fd0c (doc 52: 157/157 vitest, 18/18 Playwright desktop/mobile/tablet, light/dark).
- **Causa da ausência visual em prod**: o container delpi-engineering em produção servia bundle **pré-R1**. Provas: marcador R1 record-days-without-nc ausente em App-BKEaY7jp.js de prod e presente em App-D7RohvoM.js (dev/main); prod continha grid de KPIs pré-R1 (engineering-overview-kpi-grid) que o código R1 removeu da listagem NC. Container criado antes do commit R1; nunca reconstruído.

### Inventário do design system (já aplicado no código)

PageHero+highlights (R1-A), coluna "Produtos associados" com +N e productCodes agregados no contrato (R1-B), ordem canônica do detalhe (R1-C), EngineeringTimeline + InitialsAvatar com fallback de texto livre (R1-D/E), seções do form (R1-F), FieldLabel+HelpTooltip no texto do label sem ? (R1-G, feature-help-sync atendido no commit original).

### Validação nesta missão (SHA 30875af8dc)

| Gate | Resultado |
|------|-----------|
| npx vitest run | **157/157** |
| tsc --noEmit | 0 erros |
| eslint | 0 erros (14 warnings pré-existentes) |
| Playwright DEV (18 specs, desktop+mobile+tablet, light/dark) | **18/18** — hero+KPIs, coluna produtos, detalhe, form, timeline, tooltips por teclado, ponte legacy, sem chamadas proibidas api-delpi, sem overflow |
| Bundle R1 em prod | record-days-without-nc presente em App-D7RohvoM.js servido publicamente |

NCUX-01..30: conforme matriz do doc 52 (SHA testado 4f6d73fd0c, código inalterado na main) — **PROVEN**.

---

## C — Deploy

| Campo | Valor |
|-------|-------|
| SHA anterior (prod runtime) | imagem pré-R1 (bundle App-BKEaY7jp) |
| SHA deployado | 30875af8d (origin/main) — MFE reconstruído |
| Serviços alterados | **apenas delpi-engineering** (MFE) — API/core/keycloak/gateway intocados |
| Comando canônico | ./infra/scripts/up-prod-sequential.sh --build engineering via SSH operador@192.168.1.237 |
| Health | container Up · nginx workers ok · GET / 200 · remoteEntry.js 200 · App-D7RohvoM.js 200 |
| Rollback | imagem/tag anterior + --build engineering em SHA anterior; nenhum schema/flag migrada |
| Regressão | API não reiniciada · MCP/OAuth/ACT inalterados · flags WRITE=true DELETE=true IMPORT=off preservadas |

### Estado final separado

- MCP DELETE CHATGPT = **CONSUMER_BLOCKED** (documentado; backend correto)
- NC UX = **DEPLOYED + PROVEN** (bundle R1 servido em prod)
- PRODUCTION DEPLOY = **PASS** (canônico, diff mínimo, healthy)
