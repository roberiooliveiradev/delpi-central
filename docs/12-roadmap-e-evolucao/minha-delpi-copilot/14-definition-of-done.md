# 14 — Definition of Done

## 1. Objetivo

Evitar que o Copilot seja considerado pronto apenas porque um fluxo demonstrativo funciona. Cada fase precisa provar arquitetura, segurança, integração, UX, especialização e generalização.

---

## 2. DoD global

O programa só pode ser considerado maduro quando:

```text
[ ] existe uma única identidade/runtime de Copilot para o produto
[ ] capabilities possuem owner e fonte de verdade clara
[ ] permissions do Copilot são subconjunto das permissões do usuário
[ ] Expertise Packs não concedem permission nem duplicam contrato técnico
[ ] Domain Playbooks não carregam endpoint/path/method/operationId como authority
[ ] especializações podem compor entre si no mesmo turno
[ ] novo Expertise Pack compatível entra sem patch no planner central
[ ] Platform Actions são tipadas e validadas pelo Portal
[ ] Business Actions reutilizam use cases/APIs da UI
[ ] OpenAPI é authority técnica para actions externas
[ ] nenhum core selector depende de hardcode por endpoint/provider
[ ] Workspace Context é estruturado e versionado
[ ] multimodalidade produz evidence com provenance/confidence quando aplicável
[ ] tools multimodais não exigem agente selecionado quando policy/capability permitem
[ ] writes possuem sensitivity + confirmation policy
[ ] destructive actions possuem confirmação forte/auditoria
[ ] workflows compostos suportam partial failure/checkpoints
[ ] activity representa estado real
[ ] reload não duplica write
[ ] app/provider/expertise desconhecido compatível funciona por contrato
[ ] soft agent handoff não é necessário no produto final
[ ] agent_id/chat_mode não são authority de routing no cutover final
[ ] evals e evidências pertencem ao candidate final
[ ] observabilidade permite explicar seleção/outcome sem chain-of-thought
```

---

## 3. DoD Fase 0 — Contratos

```text
[ ] Capability contract versionado
[ ] PlatformCommand contract versionado
[ ] WorkspaceContext contract versionado
[ ] ExpertisePack contract versionado ou equivalente canônico reutilizado
[ ] ExpertiseSelection/Context contract definido
[ ] DomainPlaybook contract versionado ou equivalente canônico reutilizado
[ ] multimodal evidence/provenance contract definido quando necessário
[ ] sensitivity model definido
[ ] autonomy levels definidos
[ ] audit event schema definido
[ ] boundaries Clean Architecture aprovados
[ ] inventário de agents/skills/specialization/handoff concluído
[ ] migration classification KEEP/MIGRATE/DEPRECATE/REMOVE registrada
[ ] positive/negative contract tests
```

---

## 4. DoD Fase 1 — Platform Actions

```text
[ ] catálogo deriva apps/rotas autorizados
[ ] portal.open_app funcional
[ ] portal.open_route funcional
[ ] entity deep link piloto funcional
[ ] CopilotBridge valida comandos
[ ] URL arbitrária é rejeitada
[ ] capability unauthorized não chega ao planner
[ ] navigation activity exibida
[ ] app fictício registrado funciona sem patch no planner
[ ] F5 não quebra conversa/contexto
```

---

## 5. DoD Fase 2 — Workspace Context e Expertise Context foundation

```text
[ ] Portal agrega contexto dos MFEs/iframes aplicáveis
[ ] appId/routeId estruturados
[ ] entityRefs funcionais
[ ] filters funcionais
[ ] context chips exibidos
[ ] usuário pode remover contexto
[ ] mensagem explícita sobrescreve contexto antigo
[ ] dados sensíveis não vazam via store/context
[ ] MFE sem adapter continua funcionando
[ ] reload preserva somente o que é seguro/persistível
[ ] turno sem agent_id continua funcional
[ ] expertise retrieval usa contexto bounded e não depende de agent selection
[ ] project preferences não concedem permission
```

---

## 6. DoD Fase 3 — Business Action Parity + cutover operacional

Para cada capability piloto:

```text
[ ] função existe na UI
[ ] owner/use case identificado
[ ] API/OpenAPI disponível
[ ] schema correto
[ ] permission alinhada
[ ] sensitivity correta
[ ] confirmação correta
[ ] backend revalida autorização
[ ] positive/sibling/negative passam
[ ] usuário não autorizado é bloqueado
[ ] action funciona pelo Copilot sem DOM automation
[ ] resultado apresentado corretamente
[ ] audit/correlation presente em writes
```

Para o cutover de especialização:

