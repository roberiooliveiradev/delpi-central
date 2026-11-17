/** Aba Roteiro da Ficha do Produto — Routing Study Workspace V2.
 *
 * UMA página scrollável (sem navegação interna de três abas — decisão
 * V2): contexto/filtros → KPIs → operações oficiais → estudo de
 * balanceamento (análise rápida OU postos hipotéticos) → resultados e
 * cenários → análise visual → proveniência.
 *
 * Consulta oficial `GET /v1/products/{code}/routing` (delegação ao
 * owner) e cálculo determinístico `POST /v1/products/{code}/line-balance`
 * do domínio EVA. O MFE nunca recalcula: dedup, conteúdo de trabalho,
 * takt e cenários FFD vêm do backend. Aritméticas locais são só de
 * exibição (prévia de takt, consolidação visual, conversão min→s).
 *
 * Postos hipotéticos, operadores e paralelismo são `DRAFT_LOCAL /
 * SIMULATION` — persistidos em sessionStorage por identidade+contexto
 * (routing-study-session-state-contract.md), nunca enviados ao
 * contrato `line-balance` nem apresentados como viabilidade validada. */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  ChevronDown,
  ChevronUp,
  Clock3,
  Factory,
  ListOrdered,
  Wrench,
} from "lucide-react";

