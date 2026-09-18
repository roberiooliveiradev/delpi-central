# Transformômetro — ciclo de inteligência e melhoria de processo

> **Status deste documento:** TARGET arquitetural e de produto. **IMPLEMENTATION = NOT AUTHORIZED.**  
> **ADR:** [`adr-ciclo-inteligencia-processo.md`](../../../transformometro-api/docs/architecture/adr-ciclo-inteligencia-processo.md)  
> **Classificação:** o que está no código neste HEAD é PROVEN só onde a seção diz PROVEN. O restante é TARGET, TO_INVENTORY ou PLANNED.  
> Documentação não prova runtime.

O produto deve cobrir o ciclo:

```text
PROCESSO → EVIDÊNCIA → DIAGNÓSTICO → REDESENHO → REGISTRO → MEDIÇÃO → APRENDIZADO
```

Método é lente. Não é tela obrigatória e não é entidade.

```text
METHOD != DOMAIN ENTITY
GUIDANCE != SOURCE OF TRUTH
INFERRED != FACT
PROPOSED != SAVED
TO-BE != PRODUCTION STATE
AS-IS != TO-BE
PROBLEM != CAUSE
CAUSE HYPOTHESIS != PROVEN ROOT CAUSE
ESTIMATED GAIN != MEASURED GAIN
RECOMMENDATION != AUTHORIZATION
```

Estados epistemológicos a preservar em artefatos futuros relevantes: `OBSERVED/INFORMED`, `CALCULATED`, `INFERRED`, `PROPOSED`, `UNKNOWN`. Não copiar esses campos para todas as tabelas. Avaliar metadata, relação, value object ou registro de auditoria já existente.

## 1. O que já está comprovado no código

Revalidado em `GptEntity`, workspace do MFE, ADRs de diagrama/decomposição e constantes MCP/Actions. Não é inventário de produção ao vivo.

| Capability | Estado | Owner | Fonte observada |
|---|---|---|---|
| Processo-mestre | PROVEN | Transformômetro | `process`; campos incluem nome, status, descrição, objetivo, gestor, família |
| Escopo organizacional do mestre | PROVEN | Transformômetro | `todas_filiais_ativas`, `filial_ids`, `setor_ids` (`ProcessoEscopoRepository`). **Não é SIPOC** |
| Instância operacional | PROVEN | Transformômetro | `instance` = processo × unidade × departamentos. Contexto JSON `instancia_contexto_v1` |
| Revisão / cenário | PROVEN | Transformômetro | `revision` (baseline, melhoria, automação, correção). Ativação governada existe |
| Medição de revisão | PROVEN | Transformômetro | `measurement` = valor mensal da revisão, não definição de indicador |
| Investimento | PROVEN | Transformômetro | `investment` na revisão |
| Recurso compartilhado, custo, vínculo | PROVEN | Transformômetro | catálogo transversal + custo vigente + vínculo na revisão |
| Árvore de decomposição | PROVEN | Transformômetro | `decomposition_tree_v1` 1:1 com o mestre. Níveis: `processo_chave`, `tarefa`, `sub_tarefa` **dentro** do mestre |
| Escopo de árvore na instância | PROVEN | Transformômetro | `instance_decomposition_scope` |
| Overlay de árvore na revisão | PROVEN | Transformômetro | `revision_decomposition_overlay` |
| Diagrama macro | PROVEN | Transformômetro | `flowchart_v1` é a fonte do diagrama. Mermaid é derivado |
| Escopo e overlay de diagrama | PROVEN | Transformômetro | instância e revisão |
| Vínculo nó de fluxo → nó da árvore | PROVEN como opcional | Transformômetro | ADR: `flowchart_v1.nodes[].meta.decomposition_id`. Não é obrigatório |
| Matriz impacto × esforço | PROVEN | Transformômetro | `impact_effort_matrix` por revisão |
| Evidência de revisão | PROVEN | Transformômetro | metadata; upload binário de evidência no MCP permanece limitado/UI |
| Ata | PROVEN | Transformômetro | `meeting_minute` |
| Timeline | PROVEN | Transformômetro | `get_process_timeline` / auditoria existente. Não é event sourcing |
| Dashboard / analyze | PROVEN | Transformômetro | visões meta, summary, processes, instances, rows |
| Contexto de processo | PROVEN parcial | Transformômetro | `get_process_context` compõe registros, diagrama e decomposição. Não inclui achados, causas nem plano de ação |
| Guia metodológico TÉO | PROVEN | TÉO methodology | `tm_app/application/methodology/guide.py`. Editorial: `docs/gpt-actions/teo-method-playbooks.md` |
| MCP | PROVEN no código | adapter | 33 tools: 10 READ, 1 ANALYSIS, 11 PREPARE, 11 ACT. Inclui `get_methodology_guide` |
| GPT Actions | PROVEN no código | adapter legado | 21 operationIds importáveis, incluindo `gpt_get_methodology_guide`. `gpt_get_openapi_schema` é rota meta, fora da contagem. Lifecycle: `LEGACY_TRANSITIONAL_BRIDGE` |

