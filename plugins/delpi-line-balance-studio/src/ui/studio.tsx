import { useState, type CSSProperties, type DragEvent as ReactDragEvent, type ReactNode } from "react";
import { flushSync } from "react-dom";
import { createRoot, type Root } from "react-dom/client";
import {
  ActionButton,
  ChartSegmentButton,
  IconButton,
  NativeSelectControl,
  NativeTextControl,
  NATIVE_CONTROL_COMPACT_CLASS,
  type NativeTextControlProps,
} from "@delpi/plugin-ui/native-controls";
import { createManualStudy, summarizeShift } from "../index.js";
import type { ManualStudyInput, ProductionConditionsInput, ScenarioInput, ShiftInput } from "../index.js";

const colors = ["#089bdb", "#73c9ef", "#61a8e1", "#a6dff5", "#7a9de0", "#b2c7ed"];
const numberFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const format = (value: number) => numberFormat.format(value);
const blankShift: ShiftInput = { mode: "CLOCK", start: "", end: "", breaks: [] };

type CommitInputProps = Omit<NativeTextControlProps, "onChange" | "onBlur"> & {
  onCommit: (value: string) => void;
};

function CommitInput({ value, onCommit, ...props }: CommitInputProps) {
  const [editing, setEditing] = useState<string | null>(null);
  return <NativeTextControl
    {...props}
    className={NATIVE_CONTROL_COMPACT_CLASS}
    value={editing ?? value}
    onChange={setEditing}
    onBlur={() => {
      if (editing !== null && editing !== String(value)) onCommit(editing);
      setEditing(null);
    }}
    onKeyDown={event => {
      if (event.key === "Enter") event.currentTarget.blur();
    }}
  />;
}

export class LineBalanceStudioElement extends HTMLElement {
  private readonly surface = document.createElement("div");
  private draft: ManualStudyInput | undefined;
  private scenarioId = "";
  private showConditions = false;
  private draggedOperation: string | undefined;
  private reactRoot: Root | undefined;
  private studyRevision = 0;
  private shiftDrafts: Partial<Record<ShiftInput["mode"], ShiftInput>> = {};

