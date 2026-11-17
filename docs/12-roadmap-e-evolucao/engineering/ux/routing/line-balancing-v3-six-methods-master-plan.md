# EVA / Portal Engenharia — Plano Mestre V3: seis métodos de balanceamento de linha

> **DECISÃO VINCULANTE MAIS RECENTE — GREENFIELD DELPI LINE BALANCE STUDIO (2026-11-17):** a ferramenta do ecossistema Minha DELPI será **implementada do zero em `plugins/delpi-line-balance-studio/`**. **Não extrair, copiar, adaptar, importar nem refatorar componentes específicos, modelos, estados ou helpers** da implementação de balanceamento/Yamazumi de `plugins/engineering`. A V3 de Processos/Roteiro é LEGACY preservado, não base de implementação nem referência de prompt. **Permitidos apenas** componentes públicos genéricos do `@delpi/plugin-ui`, contratos oficiais independentes e padrões corporativos transversais. O primeiro consumidor do Studio será o Portal Engenharia após validação independente. [Contrato greenfield e docs](../../../../../plugins/delpi-line-balance-studio/README.md). Esta instrução **prevalece** sobre trechos anteriores do presente documento que falem em extração/reuso da V3.


> **DECISÃO DE PRODUTO POSTERIOR — 2026-11-17 / NOVO HOST DE PROCESSOS:** O catálogo de **seis métodos (M1–M6) permanece integralmente válido** e o **Yamazumi (M5) continua sendo o primeiro a detalhar/implementar**. O destino de novas implementações deixa de ser a aba `Ficha do Produto → Roteiro` e passa a ser **Portal Engenharia → card/seção `Processos` → página própria `Processos` → ferramenta `Balanceamento de linha`**. A aba Roteiro existente permanece funcional, sem novos desenvolvimentos de métodos, sem remoção, regressão ou migração automática nesta decisão. A V2 da página de produto é referência histórica/reuso técnico, **não o novo host de UI**. **Status:** `TARGET / ARCHITECTURE_DECISION_REQUIRED` para formalizar entrada no catálogo/rota, contratos e autorização; nenhuma implementação nesta atualização.

**Data da decisão de produto:** 2026-11-17  
**Estado:** `TARGET / PLAN_APPROVED_BY_PRODUCT_DIRECTION / IMPLEMENTATION_NOT_AUTHORIZED_BY_THIS_DOCUMENT`  
**Sequência dirigida pelo Product Owner:** primeiro **Método 5 — Yamazumi interativo**, depois os demais métodos de forma incremental, mantendo todos registrados desde agora. A numeração 1–6 identifica o catálogo funcional, **não a ordem de execução**.  
**Owner UX/workflows:** Portal Engenharia. **Owner algoritmos/cálculos e contratos:** domínio Engenharia/EVA, com aprovação de Engineering owners. **Fonte canônica:** API-DELPI/roteiro oficial. **Plugin UI:** owner de gráfico, componentes e design system. **Identidade/autorização:** Keycloak/Core. **Status de execução:** `TEST_NOT_RUN`.  
**Propósito desta entrega documental:** preservar o contexto completo dos seis métodos e definir um primeiro detalhamento de Yamazumi no MESMO documento mestre; o host alvo atual é **Processos** (não a aba Roteiro da ficha). Não alterar frontend, API, MCP, solver, autenticação ou deploy.

## 0. Referências, precedência e evidência

