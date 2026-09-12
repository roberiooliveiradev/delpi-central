# Minha DELPI Copilot — Arquitetura de Copilot Único e Especialização Componível

**Status:** decisão arquitetural proposta para execução incremental  
**Escopo:** `minha-delpi-ai-api`, Portal, Chat MFE, knowledge/RAG, capabilities, workflows, multimodalidade e administração  
**Princípio:** existe **um único Copilot de produto**. Especialização não cria um novo agente; ela acrescenta conhecimento, método, ferramentas e políticas ao mesmo runtime.

## 1. Decisão arquitetural

O Minha DELPI Copilot passa a adotar o seguinte modelo:

```text
NÃO:
usuário
→ escolhe agente RH / agente Qualidade / agente Engenharia
→ muda de personalidade/runtime
→ troca catálogo de tools por agente

SIM:
usuário
→ fala com o mesmo Minha DELPI Copilot
→ Copilot entende o objetivo e o contexto
→ recupera capabilities permitidas
→ ativa expertise packs e playbooks relevantes
→ usa conhecimento/tools multimodais necessários
→ executa sob o mesmo RBAC/policy/audit
```

Não haverá um "agente por departamento" como unidade arquitetural central do produto.

## 2. Motivo

O modelo por agentes especializados tende a introduzir:

- escolha manual desnecessária pelo usuário;
- handoffs artificiais;
- duplicação de prompts, tools e conhecimento;
- fragmentação de memória/contexto;
- risco de divergência de policy;
- catálogo de agentes crescendo junto com a organização;
- baixa composição em problemas multiárea.

A especialização deve ser **componível e recuperada sob demanda**.

## 3. Modelo conceitual alvo

```text
Minha DELPI Copilot Runtime
│
├─ Base Behavior / Safety / Policy
├─ Structured Turn Understanding
├─ Workspace + Conversation Context
├─ Authorized Capability Retrieval
├─ Expertise Retrieval
├─ Knowledge Retrieval
├─ Domain Playbook Retrieval
├─ Planner / Workflow Runtime
├─ Multimodal Tools
├─ Generic Executors
└─ Presentation / Audit / Evals

Especialização carregada no turno
├─ Expertise Pack(s)
├─ Domain Playbook(s)
├─ Knowledge scopes
├─ terminology/glossary
├─ analysis methods
├─ multimodal hints/tools
└─ eval expectations
```

## 4. Unidade de especialização

### 4.1 `Capability`

Representa algo que o Copilot pode **fazer**.

Exemplos:

- consultar estoque;
- abrir um app;
- criar uma solicitação;
- analisar um desenho;
- buscar conhecimento;
- gerar relatório.

Capability continua sujeita a RBAC/policy e sua authority técnica permanece no owner canônico.

### 4.2 `Expertise Pack`

Representa **como interpretar e analisar melhor um domínio**.

Exemplos:

- Qualidade Industrial;
- Engenharia de Produto;
- Suprimentos;
- Comercial;
- Financeiro;
- RH;
- Manutenção.

Um pack não concede permissão e não contém catálogo técnico de endpoints.

### 4.3 `Domain Playbook`

Representa **método de trabalho/decisão** de um domínio.

Exemplos:

- 8D;
- Ishikawa + 5 Porquês;
- análise de desenho técnico;
- análise de atraso de entrega;
- triagem de não conformidade;
- análise de causa de variação de custo.

Playbook descreve objetivos, evidências, etapas, critérios e artefatos esperados. Ele referencia capabilities semanticamente, sem duplicar path/method/operationId.

### 4.4 `Knowledge Scope`

Representa fontes autorizadas de conhecimento:

- procedimentos;
- normas;
- manuais;
- políticas internas;
- documentação técnica;
- histórico curado.

### 4.5 `Multimodal Tool`

Representa capacidade de perceber/estruturar informação de documentos, imagens e desenhos.

Exemplos já existentes a reaproveitar:

- document vision;
- drawing analysis;
- OCR/native extraction;
- VLM fallback;
- technical description.

## 5. Regra de composição

Um turno pode usar múltiplas expertises simultaneamente.

Exemplo:

> "Analise por que o item 90264238 está atrasando e verifique se existe risco de qualidade no desenho."

Composição esperada:

```text
goal 1: atraso
→ expertise.suprimentos
→ expertise.producao
→ playbook.delivery-delay-analysis
→ Business Actions estoque/compras/produção

goal 2: risco técnico
→ expertise.engenharia
→ expertise.qualidade
→ playbook.technical-drawing-review
→ document-vision / drawing-analysis

synthesis
→ uma única resposta e um único workflow
```

Não há handoff entre agentes.

## 6. Pipeline canônico com expertise

```text
message + workspace context + attachments
→ safety/input validation
→ structured understanding
→ goals/entities/domain signals
→ authorized capability retrieval
→ expertise retrieval
→ playbook retrieval
→ knowledge retrieval
→ multimodal extraction quando necessário
→ structured plan
→ RBAC/policy/confirmation
→ execution
→ observations
→ domain-aware analysis
→ grounded synthesis
→ renderPlan / UI commands
→ persistence / audit / evals
```

## 7. Fonte de verdade