UI atual do processo (`processWorkspaceNav.ts`), PROVEN como navegação, não como modelo de domínio:

```text
Visão geral · Dados do processo · Mapeamento · Diagrama macro · Arquivos · Melhorias · Priorização (matriz) · Linha do tempo
```

Revisão: vigência, matriz, mapeamento, diagrama, medição, investimentos, recursos, evidências.

## 2. Lacunas (não são runtime)

Estas letras do pedido foram procuradas. Nenhuma virou entidade neste passe.

| Item | Classificação | Por quê |
|---|---|---|
| A. Escopo estruturado / interfaces | TARGET | O escopo PROVEN é só unidade/departamento |
| B. SIPOC | TARGET como view | Método PROVEN no guia. Sem entidade |
| C. Semântica rica da atividade | TARGET | Árvore PROVEN não carrega, como contrato obrigatório, papel, entrada, saída, sistema, regra, tempo, handoff |
| D–H. Achado, diagnóstico, hipótese, evidência de causa, fator crítico | TARGET | Evidência PROVEN é anexo/metadata de revisão, não vínculo de diagnóstico |
| I. Definição de KPI | TARGET | `measurement` é valor, não definição |
| J. AS-IS × TO-BE explícito na UX | TARGET de projeção | Overlays e tipos de revisão já existem |
| K. Plano de ação | TO_INVENTORY → TARGET | Sem entidade no Transformômetro. Planos de ação de Qualidade são outro bounded context |
| L. Aprendizado pós-implantação | TARGET | Timeline existe; eventos de aprendizado não estão modelados |
| M. Arquitetura corporativa / cadeia de valor | TARGET | `processo_chave` da árvore não é arquitetura da empresa |

## 3. Modelo conceitual alvo

Não implementar.

```text
EMPRESA / CADEIA DE VALOR
  → MACROPROCESSO
  → PROCESSO-CHAVE
  → PROCESSO PONTA A PONTA
  → ETAPA / SUBPROCESSO / ATIVIDADE
  → ESCOPO / INTERFACES
  → AS-IS
  → DIAGNÓSTICO
  → OPORTUNIDADES
  → PRIORIZAÇÃO
  → TO-BE
  → PLANO DE AÇÃO
  → IMPLANTAÇÃO
  → MEDIÇÃO
  → APRENDIZADO
```

Distinções que já existem e não podem colapsar:

| Conceito | Onde vive hoje | Não confundir com |
|---|---|---|
| Processo-mestre | `process` | instância, revisão, arquitetura corporativa |
| Instância | aplicação por unidade/departamento | o mapa corporativo do mestre |
| Revisão | cenário calculável | estado de produção, até ativação verificada |
| Baseline | tipo/papel de revisão calculável | o cadastro mestre |
| Composição calculada | merge de diagrama/árvore | documento editável |
| TO-BE | proposta | revisão ativa |

## 4. O que pertence a qual owner

