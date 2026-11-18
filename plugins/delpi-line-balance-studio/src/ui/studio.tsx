import {
  Timer, Clock3, ChartColumn, CircleDashed,
  PackageSearch, SquarePen, Gauge, ListOrdered, GitBranch, Columns3,
  ChartNoAxesColumnIncreasing, UsersRound,
} from "lucide-react";
import { useRef, useState, type DragEvent as ReactDragEvent, type ReactNode } from "react";
import { flushSync } from "react-dom";
import { createRoot, type Root } from "react-dom/client";
import {
  ActionButton,
  NavigationCard,
  navigationCardBemClasses,
  CollapsibleToolRail,
  type ToolRailGroup,
  DataTable,
  dataTableBemClasses,
  SectionCard,
  sectionCardKaizenBemClasses,
  SimpleKpiCard,
  simpleKpiCardBemClasses,
  StackedColumnChart,
  StateBox,
  StatusBadge,
  statusBadgeBemClasses,
  IconButton,
  ModernSelectControl,
  NativeTextControl,
  NATIVE_CONTROL_COMPACT_CLASS,
  type NativeTextControlProps,
} from "@delpi/plugin-ui/workspace-controls";
import { createManualStudy, createObservedStudy, listMethods, summarizeShift } from "../index.js";
import studioStyles from "./studio.css?inline";
import type { MethodId, ProductionConditionsInput, ScenarioInput, ShiftInput, StudioStudyInput } from "../index.js";

/** Origem do estudo escolhida nos cards de entrada. */
export type StudioOrigin = "OBSERVED_ROUTING" | "MANUAL";

/** Estado da consulta de roteiro oficial dirigida pelo host — o Studio só
 * apresenta e emite intenções; HTTP, AuthZ, filial e estágio são do host. */
export type StudioRoutingState = Readonly<{
  phase: "idle" | "searching" | "awaiting-stage" | "error";
  productCode?: string;
  branch?: string;
  branchOptions?: readonly { value: string; label: string }[];
  stage?: string;
  stageOptions?: readonly { value: string; label: string }[];
  /** Mensagem resolvida pelo host (erro ou orientação) — nunca montada aqui. */
  message?: string;
}>;

/** Resultado da análise oficial M1 executada pelo host (BFF/domínio) —
 * o Studio só apresenta; nunca executa nem estima o cálculo oficial. */
export type StudioAnalysisState = Readonly<{
  phase: "idle" | "running" | "result" | "error";
  /** Impedimentos de parâmetros — o host os resolve e o Studio os exibe. */
  issues?: readonly string[];
  /** Mensagem de erro resolvida pelo host (AuthZ, 404, indisponibilidade). */
  message?: string;
  result?: Readonly<{
    taktMinutes?: number | null;
    workContentMinutes?: number | null;
    theoreticalMinStations?: number | null;
    bottleneckOperation?: string | null;
    /** Operações sem tempo oficial — UNKNOWN, nunca zero. */
    operationsMissingTime?: number;
    /** false → a resposta oficial não cobriu o estágio do estudo. */
    stageCovered: boolean;
  }>;
}>;

/** Linha oficial do roteiro OBSERVED — metadados técnicos (CT, recurso,
 * tempo padrão, setup) apresentados sob demanda na bancada, sem virar uma
 * segunda tabela concorrente. */
export type StudioOfficialOperation = Readonly<{
  key: string;
  code?: string | null;
  description?: string | null;
  workCenter?: string | null;
  resource?: string | null;
  timeMinutesPiece?: number | null;
  setupHours?: number | null;
}>;

/** Estado de persistência do rascunho local, resolvido pelo host. */
export type StudioDraftSaveState = Readonly<{
  label: string;
  tone: "success" | "warning";
}>;

/** Eventos públicos emitidos pelo elemento (bubbles + composed). */
export const STUDIO_EVENTS = {
  originSelect: "studio-origin-select",
  routingSearch: "studio-routing-search",
  routingContext: "studio-routing-context",
  manualStudy: "studio-manual-study",
  originReset: "studio-origin-reset",
  methodChange: "studio-method-change",
  analysisRun: "studio-analysis-run",
  exportRequest: "studio-export",
  clearRequest: "studio-clear-study",
} as const;