import { getCurrentAccessToken, HomeApiError } from "../../../api/httpClient";
import { getSubjectFromAccessToken } from "../../../app/authDisplayName";
import {
  EngineeringActionButton,
  EngineeringChartCard,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringFilterSelect,
  EngineeringFormActions,
  EngineeringInteractiveDataCard,
  EngineeringKpiCard,
  EngineeringLoadingActivityCard,
  EngineeringScopeChipBar,
  EngineeringSectionCard,
  EngineeringSegmentToggle,
  EngineeringStateBanner,
  EngineeringStatusBadge,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import { EngineeringConfirmDialog } from "../../../ui/EngineeringConfirmDialog";
import type { MultiTypeSeriesSpec } from "@delpi/plugin-ui/index";
import {
  fetchProductRouting,
  postProductLineBalance,
} from "../api/productApi";
import { DataTable, type DataTableColumn } from "../components/dataTableUi";
import type {
  LineBalanceStage,
  ProductLineBalanceResult,
  ProductRoutingResult,
} from "../types";
import {
  resolveChartTimeUnit,
  toChartValue,
  type ChartTimeUnit,
} from "./chartUnits";
import { RoutingSeriesChart } from "./RoutingSeriesChart";
import {
  buildOpsTimeExportPayload,
  buildOpsVsTaktExportPayload,
  buildSimDistributionExportPayload,
  type RoutingChartContext,
} from "./routingChartExport";
import { PostConfigurator } from "./PostConfigurator";
import {
  formatHours,
  formatMinutes,
  formatRatio,
  groupRoutingRows,
  stageLabel,
  type RoutingOperationView,
  type RoutingStageView,
} from "./routingGrouping";
import { inputsFingerprint, type StudyInputs } from "./routingStudyDraft";
import {
  useRoutingStudyDraft,
  type BalanceRunParams,
  type ScenarioState,
} from "./useRoutingStudyDraft";


type RoutingData = ProductRoutingResult & { truncated?: boolean };

function isForbidden(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 403;
}

function isNotFound(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 404;
}

/** Estados honestos da fonte — 403/404/502 jamais viram "sem dados". */
function RoutingSourceError({ error }: { error: unknown }) {
  if (isForbidden(error)) {
    return (
      <EngineeringEmptyState message="Acesso negado pela fonte oficial — você não tem autorização para consultar o roteiro." />
    );
  }
  if (isNotFound(error)) {
    return (
      <EngineeringEmptyState message="Produto não encontrado ou sem roteiro na fonte oficial." />
    );
  }
  return (
    <EngineeringStateBanner variant="error">
      {error instanceof HomeApiError
        ? error.message
        : "Fonte oficial de roteiro indisponível."}
    </EngineeringStateBanner>
  );
}

function stageKeyOf(stage: {
  product_code: string;
  bom_level: number;
}): string {
  return `${stage.product_code}#${stage.bom_level}`;
}

/* --- Operações ------------------------------------------------------- */

function OperationDetail({ op }: { op: RoutingOperationView }) {
  return (
    <div className="engineering-routing__op-detail">
      <EngineeringDetailFieldGrid
        fields={[
          { label: "Recurso", value: op.resource_code ?? "—" },
          { label: "Setup", value: formatHours(op.setup_hours) },
          { label: "Tipo", value: op.operation_type ?? "—" },
          {
            label: "Operação obrigatória",
            value: op.mandatory_operation ?? "—",
          },
          {
            label: "Sequência obrigatória",
            value: op.mandatory_sequence ?? "—",
          },
          {
            label: "Apontamento obrigatório",
            value: op.mandatory_report ?? "—",
          },
          {
            label: "Linhas oficiais fundidas",
            value: String(op.source_rows),
            hint: "A fonte repete a operação uma vez por componente da BOM — a consolidação usa a identidade oficial.",
          },
        ]}
      />
      {op.components.length ? (
        <div
          role="group"
          aria-label={`Componentes da operação ${op.operation_code}`}
        >
          <p className="engineering-routing__muted">
            Componentes vinculados
          </p>
          <ul className="engineering-routing__components">
            {op.components.map((c) => (
              <li key={c.code}>
                <strong>{c.code}</strong>
                {c.description ? ` — ${c.description}` : ""}
                {c.sequence ? (
                  <span className="engineering-routing__muted">
                    {` · seq. ${c.sequence}`}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="engineering-routing__muted">
          Nenhum componente associado a esta operação no payload oficial.
        </p>
      )}
    </div>
  );
}

function OperationCard({
  op,
  expanded,
  onToggle,
}: {
  op: RoutingOperationView;
  expanded: boolean;
  onToggle: () => void;
}) {
  const timeLabel =
    op.time_minutes_piece != null
      ? `${formatMinutes(op.time_minutes_piece)}/peça`
      : "—";
  return (
    <EngineeringInteractiveDataCard
      ariaLabel={`Operação ${op.operation_code || "—"} · ${
        op.operation_description ?? "—"
      }`}
      ariaExpanded={expanded}
      onActivate={onToggle}
    >
      <div className="engineering-routing__op-head">
        <span className="engineering-routing__op-num" aria-hidden="true">
          {op.operation_code || "—"}
        </span>
        <span className="engineering-routing__op-text">
          <strong className="engineering-routing__op-desc">
            {op.operation_description ?? "—"}
          </strong>
          <span className="engineering-routing__op-meta">
            {op.work_center ?? "—"} · {timeLabel}
          </span>
        </span>
        {expanded ? (
          <ChevronUp
            className="engineering-routing__op-chevron"
            size={18}
            aria-hidden="true"
          />
        ) : (
          <ChevronDown
            className="engineering-routing__op-chevron"
            size={18}
            aria-hidden="true"
          />
        )}
      </div>
      {expanded ? <OperationDetail op={op} /> : null}
    </EngineeringInteractiveDataCard>
  );
}

function StageKpis({ stage }: { stage: RoutingStageView }) {
  const workCenters = new Set(
    stage.operations.map((o) => o.work_center).filter(Boolean),
  ).size;
  const resources = new Set(
    stage.operations.map((o) => o.resource_code).filter(Boolean),
  ).size;
  const timed = stage.operations.filter((o) => o.time_minutes_piece != null);
  const allTimed = timed.length === stage.operations.length;
  const stageMinutes = timed.reduce(
    (sum, o) => sum + (o.time_minutes_piece ?? 0),
    0,
  );
  return (
    <div className="engineering-routing__kpis" role="group" aria-label="Indicadores do estágio selecionado">
      <EngineeringKpiCard
        title="Operações"
        titleHint="Operações distintas pela identidade oficial (produto × nível × operação × CT × recurso) — não é o número de linhas do retorno."
        value={String(stage.operations.length)}
        icon={<ListOrdered size={18} aria-hidden="true" />}
      />
      <EngineeringKpiCard
        title="Centro de trabalho"
        value={String(workCenters)}
        icon={<Factory size={18} aria-hidden="true" />}
      />
      <EngineeringKpiCard
        title="Recurso"
        value={String(resources)}
        icon={<Wrench size={18} aria-hidden="true" />}
      />
      <EngineeringKpiCard
        title="Tempo padrão"
        titleHint="Soma dos tempos por peça com valor oficial no estágio selecionado — não soma outros níveis da BOM."
        value={formatMinutes(stageMinutes)}
        subtitle={allTimed ? undefined : "parcial — há operação sem tempo oficial"}
        icon={<Clock3 size={18} aria-hidden="true" />}
      />
    </div>
  );
}

function OperationsSection({
  stage,
  rowsTotal,
}: {
  stage: RoutingStageView;
  rowsTotal: number;
}) {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  useEffect(() => {
    setExpandedKey(null);
  }, [stage.key]);

  const setupTotal = stage.operations.reduce(
    (sum, o) => sum + (o.setup_hours ?? 0),
    0,
  );

  return (
    <>
      <EngineeringDetailCard
        title="Operações do estágio"
        titleHint="Um card por operação única. Selecione um card para expandir recurso, setup, obrigatoriedade e componentes."
        headerActions={
          <EngineeringStatusBadge
            label={`${stage.operations.length} ${stage.operations.length === 1 ? "operação" : "operações"}`}
            variant="info"
          />
        }
      >
        {stage.operations.length ? (
          <div
            className="engineering-routing__ops"
            role="list"
            aria-label="Operações do estágio"
          >
            {stage.operations.map((op) => (
              <div role="listitem" key={op.key}>
                <OperationCard
                  op={op}
                  expanded={expandedKey === op.key}
                  onToggle={() =>
                    setExpandedKey((k) => (k === op.key ? null : op.key))
                  }
                />
              </div>
            ))}
          </div>
        ) : (
          <EngineeringEmptyState message="Nenhuma operação neste estágio." />
        )}
      </EngineeringDetailCard>

      <EngineeringSectionCard
        title="Detalhes técnicos do estágio"
        subtitle="Métricas secundárias do retorno oficial — não são indicadores de desempenho."
        collapsible
        defaultOpen={false}
      >
        <EngineeringDetailFieldGrid
          fields={[
            {
              label: "Linhas da consulta",
              value: String(rowsTotal),
              hint: "Registros retornados pela fonte — uma operação pode repetir por componente.",
            },
            {
              label: "Setup total do estágio",
              value: setupTotal ? formatHours(setupTotal) : "—",
            },
            {
              label: "Estágio",
              value: stageLabel(stage),
            },
            {
              label: "Roteiro",
              value: stage.route_code ?? "—",
            },
            {
              label: "Filial",
              value: stage.branch ?? "todas",
            },
            {
              label: "Componentes vinculados",
              value: String(
                stage.operations.reduce(
                  (sum, o) => sum + o.components.length,
                  0,
                ),
              ),
            },
          ]}
        />
      </EngineeringSectionCard>
    </>
  );
}

/* --- Estudo de balanceamento ------------------------------------------- */

function numberOrUndefined(text: string): number | undefined {
  const trimmed = text.trim();
  if (!trimmed) return undefined;
  const n = Number(trimmed.replace(",", "."));
  return Number.isFinite(n) ? n : undefined;
}

type StudyValidation = {
  errors: string[];
  params: BalanceRunParams | null;
  taktPreview: number | null;
};

/** Validação dos inputs PROVIDed — mesmas regras do domínio (demanda e
 * disponível > 0, pausas < turno, opcionais positivos quando presentes). */
function validateStudyInputs(
  inputs: StudyInputs,
  branch: string,
): StudyValidation {
  const demandN = numberOrUndefined(inputs.demand);
  const shiftN = numberOrUndefined(inputs.shiftMinutes);
  const breakParsed = numberOrUndefined(inputs.breakMinutes);
  const breakN = breakParsed ?? 0;
  const stationsN = numberOrUndefined(inputs.numStations);
  const batchN = numberOrUndefined(inputs.batchSize);

  const errors: string[] = [];
  if (inputs.demand.trim() && !(demandN !== undefined && demandN > 0)) {
    errors.push("Demanda deve ser um número maior que zero.");
  }
  if (inputs.shiftMinutes.trim() && !(shiftN !== undefined && shiftN > 0)) {
    errors.push("Duração do turno deve ser maior que zero.");
  }
  if (
    inputs.breakMinutes.trim() &&
    (breakParsed === undefined || breakParsed < 0)
  ) {
    errors.push("Pausas devem ser um número não negativo.");
  }
  if (
    shiftN !== undefined &&
    shiftN > 0 &&
    inputs.breakMinutes.trim() &&
    breakN >= shiftN
  ) {
    errors.push("Pausas devem ser menores que a duração do turno.");
  }
  if (
    inputs.numStations.trim() &&
    !(stationsN !== undefined && stationsN > 0)
  ) {
    errors.push("Número de postos deve ser positivo.");
  }
  if (inputs.batchSize.trim() && !(batchN !== undefined && batchN > 0)) {
    errors.push("Tamanho do lote deve ser positivo.");
  }
  const available = shiftN !== undefined ? shiftN - breakN : undefined;
  const valid =
    demandN !== undefined &&
    demandN > 0 &&
    available !== undefined &&
    available > 0 &&
    errors.length === 0;
  const params = valid
    ? {
        demand: demandN!,
        available_minutes: available!,
        ...(stationsN ? { num_stations: stationsN } : {}),
        ...(batchN ? { batch_size: batchN } : {}),
        ...(branch ? { branch } : {}),
      }
    : null;
  const taktPreview =
    params && demandN ? params.available_minutes / demandN : null;
  return { errors, params, taktPreview };
}

const SAVE_STATUS_LABEL: Record<string, string> = {
  saving: "Salvando…",
  saved: "Salvo nesta aba",
  save_error: "Não foi possível salvar o rascunho",
  storage_unavailable:
    "Rascunho não persistido — armazenamento de sessão indisponível",
};

function StudySection({
  study,
  stage,
  branch,
  running,
  balanceError,
  onRun,
  onRequestClear,
}: {
  study: ReturnType<typeof useRoutingStudyDraft>;
  stage: RoutingStageView;
  branch: string;
  running: boolean;
  balanceError: unknown;
  onRun: (params: BalanceRunParams) => void;
  onRequestClear: () => void;
}) {
  const active = study.active;
  const validation = useMemo(
    () => validateStudyInputs(active?.inputs ?? {
      demand: "",
      shiftMinutes: "",
      breakMinutes: "",
      batchSize: "",
      numStations: "",
    }, branch),
    [active?.inputs, branch],
  );
  if (!active) return null;

  const available =
    validation.params?.available_minutes ??
    (() => {
      const shiftN = numberOrUndefined(active.inputs.shiftMinutes);
      const breakN = numberOrUndefined(active.inputs.breakMinutes) ?? 0;
      return shiftN !== undefined ? shiftN - breakN : undefined;
    })();
  const canSubmit = validation.params !== null && !running;

  return (
    <EngineeringSectionCard
      title="Estudo de balanceamento"
      subtitle="Parâmetros PROVIDED + hipóteses SIMULATION de organização da linha — cálculo sempre pelo domínio oficial."
      actions={
        study.status !== "idle" ? (
          <EngineeringStatusBadge
            label={SAVE_STATUS_LABEL[study.status] ?? study.status}
            variant={
              study.status === "saved"
                ? "success"
                : study.status === "save_error" ||
                    study.status === "storage_unavailable"
                  ? "warning"
                  : "neutral"
            }
          />
        ) : (
          <EngineeringStatusBadge label="Rascunho nesta aba" variant="neutral" />
        )
      }
    >
      {study.notice === "restored" ? (
        <EngineeringStateBanner variant="default">
          Rascunho recuperado nesta aba — resultados anteriores não são
          restaurados; recalcule para valores atuais.
        </EngineeringStateBanner>
      ) : null}
      {study.notice === "restore_invalid" ? (
        <EngineeringStateBanner variant="default">
          Rascunho anterior incompatível descartado — o estudo recomeçou
          vazio neste contexto.
        </EngineeringStateBanner>
      ) : null}
      {study.notice === "stale_reference" ? (
        <EngineeringStateBanner variant="default">
          O roteiro oficial mudou desde o rascunho salvo — vínculos de
          operações foram revisados pela fonte atual.
        </EngineeringStateBanner>
      ) : null}
      {balanceError ? <RoutingSourceError error={balanceError} /> : null}
      {validation.errors.length ? (
        <EngineeringStateBanner variant="error">
          {validation.errors.join(" ")}
        </EngineeringStateBanner>
      ) : null}

      {study.scenarios.length > 1 ? (
        <EngineeringScopeChipBar
          aria-label="Cenários do estudo"
          chips={study.scenarios.map((s) => ({
            id: s.clientId,
            label: `Cenário ${s.label}`,
            active: s.clientId === study.activeScenarioId,
            onSelect: () => study.selectScenario(s.clientId),
          }))}
        />
      ) : null}

      <div className="engineering-routing__balance-grid">
        <EngineeringDetailCard
          title="Condições de produção"
          titleHint="Parâmetros PROVIDED pelo usuário — o tempo produtivo é derivado de turno − pausas e enviado como available_minutes ao domínio EVA."
        >
          <div
            className="engineering-routing__form-grid"
            role="group"
            aria-label="Condições de produção"
          >
            <EngineeringTextField
              id="routing-demand"
              label="Demanda por período (peças)"
              value={active.inputs.demand}
              onChange={(v) => study.updateInputs({ demand: v })}
              required
              hint="Peças a produzir no período analisado."
              disabled={running}
            />
            <EngineeringTextField
              id="routing-shift"
              label="Duração do turno (min)"
              value={active.inputs.shiftMinutes}
              onChange={(v) => study.updateInputs({ shiftMinutes: v })}
              required
              hint="Minutos totais do período, antes das pausas."
              disabled={running}
            />
            <EngineeringTextField
              id="routing-break"
              label="Pausas (min)"
              value={active.inputs.breakMinutes}
              onChange={(v) => study.updateInputs({ breakMinutes: v })}
              hint="Minutos não produtivos do turno — subtraídos do tempo disponível."
              disabled={running}
            />
          </div>
          <EngineeringDetailFieldGrid
            fields={[
              {
                label: "Tempo produtivo",
                value:
                  available !== undefined && available > 0
                    ? formatMinutes(available)
                    : "—",
                hint: "Turno − pausas.",
              },
              {
                label: "Prévia do takt",
                value:
                  validation.taktPreview !== null
                    ? `${formatMinutes(validation.taktPreview)} / peça`
                    : "—",
                hint: "Prévia aritmética de interface (disponível ÷ demanda) — o resultado oficial vem do domínio.",
              },
            ]}
          />
        </EngineeringDetailCard>

        <EngineeringDetailCard
          title="Organização da linha"
          titleHint="Análise rápida usa só os parâmetros — configurar postos registra uma hipótese local de arranjo."
        >
          <EngineeringSegmentToggle
            ariaLabel="Organização da linha"
            value={active.mode}
            onChange={(m) => study.setMode(m)}
            options={[
              { value: "quick", label: "Análise rápida" },
              { value: "posts", label: "Configurar postos" },
            ]}
            disabled={running}
          />
          <div
            className="engineering-routing__form-grid"
            role="group"
            aria-label="Configuração opcional"
          >
            <EngineeringTextField
              id="routing-stations"
              label="Postos atuais"
              value={active.inputs.numStations}
              onChange={(v) => study.updateInputs({ numStations: v })}
              hint="Informado, o domínio verifica viabilidade e eficiência do arranjo — não equivale a operadores nem à quantidade de CTs."
              disabled={running}
            />
            <EngineeringTextField
              id="routing-batch"
              label="Tamanho do lote"
              value={active.inputs.batchSize}
              onChange={(v) => study.updateInputs({ batchSize: v })}
              hint="Somente com lote explícito o setup é amortizado por peça."
              disabled={running}
            />
          </div>
        </EngineeringDetailCard>
      </div>

      {active.mode === "posts" ? (
        <>
          <EngineeringStateBanner variant="default">
            Configuração hipotética — DRAFT_LOCAL/SIMULATION. O motor
            atual não valida alocação por posto, precedência, operadores
            ou paralelismo; a análise rápida abaixo calcula apenas com os
            parâmetros e não verifica esta distribuição manual.
          </EngineeringStateBanner>
          <PostConfigurator
            posts={active.posts}
            operations={stage.operations}
            maxPosts={study.maxPosts}
            disabled={running}
            onAdd={study.addPost}
            onPatch={study.patchPost}
            onMove={study.movePost}
            onRemove={study.removePost}
          />
        </>
      ) : null}

      <EngineeringFormActions align="end">
        <EngineeringActionButton
          variant="default"
          disabled={
            running || study.scenarios.length >= study.maxScenarios
          }
          onClick={study.addScenario}
        >
          Novo cenário
        </EngineeringActionButton>
        <EngineeringActionButton
          variant="default"
          disabled={running}
          onClick={onRequestClear}
        >
          Limpar estudo
        </EngineeringActionButton>
        <EngineeringActionButton
          variant="primary"
          disabled={!canSubmit}
          onClick={() => validation.params && onRun(validation.params)}
        >
          {running ? "Calculando…" : "Calcular análise rápida"}
        </EngineeringActionButton>
      </EngineeringFormActions>
      {active.mode === "posts" ? (
        <p className="engineering-routing__muted">
          A análise rápida não valida a distribuição manual configurada —
          o cálculo usa somente os parâmetros informados.
        </p>
      ) : null}
    </EngineeringSectionCard>
  );
}

/* --- Resultados e cenários ---------------------------------------------- */

function BalanceStageFields({ stage }: { stage: LineBalanceStage }) {
  return (
    <EngineeringDetailFieldGrid
      fields={[
        {
          label: "Takt",
          value: formatMinutes(stage.takt_minutes),
          hint: "Tempo produtivo ÷ demanda — CALCULATED.",
        },
        {
          label: "Conteúdo de trabalho",
          value: formatMinutes(stage.work_content_minutes),
          hint: "Soma dos tempos por peça das operações com tempo oficial.",
        },
        {
          label: "Mínimo teórico de postos",
          value:
            stage.theoretical_min_stations != null
              ? String(stage.theoretical_min_stations)
              : "—",
          hint: "Limite inferior matemático — não é dimensionamento aprovado.",
        },
        {
          label: "Gargalo candidato",
          value: stage.bottleneck_candidate
            ? `${stage.bottleneck_candidate.operation_code} · ${formatMinutes(stage.bottleneck_candidate.minutes_piece)}`
            : "—",
        },
        {
          label: "Operações acima do takt",
          value: String(stage.over_takt_operations.length),
        },
        {
          label: "Setup amortizado por peça",
          value: stage.setup_minutes_piece_amortized
            ? formatMinutes(stage.setup_minutes_piece_amortized)
            : "—",
          hint: "Só calculado quando o lote é informado.",
        },
      ]}
    />
  );
}

const SCENARIO_COLUMNS: DataTableColumn<{
  scenario: ScenarioState;
  stage: LineBalanceStage | null;
}>[] = [
  {
    key: "id",
    header: "Cenário",
    render: (r) => `Cenário ${r.scenario.label}`,
  },
  {
    key: "branch",
    header: "Filial",
    render: (r) => r.scenario.computed?.params.branch ?? "—",
  },
  {
    key: "demand",
    header: "Demanda",
    align: "right",
    render: (r) => String(r.scenario.computed?.params.demand ?? "—"),
  },
  {
    key: "available",
    header: "Tempo produtivo",
    align: "right",
    render: (r) =>
      r.scenario.computed
        ? formatMinutes(r.scenario.computed.params.available_minutes)
        : "—",
  },
  {
    key: "stations",
    header: "Postos",
    align: "right",
    render: (r) => String(r.scenario.computed?.params.num_stations ?? "—"),
  },
  {
    key: "batch",
    header: "Lote",
    align: "right",
    render: (r) => String(r.scenario.computed?.params.batch_size ?? "—"),
  },
  {
    key: "takt",
    header: "Takt",
    align: "right",
    render: (r) => (r.stage ? formatMinutes(r.stage.takt_minutes) : "—"),
  },
  {
    key: "content",
    header: "Conteúdo",
    align: "right",
    render: (r) =>
      r.stage ? formatMinutes(r.stage.work_content_minutes) : "—",
  },
  {
    key: "min",
    header: "Mín. teórico",
    align: "right",
    render: (r) =>
      r.stage?.theoretical_min_stations != null
        ? String(r.stage.theoretical_min_stations)
        : "—",
  },
  {
    key: "over",
    header: "Acima do takt",
    align: "right",
    render: (r) =>
      r.stage ? String(r.stage.over_takt_operations.length) : "—",
  },
];

function ResultsSection({
  scenarios,
  stage,
  branch,
  active,
}: {
  scenarios: ScenarioState[];
  stage: RoutingStageView;
  branch: string;
  active: ScenarioState | null;
}) {
  const stageResults = (s: ScenarioState) =>
    s.computed?.result.stages.find(
      (st) => stageKeyOf(st) === stageKeyOf(stage),
    ) ?? null;

  const withResult = scenarios.filter((s) => s.computed);
  const activeStage = active ? stageResults(active) : null;
  const currentFingerprint = active
    ? inputsFingerprint(
        validateStudyInputs(active.inputs, branch).params ?? {},
      )
    : null;
  const activeStale = Boolean(
    active?.computed && active.computed.fingerprint !== currentFingerprint,
  );

  if (!withResult.length) return null;

  return (
    <EngineeringDetailCard
      title="Resultados e cenários"
      titleHint="Métricas CALCULATED do domínio EVA sobre o roteiro OBSERVED e parâmetros PROVIDED — nunca dimensionamento aprovado."
      headerActions={
        <>
          {active ? (
            <EngineeringStatusBadge
              label={`Cenário ${active.label}`}
              variant="neutral"
            />
          ) : null}
          {activeStale ? (
            <EngineeringStatusBadge label="STALE" variant="warning" />
          ) : null}
          {active?.computed ? (
            <EngineeringStatusBadge
              label={active.computed.result.data_class || "—"}
              variant={
                active.computed.result.data_class === "CALCULATED"
                  ? "success"
                  : active.computed.result.data_class === "PARTIAL"
                    ? "warning"
                    : "neutral"
              }
            />
          ) : null}
        </>
      }
    >
      {activeStale ? (
        <EngineeringStateBanner variant="default">
          Os parâmetros mudaram após este cálculo — o resultado abaixo é
          STALE até nova execução do balanceamento.
        </EngineeringStateBanner>
      ) : null}
      {active?.computed && activeStage ? (
        <>
          <BalanceStageFields stage={activeStage} />
          {activeStage.station_check ? (
            <EngineeringStateBanner
              variant={
                activeStage.station_check.feasible === false
                  ? "error"
                  : "default"
              }
            >
              {`Viabilidade com ${activeStage.station_check.num_stations} posto(s): ciclo requerido ${formatMinutes(activeStage.station_check.required_cycle_minutes)}${
                activeStage.station_check.theoretical_efficiency != null
                  ? ` · eficiência teórica ${formatRatio(activeStage.station_check.theoretical_efficiency)}`
                  : ""
              }${
                activeStage.station_check.feasible === false
                  ? " — abaixo do mínimo teórico, configuração inviável para o takt."
                  : ""
              }`}
            </EngineeringStateBanner>
          ) : null}
          {activeStage.limitations.length ? (
            <ul className="engineering-routing__limitations">
              {activeStage.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          ) : null}
          {activeStage.balance_scenario ? (
            <EngineeringStateBanner variant="default">
              {`Cenário SIMULATION (${activeStage.balance_scenario.type}): ${activeStage.balance_scenario.stations_used} posto(s) hipotéticos, ociosidade ${formatMinutes(activeStage.balance_scenario.idle_minutes_total)} — alocação por capacidade de takt, sem precedência; exige revisão da Engenharia.`}
            </EngineeringStateBanner>
          ) : null}
        </>
      ) : active?.computed && !activeStage ? (
        <EngineeringStateBanner variant="default">
          O cenário ativo não retornou o estágio selecionado — verifique
          filial e nível da BOM.
        </EngineeringStateBanner>
      ) : (
        <EngineeringEmptyState message="Cenário ativo sem cálculo — execute a análise rápida para comparar." />
      )}

      {withResult.length > 1 ? (
        <DataTable
          columns={SCENARIO_COLUMNS}
          rows={withResult.map((s) => ({
            scenario: s,
            stage: stageResults(s),
          }))}
          rowKey={(r) => r.scenario.clientId}
          layout="embedded"
          compact
          emptyMessage="Sem cenários para comparar."
        />
      ) : null}
    </EngineeringDetailCard>
  );
}

/* --- Análise visual ---------------------------------------------------- */

function VisualSection({
  stage,
  scenarios,
  code,
  branch,
}: {
  stage: RoutingStageView;
  scenarios: ScenarioState[];
  code: string;
  branch: string;
}) {
  const active = scenarios.find((s) => s.computed) ?? null;
  const activeStage: LineBalanceStage | null = active?.computed
    ? (active.computed.result.stages.find(
        (st) => stageKeyOf(st) === stageKeyOf(stage),
      ) ?? null)
    : null;
  const timedOps = stage.operations.filter(
    (o) => o.time_minutes_piece != null,
  );
  const missingCount = stage.operations.length - timedOps.length;
  const autoUnit = useMemo(
    () =>
      resolveChartTimeUnit(
        timedOps.map((o) => o.time_minutes_piece ?? 0),
      ),
    [timedOps],
  );
  const takt = activeStage?.takt_minutes ?? null;
  const sim = activeStage?.balance_scenario ?? null;
  const unitHint = ` ${autoUnit.note}`;
  const hasComputedCharts = takt != null || sim != null;

  const exportContext = (unit: ChartTimeUnit): RoutingChartContext => ({
    productCode: code,
    branch,
    stageLabel: stageLabel(stage),
    scenarioLabel: active ? `Cenário ${active.label}` : null,
    unit: unit.unit,
  });

  /* Linhas categóricas em MINUTOS — a conversão de exibição s/min fica na
   * camada de apresentação (RoutingSeriesChart). */
  const opsData = timedOps.map((o) => ({
    categoria: o.operation_code || "—",
    tempo: o.time_minutes_piece,
    ...(takt != null && o.time_minutes_piece != null && o.time_minutes_piece > takt
      ? { fill: "var(--delpi-ui-danger, #dc2626)" }
      : {}),
  }));
  const timeSeries: MultiTypeSeriesSpec[] = [
    {
      dataKey: "tempo",
      name: "Tempo por peça",
      fill: "var(--delpi-ui-accent, #2563eb)",
    },
  ];
  const timeVsTaktSeries: MultiTypeSeriesSpec[] = [
    ...timeSeries,
    {
      dataKey: "takt",
      name: "Takt",
      fill: "var(--delpi-ui-warning, #d97706)",
      plotAs: "line",
    },
  ];
  const simData = (sim?.stations ?? []).map((st, i) => ({
    categoria: `Posto ${i + 1}`,
    carga: st.load_minutes,
    ...(takt != null ? { takt } : {}),
  }));
  const simSeries: MultiTypeSeriesSpec[] = [
    {
      dataKey: "carga",
      name: "Carga por posto",
      fill: "var(--delpi-ui-accent, #2563eb)",
    },
    ...(takt != null
      ? [
          {
            dataKey: "takt",
            name: "Takt",
            fill: "var(--delpi-ui-warning, #d97706)",
            plotAs: "line",
          } as MultiTypeSeriesSpec,
        ]
      : []),
  ];

  return (
    <EngineeringSectionCard
      title="Análise visual"
      subtitle="Gráficos contextuais — tempos oficiais sempre disponíveis; takt e distribuição somente com resultado compatível."
    >
      <div className="engineering-routing__charts">
        <EngineeringChartCard
          title="Tempo por peça"
          titleHint={`Tempo padrão por peça — dados OBSERVED do roteiro oficial do estágio selecionado. Operações sem tempo oficial não são plotadas como zero.${unitHint}`}
          hint={
            missingCount
              ? `${missingCount} operação(ões) sem tempo oficial excluída(s) do gráfico.`
              : undefined
          }
        >
          <RoutingSeriesChart
            storageKey={`engineering:routing:${code}:ops-time`}
            idPrefix="en-routing-ops-time"
            data={opsData.map(({ fill, ...row }) => row)}
            series={timeSeries}
            autoUnit={autoUnit}
            buildExportPayload={(unit) =>
              buildOpsTimeExportPayload(
                exportContext(unit),
                timedOps.map((o) => ({
                  operation: o.operation_code || "—",
                  workCenter: o.work_center ?? "—",
                  description: o.operation_description,
                  time: toChartValue(o.time_minutes_piece, unit),
                })),
                unit.decimalPlaces,
              )
            }
            emptyMessage="Nenhuma operação com tempo oficial neste estágio."
          />
        </EngineeringChartCard>

        {takt != null ? (
          <EngineeringChartCard
            title="Tempo × takt"
            titleHint={`Comparação dos tempos por peça ao takt CALCULATED do cenário ativo — operações acima são candidatas a gargalo.${unitHint}`}
          >
            <RoutingSeriesChart
              storageKey={`engineering:routing:${code}:ops-vs-takt`}
              idPrefix="en-routing-ops-takt"
              data={opsData.map((row) => ({ ...row, takt }))}
              series={timeVsTaktSeries}
              autoUnit={autoUnit}
              categoryFillKey="fill"
              buildExportPayload={(unit) =>
                buildOpsVsTaktExportPayload(
                  exportContext(unit),
                  timedOps.map((o) => ({
                    operation: o.operation_code || "—",
                    workCenter: o.work_center ?? "—",
                    description: o.operation_description,
                    time: toChartValue(o.time_minutes_piece, unit),
                    overTakt:
                      o.time_minutes_piece != null
                        ? o.time_minutes_piece > takt
                        : null,
                  })),
                  toChartValue(takt, unit),
                  unit.decimalPlaces,
                )
              }
              emptyMessage="Nenhuma operação com tempo oficial neste estágio."
            />
          </EngineeringChartCard>
        ) : null}

        {sim ? (
          <EngineeringChartCard
            title="Distribuição simulada"
            titleHint={`Carga por posto hipotético do cenário FFD do domínio — alocação por capacidade de takt, sem precedência nem restrições físicas.${unitHint}`}
          >
            <EngineeringStatusBadge
              label="SIMULATION"
              variant="warning"
            />
            <RoutingSeriesChart
              storageKey={`engineering:routing:${code}:sim-distribution`}
              idPrefix="en-routing-sim-dist"
              data={simData}
              series={simSeries}
              autoUnit={autoUnit}
              buildExportPayload={(unit) =>
                buildSimDistributionExportPayload(
                  exportContext(unit),
                  (sim?.stations ?? []).map((st, i) => ({
                    station: `Posto ${i + 1}`,
                    load: toChartValue(st.load_minutes, unit),
                    operations: st.operations.join(", "),
                  })),
                  unit.decimalPlaces,
                )
              }
              emptyMessage="Cenário sem postos."
            />
          </EngineeringChartCard>
        ) : null}
      </div>
      {!hasComputedCharts ? (
        <p className="engineering-routing__muted">
          Execute a análise rápida para comparar operações ao takt e ver
          a distribuição simulada do domínio.
        </p>
      ) : null}
    </EngineeringSectionCard>
  );
}

/* --- Aba --------------------------------------------------------------- */

export function ProductRoutingTab({ code }: { code: string }) {
  const [branch, setBranch] = useState("");
  const [branches, setBranches] = useState<string[]>([]);
  const [routing, setRouting] = useState<RoutingData | null>(null);
  const [routingError, setRoutingError] = useState<unknown>(null);
  const [routingLoading, setRoutingLoading] = useState(true);
  const [stageKey, setStageKey] = useState<string | null>(null);
  const [balanceRunning, setBalanceRunning] = useState(false);
  const [balanceError, setBalanceError] = useState<unknown>(null);
  const [clearOpen, setClearOpen] = useState(false);
  const [clearedNotice, setClearedNotice] = useState(false);
  const balanceAbort = useRef<AbortController | null>(null);

  /* `sub` do JWT — escopo estável do rascunho por identidade, sem
   * persistir credencial nem PII (mesmo padrão dos favoritos do shell). */
  const identity = useMemo(
    () => getSubjectFromAccessToken(getCurrentAccessToken()),
    [],
  );

  useEffect(() => {
    setBalanceError(null);
    setStageKey(null);
    setBranch("");
    setBranches([]);
    setClearedNotice(false);
  }, [code]);

  const prevBranch = useRef(branch);
  useEffect(() => {
    if (prevBranch.current !== branch) {
      prevBranch.current = branch;
      setBalanceError(null);
    }
  }, [branch]);

  useEffect(() => {
    const controller = new AbortController();
    setRoutingLoading(true);
    setRoutingError(null);
    fetchProductRouting(
      code,
      { branch: branch || undefined },
      controller.signal,
    )
      .then((result) => {
        if (controller.signal.aborted) return;
        setRouting(result);
        setBranches((prev) => {
          const next = new Set(prev);
          for (const item of result.items ?? []) {
            if (item.branch) next.add(String(item.branch));
          }
          return [...next].sort();
        });
      })
      .catch((err) => {
        if (!controller.signal.aborted) setRoutingError(err);
      })
      .finally(() => {
        if (!controller.signal.aborted) setRoutingLoading(false);
      });
    return () => controller.abort();
  }, [code, branch]);

  const grouped = useMemo(
    () => groupRoutingRows(routing?.items ?? []),
    [routing],
  );
  useEffect(() => {
    if (
      grouped.stages.length &&
      !grouped.stages.some((s) => s.key === stageKey)
    ) {
      setStageKey(null);
    }
  }, [grouped, stageKey]);
  const stage =
    grouped.stages.find((s) => s.key === stageKey) ??
    grouped.stages[0] ??
    null;

  const study = useRoutingStudyDraft({
    identity,
    productCode: code,
    branch,
    stage,
  });

  const runBalance = useCallback(
    (params: BalanceRunParams) => {
      if (!study.activeScenarioId) return;
      const scenarioId = study.activeScenarioId;
      balanceAbort.current?.abort();
      const controller = new AbortController();
      balanceAbort.current = controller;
      setBalanceRunning(true);
      setBalanceError(null);
      postProductLineBalance(code, params, controller.signal)
        .then((result) => {
          if (controller.signal.aborted) return;
          study.attachResult(scenarioId, params, result);
        })
        .catch((err) => {
          if (!controller.signal.aborted) setBalanceError(err);
        })
        .finally(() => {
          if (!controller.signal.aborted) setBalanceRunning(false);
        });
    },
    [code, study],
  );

  const confirmClear = useCallback(() => {
    const removed = study.clearStudy();
    setClearOpen(false);
    if (removed) setClearedNotice(true);
  }, [study]);

  const branchOptions = useMemo(
    () => [
      { value: "", label: "Todas as filiais" },
      ...branches.map((b) => ({ value: b, label: `Filial ${b}` })),
    ],
    [branches],
  );
  const stageOptions = useMemo(
    () =>
      grouped.stages.map((s) => ({
        value: s.key,
        label: stageLabel(s),
      })),
    [grouped],
  );

  return (
    <div className="engineering-routing">
      {routingLoading ? (
        <EngineeringLoadingActivityCard
          title="Carregando roteiro oficial"
          description="Consultando o roteiro de fabricação na fonte oficial."
        />
      ) : null}
      {routingError ? <RoutingSourceError error={routingError} /> : null}

      {!routingLoading && !routingError && routing ? (
        grouped.stages.length && stage ? (
          <>
            {routing.truncated ? (
              <EngineeringStateBanner variant="default">
                Resposta parcial: a fonte oficial excedeu o limite de
                páginas agregadas — indicadores e gráficos refletem
                apenas os registros recebidos.
              </EngineeringStateBanner>
            ) : null}
            {clearedNotice ? (
              <EngineeringStateBanner variant="default">
                Estudo limpo nesta aba — o roteiro oficial não foi
                alterado.
              </EngineeringStateBanner>
            ) : null}

            <EngineeringSectionCard
              title="Roteiro de fabricação"
              subtitle={`${code} · Operações e análises de processo`}
              actions={
                <div
                  className="engineering-routing__scope"
                  role="group"
                  aria-label="Escopo do roteiro"
                >
                  <EngineeringFilterSelect
                    label="Filial"
                    value={branch}
                    onChange={setBranch}
                    options={branchOptions}
                    disabled={routingLoading}
                  />
                  {stageOptions.length > 1 ? (
                    <EngineeringFilterSelect
                      label="Estágio produtivo"
                      value={stage?.key ?? ""}
                      onChange={setStageKey}
                      options={stageOptions}
                      disabled={routingLoading}
                    />
                  ) : null}
                </div>
              }
            />

            <StageKpis stage={stage} />

            <OperationsSection stage={stage} rowsTotal={grouped.rows_total} />

            {study.ready ? (
              <StudySection
                study={study}
                stage={stage}
                branch={branch}
                running={balanceRunning}
                balanceError={balanceError}
                onRun={runBalance}
                onRequestClear={() => setClearOpen(true)}
              />
            ) : null}

            <ResultsSection
              scenarios={study.scenarios}
              stage={stage}
              branch={branch}
              active={study.active}
            />

            <VisualSection
              stage={stage}
              scenarios={study.scenarios}
              code={code}
              branch={branch}
            />

            <p className="engineering-routing__muted engineering-routing__provenance">
              Dados OBSERVED do roteiro oficial · métricas CALCULATED do
              domínio EVA · postos e cenários são DRAFT_LOCAL/SIMULATION
              — a Engenharia decide e aprova alterações de processo.
            </p>
          </>
        ) : (
          <EngineeringEmptyState message="Este produto não possui roteiro de fabricação na fonte oficial para o escopo selecionado." />
        )
      ) : null}

      <EngineeringConfirmDialog
        open={clearOpen}
        title="Limpar estudo"
        message="Este comando descarta os preenchimentos, postos hipotéticos, ordenação, vínculos de operações e cenários salvos nesta aba e para este contexto. Não altera roteiro, BOM, ERP ou qualquer registro oficial."
        confirmLabel="Limpar estudo"
        cancelLabel="Cancelar"
        variant="danger"
        onConfirm={confirmClear}
        onCancel={() => setClearOpen(false)}
      />
    </div>
  );
}
