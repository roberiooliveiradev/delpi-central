/** Aba Roteiro da Ficha do Produto (Doc 126).
 *
 * Três seções internas — Operações, Balanceamento e Análise visual —
 * sobre o roteiro oficial (`GET /v1/products/{code}/routing`, delegação
 * ao owner) e a calculadora determinística do domínio EVA
 * (`POST /v1/products/{code}/line-balance`).
 *
 * O MFE nunca recalcula: dedup, conteúdo de trabalho, takt consolidado,
 * gargalos e cenários FFD são produzidos pelo backend. A única aritmética
 * local é a prévia de takt do formulário (disponível ÷ demanda), e a
 * consolidação visual das linhas usa a identidade oficial da operação.
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

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringChartCard,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringLoadingActivityCard,
  EngineeringMetricStrip,
  EngineeringSelectField,
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
import type {
  LineBalanceStage,
  ProductLineBalanceResult,
  ProductRoutingResult,
} from "../types";
import {
  formatHours,
  formatMinutes,
  formatRatio,
  groupRoutingRows,
  stageLabel,
  type RoutingOperationView,
  type RoutingStageView,
} from "./routingGrouping";

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

/** Linha expansível da listagem — identidade oficial da operação com
 * os componentes BOM fundidos (dedup visual do contrato). */
