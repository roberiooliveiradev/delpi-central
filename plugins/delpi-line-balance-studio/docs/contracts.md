# API pública do Studio v0.1

## Escopo do primeiro incremento

O Studio compõe estudos de Engenharia de Processos. O Portal Engenharia é o primeiro consumidor previsto. Outros portais podem usar o mesmo pacote. As APIs de Engenharia mantêm a autoridade sobre métodos de cálculo, viabilidade e dados oficiais. Esta versão é uma biblioteca TypeScript sem dependências de execução.

| Requisito | Critério de aceite |
| --- | --- |
| RQ-LBS-01 · Pacote independente | AC-LBS-01 · Compilar e importar pelo nome do pacote em um consumidor independente. |
| RQ-LBS-02 · Estudo manual | AC-LBS-02 · Criar rascunho sem SKU com operações, postos e cenários. Preservar tempos desconhecidos e operações não atribuídas. Recusar referências inválidas e atribuição duplicada no mesmo cenário. |
| RQ-LBS-03 · Condições de produção | AC-LBS-03 · Derivar minutos produtivos a partir de horários ou duração informada. Validar pausas múltiplas, sobreposições, limites e turnos noturnos. |
| RQ-LBS-04 · Catálogo único | AC-LBS-04 · Expor M1–M6 como planejados e indicar M5 como próxima implementação. |

## Contrato local

- `createManualStudy(input)` recebe um DTO interno tipado e devolve um snapshot independente do objeto de entrada ou erros com caminho e código. É determinístico, sem I/O, persistência, identificação de usuário ou efeitos externos. A pós-condição de sucesso é um estudo `MANUAL / DRAFT_LOCAL`, com cenários `SIMULATION`, tempos informados `PROVIDED` e tempos ausentes `UNKNOWN`. Atribuições fazem referência aos IDs locais e cada operação pode estar em até um posto por cenário.
- A entrada é um DTO fornecido por código consumidor. JSON externo, arquivos e respostas HTTP devem ser convertidos e validados por adapters próprios antes de cruzar esta fronteira. A forma retornada leva `schemaVersion: 1`. A raiz do pacote é a superfície pública do pacote `0.1.0`.
- `summarizeShift(input)` devolve minutos brutos, de pausa e produtivos, com origem `CALCULATED`, ou erros estruturados. Em modo relógio, horários são locais, sem data ou fuso, no formato `HH:mm`. O término anterior ao início representa a madrugada seguinte. Início e término iguais são ambíguos e inválidos. Pausas usam intervalos contíguos semiabertos e podem encostar. Em modo duração, pausas são minutos informados e o total pode abranger até 24 horas. Ambos os modos exigem tempo produtivo positivo.
- Tempo de operação informado em segundos finitos positivos, incluindo frações. Ausência explícita usa `null`. Demanda opcional em unidades por turno configurado e lote opcional em unidades. Quando preenchidos, ambos são inteiros seguros positivos. IDs e nomes precisam ter conteúdo. IDs de operações, postos e cenários são únicos em suas respectivas coleções.
- O catálogo expõe somente identificação, nome e disponibilidade. Esta versão não calcula takt, capacidade, precedência ou viabilidade. Resumos de turno são aritmética de calendário da simulação local.
- AuthN, AuthZ e auditoria do host são aplicáveis quando houver integração oficial. Aqui a biblioteca não recebe credenciais, não registra dados e não abre rede. O consumidor pode apresentar códigos de validação sem registrar o conteúdo do estudo.

## Folha de estilo do elemento

- `src/ui/studio.css` é a folha única do elemento: importa `@delpi/plugin-ui/native-controls.css` (estilos canônicos dos controles do kit) e declara apenas o layout do Studio. O elemento injeta o CSS processado via `<style>` no próprio shadow root — os hosts precisam resolver `*.css?inline` no bundler (Vite nativo; esbuild via plugin do `prepare-preview.mjs`) e o alias do especificador `@delpi/plugin-ui/native-controls.css`. Nenhum pedido de rede é feito para CSS e nenhum host deve fornecer uma folha paralela.

## Abstraction Gate

A API pública resolve o consumo do mesmo estado por futuros editores e portais. As únicas divisões são estudo manual, horário do turno e catálogo. Integrações de dados oficiais, persistência, métodos computacionais e UI serão contratados à medida que houver consumidores e requisitos concretos. A remoção do pacote é suficiente para reverter este incremento enquanto nenhum portal o importar.

## Entrada aditiva — roteiro oficial observado (RQ-LBS-12)