| Conceito | Owner | Fonte de verdade | Consumers | Quem escreve | Não é owner |
|---|---|---|---|---|---|
| Processo, instância, revisão, medição, investimento | Transformômetro | Postgres `transformometro` | MFE, MCP, GPT Actions, gateway S2S | API do Transformômetro | TÉO, ChatGPT, DÉLIA |
| Diagrama `flowchart_v1` | Transformômetro | documento do processo | MFE, composição, Mermaid derivado | API | prompt, Mermaid como original |
| Árvore `decomposition_tree_v1` | Transformômetro | documento do processo | MFE, export, vínculo opcional com fluxo | API | arquitetura corporativa |
| Escopo organizacional | Transformômetro | `ProcessoEscopoRepository` | cadastro de instância | API | SIPOC |
| Matriz impacto×esforço | Transformômetro | por revisão | MFE, Actions/MCP genéricos | API | score único de CTP |
| Evidência | Transformômetro | metadata de revisão | MFE, `list_evidence` / manage | API | diagnóstico (ainda) |
| Ata | Transformômetro | meeting minute | MFE, Actions | API | plano de ação |
| Guia de método | TÉO methodology | `guide.py` | MCP e GPT Action de metodologia | ninguém persiste o guia | domínio |
| Identidade | Keycloak | realm `delpi` | todos os apps | Keycloak | Transformômetro |
| RBAC transversal de apps | Core | permissões | portal | Core | prompt, cargo, MFE |
| KPI de engenharia fora do TM | strategic-indicators / api-delpi | contrato S2S | dashboards | owner daquele contexto | tabela `measurement` |
| Plano de ação de Qualidade | api-delpi / quality-action-plans | outro schema | aquele MFE | aquela API | Transformômetro |
| DÉLIA | orquestração futura | não é SoT de processo | — | — | domínio do TM |
| Automation Hub | execução técnica quando existir | não é SoT de processo | — | — | diagnóstico |

AuthZ futura: capability do TÉO ≤ capability do usuário autenticado. Artefato novo não cria permissão nova por padrão. Revisar view, manage, escopo de instância e catalog admin. Backend decide. Cargo, prompt, frontend, metadata de Action e profile não autorizam.

Writes MCP futuros continuam: ler estado → PREPARE da mudança exata → validar → mostrar → confirmação explícita → ACT → read-back autoritativo → verificar. GPT Actions legado não usa `proposal_handle`. Essa diferença é de superfície, não licença para bypass.

## 5. Método → resultado de domínio

| Método | Para que serve | Saída | Destino de domínio | Persistir? | Entidade nova? | Notas |
|---|---|---|---|---|---|---|
| Macroprocesso / processo-chave / ponta a ponta | Estruturar a cadeia e o fluxo | Hierarquia e limites | Arquitetura corporativa (TARGET) ou árvore do mestre quando o nível já for o processo individual | Só após confirmação e write governado | Não para o método | Árvore atual já tem `processo_chave` **dentro** do mestre. Não promover isso a cadeia da empresa |
| SIPOC | Limite, fornecedores, entradas, saídas, clientes | Escopo/interfaces | Artefato ou projeção de processo. Não a tabela de escopo organizacional | TARGET | Não `SipocEntity` | View sobre o modelo de interfaces |
| Lean | Desperdício e fluxo | Achados | Diagnóstico | TARGET | Não | Classe Lean é rótulo do achado, não fato |
| Ishikawa | Famílias de causa | Hipóteses | Modelo causal | TARGET | Não | Não forçar 6M |
| 5 Porquês | Uma cadeia | Hipótese + evidência necessária | Mesmo modelo causal | TARGET | Não | Último porquê ≠ causa comprovada |
| CTP | Priorizar fatores | Criticidade e implementabilidade em eixos separados | Rever `impact_effort_matrix` antes de agregado novo | TARGET | TO_INVENTORY | Matriz atual é impacto×esforço da revisão, não os dois eixos do playbook |
| TDR | Redesenho | Proposta TO-BE | Revisão cenário, overlays, medição proposta, investimento | Só como PROPOSED até ativação verificada | Não | Automação sugerida ≠ implementada |
| KPI | Definir indicador | Definição | Conceito novo ou evolução explícita de measurement | TARGET | TO_INVENTORY | Fórmula inventada não é política da empresa |
| AS-IS | Estado atual | Projeção | Baseline + overlays + medição | Já persiste peças; falta a projeção explícita | Não | Mestre ≠ composição ≠ baseline |
| TO-BE | Estado futuro proposto | Projeção | Cenário não ativo | Já persiste peças | Não | Discussão no chat ≠ salvo |
| SWOT | Contexto estratégico | Leitura, não fluxo | Guidance. Artefato só se uma fase provar necessidade de `Strategic Analysis` | Não por default | Não | SWOT de processo, de departamento e corporativo não são a mesma coisa |

