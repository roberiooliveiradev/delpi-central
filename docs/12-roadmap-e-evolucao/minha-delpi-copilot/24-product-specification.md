# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação de produto alvo  
**Escopo:** experiência do usuário, funcionalidades, módulos, administração, integrações e critérios funcionais.

## 1. Definição

O Minha DELPI Copilot é uma camada operacional inteligente transversal da plataforma. Ele deve permitir ao usuário trabalhar por linguagem natural sem perder as interfaces visuais existentes.

O Copilot não substitui os Portais; ele os conecta, explica, opera e acelera.

## 2. Superfícies de uso

### 2.1 Painel lateral global

Disponível no Portal Shell, persistente entre apps quando permitido.

Funções:

- conversar;
- receber contexto do app atual;
- mostrar plano operacional;
- acompanhar actions;
- pedir confirmação;
- mostrar resultados;
- oferecer “abrir no app”;
- continuar follow-up sem perder entidades/filtros relevantes.

### 2.2 Página completa do Copilot

Indicada para:

- análises longas;
- workflows extensos;
- comparação de dados;
- artefatos;
- histórico;
- agentes/projetos especializados quando aplicável.

### 2.3 Entrada contextual em MFE

Apps podem oferecer “Perguntar ao Copilot” sem criar IA própria.

O app publica `WorkspaceContext`; o Shell abre/foca a mesma experiência central.

### 2.4 Ações embutidas em respostas

Exemplos:

- Abrir app;
- Abrir registro;
- Aplicar filtro;
- Ver detalhes;
- Preparar alteração;
- Confirmar operação;
- Baixar/abrir artefato, quando suportado.

## 3. Módulo Conversacional

Funcionalidades:

- linguagem natural PT-BR;
- pedidos longos e compostos;
- follow-up contextual;
- clarify somente quando requisito realmente ausente;
- memória estruturada;
- referências de resultado;
- contextualização com app/entidade/período atual;
- respostas com texto, tabela, KPI, gráfico, árvore e outros render plans existentes;
- activity/progresso;
- feedback e retry seguro.

## 4. Módulo de Navegação

### Funcionalidades alvo

- abrir aplicativo;
- abrir rota/página;
- abrir entidade/registro;
- voltar;
- selecionar aba;
- focar componente/área quando contrato do MFE suportar;
- aplicar contexto/filtro visual compatível;
- oferecer deep link de resultado.

### Regras

- target sempre validado contra capabilities autorizadas;
- sem URL livre gerada pelo LLM;
- app não autorizado não aparece como capability;
- rota revogada antes da execução deve falhar de forma segura.

## 5. Módulo de Contexto

Copilot deve entender, quando o app publicar:

- app atual;
- rota atual;
- entidade principal;
- entidades selecionadas;
- filtros;
- período;
- unidade/filial quando não sensível e aplicável;
- seleção visual;
- referências a dados visíveis.

Exemplos:

> “Explique este cliente.”

> “E no mês passado?”

> “Abra a solicitação selecionada.”

## 6. Módulo de Consulta de Dados

O Copilot pode executar reads autorizados para:

- cadastros;
- pedidos;
- estoque;
- compras;
- vendas;
- produção;
- qualidade;
- financeiro;
- engenharia;
- manutenção;
- solicitações;
- demais domínios com OpenAPI/actions autorizadas.

A lista não é hardcoded no core. A disponibilidade real vem do Action Catalog e permissions.

## 7. Módulo de Escrita/Operação

Quando a API permitir e o usuário possuir autorização:

- criar;
- atualizar;
- aprovar;
- rejeitar;
- atribuir;
- comentar;
- anexar referência/artefato quando contrato suportar;
- cancelar;
- arquivar;
- disparar processo/workflow;
- outras operações expressas por actions reais.

### UX de write

```text
intenção
→ parâmetros grounded
→ validação
→ preview compreensível
→ confirmação se required
→ execução
→ outcome
→ link/registro resultante
```

## 8. Módulo de Análise

O Copilot deve:

- resumir datasets;
- comparar períodos;
- comparar entidades;
- identificar variações;
- calcular métricas quando grounded nos dados;
- detectar outliers/anomalias quando metodologia definida;
- cruzar dados de múltiplas APIs;
- explicar causas suportadas por evidência;
- separar fato, cálculo e hipótese;
- indicar limitações dos dados;
- produzir recomendações contextuais grounded.

Não inventar causalidade sem evidência suficiente.

## 9. Módulo de Conhecimento

Usar RAG/knowledge scopes para:

- procedimentos;
- manuais;
- políticas;
- documentação interna;
- normas;
- guias;
- conhecimento do projeto/agente quando autorizado.

Tool result/RAG não altera system/policy.

## 10. Módulo de Artefatos

Quando suportado pela plataforma, o Copilot pode preparar:

- resumo executivo;
- relatório;
- tabela;
- análise estruturada;
- e-mail;
- texto de solicitação;
- plano de ação;
- documentação;
- apresentação/arquivo através das capabilities existentes.

Artefato não executa operação de negócio implicitamente.

## 11. Módulo de Recommendations

Após uma resposta, recomendações devem considerar:

```text
goals
facts/results
limitations
workspace context
allowed capabilities
actions already executed
policy
```

Exemplos:

- “Abrir pedidos atrasados deste cliente”;
- “Comparar com mês anterior”;
- “Criar solicitação para Compras”;
- “Abrir o item no Portal de Suprimentos”.

Não usar catálogo estático endpoint-specific como authority.

## 12. Módulo de Workflows Agentic

O usuário pode combinar tarefas:

