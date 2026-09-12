# Minha DELPI Copilot — Matriz de Onboarding dos Apps

**Status:** inventário inicial / `TO_INVENTORY`  
**Owner de atualização factual:** C0.S0 + readiness scanner futuro  
**Regra:** nenhum campo sem evidence vira comprovado por suposição.

## 1. Níveis AI-ready

| Nível | Nome | Critério mínimo |
|---|---|---|
| L0 | NOT_INVENTORIED | não auditado |
| L1 | DISCOVERABLE | app/rotas/permissions discoverable |
| L2 | CONTEXT_READY | EntityRef/deep link + Workspace Context quando material |
| L3 | READ_READY | Business reads via contrato canônico + RBAC + outcome/evidence |
| L4 | WRITE_READY | writes via API + policy/Decision Gate + idempotency/audit |
| L5 | WORKFLOW_READY | capabilities confiáveis para Durable Workflows/events necessários |

Nível maior pressupõe requisitos materiais anteriores.

## 2. Classificação ortogonal de iframe

```text
I0 PORTAL_ONLY
I1 CONTEXTUAL
I2 INTERACTIVE
I3 AI_READY
```

I3 exige Business Actions por API/OpenAPI; bridge visual sozinho não basta.

## 3. Campos obrigatórios por app

C0.S0 deve registrar, quando aplicável:

```text
appId
name
renderMode
plugin/MFE path
backend/domain owner
Core registration
/me/apps routes
permissions
canonical entity types/IDs
entity deep-link support
Workspace Context support
OpenAPI location/quality
business reads
business writes
destructive/high-risk actions
risk/sensitivity owner
Decision Gate readiness
idempotency/concurrency support
outcome/evidence/freshness support
domain events relevant to workflows/watch
current AI/agent integration
AI-ready level
iframe integration class
iframe origin/SSO/bridge/CSP
knowledge/help sources
owner/team
candidate wave
blockers
evidence paths/hashes/verifiedAt
```

## 4. Inventário inicial — candidatos conhecidos

A lista é ponto de partida, não prova de existência/owner. C0.S0 deve reconciliar com `plugins/`, manifests, Core registrations, APIs e roadmaps reais.

| Área/app | Referência conhecida | Nível | Wave candidata | Estado |
|---|---|---:|---|---|
| Minha DELPI Chat | `plugins/minha-delpi-chat` + AI API | revalidar | Fundação | TO_INVENTORY |
| Portal Comercial | portal comercial | L0 | Wave 1 candidata | TO_INVENTORY |
| Portal Suprimentos | portal suprimentos | L0 | Wave 1 candidata | TO_INVENTORY |
| Minhas Solicitações | `my-requests` | L0 | Wave 1 candidata | TO_INVENTORY |
| Portal Engenharia | engineering | L0 | Wave 2 | TO_INVENTORY |
| Portal Financeiro | financial | L0 | Wave 2 | TO_INVENTORY |
| Production Control | production-control | L0 | Wave 2 | TO_INVENTORY |
| Production Pulse | production-pulse | L0 | Wave 2 | TO_INVENTORY |
| Apontamento Produção | production-appointments | L0 | Wave 2 | TO_INVENTORY |
| Eficiência Fabril | eficiencia-fabril | L0 | Wave 2 | TO_INVENTORY |
| Acompanhamento Refugos | scrap-monitoring | L0 | Wave 2 | TO_INVENTORY |
| Indicadores Estratégicos | strategic indicators | L0 | Wave 2 | TO_INVENTORY |
| Manutenção | maintenance | L0 | Wave 2 | TO_INVENTORY |
| Customer Experience | customer-experience | L0 | Wave 2 | TO_INVENTORY |
| Planos de Ação Qualidade | quality-action-plans | L0 | Wave 2 | TO_INVENTORY |
| Labels Qualidade | quality-labels | L0 | Wave 3 | TO_INVENTORY |
| Inspeções Entrada | inspecoes-entrada | L0 | Wave 2 | TO_INVENTORY |
| Inspeções Processo | inspecoes-processo | L0 | Wave 3 | TO_INVENTORY |
| Solicitações Compras | purchase requests | L0 | Wave 2 | TO_INVENTORY |
| Controle MP | controle-mp | L0 | Wave 3 | TO_INVENTORY |
| Emissão NF | invoice issuance | L0 | Wave 3 | TO_INVENTORY |
| Lançamento NF | lancamento-notas-fiscais | L0 | Wave 3 | TO_INVENTORY |
| Despesas Viagem | travel expenses | L0 | Wave 3 | TO_INVENTORY |
| CIPA | cipa | L0 | Wave 3 | TO_INVENTORY |
| Comitê Ética/Conduta | ética/conduta | L0 | Wave 3 | TO_INVENTORY |
| Auditoria 5S | auditoria-5s | L0 | Wave 3 | TO_INVENTORY |
| Central Agendamento | central-agendamento | L0 | Wave 3 | TO_INVENTORY |
| Delpi Reports | delpi-reports | L0 | Wave 3 | TO_INVENTORY |
| TV Dashboard | tv-dashboard | L0 | Wave 3 | TO_INVENTORY |
| Transformômetro | transformometro | L0 | Wave 3 | TO_INVENTORY |

Adicionar/remover linhas somente com evidence.

## 5. Critério de Wave 1

Escolher apps que maximizem aprendizado e reduzam risco:

- Core registration e routes estáveis;
- owner disponível;
- EntityRef/deep-link claro;
- OpenAPI real e razoável;
- read forte e de valor;
- Workspace Context útil;
- baixo risco para piloto;
- caminho futuro de write governado;
- testes/observability possíveis.

Comercial, Suprimentos e Minhas Solicitações são apenas candidatos até C0.S0.

## 6. Readiness score

Score pode ajudar priorização, mas **não substitui gates**.

Itens possíveis:

```text
Core registration
routes/RBAC
EntityRef/deep-link
Workspace Context
OpenAPI quality
read action
outcome/evidence
write action
Decision Gate readiness
idempotency
contract/eval tests
observability
event readiness quando necessário
```

Bloqueio de segurança vence score.

## 7. Evidence por linha

```text
gitSha
manifest path
Core registration evidence
route/permission source
OpenAPI source/hash
entity/deep-link contract
Workspace Context contract/test
Decision/idempotency contract
event source quando aplicável
iframe origin/SSO/protocol quando aplicável
smoke/eval
lastVerifiedAt
```

Sem evidence: `TO_INVENTORY`.

## 8. Promoção AI-ready

### L1 → L2
Context/Entity foundations comprovadas.

### L2 → L3
Generic read + RBAC + outcome/evidence tests.

### L3 → L4
Write + Decision Gate + idempotency/audit tests.

### L4 → L5
Workflow safety + retry/resume/events quando o use case exigir.

## 9. Promoção iframe

```text
I0 → I1
handshake/security + context lifecycle

I1 → I2
generic declared visual commands + observations

I2 → I3
Business Actions via API/OpenAPI + RBAC/policy/Decision Gate/evals
```

Fonte: [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).

## 10. Regra foundation-first

Onboarding de app **não cria novos primitives**. Se um app exigir variante de EntityRef, Evidence, Decision, Workspace ou Event, primeiro validar se existe gap real na foundation e versionar de forma compartilhada.