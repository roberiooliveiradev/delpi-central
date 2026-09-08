# Guia de desenvolvimento — minha-delpi-ai-api

**Status:** vigente  
**Público:** desenvolvedores backend/integrações do Minha DELPI AI

## 1. Regras antes de alterar código

Leia:

1. `documentos/instrucoes_oficiais_gpt_arquiteto_delpi_central.md`;
2. `.cursor/rules/development-standards-index.mdc`;
3. regras especializadas indicadas pelo índice;
4. arquitetura vigente em [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md);
5. para IA/evals: [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md).

Documentos datados de roadmap/changelog não substituem fontes canônicas atuais.

---

## 2. Estrutura de camadas

```text
app/
  domain/
    entities/
    ports/
    services/
    skills/
    prompt_policies/

  application/
    use_cases/
    services/
    dto/

  infrastructure/
    persistence/
    gateways/
    content/
    config/

  interfaces/http/
    routes/

  composition/

  content/pt-BR/
    assistant/
    labels/
    skills/
```

Regras:

- domain não importa infrastructure/interfaces;
- use case não instancia repository/gateway diretamente;
- composição/DI fica em `composition/`;
- send/stream/simulate reutilizam serviços base sempre que a responsabilidade é comum;
- texto PT-BR editável fica em conteúdo/config, não espalhado no Python.

---

## 3. Onde implementar

| Tipo de mudança | Lugar canônico |
|-----------------|----------------|
| Intenção/capability/clarify | domain/application services do pipeline base |
| RAG/contexto/memória | serviços canônicos de turno/RAG/memory |
| OpenAPI action | import/index + Action Catalog + planner/validator + executor genérico |
| Argument binding | schema OpenAPI/validator genérico |
| Policy/RBAC/confirmation | policy services canônicos |
| Apresentação | schema-driven API + renderPlan; MFE render-only |
| Texto/UX/vocabulário | `app/content/pt-BR/assistant/*.json` |
| LLM policy transversal | `domain/prompt_policies/*.md` |
| Endpoint HTTP | interface fina + use case + composition |
| Integração HTTP | gateway/adapter com timeout/resiliência/observabilidade |

Nunca criar solução por endpoint/provider quando a responsabilidade é transversal.

---

## 4. Actions OpenAPI

Fluxo vigente:

```text
OpenAPI
→ import/index
→ Action Catalog
→ agent binding + allowed actions
→ request decomposition
→ hybrid retrieval top-K
→ structured planner
→ OpenAPI argument validation
→ RBAC/policy/confirmation
→ ExecuteExternalActionUseCase
→ HTTP gateway
→ schema-driven presentation
```

Checklist completo: [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md).

### Proibido

- ensinar endpoint ao chat com marker/path rule técnico;
- criar intent por operation;
- selector por provider;
- duplicar path/operationId/params/schema em JSON do assistente;
- inventar URL/operationId via LLM;
- presenter obrigatório por endpoint.

### api-delpi

Quando uma operation nova entra na api-delpi:

1. implementar/validar contrato da própria api-delpi;
2. publicar OpenAPI completo;
3. `scripts/sync_api_delpi_openapi.py`;
4. verificar Action Catalog/index;
5. confirmar binding/allowed actions;
6. testar retrieval/planner/arguments;
7. validar outcome e apresentação;
8. executar R1–R11 relevantes.

Não estender `ExternalActionSelectionService` ou um catálogo paralelo para ensinar a rota nova.

---

## 5. Pedidos longos e multi-turn

Não reduzir frases longas à primeira intenção.

```text
pedido
→ subtarefas
→ dependências
→ capabilities/actions por subtarefa
→ execução segura
→ síntese completa
```

Follow-up reutiliza estado estruturado da conversa, não substring de path ou entidade inferida de forma global.

Mudanças nessas áreas devem cobrir `task_decomposition_recall`, `multi_request_completion_rate` e R6/R9.

---

## 6. Send, stream e simulate

O comportamento semântico deve permanecer equivalente entre superfícies.

Compartilhar serviços de:

- preparação do turno;
- routing/planning;
- tools;
- RAG;
- conclusão;
- metadata/presentation.

Stream adiciona transporte SSE/checkpoints, mas não uma inteligência paralela.

R7 do protocolo canônico mede essa paridade.

---

## 7. Conteúdo JSON

JSON do assistente serve para:

- copy/UX;
- vocabulário corporativo;
- thresholds/config transversal;
- policy declarativa não técnica;
- labels/presentation hints opcionais.

Não serve para recriar o OpenAPI.

Antes de criar nova chave, procurar loader/fonte canônica existente e evitar duplicidade.

---

## 8. Testes e eval-driven development

### Unitários/arquitetura

```bash
cd minha-delpi-ai-api
pytest tests/unit -q
python scripts/audit_clean_architecture.py
```

### Mudança de inteligência

Seguir [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md):

```text
BASELINE
→ bug + sibling + negative
→ fix canônico
→ CANDIDATE no mesmo corpus/config
→ R1–R11
→ outcome/safety/efficiency
→ live/surfaces
→ decisão
```

Mudança em motor de tools exige API externa desconhecida + teste metamórfico.

Não declarar sucesso porque um único prompt funciona ou porque um smoke isolado imprime PASS.

---

## 9. Composition root

Serviço/use case com dependências:

1. definir port/serviço na camada correta;
2. implementar adapter quando necessário;
3. registrar factory/composição;
4. handler HTTP resolve a factory;
5. testes substituem ports/gateways por doubles.

Nunca instanciar repository concreto em rota HTTP ou domínio.

---

## 10. HTTP externo

Seguir `http-integration-resilience.mdc` e `ai-external-tools-security.mdc`.

Obrigatório conforme o caso:

- connect/read/total timeout;
- limites de bytes/content type;
- retry apenas quando semanticamente seguro;
- idempotência para write retry;
- 429/Retry-After/backoff+jitter;
- redirects/egress conforme security policy;
- correlation/observability;
- redaction de secrets.

---

## 11. Segurança

- Keycloak/OIDC é a identidade canônica;
- JWT não carrega a lista completa de permissões;
- autorização efetiva respeita Core/RBAC e policy do agente/action;
- `allowed_action_ids` restringe candidates;
- write/admin/destructive exigem confirmação/policy aplicável;
- prompt/RAG/tool result não pode sobrescrever policy;
- nunca logar token, API key, password ou secret.

---

## 12. Migrations

- migrations são imutáveis depois de aplicadas em ambientes compartilhados;
- mudanças novas usam migration nova;
- dados operacionais de configuração de agente/provider não devem ser inseridos em migration de schema;
- seguir `migrations-immutable-checksum.mdc`.

---

## 13. Checklist de PR

- [ ] responsabilidade implementada na camada canônica;
- [ ] sem duplicação de contrato/fonte de verdade;
- [ ] send/stream/simulate alinhados quando aplicável;
- [ ] OpenAPI/Action Catalog usados como fonte técnica de actions;
- [ ] nenhuma regra nova por endpoint/provider no core;
- [ ] security/RBAC/confirmation preservados;
- [ ] timeout/resilience/observability em integração HTTP;
- [ ] tests relevantes verdes;
- [ ] mudança de IA passou protocolo R1–R11;
- [ ] outcome real validado quando aplicável;
- [ ] API externa desconhecida testada se motor de tools mudou;
- [ ] docs canônicas atualizadas, sem orientação concorrente;
- [ ] Architecture Enforcement verde.

## Referências vigentes

- [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
- [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md)
- [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md)
- [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)
- `.cursor/rules/development-standards-index.mdc`
