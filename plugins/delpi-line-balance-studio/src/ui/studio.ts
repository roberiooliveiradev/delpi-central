import { createManualStudy, summarizeShift } from "../index.js";
import type { ManualStudyInput, ProductionConditionsInput, ScenarioInput, ShiftInput } from "../index.js";

const colors = ["#089bdb", "#73c9ef", "#61a8e1", "#a6dff5", "#7a9de0", "#b2c7ed"];
const numberFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const format = (value: number) => numberFormat.format(value);
const escapeText = (value: string) => value.replace(/[&<>"']/g, char =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char] ?? char);
const blankShift: ShiftInput = { mode: "CLOCK", start: "", end: "", breaks: [] };

export class LineBalanceStudioElement extends HTMLElement {
  private readonly surface = document.createElement("div");
  private draft: ManualStudyInput | undefined;
  private scenarioId = "";
  private showConditions = false;
  private draggedOperation: string | undefined;
  private replaceFrame = 0;
  private pointerDown = false;
  private shiftDrafts: Partial<Record<ShiftInput["mode"], ShiftInput>> = {};

  constructor() {
    super();
    const root = this.attachShadow({ mode: "open" });
    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = new URL("./studio.css", import.meta.url).href;
    root.append(stylesheet, this.surface);
    this.surface.addEventListener("click", this.onClick);
    this.surface.addEventListener("pointerdown", () => { this.pointerDown = true; });
    this.surface.addEventListener("change", this.onChange);
    this.surface.addEventListener("dragstart", this.onDragStart);
    this.surface.addEventListener("dragover", this.onDragOver);
    this.surface.addEventListener("drop", this.onDrop);
    this.surface.addEventListener("dragend", this.clearDrag);
  }

  connectedCallback(): void {
    document.addEventListener("pointerup", this.releasePointer);
    document.addEventListener("pointercancel", this.releasePointer);
    this.render();
  }

  disconnectedCallback(): void {
    document.removeEventListener("pointerup", this.releasePointer);
    document.removeEventListener("pointercancel", this.releasePointer);
    cancelAnimationFrame(this.replaceFrame);
  }

  private readonly releasePointer = (): void => {
    this.pointerDown = false;
  };

  private scheduleEditRender(): void {
    cancelAnimationFrame(this.replaceFrame);
    this.replaceFrame = requestAnimationFrame(() => {
      if (this.pointerDown) {
        this.scheduleEditRender();
        return;
      }
      const focused = this.shadowRoot?.activeElement;
      const active = focused instanceof HTMLElement ? focused.dataset : undefined;
      this.render();
      if (!active?.field && !active?.key) return;
      const matching = Array.from(this.surface.querySelectorAll<HTMLElement>("[data-field], [data-key]"))
        .find(element => active.key
          ? element.dataset.key === active.key
          : element.dataset.field === active.field && element.dataset.id === active.id);
      matching?.focus({ preventScroll: true });
    });
  }

  get study(): ManualStudyInput | undefined { return structuredClone(this.draft); }

  set study(value: ManualStudyInput | undefined) {
    this.draft = structuredClone(value);
    this.showConditions = false;
    this.shiftDrafts = {};
    this.scenarioId = value?.scenarios[0]?.id ?? "";
    this.render();
  }

  private update(draft: ManualStudyInput, focusKey?: string, defer = false): void {
    this.draft = draft;
    if (defer) this.scheduleEditRender();
    else this.render();
    if (focusKey) {
      const field = Array.from(this.surface.querySelectorAll<HTMLElement>("[data-key]"))
        .find(element => element.dataset.key === focusKey);
      field?.focus();
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

  private readonly onClick = (event: Event): void => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>("button[data-action]");
    const study = this.draft;
    if (!button || !study) return;
    const id = button.dataset.id;
    const conditions = study.conditions ?? { shift: blankShift };
    const shift = conditions.shift;

    switch (button.dataset.action) {
      case "conditions":
        this.showConditions = !this.showConditions;
        this.render();
        this.surface.querySelector<HTMLElement>('[data-action="conditions"]')?.focus();
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
      case "operation-details": {
        const element = Array.from(this.surface.querySelectorAll<HTMLInputElement>("[data-key]"))
          .find(field => field.dataset.key === `name:${id}`);
        element?.focus();
        break;
      }
    }
  };

  private setShift(shift: ShiftInput, focusKey?: string, defer = false): void {
    const study = this.draft;
    if (study) this.update({ ...study, conditions: { ...study.conditions, shift } }, focusKey, defer);
  }

  private readonly onChange = (event: Event): void => {
    const field = event.target;
    const study = this.draft;
    if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement) || !study) return;
    const { field: kind, id, key } = field.dataset;
    const value = field.value;
    const conditions: ProductionConditionsInput = study.conditions ?? { shift: blankShift };
    const shift = conditions.shift;

    switch (kind) {
      case "study-name":
        if (value.trim()) this.update({ ...study, name: value.trim() }, undefined, true);
        else field.value = study.name;
        break;
      case "scenario":
        this.scenarioId = value;
        this.render();
        this.surface.querySelector<HTMLElement>('[data-field="scenario"]')?.focus();
        break;
      case "operation-name":
      case "duration":
        this.update({ ...study, operations: study.operations.map(operation => operation.id === id
          ? { ...operation, ...(kind === "operation-name" ? { name: value } :
            { durationSeconds: value === "" ? null : Number(value) }) } : operation) }, undefined, true);
        break;
      case "station":
        this.moveOperation(id ?? "", value, key);
        break;
      case "station-name":
        this.update({ ...study, stations: study.stations.map(station => station.id === id ? {
          ...station, name: value,
        } : station) }, undefined, true);
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
          }), key);
        }
        break;
      case "start":
      case "end":
        if (shift.mode === "CLOCK") this.setShift({ ...shift, [kind]: value }, undefined, true);
        break;
      case "shift-minutes":
        if (shift.mode === "MINUTES") this.setShift({ ...shift, durationMinutes: Number(value) }, undefined, true);
        break;
      case "break-start":
      case "break-end":
        if (shift.mode === "CLOCK") {
          const endpoint = kind === "break-start" ? "start" : "end";
          this.setShift({ ...shift, breaks: shift.breaks.map((pause, index) =>
            index === Number(id) ? { ...pause, [endpoint]: value } : pause) }, undefined, true);
        }
        break;
      case "break-minutes":
        if (shift.mode === "MINUTES") this.setShift({ ...shift, breaks: shift.breaks.map((pause, index) =>
          index === Number(id) ? Number(value) : pause) }, undefined, true);
        break;
      case "demand": {
        const { demandUnitsPerShift: previous, ...rest } = conditions;
        this.update({ ...study, conditions: value === "" ? rest : { ...rest, demandUnitsPerShift: Number(value) } }, undefined, true);
        break;
      }
      case "batch": {
        const { batchUnits: previous, ...rest } = conditions;
        this.update({ ...study, conditions: value === "" ? rest : { ...rest, batchUnits: Number(value) } }, undefined, true);
        break;
      }
    }
  };

  private readonly onDragStart = (event: DragEvent): void => {
    const element = (event.target as HTMLElement).closest<HTMLElement>("[data-drag]");
    if (!element?.dataset.drag || !event.dataTransfer) return;
    this.pointerDown = false;
    this.draggedOperation = element.dataset.drag;
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

  private renderConditions(conditions: ProductionConditionsInput): string {
    const { shift, demandUnitsPerShift, batchUnits } = conditions;
    const timeInput = (label: string, type: string, field: string, value: string, id = "") =>
      `<label class="field">${label}<input type="${type}" data-field="${field}" data-id="${id}"
        value="${escapeText(value)}" ${type === "number" ? 'min="1" step="1"' : ""}></label>`;
    const shiftFields = shift.mode === "CLOCK"
      ? timeInput("Início", "time", "start", shift.start) + timeInput("Fim", "time", "end", shift.end)
      : timeInput("Duração (min)", "number", "shift-minutes", String(shift.durationMinutes || ""));
    const pauses = shift.mode === "CLOCK"
      ? shift.breaks.map((pause, i) => timeInput(`Pausa ${i + 1} · início`, "time", "break-start", pause.start, String(i))
        + timeInput("Fim", "time", "break-end", pause.end, String(i)))
      : shift.breaks.map((pause, i) => timeInput(`Pausa ${i + 1} (min)`, "number", "break-minutes", String(pause || ""), String(i)));
    const summary = summarizeShift(shift);
    const labels: Record<string, string> = {
      BREAK_OVERLAP: "Há pausas sobrepostas.", BREAK_OUTSIDE_SHIFT: "Há uma pausa fora do turno.",
      EMPTY_BREAK: "Informe início e fim diferentes para a pausa.", INVALID_CLOCK_TIME: "Complete os horários do turno e das pausas.",
      AMBIGUOUS_SHIFT: "O início e o fim do turno precisam ser diferentes.",
      INVALID_NUMBER: "Use durações inteiras válidas.", NO_PRODUCTIVE_TIME: "Reserve tempo produtivo no turno.",
    };
    return `<section class="panel conditions" id="conditions" aria-labelledby="conditions-title">
      <h2 id="conditions-title">Condições de produção</h2>
      <div class="fields">
        <label class="field">Modo de turno<select data-field="mode" data-key="mode">
          <option value="CLOCK" ${shift.mode === "CLOCK" ? "selected" : ""}>Horários</option>
          <option value="MINUTES" ${shift.mode === "MINUTES" ? "selected" : ""}>Minutos</option>
        </select></label>${shiftFields}
        ${timeInput("Demanda por turno", "number", "demand", String(demandUnitsPerShift ?? ""))}
        ${timeInput("Tamanho do lote", "number", "batch", String(batchUnits ?? ""))}
      </div>
      ${pauses.map((pause, i) => `<div class="fields pause">${pause}<button class="button icon" data-action="remove-break"
        data-id="${i}" aria-label="Remover pausa ${i + 1}">×</button></div>`).join("")}
      <button class="button" data-action="add-break" data-key="add-break">+ Adicionar pausa</button>
      ${demandUnitsPerShift !== undefined && (!Number.isSafeInteger(demandUnitsPerShift) || demandUnitsPerShift < 1)
        ? '<p class="warning" role="status">Informe uma demanda inteira positiva.</p>' : ""}
      ${batchUnits !== undefined && (!Number.isSafeInteger(batchUnits) || batchUnits < 1)
        ? '<p class="warning" role="status">Informe um tamanho de lote inteiro positivo.</p>' : ""}
      ${summary.ok ? `<p class="note">${format(summary.value.grossMinutes)} min brutos · ${format(summary.value.breakMinutes)} min de pausa</p>` :
        `<p class="warning" role="status">${[...new Set(summary.issues.map(issue => labels[issue.code] ?? "Revise as condições do turno."))].join(" ")}</p>`}
    </section>`;
  }

  private render(): void {
    cancelAnimationFrame(this.replaceFrame);
    const study = this.draft;
    if (!study) { this.surface.replaceChildren(); return; }
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
    const metric = (label: string, value: string, detail: string) =>
      `<div class="metric"><span>${label}</span><strong>${value}</strong><small>${detail}</small></div>`;
    const axisValues = Array.from({ length: 5 }, (_, i) => scale * i / 4);
    const stationCharts = stations.map((station, i) => `<div class="station-chart" data-drop="${escapeText(station.id)}">
      <div class="track" aria-label="${escapeText(station.name)}, ${format(station.load)} segundos conhecidos">
        <div class="stack" style="height:${station.load / scale * 100}%">
          ${station.items.filter(item => item.seconds !== null).map(item => `<button type="button" class="segment" draggable="true"
            data-drag="${escapeText(item.id)}" data-action="operation-details" data-id="${escapeText(item.id)}"
            style="flex-grow:${item.seconds};background:${item.color}"
            title="${escapeText(item.name)} · ${format(item.seconds ?? 0)} s"
            aria-label="${escapeText(item.name)}, ${format(item.seconds ?? 0)} segundos. Ir para a operação.">${escapeText(item.name)}</button>`).join("")}
        </div>
        <span class="load ${takt !== null && station.load > takt ? "over" : ""}"
          style="bottom:${station.load / scale * 100}%">${format(station.load)} s${station.unknown ? "*" : ""}${takt !== null && station.load > takt ? ' <span title="Acima do takt" aria-label="Acima do takt">↑</span>' : ""}</span>
      </div>
      <div class="station-label">
        <input data-field="station-name" data-id="${escapeText(station.id)}" value="${escapeText(station.name)}" aria-label="Nome do posto ${i + 1}">
        <button class="button icon remove-station" data-action="remove-station" data-id="${escapeText(station.id)}"
          aria-label="Remover posto ${i + 1}" title="Remover posto">×</button>
      </div>
    </div>`).join("");
    const rows = operations.map((operation, index) => {
      const id = escapeText(operation.id);
      return `<tr><td class="row-number"><i style="background:${operation.color}"></i>${String(index + 1).padStart(2, "0")}</td>
      <td><input data-field="operation-name" data-id="${id}" data-key="name:${id}" value="${escapeText(operation.name)}"
        aria-label="Nome da operação ${index + 1}" required></td>
      <td><input class="duration" type="number" min="0" step="any" placeholder="Desconhecido" data-field="duration"
        data-id="${id}" aria-label="Tempo da operação ${index + 1} em segundos" value="${operation.durationSeconds ?? ""}"></td>
      <td><select data-field="station" data-id="${id}" data-key="station:${id}" aria-label="Posto da operação ${index + 1}">
        <option value="">Sem posto</option>${stations.map(station =>
          `<option value="${escapeText(station.id)}" ${assignment.get(operation.id) === station.id ? "selected" : ""}>${escapeText(station.name)}</option>`).join("")}</select></td>
      <td><button class="button icon" data-action="remove-operation" data-id="${id}" aria-label="Remover operação ${index + 1}">×</button></td>
      </tr>`;
    }).join("");

    this.surface.innerHTML = `<div class="studio">
      <header class="top"><div class="brand"><span class="brand-icon" aria-hidden="true"><i></i><i></i><i></i></span>
        <div><strong>Line Balance Studio</strong><small>DELPI · Engenharia de Processos</small></div></div>
        <span class="draft">Rascunho manual</span></header>
      <div class="workspace">
        <section class="study-header" aria-label="Estudo">
          <div class="study-title"><h1>${escapeText(study.name)}</h1>
            <label class="edit-name">Nome do estudo<input data-field="study-name" value="${escapeText(study.name)}"></label></div>
          <div class="controls">
            ${study.scenarios.length > 1 ? `<select aria-label="Cenário" data-field="scenario">${study.scenarios.map(item =>
              `<option value="${escapeText(item.id)}" ${item.id === scenario?.id ? "selected" : ""}>${escapeText(item.name)}</option>`).join("")}</select>` : ""}
            <button class="button" data-action="conditions" aria-expanded="${this.showConditions}" ${this.showConditions ? 'aria-controls="conditions"' : ""}>Condições de produção</button>
          </div>
        </section>
        ${this.showConditions ? this.renderConditions(conditions) : ""}
        <section class="metrics" aria-label="Indicadores" aria-live="polite">
          ${metric("Takt de referência", takt === null ? "—" : `${format(takt)} s`, "por unidade")}
          ${metric("Tempo produtivo", productive === null ? "—" : `${format(productive)} min`, "por turno")}
          ${metric("Maior carga", stations.length ? `${format(maxLoad)} s` : "—", incomplete ? "carga conhecida · parcial" : "por posto")}
          ${metric("Sem posto", String(unassigned), `de ${operations.length} operações`)}
        </section>
        <section class="panel" aria-labelledby="chart-title">
          <div class="panel-heading"><div><h2 id="chart-title">Yamazumi</h2><p>Carga por posto · segundos</p></div>
            <button class="button" data-action="add-station" data-key="add-station">+ Adicionar posto</button></div>
          ${stations.length ? `<div class="chart-scroll"><div class="chart" style="--station-count:${stations.length}">
            <div class="plot">
              ${axisValues.map(value => `<div class="gridline" style="bottom:${value / scale * 100}%"><span>${format(value)}</span></div>`).join("")}
              ${takt === null ? "" : `<div class="takt" style="bottom:${takt / scale * 100}%"><span>Takt ${format(takt)} s</span></div>`}
            </div>
            ${stationCharts}
          </div></div>` : '<p class="note">Adicione um posto para montar o gráfico.</p>'}
          <div class="chart-footer"><span>Arraste um bloco para outro posto ou use a tabela.</span><span class="unassign-drop" data-drop="">Solte aqui para desatribuir</span>
            ${incomplete ? "<span>* Carga parcial por tempo desconhecido.</span>" : ""}</div>
        </section>
        <section class="panel" aria-labelledby="table-title">
          <div class="panel-heading"><div><h2 id="table-title">Operações</h2><p>Edite os tempos e atribua um posto a cada operação.</p></div>
          <button class="button primary" data-action="add-operation" data-key="add-operation">+ Adicionar operação</button></div>
          ${invalidOperations ? '<p class="warning" role="status">Revise os nomes e os tempos. Use um valor positivo ou deixe o tempo em branco.</p>' : ""}
          ${rows ? `<div class="table-scroll"><table><thead><tr><th scope="col">#</th><th scope="col">Operação</th>
            <th scope="col">Tempo (s)</th><th scope="col">Posto</th><th scope="col"><span class="sr-only">Remover</span></th>
          </tr></thead><tbody>${rows}</tbody></table></div>` : '<p class="note">Adicione uma operação para começar.</p>'}
        </section>
      </div>
    </div>`;
  }
}

export function registerLineBalanceStudio(): void {
  if (!customElements.get("delpi-line-balance-studio")) {
    customElements.define("delpi-line-balance-studio", LineBalanceStudioElement);
  }
}
