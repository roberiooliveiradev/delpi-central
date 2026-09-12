# Minha DELPI Copilot — Plano Mestre Executável

**Status:** planejamento executável  
**Owner arquitetural:** plataforma Minha DELPI  
**Escopo:** `portal`, `minha-delpi-ai-api`, `plugins/minha-delpi-chat`, Core API, APIs de domínio, MFEs e apps iframe  
**Fonte funcional:** [`13-functional-catalog.md`](./13-functional-catalog.md)  
**DoD:** [`14-definition-of-done.md`](./14-definition-of-done.md)

## 1. Objetivo

Este documento converte a arquitetura do Minha DELPI Copilot em uma sequência de implantação que possa ser executada pelo Cursor sem pular dependências, criar motores paralelos ou inventar contratos.

O plano não cria uma nova IA. Ele evolui a plataforma existente.

```text
Minha DELPI AI base
+ Portal Shell
+ Core API
+ APIs OpenAPI
+ MFEs/iframes
→ Minha DELPI Copilot
```

## 2. Invariantes de execução

1. Não criar segundo motor de planner/tools fora de `minha-delpi-ai-api`.
2. Business Actions usam OpenAPI + Action Catalog + executor genérico existente.
3. Capability Catalog de negócio é projeção/índice, nunca catálogo técnico paralelo.
4. Platform Actions são genéricas e tipadas; não criar `portal.open_commercial`, `portal.open_supplies`, etc.
5. Rotas acessíveis derivam do Core API (`/me/apps`); o LLM não inventa URLs.
6. `CopilotBridge` revalida o comando contra o estado autorizado atual antes de executar.
7. Workspace Context transporta referências estruturadas e bounded state, nunca o estado React inteiro nem dump de DOM/iframe.
8. Segurança real permanece server-side. UI é experiência/defesa em profundidade.
9. Nenhum write/destructive pode ser liberado sem sensitivity, RBAC, confirmação e auditoria.
10. Nova API OpenAPI deve funcionar sem hardcode por provider/path/operationId no core genérico.
11. Novo app deve entrar por contratos e metadados canônicos, não por regras centrais específicas.
12. Não marcar etapa como concluída com `PARTIAL`, `INCONCLUSIVE`, `LEGACY_FALLBACK`, `TODO` material ou evidência stale.
13. App iframe usa bridge tipado para contexto/experiência; Business Action não é implementada por DOM automation.
14. Iframe bridge não transporta JWT/refresh token e deve validar origin/source/schema/protocol.

## 3. Dependência crítica — Onda J da AI API

A iniciativa `llm-json-decoupling` permanece com `VERIFY_FINAL_FAILED` no estado documentado atualmente.

Consequência:

- **C0–C2** podem evoluir: contratos, Platform Actions, CopilotBridge, IframeBridge e Workspace Context;
- **C3+ Business Actions em produção** ficam bloqueadas até os gates relevantes OpenAPI-first/tool-routing/argument-binding/evals estarem `PASS` no candidate vigente;
- unit/integration scaffolding de C3 pode ser preparado, mas não deve ser declarado production-ready enquanto a dependência estiver aberta.

Não duplicar a correção da Onda J dentro do Copilot. Referenciar e aguardar o owner correto.

## 4. Grafo macro

```text
C0 Fundação e inventário
 |
 +--> C1 Platform Actions / navegação / iframe PORTAL_ONLY
 |      |
 |      +--> C2 Workspace Context / iframe contextual-interativo
 |              |
 |              +--> C3 Business Action Parity
 |                       |
 |                       +--> C4 Agentic Workflows
 |                                |
 |                                +--> C5 Ecossistema AI-ready + SDK iframe
 |                                         |
 |                                         +--> C6 Autonomia governada
 |                                                  |
 |                                                  +--> C7 rollout final
 |
 +--> gates/evidence transversais em todas as fases
```

## 5. Protocolo obrigatório por subetapa

```text
REVALIDATE HEAD + git status
→ ler regras/docs/contratos aplicáveis
→ READY_TO_EXECUTE
→ baseline/preconditions
→ menor implementação correta
→ provar wiring producer→consumer
→ unit/contract
→ integration
→ positive + sibling + negative
→ RBAC/security
→ generalization/metamorphic/unknown quando aplicável
→ adversarial diff review
→ semantic residual search
→ validar postconditions
→ COMPLETE_GATE
→ atualizar ledger/docs
→ liberar dependente
```

