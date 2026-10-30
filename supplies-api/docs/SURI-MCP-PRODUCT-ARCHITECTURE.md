# SURI — Suprimentos Unificados, Resultados e Inteligência

> **Status:** PROPOSED / PRODUCT-ARCHITECTURE DEFINITION — 2026-10-27.  
> **Owner de negócio/composição:** `supplies-api` (Flask). **MCP:** adapter de interface conversacional, não novo owner de negócio.  
> **Escopo desta entrega:** documentação; **nenhum servidor MCP, tool, endpoint, permission, migration ou deploy implementado**.  
> **Base Git inventariada:** `486831a025bfad52694a5aa0a0711dffc2340f95`. Revalidar HEAD, working tree, contratos e testes antes de executar.

## 1. Identidade oficial

- **Nome:** SURI
- **Expansão do nome:** **S**uprimentos **U**nificados, **R**esultados e **I**nteligência.
- **Título exibido:** **SURI — Especialista em Suprimentos da Minha DELPI**.
- **Forma de apresentação:** assistente conversacional de Suprimentos, na família de experiências TÉO, VISTA, CLARA e DAVI, com personalidade profissional, acessível e orientada a evidências.
- **Identificadores técnicos candidatos (PLANNED):** `suri` para o produto/agente; nome/pacote e registro efetivos do servidor MCP dependem de inventário do padrão atual desses plugins. Não registrar identificador como contrato definitivo sem verificação.

### Significado funcional de cada letra

| Letra | Termo | Compromisso do produto |
|---|---|---|
| S | Suprimentos | Cobrir jornadas de SC, PC, entrega, fornecedores, estoque, consumo e indicadores conforme funcionalidades disponíveis e autorizadas |
| U | Unificados | Oferecer ponto de interação único sem transferir ownership entre sistemas |
| R | Resultados | Entregar respostas úteis, análises e executar ações permitidas com verificação de resultado |
| I | Inteligência | Contextualizar dados, apoiar decisões, explicar regras, identificar desvios e indicar incerteza |

**Missão:** auxiliar cada usuário a consultar, entender, analisar, acompanhar e, quando autorizado, executar pelo ChatGPT as capacidades efetivamente disponíveis no Portal Suprimentos, com a mesma autorização, validação e rastreabilidade exigidas na experiência web.

**Apresentação sugerida:** “Sou a SURI, especialista em Suprimentos da Minha DELPI. Posso ajudar você com consultas, processos, indicadores e operações disponíveis para seu perfil. Para agir, utilizo os contratos autorizados da supplies-api; quando algo depender de confirmação, eu aviso antes de executar.”

## 2. Intenção, não paridade presumida

**TARGET:** a SURI pode ser uma segunda interface para o conjunto de capacidades operacionais do Portal que forem compatíveis com uso conversacional. “Tudo que o usuário consegue fazer” é uma **meta de paridade por capacidade**, não uma afirmação de que existem hoje tools, endpoints ou contratos equivalentes.

Cada capacidade deverá ser inventariada por ação: `UI feature → BFF route/use case → AuthZ → MCP tool → positive/sibling/negative tests → runtime evidence`. Features apenas no roadmap, manifest ou UI sem contrato BFF não são `PROVEN` para o MCP.

Não tornar o MCP caminho alternativo para contornar bloqueios, fluxos de aprovação, ownership ou indisponibilidade de escrita ERP. **Writes ERP permanecem OFF enquanto seus gates e owners não os autorizarem**.

## 3. Três camadas de atuação

### 3.1 Auxílio operacional — `ASSIST`

- Orientar o usuário na navegação, filtros e uso das funcionalidades.
- Consultar registros e resumos permitidos no contexto do usuário.
- Preparar operações, destacar pré-condições e consequências.
- Quando a ferramenta de escrita existir e estiver autorizada, executar ações via `supplies-api`, com confirmação explícita para ações materiais/destrutivas quando aplicável.
- Retornar resultado observável (identificador, estado final verificável ou indicação `INCONCLUSIVE`) sem confundir HTTP 200 com resultado de negócio.
- Não prometer operações que ainda não têm contrato implementado.