## 6. Decisões de modelagem recomendadas (não implementadas)

Abstraction Gate aplicado como recomendação, não como schema.

**Enriquecimento da atividade.** Não colocar papel, entrada, saída, sistema, regra, tempo e handoff como colunas de `processos`. Alternativa recomendada: estender o schema do nó em `decomposition_tree_v1` só para atributos do próprio nó, num passe com revisão de schema. Achado, causa e KPI não moram no nó. Ficam em agregados que referenciam `node_id`.

**Diagrama.** Manter `flowchart_v1` canônico e Mermaid derivado. O vínculo já documentado é `meta.decomposition_id`. TARGET: tornar o vínculo compreensível na UX para a mesma atividade não existir duas vezes sem relação. Não batizar campo novo (`semantic_ref`, `source_node_id`) neste documento.

**SIPOC / interfaces.** Capability `process interfaces`, nome de produto ainda não fixado, para não colidir com escopo organizacional. Conceitos: gatilho, condição de fim, resultado, fornecedores, entradas, etapas macro, saídas, clientes, processos anteriores e posteriores, departamentos, sistemas, regras. SIPOC é view. Sem `SipocRepository`.

**Diagnóstico.** Capability TARGET. Candidatos conceituais, não tabelas: achado, problema, desperdício, risco, oportunidade, hipótese causal, causa validada, elo de evidência, fator crítico. Um achado deve poder apontar para processo, instância, revisão, nó da árvore, nó do diagrama, evidência, ata e melhoria, pelo menor acoplamento que o contrato permitir.

**KPI.** Separar definição e medição. `measurement` continua sendo o valor. Definição candidata: nome, propósito, descrição, fórmula, status da fórmula, unidade, direção, fonte, frequência, owner, grão, baseline, meta, estado de evidência da meta, notas de qualidade. Dashboard de engenharia fora do TM não fecha essa lacuna.

**AS-IS / TO-BE.** Não criar segunda fonte. A UX deve projetar AS-IS a partir de baseline + medição + overlays, e TO-BE a partir do cenário ainda não ativado. Ativação só conta com read-back autoritativo.

**Plano de ação.** Se o inventário continuar vazio, o owner provável é a melhoria/revisão, não o mestre. Campos candidatos: ação, responsável, prazo, status, dependência, evidência, resultado esperado, resultado real.

**SWOT.** Permanece guidance. Três escopos se um dia persistir: processo, departamento, corporativo. Não é estrutura obrigatória do processo.

**Arquitetura corporativa.** Agregado futuro separado. Necessidade real: sim, para não sobrecarregar um processo. Owner: Transformômetro, não a árvore de um mestre. Equivalente existente: não. Implementar só depois das fases de processo individual.

**Completude.** Lista objetiva de artefatos: identificação, escopo/interfaces, mapeamento, diagrama, diagnóstico, indicadores, baseline, melhoria, TO-BE, plano, evidências. Saída: `PRESENT`, `MISSING`, `PARTIAL`, `NOT_APPLICABLE`. Sem nota de “processo bom”.

## 7. Matriz current → target