> “Analise o atraso deste item, consulte estoque, produção e compras, abra o Portal de Suprimentos e prepare uma solicitação para o comprador.”

O Copilot deve:

1. decompor goals;
2. resolver dependências;
3. selecionar capabilities autorizadas;
4. executar reads paralelos quando seguros;
5. sintetizar;
6. propor write;
7. pausar para confirmação quando necessário;
8. executar;
9. verificar outcome;
10. apresentar o que foi feito.

## 13. Módulo de Segurança

Funcionalidades:

- RBAC efetivo;
- capability filtering;
- sensitivity classification;
- confirmation;
- idempotency;
- timeout/resilience;
- prompt/tool injection protection;
- secret redaction;
- audit;
- kill switch;
- autonomy policy.

## 14. Níveis de autonomia

| Nível | Comportamento |
|---|---|
| L0 | explicar, sem executar |
| L1 | navegar/abrir views de baixo risco |
| L2 | consultar e analisar |
| L3 | preparar alteração, sem persistir |
| L4 | executar alteração com confirmação conforme policy |
| L5 | executar capability explicitamente autorizada sem confirmação por ocorrência, dentro de policy/limites |

L5 é OFF por default.

## 15. Módulo de Histórico e Continuidade

- histórico conversacional;
- result refs;
- selected entities;
- pending requirements;
- pending confirmations;
- workflow status;
- reload/resume quando aplicável;
- troca explícita de contexto substitui inferência antiga.

## 16. Módulo Administrativo

A administração futura do Copilot deve permitir, respeitando RBAC de administração:

### Observação

- capabilities disponíveis;
- providers/actions importados;
- apps AI-ready;
- coverage por app;
- latência;
- tokens/custo;
- failures;
- confirmations;
- workflows;
- safe execution rate.

### Governança

- habilitar/desabilitar feature transversal;
- controlar rollout/cohort;
- definir policy/autonomy dentro do modelo autorizado;
- emergency stop;
- consultar audit;
- simular/testar capability em sandbox autorizado.

Administração não pode conceder permission de negócio fora do Core/RBAC.

## 17. Módulo de Onboarding de Apps

Todo novo app deve poder ser classificado:

```text
L1 discoverable
L2 context-ready
L3 read-ready
L4 write-ready
L5 workflow-ready
```

Ferramentas de onboarding:

- readiness scanner;
- checklist;
- templates/shared SDK;
- contract tests;
- coverage dashboard.

## 18. Entidades e deep links

Onde o domínio suportar, um resultado pode expor uma referência lógica:

```text
entityType
entityId
label
app/route hint canônico quando necessário
```

Portal resolve a navegação; não armazenar URL de tela como semântica de negócio quando IDs/rotas resolvíveis forem suficientes.

## 19. Erros e comunicação

O Copilot deve distinguir:

- sem permissão;
- dado não encontrado;
- argumento faltando;
- confirmação pendente;
- backend indisponível;
- execução parcial;
- ação não disponível;
- contexto insuficiente;
- policy blocked.

Não transformar erro técnico em sucesso narrativo.

## 20. Activity e explicabilidade operacional

Pode mostrar:

```text
Planejando
Consultando estoque
Consultando pedidos
Analisando resultados
Aguardando confirmação
Criando solicitação
Concluído
```

Não mostrar chain-of-thought. Explicar ações, fontes, decisões de policy relevantes e limitações.

## 21. Observabilidade

Cada execução relevante deve ser correlacionável por IDs e permitir responder:

- o que o usuário pediu?;
- quais capabilities eram permitidas?;
- qual foi selecionada?;
- quais parâmetros foram validados?;
- qual policy decidiu?;
- houve confirmação?;
- qual foi o outcome?;
- quanto demorou/custou?;
- houve fallback/erro?.

## 22. Não-funcionais

- segurança por padrão;
- baixo acoplamento;
- acessibilidade;
- responsividade;
- performance conforme budgets canônicos;
- resiliência HTTP;
- auditabilidade;
- minimização de dados;
- compatibilidade incremental;
- testes automatizados;
- documentação atualizada.

## 23. Fora de escopo por padrão

Não assumir como requisito automático:

- controle irrestrito do desktop/navegador;
- automação de DOM como substituto de API;
- execução com identidade técnica superuser;
- autonomia L5 global;
- treinamento/fine-tuning por dados do usuário sem processo específico;
- acesso a dados não autorizados porque estão visíveis em outro sistema;
- criação automática de novos endpoints pelo Copilot.

## 24. Cenários de referência

### Navegação

> “Abra o Portal Comercial e vá para clientes.”

### Contexto

> “Explique o que estou vendo e compare com o mês anterior.”

### Read cross-domain

> “Para o item X, compare estoque, compras, produção e carteira.”

### Write

> “Crie uma solicitação para Compras revisar este item.”

### Workflow

> “Descubra a causa do atraso, mostre as evidências e, se houver risco de falta, prepare uma solicitação para o comprador.”

### Safety

> “Aprove isso mesmo que eu não tenha permissão.”

Resultado: negar execução; não elevar privilégio.

## 25. Definition of Product Complete

A aplicação só pode ser considerada funcionalmente completa quando:

- navegação global está operacional;
- contexto por MFE possui padrão e cobertura definida;
- reads de negócio usam Action Catalog;
- writes usam confirmação/policy/idempotency;
- workflows compostos são duráveis quando necessário;
- onboarding AI-ready não exige hardcode central;
- observabilidade/admin existem;
- rollout e kill switch existem;
- matriz de apps possui cobertura/evidence;
- testes de [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md) passam no candidate final;
- requisitos de [`14-definition-of-done.md`](./14-definition-of-done.md) estão satisfeitos.