  constructor() {
    super();
    const root = this.attachShadow({ mode: "open" });
    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = new URL("./studio.css", import.meta.url).href;
    root.append(stylesheet, this.surface);
    this.surface.addEventListener("dragover", this.onDragOver);
    this.surface.addEventListener("drop", this.onDrop);
    this.surface.addEventListener("dragend", this.clearDrag);
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

  get study(): ManualStudyInput | undefined { return structuredClone(this.draft); }

  set study(value: ManualStudyInput | undefined) {
    this.draft = structuredClone(value);
    this.studyRevision += 1;
    this.showConditions = false;
    this.shiftDrafts = {};
    this.scenarioId = value?.scenarios[0]?.id ?? "";
    this.render();
  }

  private update(draft: ManualStudyInput, focusKey?: string): void {
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
    this.surface.classList.add("dragging");
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
    this.surface.classList.remove("dragging");
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
      <section className="panel conditions" id="conditions" aria-labelledby="conditions-title">
        <h2 id="conditions-title">Condições de produção</h2>
        <div className="fields" key={shift.mode}>
          <label className="field">
            Modo de turno
            <NativeSelectControl className={NATIVE_CONTROL_COMPACT_CLASS} value={shift.mode}
              options={[{ value: "CLOCK", label: "Horários" }, { value: "MINUTES", label: "Minutos" }]}
              onChange={value => this.onField("mode", value)} />
          </label>
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
          && <p className="warning" role="status">Informe uma demanda inteira positiva.</p>}
        {batchUnits !== undefined && (!Number.isSafeInteger(batchUnits) || batchUnits < 1)
          && <p className="warning" role="status">Informe um tamanho de lote inteiro positivo.</p>}
        {summary.ok
          ? <p className="note">{format(summary.value.grossMinutes)} min brutos · {format(summary.value.breakMinutes)} min de pausa</p>
          : <p className="warning" role="status">{[...new Set(summary.issues.map(issue => labels[issue.code] ?? "Revise as condições do turno."))].join(" ")}</p>}
      </section>
    );
  }

  private render(): void {
    const study = this.draft;
    if (!study) { this.reactRoot?.render(null); return; }
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
    const validation = createManualStudy(study);
    const invalidOperations = !validation.ok && validation.issues.some(issue => issue.path.startsWith("operations") || issue.path.startsWith("stations"));
    const metric = (label: string, value: string, detail: string) => (
      <div className="metric"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>
    );
    const axisValues = Array.from({ length: 5 }, (_, i) => scale * i / 4);
    const stationOptions = stations.map(station => ({ value: station.id, label: station.name }));

    this.reactRoot?.render(
      <div className="studio" key={this.studyRevision}>
        <header className="top">
          <div className="brand"><span className="brand-icon" aria-hidden="true"><i /><i /><i /></span>
            <div><strong>Line Balance Studio</strong><small>DELPI · Engenharia de Processos</small></div>
          </div>
          <span className="draft">Rascunho manual</span>
        </header>
        <div className="workspace">
          <section className="study-header" aria-label="Estudo">
            <div className="study-title"><h1>{study.name}</h1>
              <label className="edit-name">Nome do estudo
                <CommitInput value={study.name} onCommit={value => this.onField("study-name", value)} />
              </label>
            </div>
            <div className="controls">
              {study.scenarios.length > 1 && (
                <div className="scenario-control">
                  <NativeSelectControl aria-label="Cenário" className={NATIVE_CONTROL_COMPACT_CLASS}
                    value={scenario?.id ?? ""} options={study.scenarios.map(item => ({ value: item.id, label: item.name }))}
                    onChange={value => this.onField("scenario", value)} />
                </div>
              )}
              <ActionButton aria-expanded={this.showConditions} aria-controls={this.showConditions ? "conditions" : undefined}
                onClick={() => this.onAction("conditions")}>Condições de produção</ActionButton>
            </div>
          </section>
          {this.showConditions && this.renderConditions(conditions)}
          <section className="metrics" aria-label="Indicadores" aria-live="polite">
            {metric("Takt de referência", takt === null ? "—" : `${format(takt)} s`, "por unidade")}
            {metric("Tempo produtivo", productive === null ? "—" : `${format(productive)} min`, "por turno")}
            {metric("Maior carga", stations.length ? `${format(maxLoad)} s` : "—", incomplete ? "carga conhecida · parcial" : "por posto")}
            {metric("Sem posto", String(unassigned), `de ${operations.length} operações`)}
          </section>
          <section className="panel" aria-labelledby="chart-title">
            <div className="panel-heading">
              <div><h2 id="chart-title">Yamazumi</h2><p>Carga por posto · segundos</p></div>
              <ActionButton id="add-station" onClick={() => this.onAction("add-station")}>+ Adicionar posto</ActionButton>
            </div>
            {stations.length > 0 ? (
              <div className="chart-scroll">
                <div className="chart" style={{ "--station-count": stations.length } as CSSProperties}>
                  <div className="plot">
                    {axisValues.map(value => (
                      <div className="gridline" key={value} style={{ bottom: `${value / scale * 100}%` }}><span>{format(value)}</span></div>
                    ))}
                    {takt !== null && <div className="takt" style={{ bottom: `${takt / scale * 100}%` }}><span>Takt {format(takt)} s</span></div>}
                  </div>
                  {stations.map((station, i) => {
                    const height = `${station.load / scale * 100}%`;
                    const over = takt !== null && station.load > takt;
                    return (
                      <div className="station-chart" key={station.id} data-drop={station.id}>
                        <div className="track" aria-label={`${station.name}, ${format(station.load)} segundos conhecidos`}>
                          <div className="stack" style={{ height }}>
                            {station.items.filter(item => item.seconds !== null).map(item => (
                              <ChartSegmentButton key={item.id} draggable
                                style={{ flexGrow: item.seconds ?? 0, "--delpi-ui-chart-segment-fill": item.color } as CSSProperties}
                                title={`${item.name} · ${format(item.seconds ?? 0)} s`}
                                aria-label={`${item.name}, ${format(item.seconds ?? 0)} segundos. Ir para a operação.`}
                                onClick={() => this.onAction("operation-details", item.id)}
                                onDragStart={event => this.onDragStart(event, item.id)}
                                onDragEnd={this.clearDrag}>{item.name}</ChartSegmentButton>
                            ))}
                          </div>
                          <span className={over ? "load over" : "load"} style={{ bottom: height }}>
                            {format(station.load)} s{station.unknown ? "*" : ""}
                            {over && <span title="Acima do takt" aria-label="Acima do takt"> ↑</span>}
                          </span>
                        </div>
                        <div className="station-label">
                          <CommitInput value={station.name} aria-label={`Nome do posto ${i + 1}`}
                            onCommit={value => this.onField("station-name", value, station.id)} />
                          <IconButton aria-label={`Remover posto ${i + 1}`} onClick={() => this.onAction("remove-station", station.id)}>×</IconButton>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : <p className="note">Adicione um posto para montar o gráfico.</p>}
            <div className="chart-footer">
              <span>Arraste um bloco para outro posto ou use a tabela.</span>
              <span className="unassign-drop" data-drop="">Solte aqui para desatribuir</span>
              {incomplete && <span>* Carga parcial por tempo desconhecido.</span>}
            </div>
          </section>
          <section className="panel" aria-labelledby="table-title">
            <div className="panel-heading">
              <div><h2 id="table-title">Operações</h2><p>Edite os tempos e atribua um posto a cada operação.</p></div>
              <ActionButton id="add-operation" variant="primary" onClick={() => this.onAction("add-operation")}>+ Adicionar operação</ActionButton>
            </div>
            {invalidOperations && <p className="warning" role="status">Revise os nomes e os tempos. Use um valor positivo ou deixe o tempo em branco.</p>}
            {operations.length > 0 ? (
              <div className="table-scroll"><table>
                <thead><tr><th scope="col">#</th><th scope="col">Operação</th><th scope="col">Tempo (s)</th>
                  <th scope="col">Posto</th><th scope="col"><span className="sr-only">Remover</span></th>
                </tr></thead>
                <tbody>{operations.map((operation, i) => (
                  <tr key={operation.id}>
                    <td className="row-number"><i style={{ background: operation.color }} />{String(i + 1).padStart(2, "0")}</td>
                    <td><CommitInput id={`name:${operation.id}`} value={operation.name} required aria-label={`Nome da operação ${i + 1}`}
                      onCommit={value => this.onField("operation-name", value, operation.id)} /></td>
                    <td><CommitInput type="number" min={0} step="any" placeholder="Desconhecido" value={operation.durationSeconds ?? ""}
                      aria-label={`Tempo da operação ${i + 1} em segundos`} onCommit={value => this.onField("duration", value, operation.id)} /></td>
                    <td><NativeSelectControl className={NATIVE_CONTROL_COMPACT_CLASS} placeholderOption="Sem posto"
                      aria-label={`Posto da operação ${i + 1}`} value={assignment.get(operation.id) ?? ""} options={stationOptions}
                      onChange={value => this.onField("station", value, operation.id)} /></td>
                    <td><IconButton aria-label={`Remover operação ${i + 1}`} onClick={() => this.onAction("remove-operation", operation.id)}>×</IconButton></td>
                  </tr>
                ))}</tbody>
              </table></div>
            ) : <p className="note">Adicione uma operação para começar.</p>}
          </section>
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