| Capability | Estado atual | Owner | Fonte atual | Target | Reusar? | Conceito novo? | MCP | GPT Actions | UI | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Cadastro do processo | PROVEN | TM | `process` | Manter | Sim | Não | genérico | genérico | Dados | PROVEN |
| Escopo organizacional | PROVEN | TM | escopo filial/setor | Manter nome distinto de SIPOC | Sim | Não | genérico no process | genérico | Dados / instância | PROVEN |
| Interfaces / SIPOC | Ausente | TM | guia apenas | Projeção ou artefato | View, não entidade | TO_INVENTORY | genérico se couber | genérico se couber | Seção Processo | TARGET |
| Mapeamento | PROVEN | TM | árvore | Nó com semântica bastante, sem virar diagnóstico | Schema do nó | TO_INVENTORY | genérico | genérico | Mapeamento | TARGET |
| Diagrama | PROVEN | TM | flowchart_v1 | Vínculo com a árvore mais explícito | `decomposition_id` opcional | Não neste passe | genérico | genérico | Diagrama | PROVEN + TARGET de UX |
| Achados / causas | Ausente | TM | — | Agregado de diagnóstico | Evidência e ata como elos | TO_INVENTORY | sem tool por método | sem Action por método | Diagnóstico | TARGET |
| Fatores críticos / CTP | Parcial | TM | matriz da revisão | Dois eixos, sem score ambíguo | Matriz se o contrato aguentar | TO_INVENTORY | genérico | genérico | Priorização | TARGET |
| Definição de KPI | Ausente | TM | — | Definição separada do valor | `measurement` só para valor | TO_INVENTORY | genérico | genérico | Indicadores | TARGET |
| Medição | PROVEN | TM | `measurement` | Continua valor CALCULATED/INFORMED | Sim | Não | genérico | genérico | Medição | PROVEN |
| AS-IS × TO-BE | Peças PROVEN, comparação não | TM | revisão + overlays | Projeção de UX | Sim | Não | `get_process_context` com seção, não payload ilimitado | idem | Melhorias | TARGET |
| Plano de ação | TO_INVENTORY | melhoria/revisão se nascer | — | Action plan | Não usar Qualidade como owner | TO_INVENTORY | genérico | genérico | Melhorias | TARGET |
| Aprendizado | Timeline PROVEN | TM | audit/timeline | Eventos de resultado sobre auditoria existente | Sim | Não event sourcing | timeline existente | `gpt_get_process_timeline` | Linha do tempo | TARGET |
| Arquitetura corporativa | Ausente | TM | — | Agregado à parte | Não a árvore do mestre | Sim, fase tardia | sem rota até o contrato | sem Action até o contrato | Fora da ficha do processo | TARGET |
| Completude | Ausente | TM | — | Present/missing/partial/n/a | Leituras atuais | Projeção | seção de contexto, não tool nova | não | Visão geral | TARGET |
| Metodologia | PROVEN guidance | TÉO | `guide.py` | Continua lente | Sim | Não | `get_methodology_guide` | `gpt_get_methodology_guide` | não vira menu por método | PROVEN |
| Portal shell | Nav atual PROVEN | MFE TM | `TransformometroNav` | Portal Transforma+ | Kit `plugin-ui`, não internals do Comercial | Não | nenhuma tool de tela | nenhuma Action de tela | shell | TARGET |
| Início | Dashboard é a home | TM dashboard | `DashboardResumo` e alertas/vencimentos | Home operacional | Leituras existentes | Projeção | não `get_transforma_home` | não | Início | PARTIAL |
| Visão geral do programa | Dashboard PROVEN | TM | resumo, evolução, processos | Overview com filtros cujo cálculo exista | Dashboard | Não | `analyze` / dashboard | não `get_portal_overview` | Visão geral | PARTIAL |
| Sala de interação | Ausente no TM | Comercial | `commercial-api` interaction rooms | Só se surgir owner transversal | Não copiar | TO_INVENTORY | não | não | Sala | TO_INVENTORY |
| Minhas tarefas | Pendência de ata PROVEN | TM atas; Comercial tem worklist própria | `pending-signatures` | Projeção de obrigações | Não task store paralelo | TO_INVENTORY | não `get_my_tasks` | não | Tarefas | PARTIAL |
| Meus processos | Lista de processos PROVEN | TM | workspace de processos | Lista no escopo autorizado | search/list existente | Não | `search_records` | genérico | Meus processos | PARTIAL |
| Portfólio | Ausente | — | — | Read model, não agregado | Abstraction Gate | Não por default | não `get_my_portfolio` | não | Portfólio | TARGET |
| Administração | Catálogos PROVEN | TM | unidades, departamentos, recursos | Só domínio TM | Telas atuais | Não | catálogo existente | genérico | Administração | PARTIAL |
| Ajuda | Tooltips PROVEN | TM | `helpTooltips` | Manual do portal | Padrão de manual, não texto do Comercial | Conteúdo próprio | guia de método já existe | `gpt_get_methodology_guide` | Ajuda | PARTIAL |
| Busca | Ausente no TM | `plugin-ui` tem `CommandPalette` | Comercial busca caminhos, não entidades TM | Busca autorizada | Palette compartilhada | TO_INVENTORY no backend | não search novo sem inventário | não | Busca | TO_INVENTORY |
| Favoritos | Ausente no TM | Comercial | `GET/PUT /me/home-favorites` | Reusar só se extraído | Não duplicar | TO_INVENTORY | não | não | Favoritos | TO_INVENTORY |
| Perfil | JWT/Keycloak | Keycloak / Core | token | Exibir identidade | Avatar do kit | Não | não | não | Perfil | PARTIAL |
| Workspace do processo | Seções PROVEN | TM | `processWorkspaceNav.ts` | IA do ciclo, mesmos dados | Sim | Não | `get_process_context` | genérico | Processo | PARTIAL |