Se houver drift material, registrar `EXECUTION_DRIFT` e não esconder a diferença.

---

# C0 — Fundação, inventário e contratos

## C0.S0 — Rebaseline e inventário real

**Objetivo:** congelar o estado real antes de qualquer runtime diff.

Inventariar:

- Portal: Router, `AuthContext`, AppLauncher, `AppHost`, eventos/bridge existentes;
- Core API: `/me`, `/me/apps`, `/me/routes`, contratos de app/route/permission;
- AI API: planner, Action Catalog, external action executor, policies, confirmation, persistence, send/stream/simulate;
- Chat MFE: transportes/eventos, side panel/page, activity, render plan;
- plugins/MFEs: manifesto, rotas, backend, OpenAPI, permissões, deep link, filtros/contexto;
- apps `iframe`/`external`: manifesto, render mode, entry/origin, SSO, owner, capacidade de integração, mensagens/eventos já existentes;
- APIs: OpenAPI real, reads, writes, destructive, sensitivity/permission;
- contratos existentes que possam ser reutilizados.

**Artefatos obrigatórios:**

- atualizar [`18-app-onboarding-matrix.md`](./18-app-onboarding-matrix.md), incluindo classificação de iframe;
- producer/consumer graph em [`17-component-and-contract-map.md`](./17-component-and-contract-map.md);
- evidence com HEAD/config e findings no ledger.

**Proibido:** implementar runtime antes de concluir o inventário.

**DoD:** não há owner/consumer relevante marcado apenas por suposição.

## C0.S1 — Freeze de ownership e contratos v1

Definir e versionar semanticamente:

- `PlatformCommandV1`;
- `PlatformCommandResultV1`;
- `WorkspaceContextV1`;
- `CapabilityProjectionV1`;
- `IframeBridgeEnvelopeV1`/handshake equivalente, se não existir contrato canônico reutilizável;
- `ConfirmationRequestV1` / `ConfirmationDecisionV1`;
- `WorkflowPlanV1` e step envelope, se ainda não existir equivalente canônico reutilizável;
- event envelope send/stream para comandos de plataforma.

Antes de criar schema novo, provar que nenhum contrato canônico existente atende ao caso.

## C0.S2 — Harness e gates-base

Criar testes de contrato que falhem antes da implementação para:

- PlatformCommand inválido;
- URL arbitrária rejeitada;
- app/route não autorizado rejeitado;
- WorkspaceContext sanitizado/limitado;
- iframe origin/source/schema/session inválidos;
- paridade send/stream do envelope;
- confirmação obrigatória não bypassável.

---

# C1 — Platform Actions e navegação

## C1.S1 — Authorized Portal Capability Projection

Derivar capabilities de navegação do retorno autorizado do Core API.

Target:

```text
/me/apps
→ AuthorizedPortalRoutes
→ CapabilityProjection(platform.navigation)
```

Sem lista manual de apps no Copilot.

Apps iframe também entram como alvo de navegação quando autorizados, independentemente de suportarem bridge avançado.

## C1.S2 — CopilotBridge

Implementar no Portal Shell:

- validator de `PlatformCommandV1`;
- registry somente de handlers **genéricos**;
- lookup/revalidation de app/route autorizados;
- delegação para Router/MFE/IframeBridge conforme adapter da experiência;
- resultado tipado;
- observabilidade.

## C1.S3 — Navegação mínima

Implementar:

- `portal.open_app`;
- `portal.open_route`.

Positive/sibling/negative obrigatórios, incluindo pelo menos um app MFE e um app iframe autorizado quando o inventário real permitir.

## C1.S4 — Transporte AI → Portal

Enviar comando tipado pelo pipeline existente de resposta/send/stream. O Chat MFE recebe e encaminha ao Bridge; não executa regras de autorização próprias.

## C1.S5 — Segurança/TOCTOU/auditoria

Testar:

- acesso autorizado;
- app não autorizado;
- rota inexistente;
- rota revogada entre planejamento e execução;
- payload adulterado;
- deep link inválido;
- replay quando não aplicável;
- iframe origin/source inválido quando bridge estiver ativo.

## C1.S6 — UX piloto

Entregar:

- “Abrir app”;
- “Ir para página”;
- action chip/botão “Abrir no app”;
- activity de navegação;
- feedback de falha sem expor rota proibida.

## C1.S7 — Iframe Bridge base

