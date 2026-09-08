# Checklist — nova API/action exposta ao chat

**Status:** vigente  
**Público:** `api-delpi`, `minha-delpi-ai-api`, integradores de providers OpenAPI  
**Regras Cursor:** `new-api-route-checklist.mdc`, `openapi-first-universal-tool-routing.mdc`  
**Evals:** [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)

## Princípio

Uma operation nova fica disponível ao agente por meio do próprio contrato OpenAPI e do Action Catalog.

```text
Provider/API
→ OpenAPI
→ import/index
→ Action Catalog
→ agent binding + allowed actions
→ retrieval top-K
→ structured planner
→ OpenAPI argument validator
→ RBAC/policy/confirmation
→ generic HTTP executor
→ schema-driven presentation
→ eval R1–R11
```

Não existe etapa de cadastro técnico paralelo da rota no chat.

---

## 1. Provider/API

O contrato deve declarar adequadamente:

- `operationId` estável e único;
- método e path;
- `summary` e `description` semanticamente úteis;
- tags quando úteis;
- path/query/header parameters com description, required e schema;
- request body/schema;
- response schema/descriptions;
- exemplos quando agregarem informação;
- autenticação/configuração do provider;
- sensitivity/policy quando aplicável.

### api-delpi

A `api-delpi` mantém seus contratos internos adicionais:

- `api_delpi_success(..., operation_id=...)`;
- metadata `entity`/`shape` quando aplicável;
- RBAC canônico;
- `openapi_agent_metadata` nas rotas chat-critical;
- padrões TOTVS e testes próprios.

Essas extensões enriquecem a experiência DELPI, mas **não são pré-requisito de plugabilidade para APIs externas**.

---

## 2. Importação e Action Catalog

Depois do deploy/publicação do OpenAPI:

1. importar/reimportar provider;
2. resolver schemas/refs aceitos pela policy de segurança;
3. persistir/atualizar Action Catalog;
4. gerar documento semântico/index;
5. vincular provider/actions ao agente;
6. verificar `allowed_action_ids` efetivos.

O documento semântico deve aproveitar o contrato real:

```text
operationId
summary
description
tags
method/path como metadata técnica
parameters + descriptions + schemas
request body
response schema
examples
```

Não copiar esses fatos para JSON manual de endpoints.

---

## 3. Seleção

A seleção deve funcionar por significado e contrato:

```text
mensagem/subtarefa
→ candidates autorizadas
→ hybrid retrieval
→ top-K
→ planner estruturado
```

Critérios:

- específica vence genérica quando o pedido exige a capability específica;
- no-tool vence quando tool não é necessária;
- provider prefix não é critério de score;
- planner não pode escolher action fora do top-K/autorizadas;
- path e operationId são identificadores da action selecionada, não heurística de intenção hardcoded.

---

## 4. Argumentos

O binding é OpenAPI-first.

Validar:

- `pathParams`;
- query params;
- headers permitidos;
- request body;
- required;
- type;
- enum;
- format;
- additional properties conforme schema;
- coerência de datas/identificadores.

Argumento obrigatório ausente:

```text
schema diz required
+ contexto não contém valor confiável
→ pending/clarify específico
```

Nunca inventar valor para evitar pergunta ao usuário.

---

## 5. Segurança e governança

Antes da execução:

- provider habilitado;
- action habilitada;
- action em `allowed_action_ids`;
- autorização do usuário preservada;
- sensitivity permitida;
- write/admin/destructive com confirmation quando exigido;
- URL final derivada exclusivamente do provider/action autorizados;
- nenhuma instrução de tool/RAG pode alterar policy;
- secrets não entram em prompt/log/resposta.

Seguir `ai-external-tools-security.mdc` e `http-integration-resilience.mdc`.

---

## 6. Execução

Usar o caminho genérico:

```text
ExecuteExternalActionUseCase
→ execution policy
→ HTTP gateway/provider auth
→ normalized result
```

Não criar client/selector/executor específico para cada API plugada, salvo adapter realmente necessário por protocolo diferente de HTTP/OpenAPI e explicitamente arquitetado.

---

## 7. Apresentação

Fallback obrigatório:

```text
responseSchema + payload runtime + metadata
→ ChatSchemaDrivenPresentationService
→ presentationDecision/renderPlan
→ MFE render-only
```

Perfis, labels e enriquecimentos especializados são opcionais.

Uma API externa sem `x-delpi` ou perfil dedicado ainda deve gerar resposta utilizável.

---

## 8. Pedidos compostos e multi-turn

A action participa do pipeline base de decomposição/contexto.

Exemplo:

```text
consulte estoque, última compra e fornecedores; depois escreva um resumo
```

Deve virar subtarefas, dependências e plano de execução, não uma intent única.

Follow-up:

```text
e no mês passado?
agora deste outro produto
mostre em tabela
```

reutiliza estado estruturado da conversa/resultado, não substring do último endpoint.

---

## 9. Testes obrigatórios

Seguir R1–R11 do protocolo canônico.

Para uma nova action:

- import/index;
- discovery/retrieval;
- sibling semelhante;
- negative/no-tool quando aplicável;
- argumentos presentes;
- argumento required ausente;
- execution/policy;
- outcome/task success;
- apresentação;
- performance/efficiency;
- follow-up quando aplicável.

Para mudança do motor de tools:

- API externa fictícia desconhecida;
- teste metamórfico com paths/operationIds diferentes e semântica equivalente;
- multi-provider;
- pedido composto;
- prompt/tool-output injection;
- action não autorizada;
- write sem confirmação.

---

## 10. Gates

Executar os testes do provider/API e os gates do repositório, incluindo:

```bash
python scripts/ci/audit_architecture_phase3.py --check --base <base>
python scripts/audit_clean_architecture.py
pytest tests/unit -q
```

Além dos testes específicos de OpenAPI/import/planner/validator/presentation alterados.

O CI deve bloquear novo:

```text
if path/provider/operationId no motor genérico
catálogo técnico paralelo por endpoint
retry inseguro de escrita
HTTP sem timeout
secret em log/config
```

---

## 11. Checklist de PR

- [ ] OpenAPI completo e semanticamente útil.
- [ ] Import/index atualiza Action Catalog.
- [ ] Agent binding/allowed actions corretos.
- [ ] Retrieval encontra a action por linguagem natural.
- [ ] Actions próximas são distinguidas corretamente.
- [ ] Argumentos validados contra schema.
- [ ] Missing required gera clarify.
- [ ] RBAC/policy/confirmation preservados.
- [ ] Executor genérico usado.
- [ ] Fallback schema-driven funciona sem extensão proprietária obrigatória.
- [ ] R1–R11 required estão PASS.
- [ ] Outcome real validado quando há oracle.
- [ ] API externa desconhecida passa se o motor foi alterado.
- [ ] Compound/multi-turn avaliados quando aplicável.
- [ ] Architecture Enforcement verde.

## Anti-padrões

- cadastrar rota manualmente no chat para torná-la descobrível;
- marker por path/operationId;
- parameter strategy por endpoint que replica o OpenAPI;
- selector/service específico para provider;
- presenter obrigatório por rota;
- regex/boost para frase de fixture;
- validar apenas path/tool e ignorar outcome;
- alterar expected do teste para esconder regressão.
