/** Aba Roteiro da Ficha do Produto (Doc 126).
 *
 * Três seções internas — Operações, Balanceamento e Análise visual —
 * sobre o roteiro oficial (`GET /v1/products/{code}/routing`, delegação
 * ao owner) e a calculadora determinística do domínio EVA
 * (`POST /v1/products/{code}/line-balance`).
 *
 * Toda a apresentação reutilizável vem do @delpi/plugin-ui via façade
 * `engineeringUi` (SectionCard, KpiCard, DataTable, FilterSelect,
 * ChartCard + ConfigurableSeriesChart). CSS local é apenas composição
 * de layout da feature — nenhum primitivo visual é recriado aqui.
 *
 * O MFE nunca recalcula: dedup, conteúdo de trabalho, takt consolidado,
 * gargalos e cenários FFD são produzidos pelo backend. As únicas
 * aritméticas locais são de exibição: prévia de takt (disponível ÷
 * demanda), consolidação visual pela identidade oficial da operação e
 * conversão min→s do gráfico quando os tempos são subminuto.
 *
 * Classes de proveniência exibidas: OBSERVED (roteiro), PROVIDED
 * (parâmetros do usuário), CALCULATED (métricas do domínio) e
 * SIMULATION (cenários hipotéticos — nunca decisão de Engenharia). */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  Clock3,
  Factory,
  ListOrdered,
  Wrench,
} from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringChartCard,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringFilterSelect,
  EngineeringFiltersRow,
  EngineeringFormActions,
  EngineeringKpiCard,
  EngineeringLoadingActivityCard,
  EngineeringSectionCard,
  EngineeringStateBanner,
  EngineeringStatusBadge,
  EngineeringTabs,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import { ConfigurableSeriesChart } from "@delpi/plugin-ui/index";
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
import {
  formatHours,
  formatMinutes,
  formatRatio,
  groupRoutingRows,
  stageLabel,
  type RoutingOperationView,
  type RoutingStageView,
} from "./routingGrouping";
import { usePortalTheme } from "./usePortalTheme";

type RoutingSection = "operations" | "balance" | "visual";

const SECTION_TABS: { id: RoutingSection; label: string }[] = [
  { id: "operations", label: "Operações" },
  { id: "balance", label: "Balanceamento" },
  { id: "visual", label: "Análise visual" },
];

const MAX_SCENARIOS = 4;

type RoutingData = ProductRoutingResult & { truncated?: boolean };

type BalanceScenario = {
  id: number;
  params: {
    demand: number;
    available_minutes: number;
    num_stations?: number;
    batch_size?: number;
    branch?: string;
  };
  result: ProductLineBalanceResult;
};

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

const OPERATION_COLUMNS: DataTableColumn<RoutingOperationView>[] = [
  {
    key: "operation",
    header: "Operação",
    mobileLabel: "Operação",
    render: (op) => op.operation_code || "—",
  },
  {
    key: "description",
    header: "Descrição",
    mobileLabel: "Descrição",
    render: (op) => op.operation_description ?? "—",
  },
  {
    key: "work_center",
    header: "Centro de trabalho",
    mobileLabel: "CT",
    render: (op) => op.work_center ?? "—",
  },
  {
    key: "time",
    header: "Tempo padrão por peça",
    mobileLabel: "Tempo/peça",
    align: "right",
    render: (op) => formatMinutes(op.time_minutes_piece),
    sortValue: (op) => op.time_minutes_piece,
  },
];