- **Owner / consumidores:** o contrato `StudioStudyInput` pertence ao Studio. Primeiro consumidor: MFE Portal Engenharia (`plugins/engineering`, rota `/apps/engineering/processes/line-balancing`), que converte `GET /v1/products/{code}/routing` em `ObservedStudyInput` uma única vez no adaptador do host.
- **Entrada:** `ObservedStudyInput` estende a forma manual com `source: "OBSERVED_ROUTING"`, `routing: { productCode, branchCode, stageId, stageLabel?, routeCode?, truncated? }` e `operations: ObservedOperationInput[]` (`id`, `name`, `durationSeconds | null`, `reference?`). A entrada manual `ManualStudyInput` permanece inalterada e retrocompatível (`source` opcional `"MANUAL"`).
- **Saída:** `createObservedStudy(input)` valida e devolve `ObservedStudy` (`source: "OBSERVED_ROUTING"`, `status: "DRAFT_LOCAL"`, operações `OBSERVED`/`UNKNOWN`, cenários `SIMULATION`). O elemento aceita a união `StudioStudyInput` no setter `study` e emite `study-change` no mesmo formato.
- **Erros:** mesmos códigos de `createManualStudy` + `REQUIRED` em `routing.productCode | branchCode | stageId`. Nunca converte roteiro observado em `MANUAL`.
- **AuthZ / limites:** a biblioteca não recebe credenciais nem abre rede; SSO, RBAC, HTTP, filial, estágio, cancelamento e truncamento permanecem no host. `routing.truncated` é exibido, não interpretado.
- **Compatibilidade:** aditivo — consumidores manuais existentes compilam sem alteração.

## Bancada unificada V4.1 — apresentação de resultados oficiais (RQ-LBS-13)

- **Owner / consumidores:** o contrato do elemento pertence ao Studio. O Portal Engenharia (`plugins/engineering`, rota `/apps/engineering/processes/line-balancing`) executa a análise oficial M1 pelo BFF/domínio autorizado e entrega ao Studio apenas o estado tipado de apresentação. Nenhum cálculo oficial migra para o Studio.
- **Propriedades novas do elemento `delpi-line-balance-studio`:**
  - `analysisState: StudioAnalysisState` — `{ phase: "idle" | "running" | "result" | "error", issues?, message?, result? }`. `result` carrega `taktMinutes`, `workContentMinutes`, `theoreticalMinStations`, `bottleneckOperation` (todos `CALCULATED` do domínio), `operationsMissingTime` (contagem de tempos `UNKNOWN`) e `stageCovered` (`false` → a resposta não cobriu o estágio do estudo). O Studio só renderiza; fases, erros e mensagens são resolvidos pelo host.
  - `officialOperations: readonly StudioOfficialOperation[]` — metadados do roteiro OBSERVED (`key`, `code`, `description`, `workCenter`, `resource`, `timeMinutesPiece`, `setupHours`) apresentados sob demanda pelo disclosure `Detalhes oficiais` na seção Operações. Somente consulta; ausência de tempo exibe `UNKNOWN`, nunca zero.
  - `draftSave: StudioDraftSaveState` — `{ label, tone }` do badge de persistência do rascunho local, resolvido pelo host.
  - `routingState: StudioRoutingState` (V4) — fases da busca de roteiro: `idle`, `searching`, `awaiting-stage` (com `branchOptions`/`stageOptions`), `error` com `message` do host.
- **Eventos novos (bubbles + composed, `CustomEvent`):**
  - `studio-analysis-run` — o usuário pediu a análise oficial M1; o host executa o BFF e devolve `analysisState`. Emitido apenas em estudo `OBSERVED_ROUTING`.
  - `studio-export` — `detail.format ∈ { "csv", "xlsx", "pdf" }`; o host produz o arquivo com o estudo/cenário vigentes.
  - `studio-clear-study` — pedido de limpeza; confirmação e descarte de persistência permanecem no host.
- **Eventos V4 inalterados:** `studio-origin-select`, `studio-routing-search`, `studio-routing-context`, `studio-manual-study`, `studio-origin-reset`, `studio-method-change`, `study-change`.
- **Ciclo de vida:** um novo `study` no setter reseta `analysisState`, `officialOperations`, `draftSave`, disclosures e confirmações — o host os republica por contexto. Resultados oficiais nunca vazam entre estudos.
- **AuthZ / limites:** SSO, RBAC, HTTP, persistência, formatos de arquivo e execução M1 permanecem no host/domínio. O Studio não abre rede, não estima resultados e não publica roteiro.
- **Compatibilidade:** aditivo — `analysisState`, `officialOperations` e `draftSave` são opcionais; hosts V4 continuam funcionais (M1 exibe diagnóstico local sem o bloco oficial, exportações fora do Studio seguem possíveis).