function OperationRow({ op }: { op: RoutingOperationView }) {
  const [open, setOpen] = useState(false);
  const detailId = `routing-op-detail-${op.key.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
  return (
    <>
      <tr>
        <td>
          <button
            type="button"
            className="engineering-routing__expander"
            aria-expanded={open}
            aria-controls={detailId}
            aria-label={
              open
                ? `Recolher detalhes da operação ${op.operation_code}`
                : `Expandir detalhes da operação ${op.operation_code}`
            }
            onClick={() => setOpen((v) => !v)}
          >
            {open ? "▾" : "▸"}
          </button>
          {op.operation_code || "—"}
        </td>
        <td>{op.operation_description ?? "—"}</td>
        <td>{op.work_center ?? "—"}</td>
        <td>{op.resource_code ?? "—"}</td>
        <td>{op.operation_type ?? "—"}</td>
        <td>{formatMinutes(op.time_minutes_piece)}</td>
        <td>{formatHours(op.setup_hours)}</td>
        <td>
          {op.components.length
            ? `${op.components.length} componente(s)`
            : "—"}
        </td>
      </tr>
      {open ? (
        <tr className="engineering-routing__op-detail-row">
          <td colSpan={8} id={detailId}>
            <div className="engineering-routing__op-detail">
              <EngineeringDetailFieldGrid
                fields={[
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
                  },
                ]}
              />
              {op.components.length ? (
                <table className="engineering-routing__components-table">
                  <caption className="engineering-routing__sr-only">
                    Componentes associados à operação {op.operation_code}
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Componente</th>
                      <th scope="col">Descrição</th>
                      <th scope="col">Sequência</th>
                    </tr>
                  </thead>
                  <tbody>
                    {op.components.map((c) => (
                      <tr key={c.code}>
                        <td>{c.code}</td>
                        <td>{c.description ?? "—"}</td>
                        <td>{c.sequence ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="engineering-routing__muted">
                  Nenhum componente associado a esta operação no payload
                  oficial.
                </p>
              )}
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}

function OperationsSection({
  stage,
  rowsTotal,
}: {
  stage: RoutingStageView;
  rowsTotal: number;
}) {
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
      <EngineeringMetricStrip
        aria-label="Indicadores do estágio selecionado"
        items={[
          {
            id: "ops",
            label: "Operações únicas",
            value: String(stage.operations.length),
          },
          {
            id: "wcs",
            label: "Centros de trabalho",
            value: String(workCenters),
          },
          {
            id: "res",
            label: "Recursos distintos",
            value: String(resources),
          },
          { id: "rows", label: "Linhas da consulta", value: String(rowsTotal) },
          {
            id: "time",
            label: "Tempo padrão do estágio",
            value: allTimed
              ? formatMinutes(stageMinutes)
              : `${formatMinutes(stageMinutes)} (parcial)`,
          },
          {
            id: "setup",
            label: "Setup total",
            value: setupTotal ? formatHours(setupTotal) : "—",
          },
        ]}
      />
      <EngineeringDetailCard
        title="Operações do estágio"
        titleHint="Uma linha por operação única (produto × nível × operação × CT × recurso). As linhas repetidas do payload — uma por componente — foram consolidadas."
      >
        <div className="engineering-routing__table-wrap">
          <table className="engineering-routing__table">
            <thead>
              <tr>
                <th scope="col">Operação</th>
                <th scope="col">Descrição</th>
                <th scope="col">Centro de trabalho</th>
                <th scope="col">Recurso</th>
                <th scope="col">Tipo</th>
                <th scope="col">Tempo peça</th>
                <th scope="col">Setup</th>
                <th scope="col">Componentes</th>
              </tr>
            </thead>
            <tbody>
              {stage.operations.map((op) => (
                <OperationRow key={op.key} op={op} />
              ))}
            </tbody>
          </table>
        </div>
      </EngineeringDetailCard>
    </>
  );
}

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
  if (
    shiftMinutes.trim() &&
    !(shiftN !== undefined && shiftN > 0)
  ) {
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
  const available =
    shiftN !== undefined ? shiftN - breakN : undefined;
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
        title="Parâmetros do cenário"
        titleHint="Parâmetros PROVIDED pelo usuário — o tempo produtivo é derivado de turno − pausas e enviado como available_minutes ao domínio EVA."
      >
        <div className="engineering-routing__calc-form" role="group" aria-label="Parâmetros de balanceamento">
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
          <EngineeringTextField
            id="routing-stations"
            label="Postos atuais (opcional)"
            value={numStations}
            onChange={setNumStations}
            hint="Informado, o domínio verifica viabilidade e eficiência do arranjo — não equivale a operadores."
            disabled={running}
          />
          <EngineeringTextField
            id="routing-batch"
            label="Tamanho do lote (opcional)"
            value={batchSize}
            onChange={setBatchSize}
            hint="Somente com lote explícito o setup é amortizado por peça."
            disabled={running}
          />
        </div>
        {errors.length ? (
          <EngineeringStateBanner variant="error">
            {errors.join(" ")}
          </EngineeringStateBanner>
        ) : null}
        <div className="engineering-routing__calc-bar">
          <p className="engineering-routing__muted" aria-live="polite">
            {taktPreview !== null
              ? `Prévia do takt: ${formatMinutes(taktPreview)} por peça (tempo produtivo ÷ demanda).`
              : "Informe demanda e turno para pré-visualizar o takt."}
          </p>
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
            {running ? "Calculando…" : "Calcular cenário"}
          </EngineeringActionButton>
        </div>
      </EngineeringDetailCard>

      {scenarios.length ? (
        <ScenarioComparison
          scenarios={scenarios}
          stageResults={stageResults}
        />
      ) : (
        <EngineeringEmptyState message="Nenhum cenário calculado ainda — informe os parâmetros e execute o motor oficial." />
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
          title={`Cenário ${latest.id} — resultado do estágio`}
          titleHint="Métricas CALCULATED do domínio EVA sobre o roteiro OBSERVED e parâmetros PROVIDED."
          headerActions={
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
          }
        >
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
          titleHint="Cada linha preserva os parâmetros PROVIDed enviados — comparação atribuível, sem persistência."
        >
          <div className="engineering-routing__table-wrap">
            <table className="engineering-routing__table">
              <thead>
                <tr>
                  <th scope="col">Cenário</th>
                  <th scope="col">Filial</th>
                  <th scope="col">Demanda</th>
                  <th scope="col">Tempo produtivo</th>
                  <th scope="col">Postos</th>
                  <th scope="col">Lote</th>
                  <th scope="col">Takt</th>
                  <th scope="col">Conteúdo</th>
                  <th scope="col">Mín. teórico</th>
                  <th scope="col">Acima do takt</th>
                </tr>
              </thead>
              <tbody>
                {scenarios.map((s) => {
                  const st = stageResults(s);
                  return (
                    <tr key={s.id}>
                      <td>{`Cenário ${s.id}`}</td>
                      <td>{s.params.branch ?? "—"}</td>
                      <td>{s.params.demand}</td>
                      <td>{formatMinutes(s.params.available_minutes)}</td>
                      <td>{s.params.num_stations ?? "—"}</td>
                      <td>{s.params.batch_size ?? "—"}</td>
                      <td>{st ? formatMinutes(st.takt_minutes) : "—"}</td>
                      <td>
                        {st ? formatMinutes(st.work_content_minutes) : "—"}
                      </td>
                      <td>
                        {st?.theoretical_min_stations != null
                          ? String(st.theoretical_min_stations)
                          : "—"}
                      </td>
                      <td>
                        {st ? String(st.over_takt_operations.length) : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </EngineeringDetailCard>
      ) : null}
    </>
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
  const points = timedOps.map((o) => ({
    label: o.operation_code || "—",
    value: o.time_minutes_piece,
  }));
  const takt = latestStage?.takt_minutes ?? null;
  const sim = latestStage?.balance_scenario ?? null;
  return (
    <div className="engineering-routing__charts">
      <EngineeringChartCard
        title="Tempos das operações"
        titleHint="Tempo padrão por peça (minutos) — dados OBSERVED do roteiro oficial do estágio selecionado. Operações sem tempo oficial não são plotadas como zero."
        hint={
          missingCount
            ? `${missingCount} operação(ões) sem tempo oficial excluída(s) do gráfico.`
            : undefined
        }
      >
        <ConfigurableSeriesChart
          chartType="bar"
          points={points}
          options={{
            seriesName: "Tempo peça (min)",
            yAxisTitle: "min",
            showGoalLine: takt != null,
            goalLineValue: takt,
          }}
          emptyMessage="Nenhuma operação com tempo oficial neste estágio."
        />
      </EngineeringChartCard>
      <EngineeringChartCard
        title="Tempo × takt"
        titleHint="Comparação dos tempos por peça ao takt CALCULATED do cenário mais recente — operações acima da linha são candidatas a gargalo."
      >
        {takt != null ? (
          <ConfigurableSeriesChart
            chartType="bar"
            points={points}
            options={{
              seriesName: "Tempo peça (min)",
              yAxisTitle: "min",
              showGoalLine: true,
              goalLineValue: takt,
              colorScale: { mode: "by_goal" },
            }}
            emptyMessage="Nenhuma operação com tempo oficial neste estágio."
          />
        ) : (
          <EngineeringEmptyState message="Execute um cenário de balanceamento para comparar as operações ao takt." />
        )}
      </EngineeringChartCard>
      <EngineeringChartCard
        title="Distribuição simulada (SIMULATION)"
        titleHint="Carga por posto hipotético do cenário FFD do domínio — alocação por capacidade de takt, sem precedência nem restrições físicas."
      >
        {sim ? (
          <>
            <EngineeringStatusBadge
              label="SIMULATION"
              variant="warning"
            />
            <ConfigurableSeriesChart
              chartType="bar"
              points={sim.stations.map((st, i) => ({
                label: `Posto ${i + 1}`,
                value: st.load_minutes,
              }))}
              options={{
                seriesName: "Carga (min)",
                yAxisTitle: "min",
                showGoalLine: takt != null,
                goalLineValue: takt,
              }}
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
      <div className="engineering-routing__filters" role="group" aria-label="Escopo do roteiro">
        <EngineeringSelectField
          id="routing-branch"
          label="Filial"
          value={branch}
          onChange={setBranch}
          options={branchOptions}
          disabled={routingLoading}
        />
        {stageOptions.length > 1 ? (
          <EngineeringSelectField
            id="routing-stage"
            label="Estágio produtivo"
            value={stage?.key ?? ""}
            onChange={setStageKey}
            options={stageOptions}
            disabled={routingLoading}
          />
        ) : null}
      </div>

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