const navCardClasses = navigationCardBemClasses("lbs");
const UI_PREFS_KEY = "delpi-lbs:ui";
const METHOD_ICONS: Record<MethodId, ReactNode> = {
  M1: <Gauge size={18} />,
  M2: <ListOrdered size={18} />,
  M3: <GitBranch size={18} />,
  M4: <Columns3 size={18} />,
  M5: <ChartNoAxesColumnIncreasing size={18} />,
  M6: <UsersRound size={18} />,
};
const METHOD_STATUS_TEXT: Record<MethodId, string> = {
  M1: "Diagnóstico local",
  M5: "Disponível",
  M2: "Planejado",
  M3: "Planejado",
  M4: "Planejado",
  M6: "Planejado",
};
const methodNames: Record<MethodId, string> = {
  M1: "Capacidade e takt",
  M2: "FFD / LCR",
  M3: "Peso posicional",
  M4: "Kilbridge–Wester",
  M5: "Yamazumi",
  M6: "Recursos",
};
const railGroups = (catalog: readonly { id: MethodId; status: string }[]): readonly ToolRailGroup[] => [
  {
    id: "methods",
    items: catalog.filter(method => method.status !== "PLANNED").map(method => ({
      id: method.id,
      label: `${method.id} · ${methodNames[method.id]}`,
      icon: METHOD_ICONS[method.id],
      statusText: METHOD_STATUS_TEXT[method.id],
    })),
  },
  {
    id: "upcoming",
    label: "Próximos métodos",
    collapsible: true,
    defaultOpen: false,
    items: catalog.filter(method => method.status === "PLANNED").map(method => ({
      id: method.id,
      label: `${method.id} · ${methodNames[method.id]}`,
      icon: METHOD_ICONS[method.id],
      statusText: METHOD_STATUS_TEXT[method.id],
      disabled: true,
    })),
  },
];
const sectionClasses = sectionCardKaizenBemClasses("lbs");
const sectionLabels = { titleHelpAriaLabel: (title: string) => `Ajuda: ${title}` };
const kpiClasses = simpleKpiCardBemClasses("lbs", "kpi", { withBody: true, withSubtitle: true });
const badgeClasses = statusBadgeBemClasses("lbs");
const tableClasses = dataTableBemClasses("lbs");
const tableLabels = {
  emptyMessage: "Adicione uma operação para começar.",
  loadingMessage: "Carregando operações…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

const colors = Array.from({ length: 6 }, (_, index) => `var(--chart-${index + 1}, var(--primary, #089bdb))`);
const numberFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const format = (value: number) => numberFormat.format(value);
const blankShift: ShiftInput = { mode: "CLOCK", start: "", end: "", breaks: [] };

type CommitInputProps = Omit<NativeTextControlProps, "onChange" | "onBlur"> & {
  onCommit: (value: string) => void;
};

function CommitInput({ value, onCommit, ...props }: CommitInputProps) {
  const [editing, setEditing] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  return <NativeTextControl
    {...props}
    ref={inputRef}
    className={NATIVE_CONTROL_COMPACT_CLASS}
    value={editing ?? value}
    onChange={setEditing}
    onBlur={() => {
      const next = inputRef.current?.value;
      if (next !== undefined && next !== String(value)) onCommit(next);
      setEditing(null);
    }}
    onKeyDown={event => {
      if (event.key === "Enter") event.currentTarget.blur();
    }}
  />;
}

export class LineBalanceStudioElement extends HTMLElement {
  private readonly surface = document.createElement("div");
  private draft: StudioStudyInput | undefined;
  private observedBaseline = new Map<string, number | null>();
  private scenarioId = "";
  private showConditions = false;
  private draggedOperation: string | undefined;
  private reactRoot: Root | undefined;
  private studyRevision = 0;
  private shiftDrafts: Partial<Record<ShiftInput["mode"], ShiftInput>> = {};
  private originChoice: StudioOrigin | null = null;
  private routingSession: StudioRoutingState = { phase: "idle" };
  private routingUnsupported = false;
  private productCodeInput = "";
  private manualNameInput = "";
  private selectedMethod: MethodId = "M5";
  private railExpanded = true;
  private confirmReset = false;
  private analysis: StudioAnalysisState = { phase: "idle" };
  private officialOps: readonly StudioOfficialOperation[] = [];
  private saveState: StudioDraftSaveState | undefined;
  private showMoreActions = false;
  private showOfficialDetails = false;
  private routingWait: ReturnType<typeof setTimeout> | undefined;
  private manualWait: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    super();
    const root = this.attachShadow({ mode: "open" });
    const stylesheet = document.createElement("style");
    stylesheet.textContent = studioStyles;
    root.append(stylesheet, this.surface);
    this.surface.addEventListener("dragover", this.onDragOver);
    this.surface.addEventListener("drop", this.onDrop);
    this.surface.addEventListener("dragend", this.clearDrag);
    let prefs: { method?: string; railExpanded?: boolean } = {};
    try { prefs = JSON.parse(globalThis.localStorage?.getItem(UI_PREFS_KEY) ?? "{}"); } catch { /* preferência corrompida não bloqueia */ }
    if (prefs.method === "M1" || prefs.method === "M5") this.selectedMethod = prefs.method;
    this.railExpanded = typeof prefs.railExpanded === "boolean"
      ? prefs.railExpanded
      : !globalThis.matchMedia?.("(max-width: 900px)").matches;
  }

  private saveUiPrefs(): void {
    try {
      globalThis.localStorage?.setItem(UI_PREFS_KEY, JSON.stringify({
        method: this.selectedMethod, railExpanded: this.railExpanded,
      }));
    } catch { /* sem persistência de preferência o Studio continua usável */ }
  }

  private emit(type: string, detail: unknown): void {
    this.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true }));
  }

  connectedCallback(): void {
    this.reactRoot = createRoot(this.surface);
    this.render();
  }

  disconnectedCallback(): void {
    this.reactRoot?.unmount();
    this.reactRoot = undefined;
  }

  private focusControl(id: string): void {
    this.shadowRoot?.getElementById(id)?.focus();
  }

  get study(): StudioStudyInput | undefined { return structuredClone(this.draft); }

  set study(value: StudioStudyInput | undefined) {
    this.draft = structuredClone(value);
    this.observedBaseline.clear();
    if (value?.source === "OBSERVED_ROUTING") {
      for (const operation of value.operations) this.observedBaseline.set(operation.id, operation.durationSeconds);
    }
    if (value) this.originChoice = value.source === "OBSERVED_ROUTING" ? "OBSERVED_ROUTING" : "MANUAL";
    this.studyRevision += 1;
    this.showConditions = false;
    this.confirmReset = false;
    this.showMoreActions = false;
    this.showOfficialDetails = false;
    /* Resultado oficial, detalhes do roteiro e estado de salvamento
     * pertencem ao ciclo do estudo anterior — o host os republica. */
    this.analysis = { phase: "idle" };
    this.officialOps = [];
    this.saveState = undefined;
    this.shiftDrafts = {};
    this.scenarioId = value?.scenarios[0]?.id ?? "";
    this.render();
  }

  /** Consulta oficial em andamento — dirigida pelo host, refletida aqui. */
  set routingState(value: StudioRoutingState | undefined) {
    this.routingSession = value ?? { phase: "idle" };
    this.routingUnsupported = false;
    this.render();
  }

  /** Análise oficial M1 — executada pelo host/BFF, exibida na bancada M1. */
  set analysisState(value: StudioAnalysisState | undefined) {
    this.analysis = value ?? { phase: "idle" };
    this.render();
  }

  /** Metadados oficiais do roteiro OBSERVED — detalhe técnico sob demanda. */
  set officialOperations(value: readonly StudioOfficialOperation[] | undefined) {
    this.officialOps = value ?? [];
    this.render();
  }

  /** Estado do rascunho local, resolvido pelo host (saved/quota/erro). */
  set draftSave(value: StudioDraftSaveState | undefined) {
    this.saveState = value;
    this.render();
  }

  private selectOrigin(origin: StudioOrigin): void {
    if (this.draft) return;
    this.originChoice = origin;
    this.routingUnsupported = false;
    this.emit(STUDIO_EVENTS.originSelect, { origin });
    this.render();
  }

  private requestRoutingSearch(): void {
    const productCode = this.productCodeInput.trim();
    if (!productCode) return;
    this.routingUnsupported = false;
    this.emit(STUDIO_EVENTS.routingSearch, { productCode });
    clearTimeout(this.routingWait);
    this.routingWait = setTimeout(() => {
      if (this.routingSession.phase === "idle" && !this.draft) {
        this.routingUnsupported = true;
        this.render();
      }
    }, 1600);
  }

  private requestManualStudy(): void {
    const name = this.manualNameInput.trim() || "Estudo manual";
    this.emit(STUDIO_EVENTS.manualStudy, { name });
    clearTimeout(this.manualWait);
    /* Sem host respondendo ao evento (demo independente, outro portal), o
     * Studio semeia o rascunho manual pelo contrato local. */
    this.manualWait = setTimeout(() => {
      if (!this.draft && this.originChoice === "MANUAL") {
        this.study = {
          id: crypto.randomUUID(), name,
          operations: [], stations: [],
          scenarios: [{ id: "a", name: "Cenário A", assignments: [] }],
        };
        this.emit("study-change", { study: this.study });
      }
    }, 350);
  }

  private requestOriginReset(): void {
    if (!this.confirmReset) {
      this.confirmReset = true;
      this.render();
      return;
    }
    this.confirmReset = false;
    this.draft = undefined;
    this.originChoice = null;
    this.productCodeInput = "";
    this.manualNameInput = "";
    this.scenarioId = "";
    this.observedBaseline.clear();
    this.emit(STUDIO_EVENTS.originReset, {});
    this.render();
  }

  private selectMethod(id: string): void {
    const method = listMethods().find(item => item.id === id);
    if (!method || method.status === "PLANNED") return;
    this.selectedMethod = method.id;
    this.saveUiPrefs();
    this.emit(STUDIO_EVENTS.methodChange, { method: method.id });
    this.render();
  }

  private update(draft: StudioStudyInput, focusKey?: string): void {
    this.draft = draft;
    if (focusKey) {
      flushSync(() => this.render());
      this.focusControl(focusKey);
    } else {
      this.render();
    }
    this.dispatchEvent(new CustomEvent("study-change", {
      detail: { study: this.study }, bubbles: true, composed: true,
    }));
  }

  private get scenario(): ScenarioInput | undefined {
    return this.draft?.scenarios.find(scenario => scenario.id === this.scenarioId) ?? this.draft?.scenarios[0];
  }

  private moveOperation(operationId: string, stationId: string, focusKey?: string): void {
    const study = this.draft;
    const scenario = this.scenario;
    if (!study || !scenario || !study.operations.some(operation => operation.id === operationId) ||
        (stationId && !study.stations.some(station => station.id === stationId))) return;
    const assignments = scenario.assignments.filter(item => item.operationId !== operationId);
    if (stationId) assignments.push({ operationId, stationId });
    this.update({
      ...study,
      scenarios: study.scenarios.map(item => item.id === scenario.id ? { ...item, assignments } : item),
    }, focusKey);
  }

  private readonly onAction = (action: string, id?: string): void => {
    const study = this.draft;
    if (!study) return;
    const conditions = study.conditions ?? { shift: blankShift };
    const shift = conditions.shift;

    switch (action) {
      case "conditions":
        this.showConditions = !this.showConditions;
        this.render();
        break;
      case "add-operation": {
        const operationId = crypto.randomUUID();
        this.update({ ...study, operations: [...study.operations, {
          id: operationId, name: "Nova operação", durationSeconds: null,
        }] }, `name:${operationId}`);
        break;
      }
      case "remove-operation":
        this.update({
          ...study,
          operations: study.operations.filter(item => item.id !== id),
          scenarios: study.scenarios.map(item => ({
            ...item, assignments: item.assignments.filter(assignment => assignment.operationId !== id),
          })),
        }, "add-operation");
        break;
      case "add-station": {
        const stationId = crypto.randomUUID();
        this.update({ ...study, stations: [...study.stations, {
          id: stationId, name: `Posto ${study.stations.length + 1}`,
        }] }, "add-station");
        break;
      }
      case "remove-station":
        this.update({
          ...study,
          stations: study.stations.filter(item => item.id !== id),
          scenarios: study.scenarios.map(item => ({
            ...item, assignments: item.assignments.filter(assignment => assignment.stationId !== id),
          })),
        }, "add-station");
        break;
      case "add-scenario": {
        if (study.scenarios.length >= 4) return;
        const scenarioId = crypto.randomUUID();
        const letter = "ABCD"[study.scenarios.length] ?? String(study.scenarios.length + 1);
        this.update({ ...study, scenarios: [...study.scenarios, {
          id: scenarioId, name: `Cenário ${letter}`, assignments: [],
        }] });
        this.scenarioId = scenarioId;
        this.render();
        break;
      }
      case "move-station-up":
      case "move-station-down": {
        const index = study.stations.findIndex(item => item.id === id);
        const target = action === "move-station-up" ? index - 1 : index + 1;
        if (index < 0 || target < 0 || target >= study.stations.length) return;
        const stations = [...study.stations];
        const current = stations[index];
        const other = stations[target];
        if (!current || !other) return;
        [stations[index], stations[target]] = [other, current];
        this.update({ ...study, stations });
        break;
      }
      case "add-break":
        this.setShift(shift.mode === "CLOCK"
          ? { ...shift, breaks: [...shift.breaks, { start: "", end: "" }] }
          : { ...shift, breaks: [...shift.breaks, 15] }, "add-break");
        break;
      case "remove-break":
        this.setShift(shift.mode === "CLOCK"
          ? { ...shift, breaks: shift.breaks.filter((_, index) => index !== Number(id)) }
          : { ...shift, breaks: shift.breaks.filter((_, index) => index !== Number(id)) }, "add-break");
        break;
      case "operation-details":
        this.focusControl(`name:${id}`);
        break;
    }
  };

  private setShift(shift: ShiftInput, focusKey?: string): void {
    const study = this.draft;
    if (study) this.update({ ...study, conditions: { ...study.conditions, shift } }, focusKey);
  }

  private readonly onField = (kind: string, value: string, id?: string): void => {
    const study = this.draft;
    if (!study) return;
    const conditions: ProductionConditionsInput = study.conditions ?? { shift: blankShift };
    const shift = conditions.shift;

    switch (kind) {
      case "study-name":
        if (value.trim()) this.update({ ...study, name: value.trim() });
        break;
      case "scenario":
        this.scenarioId = value;
        this.render();
        break;
      case "operation-name":
      case "duration":
        this.update({ ...study, operations: study.operations.map(operation => operation.id === id
          ? { ...operation, ...(kind === "operation-name" ? { name: value } :
            { durationSeconds: value === "" ? null : Number(value) }) } : operation) });
        break;
      case "station":
        this.moveOperation(id ?? "", value);
        break;
      case "station-name":
        this.update({ ...study, stations: study.stations.map(station => station.id === id ? {
          ...station, name: value,
        } : station) });
        break;
      case "mode":
        if (value !== shift.mode) {
          this.shiftDrafts[shift.mode] = shift;
          const nextMode = value === "MINUTES" ? "MINUTES" : "CLOCK";
          const summary = summarizeShift(shift);
          const minutes = (time: string): number => Number(time.slice(0, 2)) * 60 + Number(time.slice(3));
          this.setShift(this.shiftDrafts[nextMode] ?? (nextMode === "CLOCK" ? blankShift : {
            mode: "MINUTES",
            durationMinutes: summary.ok ? summary.value.grossMinutes : 0,
            breaks: summary.ok && shift.mode === "CLOCK"
              ? shift.breaks.map(pause => (minutes(pause.end) - minutes(pause.start) + 1440) % 1440) : [],
          }));
        }
        break;
      case "start":
      case "end":
        if (shift.mode === "CLOCK") this.setShift({ ...shift, [kind]: value });
        break;
      case "shift-minutes":
        if (shift.mode === "MINUTES") this.setShift({ ...shift, durationMinutes: Number(value) });
        break;
      case "break-start":
      case "break-end":
        if (shift.mode === "CLOCK") {
          const endpoint = kind === "break-start" ? "start" : "end";
          this.setShift({ ...shift, breaks: shift.breaks.map((pause, index) =>
            index === Number(id) ? { ...pause, [endpoint]: value } : pause) });
        }
        break;
      case "break-minutes":
        if (shift.mode === "MINUTES") this.setShift({ ...shift, breaks: shift.breaks.map((pause, index) =>
          index === Number(id) ? Number(value) : pause) });
        break;
      case "demand": {
        const { demandUnitsPerShift: previous, ...rest } = conditions;
        this.update({ ...study, conditions: value === "" ? rest : { ...rest, demandUnitsPerShift: Number(value) } });
        break;
      }
      case "batch": {
        const { batchUnits: previous, ...rest } = conditions;
        this.update({ ...study, conditions: value === "" ? rest : { ...rest, batchUnits: Number(value) } });
        break;
      }
    }
  };

  private readonly onDragStart = (event: ReactDragEvent<HTMLButtonElement>, operationId: string): void => {
    this.draggedOperation = operationId;
    event.dataTransfer.setData("text/plain", this.draggedOperation);
    event.dataTransfer.effectAllowed = "move";
    this.surface.dataset.delpiUiChartDragging = "true";
  };

  private readonly onDragOver = (event: DragEvent): void => {
    if (!this.draggedOperation || !(event.target as HTMLElement).closest("[data-drop]")) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
  };

  private readonly onDrop = (event: DragEvent): void => {
    const target = (event.target as HTMLElement).closest<HTMLElement>("[data-drop]");
    if (!target || !this.draggedOperation) return;
    event.preventDefault();
    const operation = this.draggedOperation;
    this.clearDrag();
    this.moveOperation(operation, target.dataset.drop ?? "");
  };

  private readonly clearDrag = (): void => {
    this.draggedOperation = undefined;
    delete this.surface.dataset.delpiUiChartDragging;
  };

  private renderConditions(conditions: ProductionConditionsInput): ReactNode {
    const { shift, demandUnitsPerShift, batchUnits } = conditions;
    const field = (label: string, type: "time" | "number", kind: string, value: string, id?: string) => (
      <label className="field">
        {label}
        <CommitInput type={type} value={value} {...(type === "number" ? { min: 1, step: 1 } : {})}
          onCommit={next => this.onField(kind, next, id)} />
      </label>
    );
    const shiftFields = shift.mode === "CLOCK"
      ? <>{field("Início", "time", "start", shift.start)}{field("Fim", "time", "end", shift.end)}</>
      : field("Duração (min)", "number", "shift-minutes", String(shift.durationMinutes || ""));
    const pauses = shift.mode === "CLOCK"
      ? shift.breaks.map((pause, i) => <>
        {field(`Pausa ${i + 1} · início`, "time", "break-start", pause.start, String(i))}
        {field("Fim", "time", "break-end", pause.end, String(i))}
      </>)
      : shift.breaks.map((pause, i) => field(`Pausa ${i + 1} (min)`, "number", "break-minutes", String(pause || ""), String(i)));
    const summary = summarizeShift(shift);
    const labels: Record<string, string> = {
      BREAK_OVERLAP: "Há pausas sobrepostas.", BREAK_OUTSIDE_SHIFT: "Há uma pausa fora do turno.",
      EMPTY_BREAK: "Informe início e fim diferentes para a pausa.", INVALID_CLOCK_TIME: "Complete os horários do turno e das pausas.",
      AMBIGUOUS_SHIFT: "O início e o fim do turno precisam ser diferentes.",
      INVALID_NUMBER: "Use durações inteiras válidas.", NO_PRODUCTIVE_TIME: "Reserve tempo produtivo no turno.",
    };
    return (
      <div id="conditions"><SectionCard title="Condições de produção" classNames={sectionClasses} labels={sectionLabels}>
        <div className="fields" key={shift.mode}>
          <div className="field">
            <label htmlFor="shift-mode">Modo de turno</label>
            <ModernSelectControl id="shift-mode" ariaLabel="Modo de turno" portalWithinShadowRoot value={shift.mode}
              options={[{ value: "CLOCK", label: "Horários" }, { value: "MINUTES", label: "Minutos" }]}
              onChange={value => this.onField("mode", value)} />
          </div>
          {shiftFields}
          {field("Demanda por turno", "number", "demand", String(demandUnitsPerShift ?? ""))}
          {field("Tamanho do lote", "number", "batch", String(batchUnits ?? ""))}
        </div>
        {pauses.map((pause, i) => (
          <div className="fields pause" key={`${shift.mode}:${i}`}>
            {pause}
            <IconButton aria-label={`Remover pausa ${i + 1}`} onClick={() => this.onAction("remove-break", String(i))}>×</IconButton>
          </div>
        ))}
        <ActionButton id="add-break" onClick={() => this.onAction("add-break")}>+ Adicionar pausa</ActionButton>
        {demandUnitsPerShift !== undefined && (!Number.isSafeInteger(demandUnitsPerShift) || demandUnitsPerShift < 1)
          && <StateBox variant="warning" dismissible={false}>Informe uma demanda inteira positiva.</StateBox>}
        {batchUnits !== undefined && (!Number.isSafeInteger(batchUnits) || batchUnits < 1)
          && <StateBox variant="warning" dismissible={false}>Informe um tamanho de lote inteiro positivo.</StateBox>}
        {summary.ok
          ? <StateBox>{format(summary.value.grossMinutes)} min brutos · {format(summary.value.breakMinutes)} min de pausa</StateBox>
          : <StateBox variant="warning" dismissible={false}>{[...new Set(summary.issues.map(issue => labels[issue.code] ?? "Revise as condições do turno."))].join(" ")}</StateBox>}
      </SectionCard></div>
    );
  }

  private renderRail(): ReactNode {
    return (
      <CollapsibleToolRail
        groups={railGroups(listMethods())}
        activeId={this.selectedMethod}
        expanded={this.railExpanded}
        ariaLabel="Métodos"
        expandLabel="Expandir métodos"
        collapseLabel="Recolher métodos"
        onExpandedChange={expanded => { this.railExpanded = expanded; this.saveUiPrefs(); this.render(); }}
        onSelect={id => this.selectMethod(id)}
      />
    );
  }

  private renderEntry(): ReactNode {
    const routing = this.routingSession;
    return (
      <section className="entry" aria-label="Novo estudo">
        <div className="entry-head">
          <h2>Novo estudo</h2>
          <p>{this.originChoice ? "Configure a origem selecionada para iniciar." : "Como deseja começar?"}</p>
        </div>
        <div className="origin-cards">
          <NavigationCard
            density="featured"
            selected={this.originChoice === "OBSERVED_ROUTING"}
            icon={<PackageSearch size={36} />}
            title="Produto DELPI"
            description="Consultar roteiro oficial"
            classNames={navCardClasses}
            aria-label="Produto DELPI — consultar roteiro oficial"
            onClick={() => this.selectOrigin("OBSERVED_ROUTING")}
          />
          <NavigationCard
            density="featured"
            selected={this.originChoice === "MANUAL"}
            icon={<SquarePen size={36} />}
            title="Estudo manual"
            description="Criar processo do zero"
            classNames={navCardClasses}
            aria-label="Estudo manual — criar processo do zero"
            onClick={() => this.selectOrigin("MANUAL")}
          />
        </div>
        {this.originChoice === "OBSERVED_ROUTING" && this.renderRoutingForm(routing)}
        {this.originChoice === "MANUAL" && (
          <div className="origin-form">
            <label className="field">Nome do estudo
              <NativeTextControl id="lb-study-name" value={this.manualNameInput}
                placeholder="Ex.: Montagem hipotética" aria-label="Nome do estudo"
                onChange={value => { this.manualNameInput = value; this.render(); }}
                onKeyDown={event => { if (event.key === "Enter") this.requestManualStudy(); }} />
            </label>
            <ActionButton id="lb-create-manual" variant="primary" onClick={() => this.requestManualStudy()}>
              Criar estudo
            </ActionButton>
          </div>
        )}
      </section>
    );
  }

  private renderRoutingForm(routing: StudioRoutingState): ReactNode {
    const searching = routing.phase === "searching";
    return (
      <div className="origin-panel">
        <div className="origin-form">
          <label className="field">Código do produto
            <NativeTextControl id="lb-product-code" value={this.productCodeInput}
              aria-label="Código do produto"
              onChange={value => { this.productCodeInput = value; this.render(); }}
              onKeyDown={event => { if (event.key === "Enter") this.requestRoutingSearch(); }} />
          </label>
          <ActionButton id="lb-search-routing" variant="primary"
            disabled={!this.productCodeInput.trim() || searching}
            onClick={() => this.requestRoutingSearch()}>
            {searching ? "Consultando…" : "Buscar roteiro"}
          </ActionButton>
        </div>
        {searching && <StateBox>Consultando o roteiro oficial…</StateBox>}
        {routing.phase === "error" && (
          <StateBox variant="warning" dismissible={false}>
            {routing.message ?? "Fonte oficial de roteiro indisponível."}
          </StateBox>
        )}
        {this.routingUnsupported && routing.phase === "idle" && (
          <StateBox variant="warning" dismissible={false}>
            A consulta oficial de roteiro é fornecida pelo portal host — indisponível neste ambiente.
          </StateBox>
        )}
        {routing.phase === "awaiting-stage" && (
          <div className="origin-form">
            <div className="field">
              <label>Filial</label>
              <ModernSelectControl ariaLabel="Filial" portalWithinShadowRoot
                value={routing.branch ?? ""} options={routing.branchOptions ?? []}
                onChange={value => this.emit(STUDIO_EVENTS.routingContext, { branch: value, stage: "" })} />
            </div>
            <div className="field">
              <label>Estágio produtivo</label>
              <ModernSelectControl ariaLabel="Estágio produtivo" portalWithinShadowRoot
                value={routing.stage ?? ""} options={routing.stageOptions ?? []}
                disabled={!routing.stageOptions?.length}
                onChange={value => this.emit(STUDIO_EVENTS.routingContext, { branch: routing.branch ?? "", stage: value })} />
            </div>
          </div>
        )}
        {routing.phase === "awaiting-stage" && routing.message && <StateBox>{routing.message}</StateBox>}
      </div>
    );
  }

  /** Análise oficial M1 — execução sempre no host/domínio; aqui só a
   * apresentação tipada recebida por `analysisState`. */
  private renderOfficialAnalysis(analysis: StudioAnalysisState): ReactNode {
    const running = analysis.phase === "running";
    const issues = analysis.issues ?? [];
    const blocked = issues.length > 0;
    const result = analysis.result;
    const kpis: { title: string; value: string; subtitle: string; icon: ReactNode }[] = result ? [
      { title: "Takt", icon: <Timer size={18} />, subtitle: "min/peça · CALCULATED",
        value: result.taktMinutes != null ? format(result.taktMinutes) : "—" },
      { title: "Conteúdo de trabalho", icon: <Clock3 size={18} />, subtitle: "min · CALCULATED",
        value: result.workContentMinutes != null ? format(result.workContentMinutes) : "—" },
      { title: "Mínimo teórico de postos", icon: <ChartColumn size={18} />, subtitle: "CALCULATED",
        value: result.theoreticalMinStations != null ? String(result.theoreticalMinStations) : "—" },
      { title: "Gargalo candidato", icon: <Gauge size={18} />, subtitle: "CALCULATED",
        value: result.bottleneckOperation ?? "—" },
    ] : [];
    return (
      <div className="official-analysis">
        <div className="official-analysis__head">
          <strong>Análise oficial M1</strong>
          <span>Calculada pelo domínio autorizado do portal sobre o roteiro OBSERVED.</span>
        </div>
        {blocked && (
          <ul className="analysis-issues" role="alert">
            {issues.map((issue, index) => <li key={index}>{issue}</li>)}
          </ul>
        )}
        <ActionButton id="lb-run-analysis" variant="primary"
          disabled={blocked || running}
          onClick={() => this.emit(STUDIO_EVENTS.analysisRun, {})}>
          {running ? "Calculando…" : "Executar análise oficial"}
        </ActionButton>
        {analysis.phase === "error" && (
          <StateBox variant="warning" dismissible={false}>
            {analysis.message ?? "Serviço de análise oficial indisponível."}
          </StateBox>
        )}
        {analysis.phase === "result" && result && !result.stageCovered && (
          <StateBox>O resultado oficial não inclui o estágio selecionado.</StateBox>
        )}
        {analysis.phase === "result" && result?.stageCovered && (
          <section className="metrics" aria-label="Resultado oficial M1" aria-live="polite">
            {kpis.map(kpi => (
              <SimpleKpiCard key={kpi.title} classNames={kpiClasses} title={kpi.title}
                valueTag="strong" icon={kpi.icon} value={kpi.value} subtitle={kpi.subtitle} />
            ))}
          </section>
        )}
        {analysis.phase === "result" && (result?.operationsMissingTime ?? 0) > 0 && (
          <StateBox>
            {result?.operationsMissingTime} operação(ões) sem tempo oficial — UNKNOWN, nunca assumidas como zero.
          </StateBox>
        )}
      </div>
    );
  }

  private renderCapacityPanel(stations: { id: string; name: string; load: number; unknown: number }[], takt: number | null, observed: boolean): ReactNode {
    return (
      <SectionCard title="Capacidade e takt" subtitle="Diagnóstico local do estudo · CALCULATED local"
        classNames={sectionClasses} labels={sectionLabels}>
        <DataTable rows={stations} rowKey={station => station.id} classNames={tableClasses}
          labels={tableLabels} layout="scroll" compact
          columns={[
            { key: "station", header: "Posto", render: station => station.name },
            { key: "load", header: "Carga conhecida", align: "right", render: station =>
              `${format(station.load)} s${station.unknown ? ` · ${station.unknown} sem tempo` : ""}` },
            { key: "takt", header: "vs takt", render: station =>
              takt === null ? "—" : station.load > takt ? `+${format(station.load - takt)} s acima` : "Dentro do takt" },
          ]}
        />
        {takt === null && (
          <StateBox>Informe turno produtivo e demanda por turno válida nas condições de produção para obter a referência de takt.</StateBox>
        )}
        {observed
          ? this.renderOfficialAnalysis(this.analysis)
          : <StateBox>Estudo manual sem contrato de cálculo oficial — os valores acima são diagnóstico local do rascunho (SIMULATION / DRAFT_LOCAL).</StateBox>}
      </SectionCard>
    );
  }

  private render(): void {
    const study = this.draft;
    if (!study) {
      this.reactRoot?.render(
        <div className="studio">
          <header className="top">
            <div className="brand">
              <strong>Balanceamento de Linha</strong>
              <small>DELPI · Engenharia de Processos</small>
            </div>
          </header>
          <div className="layout">
            {this.renderRail()}
            <div className="main">{this.renderEntry()}</div>
          </div>
        </div>,
      );
      return;
    }
    const scenario = this.scenario;
    const assignment = new Map(scenario?.assignments.map(item => [item.operationId, item.stationId]));
    const operations = study.operations.map((operation, index) => ({
      ...operation, color: colors[index % colors.length], seconds: operation.durationSeconds && operation.durationSeconds > 0
        && Number.isFinite(operation.durationSeconds) ? operation.durationSeconds : null,
    }));
    const stations = study.stations.map(station => {
      const items = operations.filter(item => assignment.get(item.id) === station.id);
      return { ...station, items, load: items.reduce((sum, item) => sum + (item.seconds ?? 0), 0),
        unknown: items.filter(item => item.seconds === null).length };
    });
    const unassigned = operations.filter(item => !assignment.has(item.id)).length;
    const conditions = study.conditions ?? { shift: blankShift };
    const summary = summarizeShift(conditions.shift);
    const productive = summary.ok ? summary.value.productiveMinutes : null;
    const demand = conditions.demandUnitsPerShift;
    const takt = productive && demand && Number.isSafeInteger(demand) && demand > 0 ? productive * 60 / demand : null;
    const maxLoad = Math.max(0, ...stations.map(station => station.load));
    const scale = Math.max(10, Math.ceil(Math.max(maxLoad, takt ?? 0) * 1.16 / 10) * 10);
    const incomplete = stations.some(station => station.unknown > 0);
    const validation = study.source === "OBSERVED_ROUTING" ? createObservedStudy(study) : createManualStudy(study);
    const invalidOperations = !validation.ok && validation.issues.some(issue => issue.path.startsWith("operations") || issue.path.startsWith("stations"));
    const stationOptions = stations.map(station => ({ value: station.id, label: station.name }));
    const observed = study.source === "OBSERVED_ROUTING" ? study.routing : undefined;
    const operationRows = operations.map((operation, index) => ({
      id: operation.id, name: operation.name, durationSeconds: operation.durationSeconds,
      reference: "reference" in operation ? operation.reference : undefined,
      index,
      origin: !observed ? "LOCAL"
        : !this.observedBaseline.has(operation.id) ? "LOCAL"
        : this.observedBaseline.get(operation.id) === operation.durationSeconds ? "OBSERVED" : "ADJUSTED",
    }));
    this.reactRoot?.render(
      <div className="studio" key={this.studyRevision}>
        <header className="top">
          <div className="brand">
            <strong>Balanceamento de Linha</strong>
            <small>DELPI · Engenharia de Processos</small>
          </div>
        </header>
        <div className="layout">
          {this.renderRail()}
          <div className="main">
            <div className="study-head">
              <div className="study-id">
                <div className="study-title-row">
                  <strong>{observed ? `Produto ${observed.productCode}` : study.name}</strong>
                  {observed && <StatusBadge classNames={badgeClasses}
                    label={`Roteiro oficial · OBSERVED${observed.truncated ? " · truncado" : ""}`} variant="success" />}
                  <StatusBadge classNames={badgeClasses} label={observed ? "Estudo local · DRAFT_LOCAL" : "Rascunho manual · DRAFT_LOCAL"} variant="info" />
                </div>
                <span className="study-sub">
                  {observed
                    ? `Filial ${observed.branchCode} · ${observed.stageLabel ?? `Estágio ${observed.stageId}`}${observed.routeCode ? ` · Roteiro ${observed.routeCode}` : ""}`
                    : "Estudo manual · sem vínculo com produto oficial"}
                </span>
                <label className="edit-name">Nome do estudo
                  <CommitInput value={study.name} onCommit={value => this.onField("study-name", value)} />
                </label>
              </div>
              <div className="study-actions">
                {study.scenarios.length > 1 && (
                  <div className="scenario-control">
                    <ModernSelectControl ariaLabel="Cenário" portalWithinShadowRoot
                      value={scenario?.id ?? ""} options={study.scenarios.map(item => ({ value: item.id, label: item.name }))}
                      onChange={value => this.onField("scenario", value)} />
                  </div>
                )}
                {study.scenarios.length < 4 && (
                  <ActionButton onClick={() => this.onAction("add-scenario")}>+ Novo cenário</ActionButton>
                )}
                <ActionButton aria-expanded={this.showConditions} aria-controls={this.showConditions ? "conditions" : undefined}
                  onClick={() => this.onAction("conditions")}>Condições de produção</ActionButton>
                <ActionButton aria-expanded={this.showMoreActions} aria-controls={this.showMoreActions ? "study-more-actions" : undefined}
                  onClick={() => { this.showMoreActions = !this.showMoreActions; this.render(); }}>
                  Mais ações ▾
                </ActionButton>
                {this.saveState && (
                  <StatusBadge classNames={badgeClasses} label={this.saveState.label} variant={this.saveState.tone} />
                )}
              </div>
            </div>
            {this.showMoreActions && (
              <div className="more-actions" id="study-more-actions" role="group" aria-label="Ações secundárias do estudo">
                <ActionButton onClick={() => this.requestOriginReset()}>Trocar origem</ActionButton>
                <span className="more-actions__sep" aria-hidden="true" />
                <ActionButton onClick={() => this.emit(STUDIO_EVENTS.exportRequest, { format: "csv" })}>Exportar CSV</ActionButton>
                <ActionButton onClick={() => this.emit(STUDIO_EVENTS.exportRequest, { format: "xlsx" })}>Exportar Excel</ActionButton>
                <ActionButton onClick={() => this.emit(STUDIO_EVENTS.exportRequest, { format: "pdf" })}>Exportar PDF</ActionButton>
                <span className="more-actions__sep" aria-hidden="true" />
                <ActionButton onClick={() => this.emit(STUDIO_EVENTS.clearRequest, {})}>Limpar estudo</ActionButton>
              </div>
            )}
            {this.confirmReset && (
              <div className="confirm-bar" role="alertdialog" aria-label="Confirmar troca de origem">
                <span>Trocar a origem encerra a sessão atual do estudo — o rascunho local salvo deste contexto permanece disponível.</span>
                <ActionButton variant="primary" onClick={() => this.requestOriginReset()}>Sim, trocar origem</ActionButton>
                <ActionButton onClick={() => { this.confirmReset = false; this.render(); }}>Manter estudo</ActionButton>
              </div>
            )}
            {this.showConditions && this.renderConditions(conditions)}
          <section className="metrics" aria-label="Indicadores" aria-live="polite">
            <SimpleKpiCard classNames={kpiClasses} title="Takt de referência" valueTag="strong" icon={<Timer size={18} />}
              value={takt === null ? "—" : `${format(takt)} s`} subtitle="por unidade" />
            <SimpleKpiCard classNames={kpiClasses} title="Tempo produtivo" valueTag="strong" icon={<Clock3 size={18} />}
              value={productive === null ? "—" : `${format(productive)} min`} subtitle="por turno" />
            <SimpleKpiCard classNames={kpiClasses} title="Maior carga" valueTag="strong" icon={<ChartColumn size={18} />}
              value={stations.length ? `${format(maxLoad)} s` : "—"} subtitle={incomplete ? "carga conhecida · parcial" : "por posto"} />
            <SimpleKpiCard classNames={kpiClasses} title="Sem posto" valueTag="strong" icon={<CircleDashed size={18} />}
              value={String(unassigned)} subtitle={`de ${operations.length} operações`} />
          </section>
          {this.selectedMethod === "M1" && this.renderCapacityPanel(stations, takt, Boolean(observed))}
          {this.selectedMethod === "M5" && (
          <SectionCard title="Yamazumi" subtitle="Carga por posto · segundos" classNames={sectionClasses} labels={sectionLabels}
            actions={stations.length > 0
              ? <ActionButton id="add-station" onClick={() => this.onAction("add-station")}>+ Adicionar posto</ActionButton>
              : undefined}>
            {stations.length > 0 ? (
              <StackedColumnChart
                columns={stations.map((station, index) => ({
                  id: station.id, label: station.name, value: station.load, partial: station.unknown > 0,
                  segments: station.items.flatMap(item => item.seconds === null ? [] : [{
                    id: item.id, label: item.name, value: item.seconds, color: item.color,
                  }]),
                  footer: <>
                    <IconButton aria-label={`Mover ${station.name} para cima`} disabled={index === 0}
                      onClick={() => this.onAction("move-station-up", station.id)}>↑</IconButton>
                    <IconButton aria-label={`Mover ${station.name} para baixo`} disabled={index === stations.length - 1}
                      onClick={() => this.onAction("move-station-down", station.id)}>↓</IconButton>
                    <CommitInput value={station.name} aria-label={`Nome do posto ${index + 1}`}
                      onCommit={value => this.onField("station-name", value, station.id)} />
                    <IconButton aria-label={`Remover posto ${index + 1}`}
                      onClick={() => this.onAction("remove-station", station.id)}>×</IconButton>
                  </>,
                }))}
                scale={scale} reference={takt} referenceLabel="Takt" referenceExceededLabel="Acima do takt"
                formatAxis={format} formatValue={value => `${format(value)} s`}
                segmentActionLabel="Ir para a operação." onSelectSegment={id => this.onAction("operation-details", id)}
                onDragSegment={this.onDragStart} onDragEnd={this.clearDrag}
                unassignLabel="Solte aqui para desatribuir"
                footer={<>
                  <span>Arraste um bloco para outro posto ou use a tabela.</span>
                  {incomplete && <span>* Carga parcial por tempo desconhecido.</span>}
                </>}
              />
            ) : (
              <div className="empty-bench" role="note">
                <strong>Nenhum posto configurado.</strong>
                <p>Crie um posto e atribua operações para visualizar as cargas.</p>
                <ActionButton variant="primary" onClick={() => this.onAction("add-station")}>+ Adicionar posto</ActionButton>
              </div>
            )}
          </SectionCard>
          )}
          <SectionCard title="Operações" subtitle="Edite os tempos e atribua um posto a cada operação."
            classNames={sectionClasses} labels={sectionLabels}
            actions={<>
              {this.officialOps.length > 0 && (
                <ActionButton aria-expanded={this.showOfficialDetails} aria-controls={this.showOfficialDetails ? "official-details" : undefined}
                  onClick={() => { this.showOfficialDetails = !this.showOfficialDetails; this.render(); }}>
                  Detalhes oficiais
                </ActionButton>
              )}
              <ActionButton id="add-operation" variant="primary"
                onClick={() => this.onAction("add-operation")}>+ Adicionar operação</ActionButton>
            </>}>
            {this.showOfficialDetails && this.officialOps.length > 0 && (
              <div id="official-details" className="official-details">
                <span className="official-details__cap">
                  Metadados do roteiro oficial OBSERVED — consulta, não edição.
                </span>
                <DataTable rows={[...this.officialOps]} rowKey={row => row.key} classNames={tableClasses}
                  labels={tableLabels} layout="scroll" compact
                  columns={[
                    { key: "op", header: "Operação", render: row => row.code || "—" },
                    { key: "desc", header: "Descrição", render: row => row.description ?? "—" },
                    { key: "ct", header: "CT", render: row => row.workCenter ?? "—" },
                    { key: "resource", header: "Recurso", render: row => row.resource ?? "—" },
                    { key: "time", header: "Tempo padrão (min/peça)", align: "right",
                      render: row => row.timeMinutesPiece != null ? format(row.timeMinutesPiece) : "UNKNOWN" },
                    { key: "setup", header: "Setup (h/lote)", align: "right",
                      render: row => row.setupHours != null ? format(row.setupHours) : "—" },
                  ]}
                />
              </div>
            )}
            {invalidOperations && <StateBox variant="warning" dismissible={false}>Revise os nomes e os tempos. Use um valor positivo ou deixe o tempo em branco.</StateBox>}
            <DataTable rows={operationRows} rowKey={operation => operation.id} classNames={tableClasses}
              labels={tableLabels} layout="scroll" compact indexColumn={{ ariaLabel: "Índice da operação" }}
              columns={[
                { key: "operation", header: "Operação", render: operation => (
                  <div className="op-cell">
                    <CommitInput id={`name:${operation.id}`} value={operation.name} required aria-label={`Nome da operação ${operation.index + 1}`}
                      onCommit={value => this.onField("operation-name", value, operation.id)} />
                    {operation.reference && <small className="op-ref">{operation.reference}</small>}
                  </div>
                ) },
                ...(observed ? [{ key: "origin", header: "Origem", render: (operation: typeof operationRows[number]) => (
                  <StatusBadge classNames={badgeClasses}
                    label={operation.origin === "OBSERVED" ? "Oficial" : operation.origin === "ADJUSTED" ? "Ajuste local" : "Local"}
                    variant={operation.origin === "OBSERVED" ? "success" : operation.origin === "ADJUSTED" ? "warning" : "info"} />
                ) }] : []),
                { key: "duration", header: "Tempo (s)", render: operation => (
                  <CommitInput type="number" min={0} step="any" placeholder="Desconhecido" value={operation.durationSeconds ?? ""}
                    aria-label={`Tempo da operação ${operation.index + 1} em segundos`} onCommit={value => this.onField("duration", value, operation.id)} />
                ) },
                { key: "station", header: "Posto", render: operation => (
                  <ModernSelectControl portalWithinShadowRoot allowEmpty emptyLabel="Sem posto"
                    ariaLabel={`Posto da operação ${operation.index + 1}`} value={assignment.get(operation.id) ?? ""} options={stationOptions}
                    onChange={value => this.onField("station", value, operation.id)} />
                ) },
                { key: "actions", header: "Ações", align: "center", render: operation => (
                  <IconButton aria-label={`Remover operação ${operation.index + 1}`}
                    onClick={() => this.onAction("remove-operation", operation.id)}>×</IconButton>
                ) },
              ]}
            />
          </SectionCard>
          </div>
        </div>
      </div>,
    );
  }
}

export function registerLineBalanceStudio(): void {
  if (!customElements.get("delpi-line-balance-studio")) {
    customElements.define("delpi-line-balance-studio", LineBalanceStudioElement);
  }
}