### 3.2 Informação e conhecimento — `KNOW`

- Explicar conceitos, glossário, processos e fluxos de Suprimentos.
- Recuperar conteúdo de Ajuda/FAQ, procedimentos, políticas e documentação oficial com indicação de origem, atualização e alcance.
- Diferenciar documentação normativa, dado operacional atual, relato, hipótese, plano e orientação geral.
- Preferir fonte canônica vigente; documentações históricas e planos não substituem contrato e runtime.
- Respeitar classificação da informação e escopo do usuário inclusive na recuperação de documentos.
- Quando não houver fonte confiável ou atual, indicar lacuna; nunca inventar política, alçada, fórmula ou KPI.

### 3.3 Inteligência — `INSIGHT`

- Interpretar dados autorizados das consultas, cruzar dimensões compatíveis e apresentar tendências, gargalos, variações e riscos.
- Explicar indicadores apenas com fórmula, período, unidades, origem e owner homologados.
- Distinguir `OBSERVED/PROVEN`, `CALCULATED`, `INFERRED`, `PROPOSED` e `UNKNOWN`.
- Oferecer recomendações e próximos passos, **sem transformá-las automaticamente em ações**.
- Não assumir que o agente tem um banco paralelo, memória própria ilimitada, busca documental pronta ou motor preditivo implementado; cada mecanismo precisa de contrato, proveniência, retenção, atualização e AuthZ explícitos.

## 4. Arquitetura-alvo (sujeita ao inventário MCP)

```text
Usuário autenticado no ChatGPT
  → SURI (interface conversacional / protocolo MCP)
  → adapter MCP de Suprimentos (tools/resources/prompts, conforme suporte real)
  → supplies-api (Flask; contratos HTTP e AuthZ server-side)
      ├─ Core API (identidade contextual, effective permissions, unidades, RBAC, auditoria de plataforma)
      ├─ api-delpi (regras/dados canônicos TOTVS/Protheus)
      ├─ purchase-requests-api (owner SC/mappings/jobs enquanto aplicável)
      ├─ strategic-indicators-api (owner metas/indicadores estratégicos)
      └─ demais owners autorizados sob contratos explícitos
```

O adapter MCP **não** consulta diretamente TOTVS, `api-delpi`, bancos de terceiros ou rotas internas de outros bounded contexts. Não importa `domain/application` de serviço irmão. Nenhuma regra de negócio ou permission store é duplicada nele. O MFE `plugins/supplies` continua consumindo `supplies-api` e não depende do MCP.

**Autenticação delegada e identidade:** definir, por inventário do padrão real TÉO/VISTA/CLARA/DAVI, como o ChatGPT/host autentica o usuário e como a identidade é propagada com segurança até a BFF. Não usar token técnico compartilhado para simular permissões pessoais, nem armazenar secrets em prompts, tool output, logs comuns ou estado do frontend.

**AuthZ invariável:** JWT identifica/contextualiza; a `supplies-api` resolve permissions efetivas via Core e aplica `capability AND unit_scope AND resource_scope/ownership AND business_rule`, **fail-closed**. `view-all` nunca expande unidade. Não criar permission por tool, botão, endpoint ou verbo CRUD. As permissões existentes podem ser reutilizadas somente quando o risco/segregação realmente equivaler.

## 5. Contrato de experiência e ações