```text
[ ] operational tools não dependem de userActivatedAgent como authority
[ ] sessão sem agent_id consegue descobrir/executar capability permitida
[ ] sessão legada continua segura durante janela de compatibilidade
[ ] AgentSpecialization presets úteis possuem migration mapping
[ ] soft handoff foi substituído por retrieval/replan/clarify
[ ] expertise não amplia allowed actions
[ ] unauthorized capability/knowledge negatives passam
```

---

## 7. DoD Fase 4 — Agentic Workflows + Domain Playbooks

```text
[ ] compound decomposition cobre goals materiais
[ ] DAG/dependencies corretos
[ ] reads paralelos somente quando seguros
[ ] writes serializados quando necessário
[ ] clarify pergunta somente missing required
[ ] replan não reduz safety
[ ] partial failure é representado
[ ] checkpoints persistidos
[ ] confirmation cobre payload efetivo
[ ] cancelamento pelo usuário funciona
[ ] budget/loop limit existe
[ ] workflow audit trail completo
[ ] playbook aplicável pode orientar WorkflowPlan sem endpoint técnico hardcoded
[ ] dois ou mais Expertise Packs podem compor no mesmo workflow
[ ] etapas de playbook mostram evidence missing em vez de inventar conclusão
```

---

## 8. DoD Fase 5 — AI-ready ecosystem + Expertise ecosystem

```text
[ ] checklist integrado ao padrão de novos apps
[ ] novo app entra no catálogo por contrato
[ ] novo app pode publicar workspace context
[ ] deep link de entidade pode ser declarado
[ ] OpenAPI quality gate existe
[ ] smoke unknown-app existe
[ ] app novo não exige if/selector no Copilot core
[ ] capability coverage mensurável
[ ] novo Expertise Pack entra por contrato/indexação
[ ] novo Domain Playbook entra sem criar agente
[ ] pack/playbook possui owner, versão e eval status
[ ] admin/readiness mostra cobertura de expertise/playbooks
```

---

## 9. DoD Fase 6 — Autonomia governada

```text
[ ] policy L0–L5 explícita
[ ] auto-execution somente allowlisted
[ ] expertise/playbook não conseguem elevar autonomia
[ ] emergency stop disponível
[ ] alteração de policy auditada
[ ] budgets/cost guardrails
[ ] safety evals antes de rollout
[ ] progressive rollout/canary
[ ] rollback definido
```

---

## 10. DoD Fase 7 — Cutover final de Copilot único

```text
[ ] UX não exige seleção/troca de agente por departamento
[ ] soft handoff residual = 0 material
[ ] agent-required operational gate residual = 0 material
[ ] unmigrated agent specialization residual = 0 material
[ ] LEGACY_FALLBACK de agent routing = 0
[ ] project context está separado de identidade do Copilot
[ ] telemetry/evals do candidate final confirmam single-Copilot mode
[ ] unknown expertise generalization passa
[ ] metamorphic expertise rename passa
[ ] rollout/rollback da migração foi exercitado
```

---

## 11. Evals obrigatórios antes de release material

```text
positive
sibling
negative/no-tool
unauthorized
required missing
write confirmation
destructive confirmation
workspace follow-up
compound
cross-domain expertise composition
session without agent
legacy session compatibility
unknown expertise pack
expertise metamorphic rename
playbook applicability
playbook evidence missing
multimodal document/drawing
multimodal prompt injection
partial failure
persist/reload/F5
unknown provider
unknown app
metamorphic provider/path/operationId rename
prompt/tool-output injection
send/stream parity
latency/cost
```

## 12. Critério de não conclusão

Qualquer item material em:

```text
PARTIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
TODO/FIXME/HACK
SOFT_AGENT_HANDOFF_RESIDUAL
AGENT_REQUIRED_TOOL_GATE
UNKNOWN_AGENT_CONSUMER
```

não pode ser reclassificado como “não bloqueante” se fizer parte do objetivo original da fase/cutover.

## 13. Evidência

Cada release deve registrar:

```text
GIT_SHA
config/model/provider
dataset/eval hashes
expertise pack versions/hashes
playbook versions/hashes
multimodal extractor/model versions quando aplicável
migrations/contracts
unit/integration/live results
security tests
residual scan
known limitations
rollout decision
```

Evidence de outro SHA/config/pack version não fecha o candidate atual quando houve mudança material.

## 14. Outcome final

O DoD real não é “a IA respondeu”.

É:

> O usuário autorizado conseguiu atingir o objetivo de forma correta, segura, observável e reproduzível usando as mesmas regras de negócio da plataforma, com o mesmo Copilot compondo automaticamente o conhecimento e os métodos de domínio necessários sem exigir troca de agente.