Implementar, quando C0 confirmar necessidade e ausência de equivalente:

- handshake `hello/bridge.ready` ou contrato canônico equivalente;
- associação iframe ↔ app autorizado;
- validation de `origin` e `event.source`;
- protocol/version/session;
- capability negotiation de experiência;
- lifecycle cleanup em navegação/logout/unmount.

Objetivo desta etapa: habilitar `PORTAL_ONLY` universal e preparar I1+, sem Business Actions por bridge.

---

# C2 — Workspace Context

## C2.S1 — Contrato compartilhado

Criar/reutilizar tipos para `WorkspaceContextV1` com bounded fields:

```text
appId
routeId
entityRefs[]
filters
selection
dateRange
visibleDataRefs[]
contextVersion
source
timestamp
```

`source` deve distinguir origem quando útil (`mfe`, `iframe`, `portal`) sem alterar semântica do contexto.

## C2.S2 — Portal Context Store

Portal mantém contexto ativo e lifecycle de troca de app/rota. Dados efêmeros por padrão.

## C2.S3 — SDK/helper para MFEs e adapter de iframe

Criar API simples para MFE publicar/limpar contexto, sem depender internamente do Copilot.

Exemplo conceitual:

```text
publishWorkspaceContext(partialContext)
clearWorkspaceContext(scope)
```

Iframe usa o contrato do [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md) e o Portal normaliza para o mesmo `WorkspaceContextV1`.

## C2.S4 — AI recebe contexto

Adicionar contexto sanitizado ao turno como input estruturado. Não concatenar JSON bruto no prompt como autoridade.

Definir quando snapshot bounded é persistido na conversa.

## C2.S5 — Piloto por app

Escolher após C0.S0. Candidatos recomendados pela relevância funcional: Comercial, Suprimentos ou Minhas Solicitações; a decisão deve ser baseada no inventário real, não nesta recomendação.

Se houver iframe com owner disponível e baixa complexidade, escolher adicionalmente um piloto `CONTEXTUAL` para validar o adapter sem alterar o piloto principal de Business Actions.

## C2.S6 — Explicação contextual

Provar fluxos:

- “explique o que estou vendo”;
- “filtre este cliente/item”;
- “e no mês passado?”;
- “abra o registro selecionado”.

## C2.S7 — Reload/segurança/relevância

Validar stale context, troca de app, F5, logout, mudança de entidade e contexto explícito novo sobrepondo inferência antiga.

## C2.S8 — Iframe contextual/interativo piloto

Para um app iframe compatível:

- `CONTEXTUAL`: publicar entity refs/filtros/view de forma bounded;
- `INTERACTIVE`: executar ao menos um comando visual genérico declarado (`view.set_view`, `view.set_filters` ou equivalente);
- retornar observation tipada;
- provar negative de origin/source/session/capability;
- provar que outro iframe compatível não exige patch app-specific no bridge.

---

# C3 — Paridade de Business Actions

**Gate de produção:** Onda J/tool pipeline aplicável `PASS` no candidate vigente.

## C3.S1 — Business Capability Projection

```text
Allowed Action Catalog
→ capability projection
```

Não copiar `path`, `operationId`, parameters ou schema para JSON manual.

## C3.S2 — Metadata operacional derivada

Derivar genericamente:

- read/write;
- sensitivity;
- requiresConfirmation;
- permissions/policy;
- idempotency expectations quando declaradas pelo contrato/policy.

## C3.S3 — Read parity piloto

Escolher action usada pela UI e provar UI/Copilot → mesma API/use case/outcome autorizado.

## C3.S4 — Write preview/confirmation

Antes do write, gerar preview grounded dos argumentos finais e confirmação forte quando policy exigir.

## C3.S5 — Write execution piloto

Executar pelo use case genérico existente; nunca por DOM automation. Para iframe, é explicitamente proibido implementar write como `click`, script injection ou comando visual equivalente.

## C3.S6 — Result → deep link

Quando houver contrato de entidade/route, oferecer `open_entity/open_route` sem duplicar semântica do endpoint.

## C3.S7 — Readiness scanner

Gerar relatório AI-ready por app usando fatos do repo/runtime, alimentando a matriz de onboarding. Apps iframe devem receber também classificação `PORTAL_ONLY`, `CONTEXTUAL`, `INTERACTIVE` ou `AI_READY`.

---

# C4 — Workflows agentic

## C4.S1 — Goal/DAG contract