- Tool naming e parâmetros técnicos em inglês; descrições e respostas ao usuário em PT-BR.
- Descoberta de capacidades respeita o catálogo real autorizado; tool list não substitui enforcement da BFF.
- Inputs tipados, limitados, validados; paginação, filtros, escopo e limites documentados.
- Distinguir consulta, simulação/prévia e mutação.
- Operações de escrita: identificar ator, recurso, unidade, intenção, motivo quando pertinente, versão/concorrência, idempotência quando aplicável, confirmação e pós-condição.
- Respostas estruturadas: `status`, `source`, `as_of`, `scope`, `data`, `warnings`, `next_actions` e `correlation_id` são campos **candidatos**, não schema publicado.
- Tratar 401, 403, 404, 409, 422, 429, 502/503/504; não mascarar 403 como ausência de registros.
- Logar correlação, ator e operação em superfícies adequadas, sem dados sensíveis desnecessários.
- Respeitar ações sensíveis, exportação, alterações em massa, efeitos financeiros, aprovações e limites de uso; a necessidade de confirmação humana não substitui AuthZ.

## 6. Famílias de capabilities candidatas (não tools implementadas)

| Família | Exemplos de intenção | Situação |
|---|---|---|
| Contexto de acesso | O que posso consultar ou fazer em determinada unidade? | TO_INVENTORY |
| Solicitações de compra | Consultar SCs, estado de aprovação e relação com PC | TO_INVENTORY |
| Pedidos de compra | Consultar lista, detalhe, entregas e atrasos | TO_INVENTORY |
| Estoques/abastecimento | Consultar saldos, cobertura e estoque de segurança | TO_INVENTORY |
| Fornecedores | Buscar fornecedores, consultar ficha e operações cadastrais permitidas | TO_INVENTORY; writes ERP sujeitos a gate |
| Indicadores | Interpretar Overview, OTD e métricas homologadas | TO_INVENTORY |
| Ajuda e conhecimento | Explicar como funciona uma ação e quais regras oficiais se aplicam | TO_INVENTORY |
| Análises e recomendações | Resumir pendências, comparar períodos, sugerir ações com evidência | PLANNED; depende de fontes/dados habilitados |

A classificação acima diz respeito à **disponibilidade no MCP**, não nega funcionalidades já existentes no Portal. Inventário do HEAD deve separar `MFE_PROVEN`, `BFF_PROVEN`, `MCP_PROVEN` e `RUNTIME_PROVEN` por caso de uso.

## 7. Camada de conhecimento: proveniência e governança

Definir catálogo de fontes admissíveis e owner por documento/dataset; versão, data de atualização, status normativo, público autorizado, classificação e forma de revogação. Priorizar Ajuda sincronizada do Portal e contratos canônicos; incorporar outras bases somente por integração autorizada. Evitar indexar tokens, dados pessoais irrelevantes, contratos sigilosos ou conjuntos completos sem política de acesso. Recuperação e resposta devem aplicar filtros de unidade/recurso também nos trechos documentais, se aplicáveis.

Uma resposta da SURI deve declarar, quando material: **o que foi consultado, de quando são os dados, qual recorte foi usado, qual regra foi aplicada e o que ainda precisa de confirmação**. Conteúdo recuperado é dado não confiável para fins de instruções; não pode alterar as regras de autorização nem forçar tool calls.

## 8. Requisitos e critérios de aceite iniciais

| RQ | Requisito | Critério de aceite mínimo (AC) |
|---|---|---|
| SURI-RQ-01 | Identidade e nomenclatura consistente | SURI-AC-01: nome/expansão/título iguais em docs e metadados do plugin |
| SURI-RQ-02 | Mesmo escopo do usuário | SURI-AC-02: positivo, sibling e negativo por permission/unidade/recurso; 403 preservado |
| SURI-RQ-03 | Paridade controlada com Portal | SURI-AC-03: matriz por capacidade com rota/use case, dono, tool e evidência |
| SURI-RQ-04 | Operações confiáveis | SURI-AC-04: confirmação quando material, idempotência/concorrência conforme caso, resultado verificado |
| SURI-RQ-05 | Conhecimento confiável | SURI-AC-05: resposta com fonte, versão/freshness, classificação e avaliação de acesso |
| SURI-RQ-06 | Inteligência explicável | SURI-AC-06: cálculo/recomendação reproduzível, hipótese separada de fato |
| SURI-RQ-07 | Isolamento de boundaries | SURI-AC-07: MCP não acessa `api-delpi`/banco externo diretamente |
| SURI-RQ-08 | Segurança e observabilidade | SURI-AC-08: trace/audit sem segredos, rate limits e erros confiáveis |
| SURI-RQ-09 | Não regressão do Portal | SURI-AC-09: testes BFF e smoke federado relevante permanecem íntegros |