- [Routing Study Workspace V2 — Visual Contract](./routing-study-workspace-v2-visual-contract.md): **referência legada da Ficha do Produto** para densidade, cards e estado de estudo. **Não usar como autoridade para hospedar novas ferramentas dentro da aba Roteiro**; o host novo é Processos.
- [Routing Study Session State](./routing-study-session-state-contract.md): estudos locais isolados e recuperáveis via `sessionStorage`; limpar/nova análise com confirmação.
- [Routing Study V2 Acceptance](./routing-study-v2-acceptance.md): experiência, auth, testes e deployment.
- Domínio existente: `engineering-api/engineering_app/domain/routing/line_balance.py`; consumidores atuais `POST /v1/products/{code}/line-balance` e `analyze(routing.line_balance)`.
- Guia de domínio: `engineering-api/engineering_app/content/eva_engineering_knowledge.json`, `routing.balance_guide` / `routing.guided_analysis`.
- UI existente/histórica, que deve permanecer sem alteração nesta fase: `plugins/engineering/src/features/products/routing/ProductRoutingTab.tsx`, `PostConfigurator.tsx` (confirmar HEAD). Reutilizar apenas contratos/serviços estáveis via boundary, sem dependência de componente interno da página de Produto.
- **Catálogo de cards PROVEN:** `plugins/engineering/src/content/engineeringRouteCatalog.ts` define `ENGINEERING_CATALOG` com seções `work/Trabalho`, `insights/Análises` e `support/Suporte`. Novo `processes/Processos` é **TARGET**, com registro de destino e permissão sujeito a inventário do roteador e Core RBAC, não autorização criada por este documento.
- Gráficos corporativos: `@delpi/plugin-ui` `ChartViewShell` + `MultiTypeSeriesChart`, integrados na Engenharia para a V2, com referência Comercial `AnalyticsRolSeriesChart.tsx`.

**Fatos verificados no domínio, não promessa de método avançado:** agrupamento de linhas repetidas por componente em operações únicas; estágio separado `(product_code,bom_level)`; takt = tempo disponível/demanda; conteúdo de trabalho de tempos oficiais; setup por LOTE somente com `batch_size`; mínimo teórico `ceil(work_content/takt)`; gargalo candidato; teste teórico `num_stations`; cenário `first_fit_decreasing` sem precedências, trabalhadores ou recursos verificados. Uma operação individual acima do takt pode ser colocada num posto pelo FFD; isso **não comprova viabilidade**. A saída FFD é `SIMULATION`, não roteiro executável.

**Classificações:** `OBSERVED` (roteiro autorizado), `PROVIDED` (inputs usuário), `CALCULATED` (saída determinística contratada), `SIMULATION / DRAFT_LOCAL` (hipóteses), `UNKNOWN` (não comprovado). Progresso: `PROVEN / TO_INVENTORY / PLANNED / TARGET`. Execução: `PASS / FAIL / PENDING / INCONCLUSIVE / TEST_NOT_RUN / STALE_EVIDENCE`.

## 0A. Decisão de produto — Portal Engenharia / Processos como host

**Visão:** concentrar ferramentas de **Engenharia de Processos** em uma área autônoma do Portal Engenharia. Não limitar mapeamento, melhoria e balanceamento à ficha de um único produto. O usuário entra pelo **quarto card de seção `Processos`**, ao lado dos existentes **Trabalho, Análises e Suporte**. Um mesmo espaço crescerá com novas ferramentas, sem adicionar abas internas à Ficha do Produto.

**Proposta de navegação/UX (TARGET):**
```text
PORTAL ENGENHARIA / INÍCIO
[Trabalho]  [Análises]  [Suporte]  [Processos]  <-- novo card de seção
                                        |
                                        v
PORTAL ENGENHARIA / PROCESSOS  (página própria)
"Engenharia de Processos — Ferramentas"
[Balanceamento de linha]              <-- PRIMEIRA FERRAMENTA, ativa quando entregue
[Mapeamento de processos]             <-- FUTURO / sem ação fingida
[Melhoria de processos]               <-- FUTURO / sem ação fingida
[Outras ferramentas de processos]     <-- FUTURO conforme owner e roadmap
                                        |
                                        v
PROCESSOS / BALANCEAMENTO DE LINHA (workspace própria, scrollável)
[Código do produto: __________] [Buscar roteiro] [Filial] [Estágio]
[Estado da consulta autorizado / operação ausente / erro]
[Operações oficiais, CTs, recursos, tempos, limitações de fonte]
[Dados produtivos: demanda, turno, pausas, lote]
[Métodos M1–M6: catálogo sem prometer os não implementados]
[YAMAZUMI: postos hipotéticos + gráfico carga×takt + cenários]
[Resultados, comparação e exportação / provenance]
[Rascunho nesta aba] [Novo cenário] [Limpar estudo]
```

**Entrada desacoplada do produto:** o usuário pode abrir a ferramenta **sem product code prévio**; informar código, acionar consulta autorizada ao roteiro oficial, selecionar filial e estágio, e iniciar estudo. Estados: sem produto, digitando, carregando, código inválido, produto não encontrado, acesso negado, roteiro vazio, roteiro disponível, seleção de estágio, estudo em edição, resultado/limitações. Não inferir filial/estágio ou executar cálculo sem contexto válido.

