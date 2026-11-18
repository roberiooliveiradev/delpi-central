/** Adaptador do contrato oficial de roteiro para o DELPI Line Balance
 * Studio (pacote `plugins/delpi-line-balance-studio`). É o ÚNICO ponto
 * de conversão entre o vocabulário oficial (`RoutingStageView`) e o DTO
 * do estudo (`StudioStudyInput`) — unidades convertidas uma única vez
 * aqui (min/peça → s/peça; setup fica fora do tempo peça), identidade e
 * proveniência preservadas (OBSERVED/UNKNOWN/DRAFT_LOCAL/SIMULATION). */

import type { TableExportPayload } from "@delpi/plugin-ui/index";
import {
  createObservedStudy,
  createManualStudy,
  summarizeShift,
  type ManualStudyInput,
  type ObservedOperationInput,
  type ObservedStudyInput,
  type ScenarioInput,
  type Station,
  type StudioStudyInput,
} from "@delpi/line-balance-studio";
import type { RoutingStageView } from "../../products/routing/routingGrouping";
import {
  computeSourceFingerprint,
  type RoutingStudyDraft,
} from "../../products/routing/routingStudyDraft";
import type { BalanceRunParams } from "../../products/routing/useRoutingStudyDraft";

const SECONDS_PER_MINUTE = 60;

/** min/peça → s/peça, arredondando a milissegundo — única conversão. */
function minutesToSeconds(minutes: number | null): number | null {
  if (minutes == null || !Number.isFinite(minutes)) return null;
  return Math.round(minutes * SECONDS_PER_MINUTE * 1000) / 1000;
}

/** Referência oficial legível — rastreabilidade, nunca identidade nova. */
function operationReference(parts: {
  code?: string | null;
  workCenter?: string | null;
  resource?: string | null;
  setupHours?: number | null;
}): string | undefined {
  const segments = [
    parts.code ? `OP ${parts.code}` : null,
    parts.workCenter ? `CT ${parts.workCenter}` : null,
    parts.resource ?? null,
    parts.setupHours != null ? `Setup ${parts.setupHours} h/lote` : null,
  ].filter((s): s is string => Boolean(s));
  return segments.length ? segments.join(" · ") : undefined;
}

function defaultScenarios(): ScenarioInput[] {
  return [{ id: "scenario-a", name: "Cenário A", assignments: [] }];
}

/** Semente OBSERVED a partir do estágio oficial já deduplicado pelo
 * adapter de domínio (`groupRoutingRows` — identidade `op.key`). */
export function buildObservedStudyInput(args: {
  stage: RoutingStageView;
  productCode: string;
  branch: string;
  stageName?: string;
  truncated?: boolean;
  stations?: Station[];
  scenarios?: ScenarioInput[];
}): ObservedStudyInput {
  const { stage } = args;
  const operations: ObservedOperationInput[] = stage.operations.map((op) => {
    const reference = operationReference({
      code: op.operation_code,
      workCenter: op.work_center,
      resource: op.resource_code,
      setupHours: op.setup_hours,
    });
    return {
      id: op.key,
      name: op.operation_description?.trim() || op.operation_code || "Operação",
      durationSeconds: minutesToSeconds(op.time_minutes_piece),
      ...(reference ? { reference } : {}),
    };
  });
  return {
    id: `lb-${stage.key}`,
    name: `Balanceamento — ${stage.product_code || args.productCode}`,
    source: "OBSERVED_ROUTING",
    routing: {
      productCode: args.productCode,
      branchCode: args.branch || "all",
      stageId: stage.key,
      stageLabel: args.stageName,
      ...(stage.route_code ? { routeCode: stage.route_code } : {}),
      ...(args.truncated ? { truncated: true } : {}),
    },
    operations,
    stations: args.stations ?? [],
    scenarios: args.scenarios ?? defaultScenarios(),
  };
}

/** Semente MANUAL — estudo sem SKU, mantido intacto pelo contrato. */
export function buildManualStudyInput(): ManualStudyInput {
  return {
    id: "lb-manual",
    name: "Novo estudo manual",
    source: "MANUAL",
    operations: [],
    stations: [],
    scenarios: defaultScenarios(),
  };
}

/* --- Rascunho em sessionStorage --------------------------------------- */

export const STUDIO_DRAFT_PREFIX = "engineering:processes:line-balance:studio:v1";

export type StudioDraftContext = {
  productCode: string;
  branch: string;
  stageKey: string;
  sourceFingerprint: string;
};

export type StudioDraftEnvelope = {
  schemaVersion: 1;
  savedAt: string;
  context: StudioDraftContext;
  study: StudioStudyInput;
};

