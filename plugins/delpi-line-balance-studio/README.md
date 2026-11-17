# DELPI Line Balance Studio

**Decisão de produto:** 2026-11-17 — desenvolvimento autorizado pelo Product Owner.  
**Status:** `AUTHORIZED / TARGET / IMPLEMENTATION_NOT_PROVEN`. Esta pasta inicia a **identidade e o contrato de escopo** da ferramenta; não contém neste commit uma aplicação executável ou build/deploy.  
**Local proposto no monorepo:** `plugins/delpi-line-balance-studio/`. **Nome de produto:** **DELPI Line Balance Studio**.  
**Primeiro consumidor:** `plugins/engineering` > Processos > Balanceamento de Linha. **Outros consumidores:** portais e ferramentas Minha DELPI, sujeitos aos contratos de integração e AuthZ existentes.  
**Tracker da versão anterior:** [Issue #250](https://github.com/roberiooliveiradev/delpi-central/issues/250).  
**Plano mestre de métodos:** [V3 — Seis métodos, Yamazumi primeiro](../../docs/12-roadmap-e-evolucao/engineering/ux/routing/line-balancing-v3-six-methods-master-plan.md).

## 1. Objetivo do produto

Uma ferramenta única, **reutilizável e independente da Ficha do Produto**, para criar, importar, analisar e comparar estudos de balanceamento e organização de linhas. O usuário escolhe o método no próprio Studio, com uma experiência **clean** baseada em visualização e tabela do **mesmo estado de estudo**. O Studio será consumido pelo Portal Engenharia primeiro, sem atrelar seu núcleo a Keycloak, API-DELPI, paths, RBAC ou CSS do host.

Inspirar-se nas interações úteis de Yamazumi comerciais (clareza visual, montagem de postos, comparativos) e editores tabulares, **sem copiar código, assets ou identidade visual de terceiros**.

## 2. Catálogo permanente de métodos

| ID | Método/capacidade | Situação do motor atual | Ordem |
|---|---|---|---|
| M1 | Diagnóstico de capacidade, takt, conteúdo e gargalos | `PROVEN` no domínio existente, via contrato oficial | Base transversal |
| M2 | FFD / Largest Candidate Rule | FFD limitado `PROVEN`; LCR `TARGET` | Incremental |
| M3 | Ranked Positional Weight (RPW) | `TARGET` | Incremental |
| M4 | Kilbridge-Wester | `TARGET` | Incremental |
| **M5** | **Yamazumi interativo** | Gráfico/postos V3 existentes no Portal Engenharia; extração V4 `TARGET` | **PRIMEIRO** |
| M6 | Dimensionamento de recursos, operadores, paralelismo e cenários | `TARGET` | Incremental |

M5 é uma **técnica de visualização e análise**, não um solver automático. M6 é um grupo de capacidades de dimensionamento, não um único algoritmo. Métodos sem contrato válido não recebem botões de execução inertes.

## 3. Distribuição e fronteiras — decisão de produto, implementação a inventariar

- **Studio**: ferramenta completa reutilizável (entrada de estudo, editores, visual e tabela, cenários, presets e seleção de métodos). O primeiro objetivo é extrair do Portal Engenharia **sem duplicar** componentes nem cálculos. Reuso real entre consumidores é o critério para a API do Studio.
- **`@delpi/plugin-ui`**: design system e componentes genéricos (cards, controls, tabelas, `ChartViewShell`, `MultiTypeSeriesChart`, exportação, drag/drop genérico se necessário). **Não colocar regras de cálculo ou semântica de Engenharia dentro do kit visual.**
- **Domínio Engineering/EVA**: owner das fórmulas, validação de método, precedência, modelagem de recursos e interpretação de viabilidade; REST/MCP são adapters, não autoridades.
- **Ports/adapters por consumer**: `loadOfficialRouting`, `runBalanceAnalysis`, `loadAuthorizedContext`, `exportStudy`, `storeLocalDraft` definidos por contratos neutros, sem SDK específico no Studio.
- **Core/Keycloak/Portal**: AuthN/AuthZ e navegação; nenhum token/segredo exposto aos artefatos ou logs. Nunca presumir que o `frontend` concede acesso.
- **Engenharia**: owner técnico de aprovação e publicação de processos. Studio gera `DRAFT_LOCAL/SIMULATION`, não roteiro oficial.

**Abstraction Gate aplicado em implementação:** reutilizar `shared-libraries.manifest.json` e convenções reais de bibliotecas/MFE; definir a forma de consumo (biblioteca ou remote) com evidência, não cadastrar prematuramente novo manifest ou pacote npm. A autorização de produto permite avançar com a pasta e implementação. Mudança de source of truth, ownership de domínio, bounded context ou autoridade técnica permanece um evento `ARCHITECTURE_DECISION_REQUIRED` para Coordination.

## 4. Experiência V4 — simples no início, aprofundada sob demanda

### A. Criar estudo
- Fonte: **produto oficial** (busca código/filial/estágio e roteiros via adapter); **processo manual** (operações `PROVIDED/DRAFT_LOCAL` sem código de produto); **importar dados** (planejado após definição do formato e validações).
- Permitir enriquecer roteiro oficial com atividades hipotéticas, **sem misturar origem na apresentação**.
- Campos avançados colapsados. Estado sem dados amigável e CTA claro.

### B. Editor de operações
- **Visual / Tabela** compartilham o mesmo estado tipado: criar, editar, duplicar como hipótese distinta, reordenar, remover, atribuir a posto, filtrar e selecionar tarefas.
- Edição em grade com `Adicionar operação`, linhas editáveis, validação de tempo/unidade, categoria e proveniência; operações oficiais nunca são alteradas na fonte.
- Drag-and-drop quando seguro, com alternativa completa por teclado/botões.
- Elementos de trabalho opcionais para detalhar uma operação; tempos manual/automático/espera só quando fornecidos ou observados, nunca gerados por inferência.

### C. Condições de produção
- Turno por **início/fim de relógio** OU **duração direta em minutos**; suportar mais de uma pausa, com início/fim, adicionar/remover, validação de sobreposição, intervalo fora do turno, virada de dia e caso multidiário explícito.
- Exibir **tempo bruto, pausas totais, tempo produtivo e prévia do takt** em feedback imediato. Entrada de demanda por período com stepper/edit, lote e número de postos com incrementos; preservar entrada precisa (sem depender apenas de slider).
- Turnos/padrões oficiais só mediante fonte e contrato disponíveis; caso contrário `PROVIDED` e presets explicitamente editáveis.

### D. Yamazumi e postos
- Postos hipotéticos configuráveis; tarefas associadas; gráfico de carga × takt; barras agregadas ou empilhadas **apenas quando categorias de tempo reais/fornecidas existem**; legenda, tooltip, unidades, exportação.
- Arrastar operações entre postos e/ou selecionar destino, com validação de duplicidades e operações não atribuídas; não inferir fracionamento/paralelização por CT ou número de operadores.
- Sincronização tabela ↔ cards ↔ gráfico, cenários A/B e comparação **antes/depois** em contextos compatíveis.
- Proteger contra falsos ganhos: tempo > takt, precedência não verificada, tempo sem valor, setup por lote e capacidade física desconhecida.

### E. Uso por outros consumidores
- O Studio recebe `source adapters`, `analysis adapters`, autorização/contexto, tema e callbacks.
- Host escolhe como navegar e de onde obter os dados; Studio não importa `features/products/routing` nem `httpClient` do Portal Engenharia.
- Persistência temporária é adapter, namespace isolado por host/usuário/contexto/versionamento, com revalidação live AuthZ.

## 5. Contratos mínimos candidatos (TARGET, revisar no HEAD)

```text
StudySource = OFFICIAL_ROUTING | MANUAL | IMPORTED
StudyOperation = { stableId, sourceRef?, stageRef?, description, durationMinutes?,
                   timeCategory?, origin, precedenceRefs?, resourceRefs? }
StudyStation = { id, name, sequence, assignmentRefs[], operatorsHypothesis?,
                 equipmentHypothesis?, notes? }
StudySchedule = { entryMode: CLOCK|MINUTES, start?, end?, grossMinutes?,
                  pauses[], period, timeZone?, overnightPolicy? }
StudyScenario = { id, methodId, sourceFingerprint?, inputs, operations,
                  stations, schedule, caveats, version }
AnalysisResult = { method, version, dataClass, measures, violations,
                   missingFields, caveats, sourceFingerprint? }
```

Sem declarar esse pseudocontrato como DTO atual. O Studio não calcula viabilidade física: operações matemáticas de prévia de UI precisam ser rotuladas e teste de domínio definitivo fica no owner competente.

## 6. Estrutura alvo de pastas (não arquivos já implementados)

```text
plugins/delpi-line-balance-studio/
  README.md                         # ESTE contrato de direção de produto
  src/
    app/                            # composição do Studio independente do host
    model/                          # estado, IDs, tipos, validação estrutural
    ports/                          # contratos de fonte, análise, persistência
    methods/
      catalog/                      # M1 ... M6, status e capacidades reais
      yamazumi/                     # composição específica de M5
    features/
      study-origin/
      operation-editor/
      shift-editor/
      station-editor/
      scenario-comparison/
    ui/                             # composição específica; base no plugin-ui
    index.ts                        # API pública contratada
  tests/
  docs/
```

**Não materializar diretórios vazios nem criar scaffold sem inventário de scripts/build/federation.** A primeira implementação real deve analisar os consumers e definir o menor diff correto.

## 7. Estratégia de implementação

1. **G0 Inventário:** confirmar HEAD e status; verificar `plugins/engineering/src/features/processes/line-balancing/LineBalancingPage.tsx`, componentes ligados a `features/products/routing`, `plugins/shared-libraries.manifest.json`, Plugin UI, rotas e contratos de backend.
2. **Extração segura:** preservar a tela em produção; retirar acoplamentos ao Produto; introduzir API pública Studio, com primeiro consumidor real.
3. **Experiência de origem manual:** estudos sem produto, operações editáveis, validação e provenance; analisar contrato backend para estudos manuais antes de expor resultado determinístico.
4. **Turnos e pausas:** editor reutilizável e testes de borda (zero, overlaps, virada do dia).
5. **Visual + tabela sincronizados:** reutilizar tabela corporativa, Yamazumi e cards no mesmo estado e com edição consistente.
6. **Cenários:** comparação, recuperação de estado, isolamento; nenhuma gravação do processo oficial.
7. **Validação:** Unit/contract/component, HML real com SSO, dark/light, responsive, keyboard, Verify independente. `INCONCLUSIVE` nunca `PASS`.
8. **Deploy:** HML primeiro; produção só após gates e procedimento canônico; smoke produtivo autenticado, ou `PENDING_USER_SMOKE` explícito; rollback.

## 8. Critérios iniciais de aceite

- `STUDIO-01`: ferramenta importável sem depender do Portal Engenharia.
- `STUDIO-02`: Portal Engenharia é consumidor real por contrato público.
- `STUDIO-03`: M1–M6 presentes no catálogo; sem funcionalidades fictícias.
- `STUDIO-04`: estudo manual sem produto oficial.
- `STUDIO-05`: entrada oficial mantém consulta autorizada e provenance.
- `STUDIO-06`: operações e elementos manuais editáveis em tabela.
- `STUDIO-07`: Visual e Tabela permanecem sincronizados.
- `STUDIO-08`: editor de turnos e múltiplas pausas validado.
- `STUDIO-09`: postos e atribuições interativos, acessíveis.
- `STUDIO-10`: Yamazumi e comparação de cenários com caveats.
- `STUDIO-11`: `@delpi/plugin-ui` é fonte dos controles, gráficos e temas.
- `STUDIO-12`: cenários/DRAFT não alteram BOM, roteiro, CT ou dados oficiais.
- `STUDIO-13`: AuthZ live, isolamento por consumidor, nenhum segredo.
- `STUDIO-14`: aba Roteiro do Produto e V3 Processos sem regressões.
- `STUDIO-15`: testes, Verify e HML→PROD com evidências reais.

## 9. Regras de estado

`AUTHORIZED` significa permissão para construir, **não** software já implementado. Nenhum registro deste README concede AuthZ ao runtime nem altera owner de algoritmo. Progresso sempre vinculado a SHA + teste + outcome.