**Separação de responsabilidades:**
- Página `Processos` é hub/catálogo de ferramentas, não bounded context ou source of truth novo por si só.
- Ferramenta `Balanceamento de linha` é consumer legítimo do contrato existente de roteiros e motor determinístico, via BFF/domain API e live AuthZ; nunca acesso direto a banco de outros sistemas.
- **Não criar dependência runtime da página `ProductRoutingTab`**. Se houver lógica compartilhável, extrair componente/serviço neutro com owner, contrato, testes e Abstraction Gate; não importar internals da ficha.
- Integrar rota/catálogo ao Portal/Core conforme contratos atuais. `ENGINEERING_CATALOG` é **apresentação, nunca autorização**. Não inventar path, permission string, manifest ou app novo antes do inventário; se novo owner/boundary/authority for necessário, `ARCHITECTURE_DECISION_REQUIRED` à Coordination.
- Manter a aba Roteiro da Ficha do Produto **inalterada** nesta iniciativa, preservando seus recursos atuais. Não removê-la nem fazer redirect involuntário.
- O `sessionStorage` da nova ferramenta deve incluir **namespace/contexto de Processos** além de principal/produto/filial/estágio, para evitar colisões ou recuperação cruzada com a ficha do produto. Isolamento e revalidação de fonte/AuthZ continuam obrigatórios.
- A primeira release pode trazer o hub com o cartão `Balanceamento de linha` ativo, enquanto as outras famílias aparecem apenas como planejadas (ou não aparecem até existir design); não criar links ou botões inertes.

**Organização futura de ferramentas (TARGET, não escopo aprovado de implementação):** mapeamento de processos, documentação e fluxos, análise e melhoria, estudos de tempos e métodos, capacidade fabril, balanceamento, comparação de cenários, padronização de trabalho e ferramentas adicionais definidas pelos owners. A ideia de Processos como área não transfere ownership de Transformômetro/TÉO ou sistemas corporativos; interoperar por contratos oficiais.

**Checklist visual do hub:** novo card nativo `SectionRouteCard`/padrão real do Plugin UI, mesmo espaçamento, grid e light/dark dos cards atuais; página Processos com título, descrição e cards de ferramentas; workspace do Balanceamento em área própria com filtros/roteiro e Yamazumi sem navegação extra; desktop/tablet/390/320 e teclado. Referência do grid existente: `docs/12-roadmap-e-evolucao/engineering/24-home-r1-features-grid.md` (`auto-fit`), inspecionar o kit real antes de codificar.

**Critérios iniciais de aceite da migração de foco (PLANNED):** `PROC-01` card Processos em Início com permissão legítima; `PROC-02` página própria de ferramentas; `PROC-03` Balanceamento acessível sem abrir produto; `PROC-04` campo código + consulta oficial com loading/erro/forbidden; `PROC-05` seleção explícita filial/estágio e dedup; `PROC-06` todos seis métodos presentes no plano, primeiro Yamazumi; `PROC-07` V2 produto sem mudanças/regressões; `PROC-08` isolamento de drafts da ficha vs Processos; `PROC-09` cálculos no domínio e read-only; `PROC-10` HML e PROD somente após gates técnicos e Verify.

## 1. Catálogo completo dos seis métodos — visão executiva

