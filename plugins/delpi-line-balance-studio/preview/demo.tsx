import { createRoot } from "react-dom/client";
import { ActionButton } from "@delpi/plugin-ui/native-controls";
import { registerLineBalanceStudio, type LineBalanceStudioElement } from "../src/ui/studio.js";
import type { ManualStudyInput } from "../src/index.js";

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
  </>,
);
studio.study = example;
