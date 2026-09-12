# Minha DELPI Copilot — Gates de Teste da Inteligência Operacional

**Status:** extensão da matriz `20-testing-and-acceptance-matrix.md`.

## 1. Evidence/Provenance

Obrigatório:

- FACT possui sourceRef válido;
- CALCULATION aponta inputs;
- HYPOTHESIS permanece rotulada;
- freshness stale gera limitação;
- fonte conflitante não vira conclusão silenciosa;
- evidence revogada por RBAC não continua acessível;
- finding multimodal aponta página/região quando aplicável;
- artifact não inventa source/evidence inexistente.

## 2. Business Graph

- traversal autorizado;
- relation inexistente;
- relation inferred vs authoritative;
- segundo entity type sem patch no planner;
- nó relacionado sem permission não vaza dado;
- source owner indisponível;
- relação stale/superseded;
- cycle/depth budget.

## 3. Copilot Task

- criação a partir de workflow;
- progress real;
- F5/reload;
- restart de worker;
- cancel;
- partial failure;
- sem duplicate write;
- evidence/result refs persistidos corretamente.

## 4. Case

- lifecycle completo;
- evidence accepted/contested/missing/superseded;
- reabertura auditada;
- acesso por membro autorizado;
- usuário removido perde acesso;
- entity source permission continua necessária;
- Case fechado promove Experience apenas via processo explícito.

## 5. Interaction Room

- participantes;
- mensagens e arquivos;
- resumo contextual;
- injection em mensagem/arquivo não altera policy;
- usuário sem acesso à entidade não recebe dado via resumo;
- Copilot usa Case context correto;
- room/event correlation.

## 6. Inbox

- pending approval aparece;
- item resolvido muda de estado;
- dedupe;
- link Task/Case válido;
- item de entidade revogada é sanitizado/indisponível;
- ordering/severity;
- leitura não dispara write.

## 7. Watch

Positive:
- evento válido casa condição;
- ADVISE gera alerta grounded;
- event retoma workflow correto.

Negative:
- duplicate event;
- evento de subject errado;
- permission revogada;
- condition inválida;
- event payload hostil;
- watch expirado/desabilitado;
- ACT sem autonomy policy deve ser bloqueado.

## 8. Durable Workflow

- wait_user/resume;
- wait_approval approved/rejected/expired;
- wait_event;
- concurrent resume;
- duplicate event;
- crash após write antes de checkpoint;
- ambiguous timeout;
- permission/policy change durante wait;
- cancellation;
- budget exhaustion;
- no infinite loop;
- version incompatibility.

## 9. Decision Gates

- risk baixo sem gate quando policy permitir;
- confirm simples;
- review+confirm com impact preview;
- approval workflow;
- arguments hash mudou;
- evidence mudou materialmente;
- approval expired;
- approver sem permission;
- backend revalidation após approval.

## 10. Simulation

- baseline correto;
- premissas explícitas;
- cálculo reproduzível;
- unsupported scenario não vira número inventado;
- sensitive input respeita RBAC;
- simulation não persiste alteração;
- Apply é nova Business Action com policy/gate;
- baseline stale invalida resultado quando aplicável.

## 11. Organizational Knowledge

- source/version/owner presentes;
- decision record sem CoT;
- experience promotion exige review;
- PII não é promovido indevidamente;
- deprecated pattern não é selecionado como atual;
- solution pattern funciona em sibling case;
- feedback não altera runtime automaticamente.

## 12. Expertise Studio

- draft não aparece em produção;
- published version rastreável;
- rollback;
- schema validation;
- eval regression bloqueia publish;
- secret detection;
- endpoint technical catalog em pack/playbook é rejeitado quando viola arquitetura;
- RBAC administrativo.

## 13. Model Router

- FAST/STANDARD/DEEP selection conforme policy;
- multimodal requirement;
- provider unavailable;
- fallback compatível;
- provider proibido por data policy rejeitado;
- latency/cost budget;
- structured output validity;
- candidate config comparado ao baseline.

## 14. Cross-feature anchor scenario

Cenário obrigatório de integração madura:

```text
reclamação de cliente
→ Case
→ Business Graph identifica produto/OP/material/fornecedor
→ desenho analisado multimodalmente
→ evidence board
→ quality + engineering expertise
→ 8D playbook
→ Task/workflow
→ falta nova revisão → wait_event/Watch
→ Inbox avisa usuário quando revisão chega
→ reanálise
→ Decision Gate para criar/alterar plano de ação
→ execução via Business Action
→ outcome/evidence/audit
```

O fluxo deve sobreviver a reload e não exigir troca manual de agente.

## 15. Release blockers adicionais

```text
claim material sem provenance quando fonte deveria existir
Business Graph bypassando RBAC
Case/Room vazando dados
Watch ACT sem policy
workflow resume duplicando write
approval antiga autorizando payload novo
simulation apresentada como fato
experience knowledge auto-publicado
model routing enviando dado a provider incompatível
```

Qualquer bloqueador material impede rollout da feature correspondente.