| ID | Método/capacidade | Pergunta de Engenharia | Inputs principais | Resultado e visualização | Maturidade comprovada | Prioridade de entrega |
|---|---|---|---|---|---|---|
| **M1** | Análise de capacidade e takt | A linha atende a demanda? Onde há gargalos? | Roteiro, demanda, tempo disponível, pausas, lote | Takt, conteúdo, mínimo teórico, bottleneck, ops > takt; indicadores e gráfico | **PROVEN** como núcleo determinístico (ver contrato) | Reuso transversal / reforço de limites |
| **M2** | Balanceamento por carga: **FFD** e **Largest Candidate Rule (LCR)** | Como agrupar operações por tempo de ciclo? | Tempo por operação, takt e, para LCR válido, precedências/restrições | Proposta de alocação, cargas e folgas por posto, violações | **FFD PROVEN**, sem precedência; **LCR TARGET** | Depois de Yamazumi |
| **M3** | **Ranked Positional Weight (RPW / Helgeson–Birnie)** | Como alocar tarefas considerando sucessoras e precedências? | Grafo dirigido acíclico de precedências, durações, restrições | Pesos posicionais, ranking, estações, violações e eficiência | **TARGET** | Incremental posterior |
| **M4** | **Kilbridge–Wester** | Como balancear por níveis/colunas de precedência? | Grafo validado, durações, takt, restrições | Níveis de precedência, sequência de alocação, postos e ociosidade | **TARGET** | Incremental posterior |
| **M5** | **Yamazumi interativo** | Como distribuir carga de trabalho entre operadores/postos e visualizar excesso ao takt? | Operações oficiais, postos hipotéticos, tempos tipados, operadores, takt e vínculos de tarefa | Barras empilhadas por posto, linha de takt, carga, perdas/ociosidade com limites | **TARGET**; visual e draft V2 reaproveitáveis | **PRIMEIRA IMPLEMENTAÇÃO** |
| **M6** | Dimensionamento de recursos e cenários | Quantos operadores/máquinas/posições paralelas e que mix de organização é necessário? | Tempo manual/automático, recursos, disponibilidade, paralelismo, turnos, lotes, restrições | Capacidade efetiva, arranjos viáveis/candidatos, trade-offs e comparativo | **TARGET** | Após fundações validadas |

**Nota de taxonomia:** M5 é predominantemente um método visual de análise e melhoria (gráfico Yamazumi), **não um algoritmo que, sozinho, encontre uma alocação ótima**. M6 é uma família de dimensionamento/estudos de capacidade, não um único algoritmo. O catálogo é orientado ao trabalho de Engenharia, sem afirmar que seis itens são seis solvers equivalentes.

## 2. Especificação funcional por método

### M1 — Análise de capacidade e takt (baseline obrigatório)

**Objetivo:** medir ritmo exigido vs tempos oficiais e localizar limitações. **Inputs:** produto autorizado, filial/estágio, demanda inteira por período, duração do turno, pausas, lote opcional; postos somente se explicitamente fornecidos. **Cálculos atuais:** tempo produtivo = turno − pausas (prévia UX); takt = disponível/demanda pelo domínio; conteúdo = soma de operações únicas válidas; setup = horas×60/lote, apenas se lote informado; mínimo teórico = teto(conteúdo/takt), sem implicar viabilidade; candidato de gargalo = maior tempo efetivo. **Saídas:** KPIs, operações acima do takt, limitações, rastreabilidade, gráfico tempo×takt. **Gates:** não confundir takt com ciclo real, gargalo candidato com gargalo medido, `station_check.feasible` baseado apenas em soma média com uma alocação executável. **Status:** núcleo `PROVEN`, revisão semântica e hardening `PLANNED`.

### M2 — Heurísticas de alocação por carga (FFD / LCR)

**Objetivo:** construir propostas por tempo de ciclo, com regras explicitamente distintas. **FFD atual:** ordenar operações por tempo decrescente; inserir na primeira estação que comportar carga ≤ takt; sem grafo de precedência; quando operação > takt, o resultado deve ser sinalizado como violação/sem solução por essa hipótese, mesmo que código atual a coloque numa estação. **LCR pretendida:** lista de candidatas ordenadas por maior tempo, mas elegíveis apenas quando predecessoras/compatibilidades permitirem; regra de desempate determinística e tratamento explícito de operação maior que ciclo. **Inputs adicionais:** DAG de precedência validado, compatibilidade de recursos/postos, política de divisão de tarefas. **Saída:** alocação por estação, carga/ociosidade, lista de tarefas não alocadas, violações e método/versão. **UX:** alternador de heurística apenas após capability contratada, gráfico comparativo; nunca reclassificar FFD como precedência-aware. **Status:** FFD `PROVEN / REQUIRES_LIMITATION_DISPLAY`; LCR `TARGET`.

### M3 — Ranked Positional Weight / Helgeson–Birnie