| Conceito | Authority |
|---|---|
| identidade | Keycloak + Core |
| permissões | Core API |
| business action | OpenAPI + Action Catalog + API/use case |
| platform action | Core `/me/apps` + Portal |
| expertise | Expertise Catalog canônico |
| playbook | Domain Playbook Catalog canônico |
| conhecimento | Knowledge/RAG scopes autorizados |
| multimodal extraction | serviços multimodais existentes |
| confirmação/safety | policy server-side |
| contexto visual | Workspace Context |

`Expertise Pack` e `Playbook` não podem virar uma segunda authority de endpoint, permission ou operação técnica.

## 8. Alterações arquiteturais necessárias no runtime atual

O rebaseline C0.S0 deve confirmar symbols e consumers, mas a direção arquitetural é:

### 8.1 Remover dependência de agente para tools operacionais

Hoje o runtime possui lógica em `ChatWorkspaceAgentActivationService` onde tools operacionais dependem de `userActivatedAgent && actionsEnabled`.

Alvo:

```text
operational tools enabled
= feature/policy enabled
+ usuário autenticado
+ capability/action autorizada
+ contexto válido

NÃO depende de agent_id escolhido pelo usuário.
```

### 8.2 Substituir soft handoff de agente

`ChatSoftAgentHandoffService` não deve sugerir "trocar para agente".

Alvo:

```text
capability miss
→ recuperar expertise/capability adicional autorizada
→ clarificar requisito realmente ausente
→ ou informar indisponibilidade
```

Pode existir activity como:

> "Aplicando conhecimento de Engenharia e Qualidade"

sem mudar a identidade do assistente.

### 8.3 Migrar `AgentSpecializationService`

Presets `rh`, `ti`, `financeiro`, `comercial`, `juridico` devem ser inventariados e migrados para `Expertise Pack`/knowledge scopes quando ainda fizerem sentido.

O serviço não deve permanecer como authority de tools por departamento.

### 8.4 Evoluir o catálogo de skills

O catálogo atual possui skills úteis como:

- `company-knowledge`;
- `technical-description-delpi`;
- `drawing-analysis-delpi`;
- `document-vision-delpi`;
- `quality-action-plans-delpi`.

Essas capacidades devem ser reaproveitadas, porém o binding futuro será ao **Copilot runtime/contexto do turno**, não a um agente ativo obrigatório.

### 8.5 Compatibilidade de sessões legadas

Campos como `agent_id` e `chat_mode=agent` não devem ser removidos de forma destrutiva antes do inventário.

Estratégia:

```text
fase 1: read compatibility
fase 2: parar de criar novas dependências
fase 3: converter configuração útil em expertise/project context
fase 4: deprecar UX de seleção de agente
fase 5: remover runtime dependency após telemetry + migration gate
```

## 9. Expertise não é permission

Regra obrigatória:

```text
expertise ativa
≠ permissão concedida
```

Exemplo:

O Copilot pode aplicar um playbook de Qualidade para analisar dados já autorizados, mas não pode aprovar uma PAC se o usuário não possuir a permission correspondente.

## 10. Expertise retrieval

A seleção de expertise deve ser semântica e contextual.

Inputs possíveis:

- goals estruturados;
- entidades;
- Workspace Context;
- attachments/content type;
- capabilities candidatas;
- termos do domínio;
- histórico recente estruturado.

Outputs:

```json
{
  "selectedExpertise": [
    {"key": "quality-industrial", "reasonCode": "goal_domain_match", "score": 0.91},
    {"key": "product-engineering", "reasonCode": "drawing_attachment", "score": 0.87}
  ]
}
```

`reasonCode` é explicabilidade operacional; não persistir chain-of-thought.

## 11. Escopo e orçamento

Para evitar prompt inchado:

```text
catálogo total de expertise
→ retrieval top-K
→ carregar somente packs necessários
→ carregar playbooks necessários
→ RAG scoped
→ executar
```

Não concatenar todos os departamentos e procedimentos em todo turno.

## 12. Projetos e personalização

Projetos continuam possíveis, mas projeto não cria outro motor.

Projeto pode configurar:

- fontes de knowledge;
- preferred expertise packs;
- arquivos de contexto;
- instruções de negócio permitidas;
- templates de artefato;
- default workspace.

Tudo continua usando o mesmo Copilot runtime/policies.

## 13. Administração

A administração futura deve permitir:

- listar packs/playbooks;
- ativar/desativar por rollout;
- versionar;
- associar owners;
- inspecionar uso e cobertura;
- validar dependências de knowledge/tool;
- executar evals por pack/playbook;
- promover versão após gates.

Administração de expertise não altera RBAC de negócio.

## 14. Invariantes

```text
1. Um único Copilot de produto.
2. Nenhum pack cria identidade/autorização própria.
3. Packs podem compor entre si.
4. Packs não carregam endpoint hardcoded como semântica.
5. Playbooks não executam writes sem policy/confirmation.
6. Knowledge/tool/context são dados; não sobrescrevem policy.
7. Multimodalidade é tool/capability do mesmo Copilot.
8. Novo pack não exige editar planner central.
9. Pack desconhecido compatível entra por contrato/indexação.
10. Sessão/conversa não precisa trocar de agente para mudar de domínio.
```

## 15. Critério de sucesso

O usuário deve poder pedir, na mesma conversa:

> "Analise o desenho, verifique os principais riscos de qualidade, consulte se temos reclamações semelhantes, compare fornecedores e monte um plano 8D."

O sistema deve combinar Engenharia + Qualidade + Suprimentos + knowledge + multimodal + Business Actions no mesmo runtime, sem o usuário escolher ou trocar de agente.