## 8. Informação / UX alvo

Não autoriza frontend.

```text
PROCESSO
  Visão geral
  Processo
    Dados e escopo organizacional
    Interfaces (SIPOC como view)
    Mapeamento
    Diagrama
  Diagnóstico
    Achados
    Causas
    Fatores críticos
  Indicadores
  Melhorias
    Oportunidades
    Priorização
    AS-IS × TO-BE
    Plano de ação
    Resultados
  Arquivos e evidências
  Linha do tempo
```

A navegação PROVEN permanece até um passe de UI aprovado.

O invólucro dessa ficha, quando a experiência de produto for implementada, é o **Portal Transforma+**, não um segundo domínio. Inventário do Comercial, shell, reuso e fases A–I: [PORTAL-TRANSFORMA-PLUS.md](./PORTAL-TRANSFORMA-PLUS.md). ADR: [adr-portal-transforma-plus.md](../../../transformometro-api/docs/architecture/adr-portal-transforma-plus.md).

| Peça | Estado neste HEAD |
|---|---|
| Portal shell, Início operacional, portfólio | TARGET |
| Dashboard, lista de processos, workspace, catálogos, tooltips, vencimentos, resumo financeiro | PROVEN como peças; PARTIAL como portal |
| Sala de interação, favoritos de página, busca de entidades | TO_INVENTORY (hoje são do Comercial ou inexistentes) |

## 9. Orçamento de rota e de tool

Antes de propor rota, tool ou Action:

1. CRUD genérico governado cobre?
2. `search_records` / `get_record` cobrem?
3. create/update do documento (`decomposition_tree`, `process_diagram`, overlays) cobre?
4. `get_process_context` cobre como projeção?
5. `analyze` cobre?
6. Dá para acrescentar entity schema + domínio + mapping sem tool nova?
7. A operação é de fato distinta (simular, validar, preparar, agir, agregar, transação atômica)?

CRUD simples de artefato novo prefere o contrato genérico **se** não quebrar invariante. Não forçar genérico para esconder regra.

Não criar por default: `get_sipoc`, `create_sipoc`, `create_lean`, `create_ishikawa`, `create_five_whys`, `create_tdr`, `gpt_create_finding`, `gpt_create_kpi`, `gpt_create_cause`.

`get_process_context` no alvo pode incluir, sob autorização e sob pedido: processo, interfaces, árvore, diagrama, instâncias, revisões, baseline, cenário, achados, causas, evidência, indicadores, melhorias, plano, medições, timeline. Default = resumo. Opções a desenhar depois: `sections` / `include`, projeção, read model. Não é payload ilimitado. Não implementar agora.

GPT Actions permanece ponte legada. A Action de metodologia existe porque o método precisava ser descobrível. Isso não vira precedente para uma Action por artefato.

Camadas de qualquer capability futura:

```text
domain → application → ports → adapters
```

Domain e application não importam FastAPI, SQLAlchemy, psycopg, HTTP, MCP SDK nem OpenAI. MCP e GPT Actions são adapters.

## 10. Roadmap de implementação (não autorizado)