export function studioDraftKey(identity: string | null, ctx: Omit<StudioDraftContext, "sourceFingerprint">): string {
  const who = identity?.trim() || "anonymous";
  return [STUDIO_DRAFT_PREFIX, who, ctx.productCode, ctx.branch.trim() || "all", ctx.stageKey].join(":");
}

function contextOf(args: { productCode: string; branch: string; stage: RoutingStageView }): StudioDraftContext {
  return {
    productCode: args.productCode,
    branch: args.branch,
    stageKey: args.stage.key,
    sourceFingerprint: computeSourceFingerprint(args.stage),
  };
}

export { contextOf as studioDraftContext };

function safeStorage(): Storage | null {
  try {
    return globalThis.sessionStorage ?? null;
  } catch {
    return null;
  }
}

export type StudioDraftLoad =
  | { status: "ok"; study: StudioStudyInput }
  | { status: "stale" }
  | { status: "none" };

/** Restaura rascunho do mesmo contexto/fingerprint; `stale` quando o
 * roteiro oficial mudou desde o salvamento. */
export function loadStudioDraft(key: string, ctx: StudioDraftContext): StudioDraftLoad {
  const storage = safeStorage();
  if (!storage) return { status: "none" };
  let raw: string | null = null;
  try {
    raw = storage.getItem(key);
  } catch {
    return { status: "none" };
  }
  if (!raw) return { status: "none" };
  try {
    const data = JSON.parse(raw) as Partial<StudioDraftEnvelope>;
    if (
      data.schemaVersion !== 1 ||
      !data.context ||
      data.context.productCode !== ctx.productCode ||
      data.context.branch !== ctx.branch ||
      data.context.stageKey !== ctx.stageKey ||
      !data.study ||
      typeof data.study !== "object"
    ) {
      return { status: "none" };
    }
    if (data.context.sourceFingerprint !== ctx.sourceFingerprint) return { status: "stale" };
    const study = data.study as StudioStudyInput;
    const valid =
      study.source === "OBSERVED_ROUTING" ? createObservedStudy(study) : createManualStudy(study);
    return valid.ok ? { status: "ok", study } : { status: "stale" };
  } catch {
    return { status: "none" };
  }
}

export type StudioDraftSave = "saved" | "unavailable" | "quota" | "error";

export function saveStudioDraft(key: string, ctx: StudioDraftContext, study: StudioStudyInput): StudioDraftSave {
  const storage = safeStorage();
  if (!storage) return "unavailable";
  try {
    const envelope: StudioDraftEnvelope = {
      schemaVersion: 1,
      savedAt: new Date().toISOString(),
      context: ctx,
      study,
    };
    storage.setItem(key, JSON.stringify(envelope));
    return "saved";
  } catch (e) {
    if (e instanceof DOMException && e.name === "QuotaExceededError") return "quota";
    return "error";
  }
}

export function clearStudioDraft(key: string): boolean {
  const storage = safeStorage();
  if (!storage) return false;
  try {
    storage.removeItem(key);
    return storage.getItem(key) === null;
  } catch {
    return false;
  }
}

/* --- Migração de rascunho legado (formato V2 de postos) ---------------- */

/** Converte o formato anterior (`useRoutingStudyDraft`, posts clientId +
 * operationRefs) para o DTO do Studio. Referências que não existem mais
 * no roteiro atual são descartadas — nunca inventadas. */
export function migrateLegacyDraft(
  legacy: RoutingStudyDraft,
  observed: ObservedStudyInput,
): StudioStudyInput {
  const validOps = new Set(observed.operations.map((op) => op.id));
  const stationsByPost = new Map<string, Station>();
  const scenarios: ScenarioInput[] = legacy.scenarios.map((scenario) => {
    const assignments: ScenarioInput["assignments"][number][] = [];
    const taken = new Set<string>();
    for (const post of scenario.posts) {
      if (!stationsByPost.has(post.clientId)) {
        stationsByPost.set(post.clientId, { id: post.clientId, name: post.name });
      }
      for (const ref of post.operationRefs) {
        if (validOps.has(ref) && !taken.has(ref)) {
          assignments.push({ operationId: ref, stationId: post.clientId });
          taken.add(ref);
        }
      }
    }
    return { id: scenario.clientId, name: `Cenário ${scenario.label}`, assignments };
  });
  return {
    ...observed,
    stations: [...stationsByPost.values()],
    scenarios: scenarios.length ? scenarios : defaultScenarios(),
  };
}

/* --- Parâmetros M1 derivados das condições do estudo -------------------- */

export type BalanceParamsResult =
  | { ok: true; params: BalanceRunParams }
  | { ok: false; issues: string[] };