Representar objetivos, dependências, capability refs, preconditions, confirmation boundaries e expected outcomes sem chain-of-thought.

## C4.S2 — DAG runner

Reutilizar planner/executors existentes. Não criar novo executor HTTP/tool stack.

## C4.S3 — Resiliência

Retry somente quando seguro, idempotency para writes, partial failure, compensation apenas quando o domínio possuir operação real de compensação.

## C4.S4 — Activity/checkpoints

Expor progresso operacional:

```text
planned
running
waiting_confirmation
succeeded
failed
skipped
compensated
```

## C4.S5 — Compound read workflow

Multi-app/multi-provider com reads paralelos seguros + síntese grounded.

## C4.S6 — Mixed read+write

Reads → análise → proposta → confirmação → write → verificação → deep link.

## C4.S7 — Persist/reload/resume

Workflow durável quando atravessa confirmação/reload/timeout. Não persistir chain-of-thought.

---

# C5 — Ecossistema AI-ready

## C5.S1 — Revalidar necessidade de extensão de manifesto

Somente criar campos novos se o inventário provar gap não atendido por manifesto/rotas/OpenAPI atuais.

Qualquer extensão deve ser versionada, genérica e opcional para funcionalidade OpenAPI básica.

Para iframe, metadados persistentes como origin/render mode podem vir do registro/manifesto se já houver authority adequada; capabilities visuais negociáveis devem preferencialmente ser confirmadas em runtime pelo bridge.

## C5.S2 — SDK/templates

Criar helpers compartilhados para:

- workspace context;
- entity refs/deep links;
- platform view capabilities;
- Iframe Copilot Bridge, se C0 confirmar ausência de equivalente;
- test fixtures contratuais.

## C5.S3 — Scanner de readiness

Classificar apps nos níveis definidos em `18-app-onboarding-matrix.md`, incluindo classe de integração de iframe.

## C5.S4 — Wave 1

Onboard apps com contratos mais maduros e baixo risco.

## C5.S5 — Wave 2

Onboard demais apps e resolver gaps de API/permission/context no owner correto.

## C5.S6 — Coverage dashboard/governança

Visibilidade de capabilities disponíveis, bloqueadas, writes, workflows, evals e gaps por app, incluindo maturidade dos iframes.

---

# C6 — Autonomia governada

## C6.S1 — Policy model

Autonomia é decisão server-side/policy. Não é instrução do prompt.

## C6.S2 — L3 prepare-only

Copilot prepara alteração completa sem persistir.

## C6.S3 — L4 confirmed writes

Writes somente após confirmação exigida e revalidação no instante da execução.

## C6.S4 — L5 piloto limitado

OFF por default. Apenas capabilities explicitamente allowlisted por policy, com limites, idempotency, audit e kill switch.

## C6.S5 — Admin/kill switch

Controles de disponibilidade, autonomia, rollout e emergency stop sem conceder permissão de negócio.

## C6.S6 — Verify da plataforma

Evals completas de segurança, RBAC, workflows e generalização.

---

# C7 — Rollout final

## C7.S1 — Internal canary

Cohort pequeno, reads/navigation primeiro. Iframes entram primeiro como `PORTAL_ONLY`, depois evoluem por classe conforme evidence.

## C7.S2 — Métricas e incident review

Observar TCR, correction rate, safe execution, confirmation abandonment, errors, latency/cost e falhas do bridge.

## C7.S3 — Rollout por waves

Expandir por apps, perfis, níveis de autonomia e classes de integração de iframe. Sem big-bang.

## C7.S4 — Aceite

Somente declarar Copilot production-ready quando [`14-definition-of-done.md`](./14-definition-of-done.md), [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md) e os gates aplicáveis de [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md) estiverem satisfeitos no HEAD final.

## 6. Ordem inicial obrigatória para o Cursor

```text
C0.S0
→ C0.S1
→ C0.S2
→ C1.S1
```

O Cursor não deve iniciar pelo frontend visual ou pelo workflow final.

## 7. Trilha transversal — apps iframe

A integração de iframe é parte do plano principal, não backlog opcional quando houver apps desse tipo no escopo.

```text
C0: inventário + contrato + threats
C1: PORTAL_ONLY + handshake base
C2: CONTEXTUAL + INTERACTIVE piloto
C3: Business Actions via API/OpenAPI
C5: SDK/readiness/unknown iframe
C7: rollout por maturidade
```

Fonte canônica: [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).
