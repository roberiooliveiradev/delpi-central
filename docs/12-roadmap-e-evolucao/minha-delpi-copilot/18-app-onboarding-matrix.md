# Minha DELPI Copilot — Matriz de Onboarding dos Apps

**Status:** inventário inicial; deve ser atualizado por C0.S0 com evidência real.  
**Regra:** `TO_INVENTORY` significa “não comprovado ainda”; não substituir por suposição.

## 1. Níveis AI-ready

| Nível | Nome | Critério mínimo |
|---|---|---|
| L0 | NOT_INVENTORIED | app ainda não auditado para Copilot |
| L1 | DISCOVERABLE | app/rotas/permissões descobertos pelo Core/Portal |
| L2 | CONTEXT_READY | publica Workspace Context tipado |
| L3 | READ_READY | reads relevantes utilizáveis pelo Copilot via contrato canônico |
| L4 | WRITE_READY | writes com schema/policy/confirmation/audit e paridade UI |
| L5 | WORKFLOW_READY | capabilities confiáveis em workflows compostos |

Nível maior implica requisitos dos níveis anteriores.

## 2. Campos obrigatórios por app

Para cada app, C0.S0/C5.S3 deve comprovar:

```text
appId
nome
render type (microfrontend/iframe/backend-only/external quando aplicável)
MFE/plugin path
backend owner
OpenAPI disponível?
qualidade do OpenAPI
registrado no Core?
rotas autorizadas disponíveis em /me/apps?
permissions reais
entity deep-link?
workspace context?
business reads?
business writes?
destructive actions?
sensitivity/confirmation?
integração AI atual?
nível AI-ready
iframe integration class quando aplicável
origin/SSO/bridge evidence quando aplicável
wave proposta
bloqueios
evidence
```

## 3. Inventário inicial

A lista abaixo é derivada da estrutura/documentação do monorepo já conhecida. Os detalhes técnicos não inspecionados permanecem `TO_INVENTORY`.

| Área/app | Código/roadmap conhecido | Backend provável/observado | OpenAPI | Context | Reads | Writes | Nível atual | Wave candidata | Estado |
|---|---|---|---|---|---|---|---|---|---|
| Minha DELPI Chat | `plugins/minha-delpi-chat` | `minha-delpi-ai-api` | existente para AI API | parcial/existente | sim | administração/config conforme RBAC | L1+ existente, revalidar | Fundação | TO_INVENTORY detalhado |
| Portal Comercial | roadmap `commercial` + MFE correspondente | `commercial-api` + `api-delpi` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 1 candidata | TO_INVENTORY |
| Portal Suprimentos | roadmap/plugin supplies | `supplies-api` + `api-delpi` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 1 candidata | TO_INVENTORY |
| Minhas Solicitações | roadmap/plugin `my-requests` | `requests-api` e integrações | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 1 candidata | TO_INVENTORY |
| Portal Engenharia | roadmap `engineering` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Portal Financeiro | roadmap `financial` | `financial-api` + `api-delpi` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Production Control | `production-control` | `production-control-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Production Pulse | `production-pulse` | `production-pulse-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Apontamento Produção | `production-appointments` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Eficiência Fabril | `eficiencia-fabril` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Acompanhamento Refugos | `scrap-monitoring` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Indicadores Estratégicos | plugin/API strategic indicators | `strategic-indicators-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Manutenção | roadmap/plugin maintenance | `maintenance-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Customer Experience | roadmap/plugin customer experience | `customer-experience-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Planos de Ação Qualidade | `quality-action-plans` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Labels Qualidade | `quality-labels` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Inspeções Entrada | `inspecoes-entrada` | `api-delpi`/owner específico TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Inspeções Processo | `inspecoes-processo` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Solicitações Compras | `solicitacoes-compras` / purchase requests | `purchase-requests-api` ou owner real TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 2 | TO_INVENTORY |
| Controle MP | `controle-mp` | integração via Minhas Solicitações planejada | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Emissão NF | `invoice-issuance` | owner/API TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Lançamento NF | `lancamento-notas-fiscais` | owner/API TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Despesas Viagem | app/API de travel expenses | `travel-expenses-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| CIPA | plugin/app CIPA | `cipa-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Comitê Ética/Conduta | plugin/app ética | `comite-etica-conduta-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Auditoria 5S | `auditoria-5s` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Central Agendamento | `central-agendamento` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| Delpi Reports | `delpi-reports` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |
| TV Dashboard | `tv-dashboard` | `tv-dashboard-api` | TO_INVENTORY | pouco aplicável, verificar | read-only provável, verificar | provável não | L0 | Wave 3 | TO_INVENTORY |
| Transformômetro | app/plugin transformômetro | `transformometro-api` | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | L0 | Wave 3 | TO_INVENTORY |