/** Deriva o vocabulário fechado do POST oficial a partir das condições
 * do estudo Studio — sem recalcular balanceamento no host. */
export function deriveBalanceParams(
  study: StudioStudyInput | undefined,
  branch: string,
): BalanceParamsResult {
  const issues: string[] = [];
  if (!study) return { ok: false, issues: ["Carregue um estudo antes de executar a análise oficial."] };
  const conditions = study.conditions;
  if (!conditions) return { ok: false, issues: ["Informe as condições de produção no estudo para executar a análise M1."] };
  const summary = summarizeShift(conditions.shift);
  let productive = 0;
  if (summary.ok) {
    productive = summary.value.productiveMinutes;
  } else {
    issues.push("Turno inválido — revise início/fim ou a duração e as pausas.");
  }
  const demand = conditions.demandUnitsPerShift;
  if (demand == null || !Number.isSafeInteger(demand) || demand <= 0) {
    issues.push("Informe a demanda por turno (inteiro positivo) para a análise M1.");
  }
  const batch = conditions.batchUnits;
  if (batch != null && (!Number.isSafeInteger(batch) || batch <= 0)) {
    issues.push("Lote inválido — informe um inteiro positivo ou deixe em branco.");
  }
  if (issues.length) return { ok: false, issues };
  return {
    ok: true,
    params: {
      demand: demand!,
      available_minutes: productive,
      ...(batch != null ? { batch_size: batch } : {}),
      ...(study.stations.length ? { num_stations: study.stations.length } : {}),
      ...(branch ? { branch } : {}),
    },
  };
}

/* --- Exportação do estudo ---------------------------------------------- */

const EXPORT_LIMITATION =
  "Estudo local — não é roteiro aprovado nem dimensionamento validado; sem precedência, simultaneidade ou viabilidade de recursos.";

export function buildStudioExportPayload(args: {
  productCode: string;
  branch: string;
  stageLabel: string;
  study: StudioStudyInput;
}): TableExportPayload {
  const { study } = args;
  const observedIds = new Set(
    study.source === "OBSERVED_ROUTING" ? study.operations.map((op) => op.id) : [],
  );
  const conditions = study.conditions;
  const summary = conditions ? summarizeShift(conditions.shift) : null;
  const productive = summary?.ok ? summary.value.productiveMinutes : null;
  const ctx = {
    produto: args.productCode || "—",
    filial: args.branch || "—",
    estagio: args.stageLabel || "—",
  };
  const rows = study.scenarios.flatMap((scenario) => {
    const stationByOp = new Map(scenario.assignments.map((a) => [a.operationId, a.stationId]));
    const stationName = new Map(study.stations.map((s) => [s.id, s.name]));
    return study.operations.map((op) => {
      const stationId = stationByOp.get(op.id);
      return {
        ...ctx,
        cenario: scenario.name,
        posto: stationId ? stationName.get(stationId) ?? stationId : "Sem posto",
        operacao: op.id,
        descricao: op.name,
        referencia: "reference" in op && op.reference ? op.reference : "—",
        tempo_s:
          op.durationSeconds == null
            ? "UNKNOWN"
            : op.durationSeconds.toLocaleString("pt-BR", { maximumFractionDigits: 3 }),
        demanda: conditions?.demandUnitsPerShift ?? "—",
        tempo_produtivo_min: productive ?? "—",
        lote: conditions?.batchUnits ?? "—",
        origem: observedIds.has(op.id) ? "Oficial" : "Local",
        proveniencia:
          op.durationSeconds == null
            ? "UNKNOWN"
            : observedIds.has(op.id)
              ? "OBSERVED"
              : "PROVIDED",
        limitacao: EXPORT_LIMITATION,
      };
    });
  });
  return {
    title: `Balanceamento de Linha — ${ctx.produto} — DRAFT_LOCAL · SIMULATION`,
    columns: [
      { key: "produto", label: "Produto" },
      { key: "filial", label: "Filial" },
      { key: "estagio", label: "Estágio" },
      { key: "cenario", label: "Cenário" },
      { key: "posto", label: "Posto" },
      { key: "operacao", label: "Operação (id)" },
      { key: "descricao", label: "Descrição" },
      { key: "referencia", label: "Referência oficial" },
      { key: "tempo_s", label: "Tempo por peça (s)" },
      { key: "demanda", label: "Demanda (peças/turno)" },
      { key: "tempo_produtivo_min", label: "Tempo produtivo (min)" },
      { key: "lote", label: "Lote (peças)" },
      { key: "origem", label: "Origem" },
      { key: "proveniencia", label: "Proveniência" },
      { key: "limitacao", label: "Limitação" },
    ],
    rows,
  };
}