**Objetivo:** priorizar tarefas pelo peso da própria duração + durações de sucessoras únicas no grafo. **Inputs:** operações únicas com tempos homogêneos, grafo completo e acíclico de precedência autorizado/proposto, restrições de recursos e ciclo alvo. **Cálculo esperado:** peso posicional de cada tarefa, ranking estável; atribuição apenas de tarefas elegíveis com todas predecessoras atendidas; respeitar takt e regras de recurso; explicitar empates. **Saídas:** tabela explicativa dos pesos, postos e tarefas atribuídas, carga/folga, violações, gargalo e rastreabilidade da precedência. **UX:** grafo de precedência + cards de método + gráfico de comparação. **Bloqueios:** sem precedências completas, não produzir RPW com suposta validade; oferecer cadastro **hipotético** de precedências e badge `PROVIDED / SIMULATION` quando autorizado. **Status:** `TARGET`.

### M4 — Kilbridge–Wester

**Objetivo:** criar colunas/níveis de tarefas a partir da rede de precedência, selecionar tarefas elegíveis e montar postos sob limite de ciclo. **Inputs:** DAG de precedência, tempos e restrições; regras formais de ordenação e desempate. **Saída:** matriz de níveis/colunas, sequência usada na atribuição, carga e ociosidade por estação e justificativa de tarefas não alocadas. **UX:** visual de precedência por colunas, gráfico de cargas por posto, comparação com RPW/LCR quando todos utilizarem a mesma base e regras. **Limitação:** heurística, não garantia de ótimo; incompletude ou ciclo no grafo → bloquear diagnóstico supostamente válido. **Status:** `TARGET`.

### M5 — Yamazumi interativo (**PRIMEIRO DELIVERY**)

**Objetivo:** permitir que a Engenharia visualize carga de trabalho **por posto e, quando houver base suficiente, por operador** em barras empilhadas, com linha do takt, e teste redistribuições manuais sem alterar o roteiro oficial. Yamazumi é um **instrumento visual**, não soluciona sozinho uma alocação tecnicamente viável.

**Entradas mínimas:**
1. Contexto autorizado de produto, filial e estágio (dados oficiais `OBSERVED`).
2. Operações únicas com IDs estáveis, descrição, CT, recurso e tempo padrão oficial. Não inventar tempo de operação ausente.
3. Demanda, turno, pausas → takt (parâmetros `PROVIDED`; cálculo no domínio existente ou prévia aritmética rotulada).
4. Postos hipotéticos do rascunho V2, com ordem, nome, operações associadas, operadores/posições quando explicitamente informados.
5. **Categorias de tempo** por elemento: manual, automático, caminhada/movimentação, espera, setup etc. **Somente se conhecidas/fornecidas**; se roteiro fornecer apenas tempo agregado, renderizar **uma única categoria `Tempo padrão agregado — composição desconhecida`**, nunca decompor por regra fictícia.
6. O registro de uma operação em vários postos exige política explícita de fracionamento, replicação ou paralelismo; **não duplicar/somar tempo sem identificar a hipótese**.

**Interações V1 Yamazumi desejadas:**
- Escolher cenário A/B/C/D dentro dos limites V2 existentes; uma configuração por cenário com contextos idênticos.
- Adicionar, renomear, remover e ordenar postos hipotéticos; seleção múltipla de operações vindas do roteiro.
- Mover atribuição de operação entre postos **quando integridade e restrições declaradas permitirem**; manter alternativas por teclado. Não oferecer drag-and-drop sem fallback acessível.
- Selecionar período/demanda/turno/pausas, opcional lote para setup, unidade s/min; não confundir setup do lote com tempo peça.
- Tooltip: posto, operação, CT, tempo, categoria, classificação (OBSERVED/PROVIDED), lote/assunções.
- Barras empilhadas por posto com **linha de takt**; realce `carga > takt`, `≤ takt`, desconhecido, postos sem tarefa e operações não atribuídas.
- Legenda por categoria somente quando tipagem efetiva existir; usar cores sem depender apenas da cor (labels/ícones).
- Botão `Reorganizar` atua **somente no DRAFT local**, nunca atualiza roteiro/ERP.
- `Novo cenário` preserva anterior; `Limpar estudo` mantém confirmação e escopo da V2.
- Restaurar após F5 via `sessionStorage` atual, schema versionado e revalidação da fonte; invalidar comparações se parâmetros ou revisão mudarem.
- Exportação pelo Plugin UI (CSV/Excel/PDF) com unidade, fonte, cenário, parâmetros, advertências e `DRAFT_LOCAL/SIMULATION`.