A tabela não pretende ser inventário exaustivo. C0.S0 deve comparar a árvore real de `plugins/`, manifests, Core registrations e `docs/12-roadmap-e-evolucao/` e acrescentar/remover linhas com evidência.

## 4. Critério para Wave 1

Escolher 2–3 apps que maximizem aprendizado e minimizem risco:

- registrados corretamente no Core;
- rotas estáveis;
- APIs reais documentadas;
- OpenAPI de boa qualidade;
- um caso forte de `read`;
- ao menos um caso de `write` não destrutivo para fase posterior;
- entidades com identificador/deep link claro;
- time/owner disponível para corrigir gaps.

**Candidatos atuais são somente recomendação:** Comercial, Suprimentos e Minhas Solicitações. C0.S0 deve confirmar ou alterar a escolha.

Para iframe, o piloto de bridge pode ser um app separado do piloto de Business Action. Priorizar owner disponível, origin estável, baixo risco e possibilidade de implementar contrato sem alterar regra de negócio.

## 5. Score de readiness sugerido

Pontuar 0/1 por item comprovado:

```text
Core registration
routes authorized
permissions explicit
OpenAPI available
OpenAPI required/type/enum/format quality
read action usable
write action usable
sensitivity known
confirmation policy known
entity refs/deep link
workspace context
contract tests
observability
```

Para iframe, acrescentar:

```text
render mode conhecido
origin authority conhecida
SSO mode comprovado
bridge handshake comprovado
context publish comprovado
visual command support comprovado
security negative tests comprovados
```

Não usar score para mascarar bloqueio de segurança. App com write sem RBAC/policy/confirmation não pode ser L4 independentemente da pontuação.

## 6. Evidence por linha

Cada atualização deve indicar, quando aplicável:

```text
gitSha
manifest path
backend OpenAPI path/url
permission source
route source
render mode
iframe origin source
SSO mode
bridge protocol/version
contract test
smoke/eval
last verified at
```

Sem evidence, estado continua `TO_INVENTORY`.

## 7. Classificação específica de iframe

Além do nível AI-ready global L0–L5, apps com renderização iframe possuem uma classificação ortogonal:

| Classe | Nome | Critério |
|---|---|---|
| I0 | `PORTAL_ONLY` | app/rota autorizados podem ser abertos pelo Portal; sem contexto interno |
| I1 | `CONTEXTUAL` | I0 + publica contexto bounded via protocolo validado |
| I2 | `INTERACTIVE` | I1 + aceita comandos visuais genéricos declarados e retorna observation |
| I3 | `AI_READY` | I2 + Business Actions relevantes existem via API/OpenAPI governada |

Um app pode, por exemplo, ser `L3 READ_READY` e `I1 CONTEXTUAL`, ou `L1 DISCOVERABLE` e `I0 PORTAL_ONLY`.

## 8. Campos adicionais para iframe

C0.S0 deve acrescentar por app iframe/external:

```text
renderMode
iframeIntegrationClass
entry/origin authority
allowed origins
SSO/auth mode
bridge existing? yes/no
bridge protocol/version
context publish support
visual commands suportados
runtime declared capabilities
Business API/OpenAPI support
security owner
CSP/frame constraints
last bridge verification
```

`external` sem canal controlado normalmente permanece `PORTAL_ONLY` para o Copilot.

## 9. Regras de promoção de classe iframe

```text
PORTAL_ONLY → CONTEXTUAL
somente com handshake + origin/source/schema + lifecycle + context tests

CONTEXTUAL → INTERACTIVE
somente com command allowlist + declared capabilities + observation + negative security gates

INTERACTIVE → AI_READY
somente com Business Actions por API/OpenAPI + RBAC/policy/confirmation + evals
```

`postMessage` funcionando isoladamente não promove o app para `AI_READY`.

Fonte canônica: [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).
