/** Resultados do estudo de balanceamento — apresentação neutra
 * compartilhada entre a aba Roteiro da Ficha do Produto e a ferramenta
 * Processos > Balanceamento de Linha. Renderiza somente métricas
 * CALCULATED do domínio EVA (`POST /v1/products/{code}/line-balance`)
 * sobre o roteiro OBSERVED + parâmetros PROVIDED; hipóteses marcadas
 * SIMULATION/DRAFT_LOCAL com limitações explícitas. */

import {
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringStateBanner,
  EngineeringStatusBadge,
} from "../../../ui/engineeringUi";
import { DataTable, type DataTableColumn } from "../components/dataTableUi";
import type { LineBalanceStage } from "../types";
import { formatMinutes, formatRatio } from "./routingGrouping";
import { inputsFingerprint } from "./routingStudyDraft";
import { validateStudyInputs } from "./studyInputs";
import type { ScenarioState } from "./useRoutingStudyDraft";

export function stageKeyOf(stage: {
  product_code: string;
  bom_level: number;
}): string {
  return `${stage.product_code}#${stage.bom_level}`;
}

export function BalanceStageFields({
  stage,
}: {
  stage: LineBalanceStage;
}) {
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

export function BalanceResultsSection({
  scenarios,
  stage,
  branch,
  active,
}: {
  scenarios: ScenarioState[];
  stage: {
    key: string;
    product_code: string;
    bom_level: number;
  };
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