**Indicadores propostos e seus limites:**
- Takt calculado, tempo de ciclo **alvo** (não ciclo real medido).
- Carga agregada **hipotética** por posto a partir de atividades atribuídas, usando tempos que a fonte efetivamente suportar.
- Diferença de carga hipotética vs takt e postos com excesso, **sem afirmar capacidade viável se tarefas dependem de operadores/máquinas/precedência não verificados**.
- Conteúdo total de trabalho e mínimo teórico podem ser apresentados do resultado M1, com label de método; não transformar mínimo teórico em efetivo.
- Eficiência/ociosidade por operador só quando houver contrato para tratar simultaneidade, quantidade de operadores e tempos manuais/automáticos; caso contrário `UNKNOWN`.
- Se alguma atividade não tiver tempo, não usar zero silencioso, não declarar otimização.

**Wireframe estrutural (TARGET, desktop) — NOVO HOST PROCESSOS:** consultar `§0A` para entrada por card, hub, busca de produto e estados. Abaixo está a **ferramenta Balanceamento dentro de Processos**, não a aba Roteiro da ficha:

```text
PORTAL ENGENHARIA > PROCESSOS > BALANCEAMENTO DE LINHA
[Produto/código __________] [Buscar roteiro] [Filial v] [Estágio v]
[Resumo oficial de operações / CTs / recursos / tempos após consulta]
------------------------------------------------------------------
ESTUDO DE BALANCEAMENTO [Salvo nesta aba | Recuperado]
[Demanda] [Turno] [Pausas] [Lote] [Takt prévia]
Métodos M1–M6 (catálogo contextual); M5 YAMAZUMI primeiro
[Cenário A v] [Novo cenário] [Limpar estudo]
------------------------------------------------------------------
ORGANIZAÇÃO DOS POSTOS             YAMAZUMI — CARGA × TAKT
+------------------------------+   +-------------------------------------+
| [01] Posto 01 [editar ↑ ↓ ×] |   | tempo/peça [s|min]                  |
| [operações oficiais +]       |   |   ─ ─ ─ takt alvo                   |
| [CT/recursos vinculados]     |   | ████  ███  ██  por posto           |
| [operadores? paralelos?]     |   | [Tipo] [Unidade] [Séries] [Exportar]|
| [02] Posto 02 ...            |   | legendas honestas e limites        |
| [+ Adicionar posto]          |   +-------------------------------------+
+------------------------------+
[Operações sem posto] [Acima do takt] [Restrições não verificadas]
[Diagnóstico suportado] [Comparar cenários] [Limitações e provenance]
```

**Mobile 390/320:** painel de postos em coluna; Yamazumi abaixo com viewport responsivo/scroll gráfico permitido quando necessário; toolbar do Plugin UI compacta; nunca scroll horizontal da página inteira. Sem duplicar barra de topo.

**Comportamento inicial para um roteiro de operação única:** uma barra/indicador compacto, posto opcional não auto-inferido de CT, mensagem que reorganização tem efeito limitado até múltiplas tarefas/elementos. **Não fabricar fracionamento de uma operação agregada** para parecer que existe ganho de balanceamento.

**Proposta de modelo de domínio (NÃO contrato vigente):** operação oficial identificada + edição local de atribuições; elemento de trabalho com `id, operationRef, timeMinutes, timeCategory, origin, precedenceRefs?`; posto hipotético com `id, name, order, operatorCount?, equipmentRefs?, parallelPositions?, assignmentRefs[]`; scenario com `sourceRevision/fingerprint, parameters, timeUnit, allocation, caveats`; output do solver/analyzer com `stationLoads, unassigned, overTakt, conflicts, unsupportedRules, dataClass, methodVersion`. Não implementar contratos novos sem owner e decisão.