Estas fases PI não renumeram as Fases 0–6 históricas de [ROADMAP.md](./ROADMAP.md).

Cada fase, quando for executada, precisa de: owner Transformômetro; pré-requisito da fase anterior aceita; fonte única; mudança de domínio explícita; persistência no owner; impacto de API; impacto MCP; impacto Actions; impacto de UI; migration só `up`; testes positive/sibling/negative; aceite; risco. Gates: owner, source, abstraction, domain contract, AuthZ, migration, API, MCP/Actions, UX, acceptance, runtime. Documentar a fase não a torna PROVEN.

| Fase | Conteúdo | Pré-requisito | MCP / Actions | Risco |
|---|---|---|---|---|
| PI-0 | Inventário de contratos e nomes (escopo organizacional ≠ interfaces) | Este documento | Nenhum | Implementar cedo demais |
| PI-1 | Interfaces/SIPOC como projeção + enriquecimento do nó | PI-0 e revisão de schema da árvore | Entity schema se couber; senão parar | Colisão de nome com escopo de filial |
| PI-2 | Achados, modelo causal, elos de evidência | PI-1 se o achado aponta para nó | Sem tool por método | Transformar hipótese em fato |
| PI-3 | Definição de KPI ligada à medição existente | Decisão TO_INVENTORY fechada | Genérico | Duplicar strategic-indicators |
| PI-4 | UX AS-IS × TO-BE sobre revisão e overlays | Nenhum agregado novo obrigatório | Contexto em seções | Chamar cenário de produção |
| PI-5 | Plano de ação só se o inventário continuar vazio | PI-2 | Genérico na melhoria/revisão | Importar o módulo de Qualidade |
| PI-6 | Aprendizado, resultado verificado, completude | Timeline atual | Estender timeline, não tool nova | Event sourcing desnecessário |
| PI-7 | Arquitetura corporativa | Processo individual estável | Fora do CRUD do mestre até o contrato | Reusar `decomposition_tree` da empresa inteira |

A experiência **Portal Transforma+** não cria fases PI novas. O adendo [PORTAL-TRANSFORMA-PLUS.md](./PORTAL-TRANSFORMA-PLUS.md) guarda UX. A ordem de implementação está só em [ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md). As fases PI e A–I não são calendário.

## 11. Busca residual

Classificação desta passagem. Não é prova de ausência em produção.

| Termo | Onde apareceu | Classe |
|---|---|---|
| SIPOC, Lean, Ishikawa, five whys, CTP, TDR, SWOT, AS-IS, TO-BE | `guide.py` e playbook editorial | CURRENT como método; TARGET como resultado persistido |
| `decomposition_id` | ADR de decomposição | CURRENT, opcional |
| `impact_effort` / matriz | Playbook 21 e entidade | CURRENT |
| `measurement` | entidade da revisão | CURRENT como valor; não é definição de KPI |
| `get_process_context` | serviço de contexto | CURRENT parcial |
| escopo de processo | `ProcessoEscopoRepository` | CURRENT organizacional; não é SIPOC |
| plano de ação | playbook TÉO (texto) e quality-action-plans | HISTORICAL/outro contexto. Entidade TM = TO_INVENTORY |
| cadeia de valor / arquitetura corporativa | este documento | TARGET |
| finding / diagnostic / root cause no TM | não achado como agregado | TO_INVENTORY |
| KPI do dashboard MFE | rótulo de UI do ROI | CURRENT de cálculo; não é Indicator Definition |
| «Macroprocesso» na UI do Playbook 20 | rótulo do mestre | DRIFT de vocabulário em relação à arquitetura corporativa TARGET |

## 12. Gates e o que este passe não faz

Não há migration, tabela, model, endpoint, tool, Action, OpenAPI, Keycloak, RBAC, frontend nem runtime alterados por este arquivo.

```text
ARCHITECTURE TARGET = DOCUMENTED
CAPABILITY GAP MAP = DOCUMENTED
DOMAIN TARGET = DOCUMENTED
MCP/ACTIONS EXPOSURE STRATEGY = DOCUMENTED
ROUTE BUDGET POLICY = DOCUMENTED
IMPLEMENTATION = NOT AUTHORIZED
```