const COMPONENT_COLUMNS: DataTableColumn<{
  code: string;
  description: string | null;
  sequence: string | null;
}>[] = [
  { key: "code", header: "Componente", render: (c) => c.code },
  {
    key: "description",
    header: "Descrição",
    render: (c) => c.description ?? "—",
  },
  { key: "sequence", header: "Sequência", render: (c) => c.sequence ?? "—" },
];

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
        <DataTable
          columns={COMPONENT_COLUMNS}
          rows={op.components}
          rowKey={(c) => c.code}
          layout="embedded"
          compact
          emptyMessage="Nenhum componente associado."
        />
      ) : (
        <p className="engineering-routing__muted">
          Nenhum componente associado a esta operação no payload oficial.
        </p>
      )}
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
  const setupTotal = stage.operations.reduce(
    (sum, o) => sum + (o.setup_hours ?? 0),
    0,
  );

  return (
    <>
      <div className="engineering-routing__kpis" role="group" aria-label="Indicadores do estágio selecionado">
        <EngineeringKpiCard
          title="Operações únicas"
          titleHint="Operações distintas pela identidade oficial (produto × nível × operação × CT × recurso) — não é o número de linhas do retorno."
          value={String(stage.operations.length)}
          icon={<ListOrdered size={18} aria-hidden="true" />}
        />
        <EngineeringKpiCard
          title="Centros de trabalho"
          value={String(workCenters)}
          icon={<Factory size={18} aria-hidden="true" />}
        />
        <EngineeringKpiCard
          title="Recursos distintos"
          value={String(resources)}
          icon={<Wrench size={18} aria-hidden="true" />}
        />
        <EngineeringKpiCard
          title="Tempo padrão do estágio"
          titleHint="Soma dos tempos por peça com valor oficial no estágio selecionado — não soma outros níveis da BOM."
          value={formatMinutes(stageMinutes)}
          subtitle={allTimed ? undefined : "parcial — há operação sem tempo oficial"}
          icon={<Clock3 size={18} aria-hidden="true" />}
        />
      </div>

      <EngineeringDetailCard
        title="Operações do estágio"
        titleHint="Uma linha por operação única. Selecione uma linha para expandir recurso, setup, obrigatoriedade e componentes."
        headerActions={
          <EngineeringStatusBadge
            label={`${stage.operations.length} ${stage.operations.length === 1 ? "operação" : "operações"}`}
            variant="info"
          />
        }
      >
        <DataTable
          columns={OPERATION_COLUMNS}
          rows={stage.operations}
          rowKey={(op) => op.key}
          indexColumn={{ ariaLabel: "Seq." }}
          expandedRowKey={expandedKey}
          onExpandedRowKeyChange={setExpandedKey}
          onRowClick={(op) =>
            setExpandedKey((k) => (k === op.key ? null : op.key))
          }
          renderExpandedRow={(op) => <OperationDetail op={op} />}
          rowClickRole="button"
          emptyMessage="Nenhuma operação neste estágio."
        />
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

/* --- Balanceamento ---------------------------------------------------- */

function numberOrUndefined(text: string): number | undefined {
  const trimmed = text.trim();
  if (!trimmed) return undefined;
  const n = Number(trimmed.replace(",", "."));
  return Number.isFinite(n) ? n : undefined;
}

function BalanceSection({
  stage,
  branch,
  onRun,
  running,
  scenarios,
}: {
  stage: RoutingStageView;
  branch: string;
  onRun: (params: BalanceScenario["params"]) => void;
  running: boolean;
  scenarios: BalanceScenario[];
}) {
  const [demand, setDemand] = useState("");
  const [shiftMinutes, setShiftMinutes] = useState("");
  const [breakMinutes, setBreakMinutes] = useState("");
  const [numStations, setNumStations] = useState("");
  const [batchSize, setBatchSize] = useState("");

  const demandN = numberOrUndefined(demand);
  const shiftN = numberOrUndefined(shiftMinutes);
  const breakN = numberOrUndefined(breakMinutes) ?? 0;
  const stationsN = numberOrUndefined(numStations);
  const batchN = numberOrUndefined(batchSize);

  const errors: string[] = [];
  if (demand.trim() && !(demandN !== undefined && demandN > 0)) {
    errors.push("Demanda deve ser um número maior que zero.");
  }
  if (shiftMinutes.trim() && !(shiftN !== undefined && shiftN > 0)) {
    errors.push("Duração do turno deve ser maior que zero.");
  }
  if (breakMinutes.trim() && !(breakN >= 0)) {
    errors.push("Pausas não podem ser negativas.");
  }
  if (
    shiftN !== undefined &&
    shiftN > 0 &&
    breakMinutes.trim() &&
    breakN >= shiftN
  ) {
    errors.push("Pausas devem ser menores que a duração do turno.");
  }
  if (numStations.trim() && !(stationsN !== undefined && stationsN > 0)) {
    errors.push("Número de postos deve ser positivo.");
  }
  if (batchSize.trim() && !(batchN !== undefined && batchN > 0)) {
    errors.push("Tamanho do lote deve ser positivo.");
  }
  const available = shiftN !== undefined ? shiftN - breakN : undefined;
  const canSubmit =
    demandN !== undefined &&
    demandN > 0 &&
    available !== undefined &&
    available > 0 &&
    errors.length === 0 &&
    !running;
  const taktPreview =
    canSubmit && demandN ? available! / demandN : null;

  const stageResults = (s: BalanceScenario) =>
    s.result.stages.find((st) => stageKeyOf(st) === stageKeyOf(stage)) ??
    null;

  return (
    <>
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
            value={demand}
            onChange={setDemand}
            required
            hint="Peças a produzir no período analisado."
            disabled={running}
          />
          <EngineeringTextField
            id="routing-shift"
            label="Duração do turno (min)"
            value={shiftMinutes}
            onChange={setShiftMinutes}
            required
            hint="Minutos totais do período, antes das pausas."
            disabled={running}
          />
          <EngineeringTextField
            id="routing-break"
            label="Pausas (min)"
            value={breakMinutes}
            onChange={setBreakMinutes}
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
                taktPreview !== null
                  ? `${formatMinutes(taktPreview)} / peça`
                  : "—",
              hint: "Prévia aritmética de interface (disponível ÷ demanda) — o resultado oficial vem do domínio.",
            },
          ]}
        />
      </EngineeringDetailCard>

      <EngineeringDetailCard
        title="Configuração opcional"
        titleHint="Postos e lote são opcionais — sem lote explícito o setup não é amortizado por peça."
      >
        <div
          className="engineering-routing__form-grid"
          role="group"
          aria-label="Configuração opcional"
        >
          <EngineeringTextField
            id="routing-stations"
            label="Postos atuais"
            value={numStations}
            onChange={setNumStations}
            hint="Informado, o domínio verifica viabilidade e eficiência do arranjo — não equivale a operadores."
            disabled={running}
          />
          <EngineeringTextField
            id="routing-batch"
            label="Tamanho do lote"
            value={batchSize}
            onChange={setBatchSize}
            hint="Somente com lote explícito o setup é amortizado por peça."
            disabled={running}
          />
        </div>
      </EngineeringDetailCard>

      {errors.length ? (
        <EngineeringStateBanner variant="error">
          {errors.join(" ")}
        </EngineeringStateBanner>
      ) : null}

      <EngineeringFormActions align="end">
        <EngineeringActionButton
          variant="primary"
          disabled={!canSubmit}
          onClick={() =>
            onRun({
              demand: demandN!,
              available_minutes: available!,
              ...(stationsN ? { num_stations: stationsN } : {}),
              ...(batchN ? { batch_size: batchN } : {}),
              ...(branch ? { branch } : {}),
            })
          }
        >
          {running ? "Calculando…" : "Calcular balanceamento"}
        </EngineeringActionButton>
      </EngineeringFormActions>

      {scenarios.length ? (
        <ScenarioComparison
          scenarios={scenarios}
          stageResults={stageResults}
        />
      ) : (
        <EngineeringEmptyState message="Nenhum cenário calculado ainda — informe as condições e execute o balanceamento pelo motor oficial." />
      )}
    </>
  );
}

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
  scenario: BalanceScenario;
  stage: LineBalanceStage | null;
}>[] = [
  {
    key: "id",
    header: "Cenário",
    render: (r) => `Cenário ${r.scenario.id}`,
  },
  {
    key: "branch",
    header: "Filial",
    render: (r) => r.scenario.params.branch ?? "—",
  },
  {
    key: "demand",
    header: "Demanda",
    align: "right",
    render: (r) => String(r.scenario.params.demand),
  },
  {
    key: "available",
    header: "Tempo produtivo",
    align: "right",
    render: (r) => formatMinutes(r.scenario.params.available_minutes),
  },
  {
    key: "stations",
    header: "Postos",
    align: "right",
    render: (r) => String(r.scenario.params.num_stations ?? "—"),
  },
  {
    key: "batch",
    header: "Lote",
    align: "right",
    render: (r) => String(r.scenario.params.batch_size ?? "—"),
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

function ScenarioComparison({
  scenarios,
  stageResults,
}: {
  scenarios: BalanceScenario[];
  stageResults: (s: BalanceScenario) => LineBalanceStage | null;
}) {
  const latest = scenarios[scenarios.length - 1];
  const latestStage = stageResults(latest);
  return (
    <>
      {latestStage ? (
        <EngineeringDetailCard
          title="Resultado oficial"
          titleHint="Métricas CALCULATED do domínio EVA sobre o roteiro OBSERVED e parâmetros PROVIDED."
        >
          <div className="engineering-routing__badges">
            <EngineeringStatusBadge
              label={`Cenário ${latest.id}`}
              variant="neutral"
            />
            <EngineeringStatusBadge
              label={latest.result.data_class || "—"}
              variant={
                latest.result.data_class === "CALCULATED"
                  ? "success"
                  : latest.result.data_class === "PARTIAL"
                    ? "warning"
                    : "neutral"
              }
            />
          </div>
          <BalanceStageFields stage={latestStage} />
          {latestStage.station_check ? (
            <EngineeringStateBanner
              variant={
                latestStage.station_check.feasible === false
                  ? "error"
                  : "default"
              }
            >
              {`Viabilidade com ${latestStage.station_check.num_stations} posto(s): ciclo requerido ${formatMinutes(latestStage.station_check.required_cycle_minutes)}${
                latestStage.station_check.theoretical_efficiency != null
                  ? ` · eficiência teórica ${formatRatio(latestStage.station_check.theoretical_efficiency)}`
                  : ""
              }${
                latestStage.station_check.feasible === false
                  ? " — abaixo do mínimo teórico, configuração inviável para o takt."
                  : ""
              }`}
            </EngineeringStateBanner>
          ) : null}
          {latestStage.limitations.length ? (
            <ul className="engineering-routing__limitations">
              {latestStage.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          ) : null}
          {latestStage.balance_scenario ? (
            <EngineeringStateBanner variant="default">
              {`Cenário SIMULATION (${latestStage.balance_scenario.type}): ${latestStage.balance_scenario.stations_used} posto(s) hipotéticos, ociosidade ${formatMinutes(latestStage.balance_scenario.idle_minutes_total)} — alocação por capacidade de takt, sem precedência; exige revisão da Engenharia.`}
            </EngineeringStateBanner>
          ) : null}
        </EngineeringDetailCard>
      ) : (
        <EngineeringStateBanner variant="default">
          O cenário mais recente não retornou o estágio selecionado —
          verifique filial e nível da BOM.
        </EngineeringStateBanner>
      )}

      {scenarios.length > 1 ? (
        <EngineeringDetailCard
          title="Comparação de cenários"
          titleHint="Cada linha preserva os parâmetros PROVIDED enviados — comparação atribuível, sem persistência."
        >
          <DataTable
            columns={SCENARIO_COLUMNS}
            rows={scenarios.map((s) => ({
              scenario: s,
              stage: stageResults(s),
            }))}
            rowKey={(r) => String(r.scenario.id)}
            layout="embedded"
            compact
            emptyMessage="Sem cenários para comparar."
          />
        </EngineeringDetailCard>
      ) : null}
    </>
  );
}

/* --- Análise visual ---------------------------------------------------- */

function ThemedSeriesChart({
  title,
  unit,
  points,
  taktValue,
  colorByGoal,
  emptyMessage,
}: {
  title: string;
  unit: ChartTimeUnit;
  points: { label: string; value: number | null }[];
  taktValue?: number | null;
  colorByGoal?: boolean;
  emptyMessage: string;
}) {
  const portalTheme = usePortalTheme();
  const takt = toChartValue(taktValue ?? null, unit);
  return (
    <ConfigurableSeriesChart
      chartType="bar"
      points={points}
      options={{
        title,
        seriesName: `Tempo por peça (${unit.unit})`,
        yAxisTitle: unit.unit,
        theme: portalTheme.mode,
        backgroundColor: portalTheme.surface,
        valueFormat: "number",
        decimalPlaces: unit.decimalPlaces,
        showGoalLine: takt != null,
        goalLineValue: takt ?? undefined,
        ...(colorByGoal && takt != null
          ? { colorScale: { mode: "by_goal", polarity: "high_is_bad" } }
          : {}),
      }}
      emptyMessage={emptyMessage}
    />
  );
}

function VisualSection({
  stage,
  scenarios,
}: {
  stage: RoutingStageView;
  scenarios: BalanceScenario[];
}) {
  const latest = scenarios.length
    ? scenarios[scenarios.length - 1]
    : null;
  const latestStage: LineBalanceStage | null = latest
    ? (latest.result.stages.find(
        (st) => stageKeyOf(st) === stageKeyOf(stage),
      ) ?? null)
    : null;
  const timedOps = stage.operations.filter(
    (o) => o.time_minutes_piece != null,
  );
  const missingCount = stage.operations.length - timedOps.length;
  const unit = useMemo(
    () =>
      resolveChartTimeUnit(
        timedOps.map((o) => o.time_minutes_piece ?? 0),
      ),
    [timedOps],
  );
  const points = timedOps.map((o) => ({
    label: o.operation_code || "—",
    value: toChartValue(o.time_minutes_piece, unit),
  }));
  const takt = latestStage?.takt_minutes ?? null;
  const sim = latestStage?.balance_scenario ?? null;
  const unitHint = unit.unit === "s" ? ` ${unit.note}` : "";

  return (
    <div className="engineering-routing__charts">
      <EngineeringChartCard
        title="Tempos das operações"
        titleHint={`Tempo padrão por peça — dados OBSERVED do roteiro oficial do estágio selecionado. Operações sem tempo oficial não são plotadas como zero.${unitHint}`}
        hint={
          missingCount
            ? `${missingCount} operação(ões) sem tempo oficial excluída(s) do gráfico.`
            : undefined
        }
      >
        <ThemedSeriesChart
          title={`Tempo por peça (${unit.unit})`}
          unit={unit}
          points={points}
          emptyMessage="Nenhuma operação com tempo oficial neste estágio."
        />
      </EngineeringChartCard>

      <EngineeringChartCard
        title="Tempo × takt"
        titleHint={`Comparação dos tempos por peça ao takt CALCULATED do cenário mais recente — operações acima da linha são candidatas a gargalo.${unitHint}`}
      >
        {takt != null ? (
          <ThemedSeriesChart
            title={`Tempo × takt (${unit.unit})`}
            unit={unit}
            points={points}
            taktValue={takt}
            colorByGoal
            emptyMessage="Nenhuma operação com tempo oficial neste estágio."
          />
        ) : (
          <EngineeringEmptyState message="Execute um cenário de balanceamento para comparar as operações ao takt." />
        )}
      </EngineeringChartCard>

      <EngineeringChartCard
        title="Distribuição simulada"
        titleHint={`Carga por posto hipotético do cenário FFD do domínio — alocação por capacidade de takt, sem precedência nem restrições físicas.${unitHint}`}
      >
        {sim ? (
          <>
            <EngineeringStatusBadge
              label="SIMULATION"
              variant="warning"
            />
            <ThemedSeriesChart
              title={`Carga por posto (${unit.unit})`}
              unit={unit}
              points={sim.stations.map((st, i) => ({
                label: `Posto ${i + 1}`,
                value: toChartValue(st.load_minutes, unit),
              }))}
              taktValue={takt}
              emptyMessage="Cenário sem postos."
            />
          </>
        ) : (
          <EngineeringEmptyState message="Nenhum cenário simulado disponível — execute o balanceamento." />
        )}
      </EngineeringChartCard>
    </div>
  );
}

/* --- Aba --------------------------------------------------------------- */

export function ProductRoutingTab({ code }: { code: string }) {
  const [section, setSection] = useState<RoutingSection>("operations");
  const [branch, setBranch] = useState("");
  const [branches, setBranches] = useState<string[]>([]);
  const [routing, setRouting] = useState<RoutingData | null>(null);
  const [routingError, setRoutingError] = useState<unknown>(null);
  const [routingLoading, setRoutingLoading] = useState(true);
  const [stageKey, setStageKey] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<BalanceScenario[]>([]);
  const [balanceRunning, setBalanceRunning] = useState(false);
  const [balanceError, setBalanceError] = useState<unknown>(null);
  const scenarioSeq = useRef(0);
  const balanceAbort = useRef<AbortController | null>(null);

  /* Troca de produto: descarta cenários anteriores — atribuição por
   * produto é condição da comparação honesta. */
  useEffect(() => {
    setScenarios([]);
    setBalanceError(null);
    setStageKey(null);
    setBranch("");
    setBranches([]);
  }, [code]);

  /* Troca de filial muda a fonte dos cenários — descartar resultados
   * calculados sob outra filial mantém a comparação atribuível. */
  const prevBranch = useRef(branch);
  useEffect(() => {
    if (prevBranch.current !== branch) {
      prevBranch.current = branch;
      setScenarios([]);
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

  const runBalance = useCallback(
    (params: BalanceScenario["params"]) => {
      balanceAbort.current?.abort();
      const controller = new AbortController();
      balanceAbort.current = controller;
      setBalanceRunning(true);
      setBalanceError(null);
      postProductLineBalance(code, params, controller.signal)
        .then((result) => {
          if (controller.signal.aborted) return;
          scenarioSeq.current += 1;
          const id = scenarioSeq.current;
          setScenarios((prev) =>
            [...prev, { id, params, result }].slice(-MAX_SCENARIOS),
          );
        })
        .catch((err) => {
          if (!controller.signal.aborted) setBalanceError(err);
        })
        .finally(() => {
          if (!controller.signal.aborted) setBalanceRunning(false);
        });
    },
    [code],
  );

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

            <EngineeringSectionCard
              title="Roteiro de fabricação"
              subtitle="Consulte as operações, avalie a capacidade e analise o balanceamento do produto."
              actions={
                <EngineeringFiltersRow
                  compact
                  ariaLabel="Escopo do roteiro"
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
                </EngineeringFiltersRow>
              }
            >
              <EngineeringTabs
                mode="tabs"
                aria-label="Seções do roteiro"
                activeId={section}
                items={SECTION_TABS.map((t) => ({
                  id: t.id,
                  label: t.label,
                  controlId: `routing-panel-${t.id}`,
                  tabId: `routing-tab-${t.id}`,
                  onSelect: () => setSection(t.id),
                }))}
              />
            </EngineeringSectionCard>

            <div
              role="tabpanel"
              id={`routing-panel-${section}`}
              aria-labelledby={`routing-tab-${section}`}
            >
              {section === "operations" ? (
                <OperationsSection
                  stage={stage}
                  rowsTotal={grouped.rows_total}
                />
              ) : null}
              {section === "balance" ? (
                <>
                  {balanceError ? (
                    <RoutingSourceError error={balanceError} />
                  ) : null}
                  <BalanceSection
                    stage={stage}
                    branch={branch}
                    onRun={runBalance}
                    running={balanceRunning}
                    scenarios={scenarios}
                  />
                </>
              ) : null}
              {section === "visual" ? (
                <VisualSection stage={stage} scenarios={scenarios} />
              ) : null}
            </div>

            <EngineeringStateBanner variant="default">
              Dados OBSERVED do roteiro oficial; métricas CALCULATED do
              domínio EVA; cenários SIMULATION são hipóteses — a
              Engenharia decide e aprova alterações de processo. Para
              análise guiada, use a EVA pelo assistente com acesso ao MCP
              de Engenharia (canal conversacional fora do Portal).
            </EngineeringStateBanner>
          </>
        ) : (
          <EngineeringEmptyState message="Este produto não possui roteiro de fabricação na fonte oficial para o escopo selecionado." />
        )
      ) : null}
    </div>
  );
}
