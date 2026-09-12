# Minha DELPI Copilot — Protocolo de Execução para o Cursor

**Status:** obrigatório para execução do plano  
**Plano:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar execução fora de ordem, “implementação por exemplo”, contratos inventados, fechamento prematuro e criação de arquitetura paralela.

## 2. Antes de qualquer etapa

Ler, nesta ordem:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`;
2. `.cursor/rules/development-standards-index.mdc`;
3. regras específicas aplicáveis de plan/execution/test/security/OpenAPI/AI;
4. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`;
5. `16-execution-master-plan.md`;
6. `17-component-and-contract-map.md`;
7. `18-app-onboarding-matrix.md`;
8. documento específico da fase;
9. `20-testing-and-acceptance-matrix.md`;
10. `evidence/execution-ledger.md`.

Depois:

```text
git status
git rev-parse HEAD
```

Registrar `HEAD_BEFORE`.

## 3. C0.S0 é obrigatório

Não iniciar CopilotBridge, types, UI ou API antes de C0.S0 concluir o inventário real.

C0.S0 deve provar, com arquivo/símbolo/contrato:

- como `/me/apps` é produzido e consumido;
- shape real de app/route;
- Router/AppHost atuais;
- contratos send/stream do Chat;
- Action Catalog/planner/executor atuais;
- confirmation/policy atuais;
- persistence/turn metadata;
- manifests e APIs dos apps candidatos;
- convenções de shared packages/types;
- deep-link/entity patterns existentes.

Quando não houver prova, registrar `NOT_PROVEN`/`TO_INVENTORY`.

## 4. Unidade de execução

Executar somente uma subetapa `C*.S*` por vez.

Pipeline:

```text
SELECT STEP
→ REVALIDATE
→ READY_TO_EXECUTE
→ BASELINE
→ IMPLEMENT MINIMAL CORRECT DIFF
→ WIRE PRODUCER/CONSUMER
→ UNIT/CONTRACT
→ INTEGRATION
→ POSITIVE
→ SIBLING
→ NEGATIVE
→ SECURITY/RBAC
→ GENERALIZATION quando aplicável
→ ADVERSARIAL DIFF REVIEW
→ SEMANTIC RESIDUAL SEARCH
→ POSTCONDITIONS
→ COMPLETE_GATE
→ DOCS + LEDGER
→ UNLOCK NEXT
```

## 5. READY_TO_EXECUTE

Só fica `READY_TO_EXECUTE` se:

- owners e consumers da etapa estão identificados;
- contrato alvo está definido;
- dependências anteriores passaram;
- não existe working-tree conflict não entendido;
- não existe decisão de produto necessária e ausente;
- baseline/tests estão definidos;
- impacto de segurança está classificado.

Caso contrário: `BLOCKED_WITH_EVIDENCE`.

## 6. Menor diff correto

Não interpretar “menor diff” como workaround.

Correto:

```text
alterar owner canônico
+ wiring real
+ testes
+ remover substituto quando cutover estiver provado
```

Incorreto:

```text
copiar lógica para outro service
criar JSON auxiliar por endpoint
hardcodar app piloto
bypassar policy para smoke
```

## 7. Proibições específicas do Copilot

- não criar lista manual central de todos os apps para navegação;
- não criar capability business com path/method/operationId manual;
- não criar selector por app/provider/endpoint;
- não criar UI automation quando existe API/use case;
- não criar URL arbitrária produzida pelo modelo;
- não confiar no WorkspaceContext como autorização;
- não persistir chain-of-thought;
- não criar agente por departamento como novo motor;
- não criar novo HTTP executor para workflows;
- não duplicar o Action Catalog dentro do Copilot;
- não liberar write/destructive porque a UI confirmou sem revalidar backend policy;
- não declarar Onda J/tool pipeline como resolvida dentro deste plano.

## 8. Regras de evidence

Nunca escrever “PASS” sem evidência da execução correspondente.

Por teste relevante registrar:

```text
command/test
result
HEAD
config/hash quando aplicável
artifact/evidence path
```

Não reaproveitar evidence de SHA anterior após mudança material.

## 9. Residual search

Após cutover/cleanup, procurar o conceito em:

- runtime Python/TS/TSX;
- JSON/YAML/config;
- prompts/content;
- fixtures/generators;
- tests/smokes;
- scripts/CI;
- caches/materializers;
- manifests;
- docs.

Exemplos de residual proibido:

```text
appId → hardcoded URL
operationId list → business capability catalog manual
path substring → semantic selection
write endpoint → hardcoded confirmation bypass
MFE-specific command no core generic
```

## 10. Adversarial review

Antes do COMPLETE_GATE, responder:

1. Isso funciona com outro app sem editar o core?
2. Isso funciona com provider OpenAPI nunca visto quando aplicável?
3. Renomear provider/path/operationId altera semântica indevidamente?
4. Um usuário sem permissão consegue forçar a action pelo payload?
5. Um resultado/tool/context hostil consegue alterar policy?
6. Reload/retry pode duplicar write?
7. Existe uma segunda fonte de verdade criada pelo diff?
8. O fallback remanescente está dentro do objetivo final? Se sim, a etapa não pode fechar.

## 11. COMPLETE_GATE

Para fechar uma subetapa, todos os requisitos materiais precisam estar comprovados.

Estados bloqueantes:

```text
PARTIAL
ATENDIDO_PARCIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK material
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY material
TEST_NOT_RUN
STALE_EVIDENCE
```

## 12. Formato de reporte por etapa

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
REQUIREMENTS:
DEPENDENCIES:
FILES_CHANGED:
CANONICAL_OWNERS:
PRODUCERS_CONSUMERS:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
SECURITY_RBAC:
GENERALIZATION:
RESIDUAL_SEARCH:
ADVERSARIAL_REVIEW:
DRIFTS:
POSTCONDITIONS:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 13. Commit/push

Seguir `.cursor/rules/test-and-commit.mdc` e autorização atual do usuário.

Não misturar refactors não relacionados à subetapa.

Preservar mudanças não relacionadas já existentes no working tree.

## 14. Quando parar

Parar somente por:

- secret/dado obrigatório indisponível;
- risco destrutivo real em produção;
- conflito de working tree impossível de resolver com segurança;
- decisão de produto realmente não definida;
- dependência externa indisponível impedindo evidence necessária.

Registrar `BLOCKED_WITH_EVIDENCE`, não `PASS`.

## 15. Continuidade

Se a etapa fechou `COMPLETE_GATE=PASS`, continuar para a próxima desbloqueada sem pedir confirmação intermediária quando o usuário já autorizou a execução do plano.

Primeira etapa: **C0.S0**.