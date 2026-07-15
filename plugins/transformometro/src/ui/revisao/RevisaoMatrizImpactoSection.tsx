import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ImageDown } from "lucide-react";

import {
  FieldLabel,
  HelpTooltip,
  ImpactEffortMatrix,
  ImpactEffortMatrixLegend,
  NativeTextControl,
  impactEffortMatrixTransformometroClasses,
  type ImpactEffortMatrixMode,
  type ImpactEffortPoint,
} from "@delpi/plugin-ui/index";

import { ChartCard } from "../../components/ChartCard";
import { CollapsiblePanel } from "../../components/CollapsiblePanel";
import { TmNativeTextAreaField } from "../../components/ui/tmNativeFormFields";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { SegmentToggle } from "../../components/SegmentToggle";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { Revisao } from "../../data/api/transformometroApi";
import {
  fetchRevisaoMatrizImpactoEsforco,
  saveRevisaoMatrizImpactoEsforco,
  type MatrizImpactoInputsManuais,
  type MatrizImpactoPonto,
  type MatrizImpactoSaveBody,
  type MatrizImpactoVizinho,
  type RevisaoMatrizImpactoResponse,
} from "../../data/api/transformometroMatrixApi";
import { buildProcessoPath } from "../../utils/routeParser";
import { formatCurrency, formatHours } from "../../utils/format";
import {
  MATRIZ_CONFIANCA_LABELS,
  MATRIZ_QUADRANTE_LABELS,
  MATRIZ_QUADRANTE_LABELS_GRAFICO,
} from "../../content/matrizImpactoLabels";
import { exportImpactEffortMatrixPlotPng } from "../../utils/exportImpactEffortMatrixPng";
import { DS_GHOST_BTN } from "../../components/ghostChrome";

type Props = {
  revisao: Revisao;
  revisoesReferencia?: Revisao[];
  getAccessToken?: () => string | undefined;
  onError: (message: string | null) => void;
  onNavigate?: (path: string) => void;
  rateioExcedeGanho?: boolean;
};

const M = TM_HELP_TOOLTIPS.matriz;

const MODO_OPTIONS: Array<{ value: ImpactEffortMatrixMode; label: string }> = [
  { value: "auto", label: "Automático" },
  { value: "hibrido", label: "Híbrido" },
  { value: "manual", label: "Manual" },
];

function resolveRevisaoLabel(revisaoId: string, revisoes: Revisao[]): string {
  const match = revisoes.find((row) => row.revisao_id === revisaoId);
  return match ? `v${match.versao_revisao}` : revisaoId.slice(0, 8);
}

function toMatrixPoint(
  point: MatrizImpactoPonto | (MatrizImpactoVizinho & { label?: string; revisao_ativa?: boolean; incluir_na_matriz?: boolean }),
  revisoes: Revisao[]
): ImpactEffortPoint {
  const label =
    "label" in point && point.label
      ? point.label
      : resolveRevisaoLabel(point.revisao_id, revisoes);

  return {
    id: point.revisao_id,
    label,
    impacto: point.impacto,
    esforco: point.esforco,
    quadrante: point.quadrante,
    revisaoAtiva: "revisao_ativa" in point ? point.revisao_ativa : false,
    muted: "incluir_na_matriz" in point ? !point.incluir_na_matriz : false,
  };
}

function emptyInputs(): MatrizImpactoInputsManuais {
  return {};
}

function inputsFromResponse(data: RevisaoMatrizImpactoResponse | null): MatrizImpactoInputsManuais {
  return { ...(data?.inputs_persistidos?.inputs_manuais ?? {}) };
}

function modoFromResponse(data: RevisaoMatrizImpactoResponse | null): ImpactEffortMatrixMode {
  return data?.inputs_persistidos?.modo ?? data?.ponto?.modo ?? "auto";
}

type ScaleFieldProps = {
  label: string;
  hint: string;
  value?: number;
  onChange: (value: number) => void;
  idPrefix: string;
};