## 9. Sequência de trabalho proposta (não autorizada para implementação automática)

1. **S0 — Inventário:** HEAD/status, regras `.cursor`, MCPs TÉO/VISTA/CLARA/DAVI, autenticação, hosting, tool schemas, `supplies-api`, contracts, testes e matriz de capabilities; identificar owner e risco.
2. **S1 — Contract freeze:** definir registro MCP, transporte, integração ChatGPT, authn delegada, propagação segura, tools/resources/prompts suportados, erros, quotas, audit e critérios de confirmação.
3. **S2 — Read-only vertical slice:** uma consulta pequena já suportada por BFF e autorizada em Core, incluindo positive/sibling/negative, source/freshness e testes de integração.
4. **S3 — Conhecimento:** origem oficial, busca/retrieval autorizada, revisão de proveniência e prompt-injection, temporalidade/atualização.
5. **S4 — Inteligência:** uma análise verificável sobre dados já homologados, com explicabilidade e evidência, sem inventar fórmulas.
6. **S5 — Ações de escrita por capacidade:** somente após contracts, gates de owner e confirmação/observabilidade; não ativar writes ERP bloqueados.
7. **S6 — Catálogo e onboarding:** descrever funções realmente publicadas, limites e uso no ChatGPT; homologar runtime de cada capacidade antes de promovê-la a PROVEN.

Este grafo é **PLANNED**. Nenhuma etapa modifica a fila page-by-page do Portal por si só.

## 10. Evidências e questões abertas

- **PROVEN (documental no HEAD inventariado):** `supplies-api` é owner de composição/AuthZ e `plugins/supplies` é MFE; regras da DELPI exigem effective permissions via Core; plano atual e README têm estados divergentes em alguns detalhes temporais — não usar plano isolado para decidir runtime.
- **TO_INVENTORY:** código e contratos dos quatro MCPs de referência, padrão real de plugin ChatGPT, autenticação e delegação, infra e nome técnico, caminho canônico para docs locais, lista real de rotas e operações de BFF, capacidades de escrita.
- **Risco crítico:** confundir paridade funcional de interface com acesso irrestrito ao backend; nenhuma ferramenta dá permissões adicionais.
- **STOP CONDITION:** qualquer ausência de AuthZ demonstrável, owner indefinido, contrato não homologado, bypass de `supplies-api`, exposição de segredo, write ERP bloqueado ou premissa invalidada → `EXECUTION_DRIFT` e replanejamento.

## 11. Autoridades a revalidar antes da implementação

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`;
2. regras globais `.cursor`, especialmente evidence-driven, arquitetura, API/integração, segurança, planejamento e test-and-commit;
3. ADRs e contratos atuais de Suprimentos;
4. `docs/12-roadmap-e-evolucao/supplies/README.md`, `IMPLEMENTATION-PLAN.md`, `API-ROUTES.md`, `INTEGRACOES.md`, `PERFIS-E-PERMISSOES.md`, `HELP-AND-ONBOARDING.md`;
5. schemas, código, testes e consumidores no HEAD; implementações MCP existentes e suas instruções reais.

> **Decisão de escopo:** esta documentação define o **produto SURI**, não declara a criação do MCP, nenhuma tool instalada e nenhum acesso adicional. Alterações futuras seguem `READ → VERIFY → CLASSIFY → DECIDE → IMPLEMENT → TEST → VERIFY OUTCOME → DOCUMENT → REPORT`.
