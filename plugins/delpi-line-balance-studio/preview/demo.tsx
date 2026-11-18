import { createRoot } from "react-dom/client";
import { ActionButton } from "@delpi/plugin-ui/native-controls";
import { registerLineBalanceStudio, STUDIO_EVENTS, type LineBalanceStudioElement, type StudioRoutingState } from "../src/ui/studio.js";
import type { ManualStudyInput, ObservedStudyInput } from "../src/index.js";

registerLineBalanceStudio();
const studio = document.querySelector<LineBalanceStudioElement>("delpi-line-balance-studio")!;
const operations = [
  { id: "o1", name: "Separar componentes", durationSeconds: 30 },
  { id: "o2", name: "Preparar fios", durationSeconds: 28 },
  { id: "o3", name: "Posicionar terminais", durationSeconds: 36 },
  { id: "o4", name: "Crimpar terminais", durationSeconds: 48 },
  { id: "o5", name: "Montar conectores", durationSeconds: 33 },
  { id: "o6", name: "Fixar proteção", durationSeconds: 22 },
  { id: "o7", name: "Inspecionar conjunto", durationSeconds: 43 },
  { id: "o8", name: "Etiquetar embalagem", durationSeconds: null },
];

/* Metadados oficiais de demonstração — o host real os extrai do roteiro
 * OBSERVED; aqui apenas exercem o contrato `officialOperations`. */
const demoOfficialOps = operations.map((operation, index) => ({
  key: operation.id,
  code: `OP${String((index + 1) * 10).padStart(3, "0")}`,
  description: operation.name,
  workCenter: "900",
  resource: `R-${(index % 3) + 1}`,
  timeMinutesPiece: operation.durationSeconds != null ? operation.durationSeconds / 60 : null,
  setupHours: index % 2 === 0 ? 0.5 : null,
}));

const example: ManualStudyInput = {
  id: "demo",
  name: "Montagem de chicote piloto",
  operations,
  stations: ["Preparação", "Crimpagem", "Montagem", "Inspeção"].map((name, index) => ({
    id: `p${index + 1}`, name,
  })),
  scenarios: [
    { id: "a", name: "Cenário A · Inicial", assignments: ["p1", "p1", "p2", "p2", "p3", "p3", "p4"]
      .map((stationId, index) => ({ operationId: operations[index]!.id, stationId })) },
    { id: "b", name: "Cenário B · Alternativo", assignments: ["p1", "p1", "p2", "p3", "p2", "p3", "p4"]
      .map((stationId, index) => ({ operationId: operations[index]!.id, stationId })) },
  ],
  conditions: {
    shift: { mode: "CLOCK", start: "07:00", end: "15:00", breaks: [
      { start: "09:00", end: "09:15" }, { start: "12:00", end: "12:45" },
    ] },
    demandUnitsPerShift: 360,
    batchUnits: 60,
  },
};

/* Adaptador fictício do host — demonstra o contrato oficial: o Studio emite
 * intenções e o host devolve `routingState` + estudo OBSERVED. */
const observedStudy = (productCode: string, stage: string): ObservedStudyInput => ({
  id: `demo-${productCode}`,
  name: `Produto ${productCode}`,
  source: "OBSERVED_ROUTING",
  routing: {
    productCode, branchCode: "01", stageId: stage,
    stageLabel: `Estágio ${stage}`, routeCode: "R-01",
  },
  operations: operations.map((operation, index) => ({
    ...operation,
    reference: `OP ${String((index + 1) * 10).padStart(3, "0")} · CT 900`,
  })),
  stations: [{ id: "p1", name: "Posto 1" }, { id: "p2", name: "Posto 2" }],
  scenarios: [{ id: "a", name: "Cenário A", assignments: [] }],
  conditions: example.conditions,
});

let queriedCode = "";
const setRouting = (state: StudioRoutingState) => { studio.routingState = state; };

studio.addEventListener(STUDIO_EVENTS.routingSearch, event => {
  queriedCode = (event as CustomEvent<{ productCode: string }>).detail.productCode;
  setRouting({ phase: "searching", productCode: queriedCode });
  setTimeout(() => setRouting({
    phase: "awaiting-stage",
    productCode: queriedCode,
    branch: "",
    branchOptions: [
      { value: "", label: "Todas as filiais" },
      { value: "01", label: "Filial 01" },
      { value: "02", label: "Filial 02" },
    ],
    stage: "",
    stageOptions: [
      { value: "", label: "Selecionar estágio…" },
      { value: "10", label: "Estágio 10 · Montagem" },
      { value: "20", label: "Estágio 20 · Inspeção" },
    ],
    message: "Selecione a filial e o estágio produtivo para carregar as operações oficiais.",
  }), 400);
});

studio.addEventListener(STUDIO_EVENTS.routingContext, event => {
  const { stage } = (event as CustomEvent<{ branch: string; stage: string }>).detail;
  if (stage) {
    studio.study = observedStudy(queriedCode || "90264302", stage);
    studio.officialOperations = demoOfficialOps;
    studio.analysisState = { phase: "idle", issues: [] };
    studio.draftSave = { label: "Rascunho salvo", tone: "success" };
  }
});

/* Análise oficial M1 — a demo simula execução host-side: recebe o evento,
 * marca running e devolve um resultado tipado (nunca calculado no Studio). */
studio.addEventListener(STUDIO_EVENTS.analysisRun, () => {
  studio.analysisState = { phase: "running" };
  setTimeout(() => {
    studio.analysisState = {
      phase: "result",
      result: {
        taktMinutes: 1.33,
        workContentMinutes: 4,
        theoreticalMinStations: 3,
        bottleneckOperation: "OP040",
        operationsMissingTime: 1,
        stageCovered: true,
      },
    };
  }, 700);
});

studio.addEventListener(STUDIO_EVENTS.exportRequest, event => {
  const { format } = (event as CustomEvent<{ format: string }>).detail;
  console.info(`[demo] exportação ${format} solicitada — host executa o download.`);
});

studio.addEventListener(STUDIO_EVENTS.clearRequest, () => {
  if (globalThis.confirm?.("Limpar o rascunho local do estudo?")) {
    newStudy();
  }
});

function newStudy() {
  studio.study = {
    id: crypto.randomUUID(), name: "Estudo manual", operations: [], stations: [],
    scenarios: [{ id: "a", name: "Cenário A", assignments: [] }],
  };
}

createRoot(document.getElementById("demo-actions")!).render(
  <>
    <ActionButton id="example" onClick={() => { studio.study = example; }}>Carregar exemplo</ActionButton>
    <ActionButton id="new" onClick={newStudy}>Novo estudo</ActionButton>
    <ActionButton id="reset" onClick={() => { studio.study = undefined; }}>Tela inicial</ActionButton>
  </>,
);