function ScaleField({ label, hint, value, onChange, idPrefix }: ScaleFieldProps) {
  return (
    <div className="tm-matrix-scale-field ds-filter-box">
      <FieldLabel className="tm-field__label" label={label} hint={hint} />
      <div className="ds-segment-toggle tm-matrix-scale-field__buttons" role="group" aria-label={label}>
        {[1, 2, 3, 4, 5].map((score) => (
          <button
            key={score}
            id={`${idPrefix}-${score}`}
            type="button"
            className={`ds-segment-toggle__btn${
              value === score ? " ds-segment-toggle__btn--active" : ""
            }`}
            aria-pressed={value === score}
            onClick={() => onChange(score)}
          >
            {score}
          </button>
        ))}
      </div>
    </div>
  );
}

export function RevisaoMatrizImpactoSection({
  revisao,
  revisoesReferencia = [],
  getAccessToken,
  onError,
  onNavigate,
  rateioExcedeGanho = false,
}: Props) {
  const plotRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<RevisaoMatrizImpactoResponse | null>(null);
  const [modo, setModo] = useState<ImpactEffortMatrixMode>("auto");
  const [inputs, setInputs] = useState<MatrizImpactoInputsManuais>(emptyInputs);

  const revisoesLookup = useMemo(() => {
    const map = new Map<string, Revisao>();
    for (const row of revisoesReferencia) {
      map.set(row.revisao_id, row);
    }
    map.set(revisao.revisao_id, revisao);
    return Array.from(map.values());
  }, [revisao, revisoesReferencia]);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const response = await fetchRevisaoMatrizImpactoEsforco(revisao.revisao_id, getAccessToken);
      setData(response);
      setModo(modoFromResponse(response));
      setInputs(inputsFromResponse(response));
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar matriz impacto × esforço");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisao.revisao_id]);

  useEffect(() => {
    void load();
  }, [load]);

  const scatterPoints = useMemo(() => {
    if (!data) return [];
    const neighbors = data.vizinhos.map((neighbor) =>
      toMatrixPoint(
        {
          ...neighbor,
          label: resolveRevisaoLabel(neighbor.revisao_id, revisoesLookup),
          incluir_na_matriz: true,
        },
        revisoesLookup
      )
    );
    const current = toMatrixPoint(data.ponto, revisoesLookup);
    const merged = new Map<string, ImpactEffortPoint>();
    for (const point of [...neighbors, current]) {
      merged.set(point.id, point);
    }
    return Array.from(merged.values());
  }, [data, revisoesLookup]);

  const handlePointSelect = useCallback(
    (point: ImpactEffortPoint) => {
      if (!onNavigate || point.id === revisao.revisao_id) return;
      const instanciaId = revisao.instancia_id ?? data?.instancia_id;
      if (!instanciaId) return;
      onNavigate(buildProcessoPath(revisao.processo_id, point.id, instanciaId));
    },
    [data?.instancia_id, onNavigate, revisao.instancia_id, revisao.processo_id, revisao.revisao_id]
  );

  async function handleSave() {
    if (modo === "auto") return;
    setSaving(true);
    onError(null);
    const body: MatrizImpactoSaveBody = {
      modo,
      inputs_manuais: inputs,
      overrides: data?.inputs_persistidos?.overrides ?? { impacto: null, esforco: null },
    };
    try {
      const response = await saveRevisaoMatrizImpactoEsforco(revisao.revisao_id, body, getAccessToken);
      setData(response);
      setModo(modoFromResponse(response));
      setInputs(inputsFromResponse(response));
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar ajustes da matriz");
    } finally {
      setSaving(false);
    }
  }

  const ponto = data?.ponto;
  const metricas = ponto?.metricas;
  const confiancaLabel = ponto ? MATRIZ_CONFIANCA_LABELS[ponto.confianca] : "—";
  const quadranteLabel = ponto ? MATRIZ_QUADRANTE_LABELS[ponto.quadrante] : "—";

  return (
    <section className="tm-impact-effort-section">
      <ChartCard
        title="Matriz impacto × esforço"
        titleHint={M.titulo}
        hint="Posicionamento desta revisão frente às demais comparáveis da melhoria."
        toolbar={
          <>
            {rateioExcedeGanho ? (
              <span
                className="tm-matrix-rateio-chip"
                role="status"
                title={M.rateioExcedeGanho}
              >
                Rateio &gt; ganho
                <HelpTooltip
                  content={M.rateioExcedeGanho}
                  ariaLabel="Ajuda: rateio excede ganho"
                />
              </span>
            ) : null}
            <button
              type="button"
              className={DS_GHOST_BTN}
              disabled={loading || !ponto}
              onClick={() =>
                exportImpactEffortMatrixPlotPng(
                  plotRef.current,
                  `matriz-revisao-${revisao.revisao_id}`,
                  () => onError("Não foi possível exportar a matriz como PNG.")
                )
              }
            >
              <ImageDown size={16} aria-hidden="true" />
              Exportar PNG
            </button>
          </>
        }
      >
        {loading ? (
          <LoadingActivityCard
            title="Carregando matriz"
            description="Calculando impacto e esforço da revisão."
            variant="compact"
          />
        ) : !ponto ? (
          <p className="ds-hint">{M.semDados}</p>
        ) : (
          <>
            <div className="tm-impact-effort-section__toolbar">
              <div className="tm-impact-effort-section__modo">
                <FieldLabel
                  className="tm-field__label tm-impact-effort-section__modo-label"
                  label={M.modoLabel}
                  hint={M.modo}
                />
                <SegmentToggle
                  ariaLabel={M.modo}
                  idPrefix="tm-matrix-modo"
                  value={modo}
                  onChange={setModo}
                  options={MODO_OPTIONS}
                />
              </div>
              <p className="tm-impact-effort-section__confianca">
                <FieldLabel
                  className="tm-impact-effort-section__confianca-label"
                  label={`${M.confiancaLabel}: ${confiancaLabel}`}
                  hint={M.confianca}
                />
              </p>
            </div>

            {ponto.confianca === "baixa" ? (
              <p className="tm-matrix-banner tm-matrix-banner--warn" role="status">
                {M.bannerBaixaConfianca}
              </p>
            ) : null}

            <div className="tm-impact-effort-section__plot-wrap" ref={plotRef}>
              <ImpactEffortMatrix
                points={scatterPoints}
                activePointId={revisao.revisao_id}
                threshold={data?.threshold ?? 50}
                classNames={impactEffortMatrixTransformometroClasses()}
                quadrantLabels={MATRIZ_QUADRANTE_LABELS_GRAFICO}
                onPointSelect={onNavigate ? handlePointSelect : undefined}
                emptyMessage={M.semDados}
                ariaLabel={M.graficoAria}
              />
            </div>

            <div className="tm-impact-effort-section__summary">
              <div className="tm-impact-effort-section__summary-head">
                <FieldLabel
                  className="tm-field__label tm-impact-effort-section__summary-label"
                  label="Posição na matriz"
                  hint={M.posicaoAtual}
                />
                <p className="tm-impact-effort-section__headline">
                  Impacto {ponto.impacto.toLocaleString("pt-BR")} · Esforço{" "}
                  {ponto.esforco.toLocaleString("pt-BR")} · {quadranteLabel}
                </p>
              </div>
              {metricas ? (
                <p className="ds-hint tm-impact-effort-section__metricas">
                  <FieldLabel
                    className="tm-field__label tm-impact-effort-section__metricas-label"
                    label={M.resumoEconomia}
                    hint={M.liquidaAnualResumo}
                  />
                  {" "}
                  {formatCurrency(metricas.economia_liquida_anual)}
                  {metricas.roi_medio != null ? ` · ROI ${metricas.roi_medio.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}×` : ""}
                  {metricas.payback_meses != null
                    ? ` · Payback ${metricas.payback_meses.toLocaleString("pt-BR", { maximumFractionDigits: 0 })} meses`
                    : ""}
                  {metricas.horas_economizadas_anual > 0
                    ? ` · ${formatHours(metricas.horas_economizadas_anual)} / ano`
                    : ""}
                </p>
              ) : null}
            </div>

            <div className="tm-impact-effort-section__legend-wrap">
              <FieldLabel
                className="tm-field__label tm-impact-effort-section__legend-label"
                label="Quadrantes"
                hint={M.quadrantes}
              />
              <ImpactEffortMatrixLegend
                className="tm-impact-effort-section__legend"
                quadrantLabels={MATRIZ_QUADRANTE_LABELS}
              />
            </div>

            <CollapsiblePanel
              className="tm-matrix-manual"
              triggerClassName="tm-matrix-manual__trigger"
              defaultOpen={modo !== "auto"}
              header={
                <span className="tm-matrix-manual__trigger-inner">
                  Ajustes qualitativos
                  <HelpTooltip
                    content={M.ajustesManuais}
                    ariaLabel="Ajuda: ajustes qualitativos"
                  />
                </span>
              }
              bodyClassName="tm-matrix-manual__body"
            >
              <div className="tm-matrix-manual__grid">
                <ScaleField
                  idPrefix="tm-matrix-impacto"
                  label="Impacto qualitativo"
                  hint={M.impactoQualitativo}
                  value={inputs.impacto_qualitativo}
                  onChange={(value) => setInputs((prev) => ({ ...prev, impacto_qualitativo: value }))}
                />
                <ScaleField
                  idPrefix="tm-matrix-esforco"
                  label="Esforço qualitativo"
                  hint={M.esforcoQualitativo}
                  value={inputs.esforco_qualitativo}
                  onChange={(value) => setInputs((prev) => ({ ...prev, esforco_qualitativo: value }))}
                />
                <ScaleField
                  idPrefix="tm-matrix-alinhamento"
                  label="Alinhamento estratégico"
                  hint={M.alinhamentoEstrategico}
                  value={inputs.alinhamento_estrategico}
                  onChange={(value) => setInputs((prev) => ({ ...prev, alinhamento_estrategico: value }))}
                />
                <ScaleField
                  idPrefix="tm-matrix-dependencias"
                  label="Dependências externas"
                  hint={M.dependenciasExternas}
                  value={inputs.dependencias_externas}
                  onChange={(value) => setInputs((prev) => ({ ...prev, dependencias_externas: value }))}
                />
                <label className="ds-filter-box tm-field">
                  <FieldLabel className="tm-field__label" label="Pessoas afetadas" hint={M.pessoasAfetadas} />
                  <NativeTextControl
                    type="number"
                    min={0}
                    value={inputs.pessoas_afetadas ?? ""}
                    onChange={(value) =>
                      setInputs((prev) => ({
                        ...prev,
                        pessoas_afetadas: value === "" ? undefined : Number(value),
                      }))
                    }
                  />
                </label>
                <TmNativeTextAreaField
                  id="tm-matrix-observacao"
                  label="Observação"
                  hint={M.observacao}
                  span
                  rows={3}
                  maxLength={2000}
                  value={inputs.observacao ?? ""}
                  onChange={(value) =>
                    setInputs((prev) => ({ ...prev, observacao: value || undefined }))
                  }
                />
              </div>
              {modo !== "auto" ? (
                <div className="tm-matrix-manual__actions">
                  <button
                    type="button"
                    className="ds-primary-btn"
                    disabled={saving}
                    onClick={() => void handleSave()}
                  >
                    {saving ? "Salvando…" : "Salvar ajustes"}
                  </button>
                </div>
              ) : (
                <p className="ds-hint tm-matrix-manual__hint">
                  {M.modoAutomaticoHint}
                  <HelpTooltip
                    content={M.modo}
                    ariaLabel="Ajuda: modo automático"
                  />
                </p>
              )}
            </CollapsiblePanel>
          </>
        )}
      </ChartCard>
    </section>
  );
}