**Fases sugeridas para M5, cada uma verificável:**
- **Y0 (inventário/gate):** RQ, dados de tempo/operadores, identidade de operação, capacidade do motor, UI kit, fontes; decidir se a primeira versão pode usar apenas agregado. Registrar `ARCHITECTURE_DECISION_REQUIRED` se novo contrato de domínio.
- **Y1 (UX e dados honestos):** wireframe high fidelity aprovado, barra única agregada quando necessário, linha do takt, integração em página V2, read-only e estado local; sem inferência de tempo manual.
- **Y2 (configuração interativa):** seleção/reordenação de operações oficiais com validação de duplicidade/sem atribuição e cenários; persistência de sessão, reset, comparação; ausência de backend solver não pode ser mascarada.
- **Y3 (cálculo governado, se autorizado):** contrato explícito de avaliação de alocação e restrições, implementação domínio/adapters sem reimplementar no MFE, testes, API e output de viabilidade qualificada.
- **Y4 (HML→PROD):** Playwright autenticado, Verify independente, comparação visual, mobile, dark/light, SSO/RBAC, deploy governado, smoke humano quando necessário.

**Critérios de aceite iniciais de Yamazumi:**
`YAM-01` usuário entende que é estudo hipotético; `YAM-02` operações oficiais e tempos com provenance; `YAM-03` gráfico de barras por posto + takt responsivo; `YAM-04` categorias desconhecidas não inventadas; `YAM-05` mover tarefas altera só rascunho; `YAM-06` sem duplicar tarefas ou violações ocultas; `YAM-07` atualização F5 restaura estudo isolado; `YAM-08` Limpar cancela/confirma; `YAM-09` tempo sem dado = UNKNOWN; `YAM-10` não proclamar viabilidade física; `YAM-11` dark/light e exportações corporativas; `YAM-12` acessibilidade teclado/aria; `YAM-13` E2E com SSO e regressão V2; `YAM-14` Verify com resultado verdadeiro (INCONCLUSIVE não vira PASS); `YAM-15` deploy HML seguido de PROD somente após gates; `YAM-16` roteiro e balanceamento oficiais inalterados.

### M6 — Dimensionamento de operadores, equipamentos e cenários de capacidade

**Objetivo:** planejar recursos humanos, equipamentos e paralelismo necessários para demanda e restrições. **Dados exigidos:** decomposição manual/automática, simultaneidade permitida, ciclo máquina, operadores por atividade, quantidade/disponibilidade de equipamentos, eficiência/perdas explicitadas, setup, lote, yield/retrabalho quando pertinente e regras de precedência. **Análises futuras:** capacidade por recurso, gargalo de máquina, carga do operador, combinações candidatas, impacto de 1 operador/máquina/turno extra; análise de sensibilidade. **UX:** comparador de cenário de recursos e possíveis trade-offs; gráficos do Plugin UI; nunca usar número de CTs como número de postos/equipamentos físicos. **Status:** `TARGET`; não inferir capacidades nem eficiência/OEE.

## 3. Roadmap por entregas (decisão de sequência)

| Ordem de execução | Entrega | Método(s) | Pré-condição / gate |
|---|---|---|---|
| **1 — AGORA / NEXT** | **Yamazumi interativo**: contrato específico, UX aprovada, barras posto×takt, organização DRAFT, persistência e testes | M5 com reuso M1 | Inventário de tempos e método de avaliação, limites honestos, decisão de owner se criar análise de alocação |
| **2** | Hardening do FFD e proposta de LCR com precedências | M2 | Contrato de grafo/violação e classificação de viabilidade |
| **3** | Grafo de precedência + RPW | M3 | Dados/grafo autorizados e heurística auditável |
| **4** | Kilbridge–Wester + comparador | M4 | Mesma base e testes de precedência |
| **5** | Dimensionamento avançado de recursos | M6 | Tempos tipados e restrições de equipamento/operador |
| **Contínuo** | Diagnóstico de capacidade, takt e cenários básicos | M1 | Reuso da capacidade `PROVEN`; corrigir limites sem quebrar REST/MCP |

A ordem após Yamazumi é proposta de roadmap, não compromisso automático de execução; cada método requer RQ/AC e decisão owner quando aplicável. Os **seis permanecem no catálogo** mesmo se a execução for reordenada.

## 4. Regras transversais de modelagem

