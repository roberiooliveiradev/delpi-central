# 14 — Definition of Done

## 1. Objetivo

Evitar que o Copilot seja considerado pronto apenas porque um fluxo demonstrativo funciona. Cada fase precisa provar arquitetura, segurança, integração, UX e generalização.

---

## 2. DoD global

O programa só pode ser considerado maduro quando:

```text
[ ] capabilities possuem owner e fonte de verdade clara
[ ] permissions do Copilot são subconjunto das permissões do usuário
[ ] Platform Actions são tipadas e validadas pelo Portal
[ ] Business Actions reutilizam use cases/APIs da UI
[ ] OpenAPI é authority técnica para actions externas
[ ] nenhum core selector depende de hardcode por endpoint/provider
[ ] Workspace Context é estruturado e versionado
[ ] writes possuem sensitivity + confirmation policy
[ ] destructive actions possuem confirmação forte/auditoria
[ ] workflows compostos suportam partial failure/checkpoints
[ ] activity representa estado real
[ ] reload não duplica write
[ ] app/provider desconhecido funciona por contrato
[ ] evals e evidências pertencem ao candidate final
[ ] observabilidade permite explicar seleção/outcome sem chain-of-thought
```

---

## 3. DoD Fase 0 — Contratos

```text
[ ] Capability contract versionado
[ ] PlatformCommand contract versionado
[ ] WorkspaceContext contract versionado
[ ] sensitivity model definido
[ ] autonomy levels definidos
[ ] audit event schema definido
[ ] boundaries Clean Architecture aprovados
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

## 5. DoD Fase 2 — Workspace Context

```text
[ ] Portal agrega contexto dos MFEs
[ ] appId/routeId estruturados
[ ] entityRefs funcionais
[ ] filters funcionais
[ ] context chips exibidos
[ ] usuário pode remover contexto
[ ] mensagem explícita sobrescreve contexto antigo
[ ] dados sensíveis não vazam via store/context
[ ] MFE sem adapter continua funcionando
[ ] reload preserva somente o que é seguro/persistível
```

---

## 6. DoD Fase 3 — Business Action Parity

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

---

## 7. DoD Fase 4 — Agentic Workflows

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
```

---

## 8. DoD Fase 5 — AI-ready ecosystem

```text
[ ] checklist integrado ao padrão de novos apps
[ ] novo app entra no catálogo por contrato
[ ] novo app pode publicar workspace context
[ ] deep link de entidade pode ser declarado
[ ] OpenAPI quality gate existe
[ ] smoke unknown-app existe
[ ] app novo não exige if/selector no Copilot core
[ ] capability coverage mensurável
```

---

## 9. DoD Fase 6 — Autonomia governada

```text
[ ] policy L0–L5 explícita
[ ] auto-execution somente allowlisted
[ ] emergency stop disponível
[ ] alteração de policy auditada
[ ] budgets/cost guardrails
[ ] safety evals antes de rollout
[ ] progressive rollout/canary
[ ] rollback definido
```

---

## 10. Evals obrigatórios antes de release material

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
partial failure
persist/reload/F5
unknown provider
unknown app
metamorphic rename
prompt/tool-output injection
send/stream parity
latency/cost
```

## 11. Critério de não conclusão

Qualquer item material em:

```text
PARTIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
TODO/FIXME/HACK
```

não pode ser reclassificado como “não bloqueante” se fizer parte do objetivo original da fase.

## 12. Evidência

Cada release deve registrar:

```text
GIT_SHA
config/model/provider
dataset/eval hashes
migrations/contracts
unit/integration/live results
security tests
residual scan
known limitations
rollout decision
```

Evidence de outro SHA não fecha o candidate atual quando houve mudança material.

## 13. Outcome final

O DoD real não é “a IA respondeu”.

É:

> O usuário autorizado conseguiu atingir o objetivo de forma correta, segura, observável e reproduzível usando as mesmas regras de negócio da plataforma.