1. **CT ≠ posto físico ≠ operador ≠ equipamento.** Nomes/contagens e associações explícitas, sem dedução automática.
2. **Grafo de precedência é dado próprio**: sequência numérica no roteiro pode ou não provar precedência; não inventar arestas a partir da aparência do card ou do código da operação.
3. **Etapas BOM separadas:** produto e `bom_level` não se misturam numa mesma linha sem escopo fabril/integração definida.
4. **Tempo manual vs automático:** com dados agregados, uma única classe `Agregado desconhecido`. Não dividir 50/50 nem atribuir ocioso fictício.
5. **Operação > takt:** alerta obrigatório e distinção entre inviabilidade do posto único, paralelização hipotética e capacidade física não validada.
6. **Métricas:** mínimo teórico não é dimensionamento; workload/estação não é ciclo real; Yamazumi não é solver; ganhos só quando premissas explicitadas.
7. **Métodos comparáveis:** mesma demanda/turno/filial/estágio/revisão/tempos/restrições e critérios; caso contrário comparação é qualitativa com advertência.
8. **Cenário local:** `sessionStorage` em escopo autorizado; refresh restaura rascunho mas nunca revoga live AuthZ; `Limpar estudo` não altera ERP.
9. **Fronteira do frontend:** MFE só interpreta/apresenta; cálculos especializados no domínio aprovado; REST e MCP adaptadores de contrato, não authorities.
10. **Testes:** unidade/invariantes, propriedades de algoritmo, casos sem tempo, op > takt, setup/lote, precedência cíclica, multi-stage, auth, armazenamento local e auditoria de provenance.

## 5. Wireframe de navegação dos métodos (visão alvo, sem seis tabs)

Na **ferramenta Balanceamento de linha dentro da página Processos**, usar um **seletor de objetivo/método** contextual no workspace scrollável — sem terceira top bar e **fora da Ficha do Produto**. Exibir os seis itens no catálogo com descrição, inputs necessários e estado:
- `Disponível` apenas quando suporte comprovado (M1/FFD limitado).
- `Em planejamento` para RPW, Kilbridge–Wester, recursos e outros não implementados.
- `Em desenvolvimento` para Yamazumi **somente quando execução iniciar e houver evidência**; documentação isolada não autoriza alegar implementação.
- Ao selecionar método não suportado, mostrar explicação e requisitos, sem CTA de cálculo inerte que pareça funcional.
- Ao selecionar Yamazumi implementado, revelar área de postos + gráfico empilhado na **mesma página própria de Balanceamento em Processos**, após buscar o roteiro oficial por código. Preservar os resultados M1 no novo consumer e não alterar a aba Roteiro da ficha.
- Evitar seis formulários simultâneos e não esconder contexto de produção ao mudar método.

## 6. Contratos e decisões antes do Yamazumi

**G0 obrigatório — inventário:** confirmar, com owners e fonte, existência de: IDs estáveis de operação, categoria de tempo, precedência, recursos/operadores, condições reais de simultaneidade; validar esquema de `RoutingStudyDraftV2` e limites de cenários; levantar componentes de barras empilhadas + referência de takt na versão corrente do Plugin UI.  
**Gate de extensão:** se novo cálculo/solver, especificar request/response, erros, validações, AuthN/AuthZ, compatibilidade, limites, observabilidade, idempotência (se write), provenance e postcondition. `ARCHITECTURE_DECISION_REQUIRED` em mudança de owner, source of truth, bounded context ou authority.  
**Sem publish:** todos os cenários iniciam DRAFT; owner de Engenharia aprova quaisquer alterações reais.  
**Verify:** evidência independente; incidente conhecido de auth do verificador pode produzir `INCONCLUSIVE`, não `PASS`.  
**HML→PROD:** apenas task futura autorizada e após gates, smoke autenticado e rollback.

## 7. Próximo passo permitido e status

**Próxima task sugerida:** `EVA-PROCESSES-HUB-YAMAZUMI-V3-CONTRACT-AND-WIREFRAME-01` — detalhar o quarto card `Processos`, catálogo/rota legítimos, nova página própria, busca de roteiro por produto, e a experiência de Yamazumi com postos/tempos/estados antes da implementação. **Não desenvolver novas features na aba Roteiro da Ficha do Produto.**

**Este commit é somente PLANO:** nenhum dos métodos M3–M6 foi implementado aqui; Yamazumi ainda é `TARGET`. A V2 da Ficha do Produto **deve permanecer em produção sem alteração por esta entrega**; o trabalho futuro será na nova área `Processos`.

**Regras de atualização deste documento:** preservar as seis entradas, seus IDs e a decisão `Yamazumi first`. Cada entrega futura acrescenta link para contrato/evidência/sha/teste e atualiza somente o status verificado da respectiva capacidade.
