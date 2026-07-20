import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ImageDown } from "lucide-react";

import {
  FieldLabel,
  ImpactEffortMatrix,
  ImpactEffortMatrixLegend,
  impactEffortMatrixTransformometroClasses,
  type ImpactEffortPoint,
} from "@delpi/plugin-ui/index";

import { ChartCard } from "../../components/ChartCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { TableHeader } from "../../components/TableHeader";
import { cenarioLabel } from "../../content/cenarioLabels";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  MATRIZ_QUADRANTE_BADGE_CLASS,
  MATRIZ_QUADRANTE_DESCRIPTIONS,
  MATRIZ_QUADRANTE_LABELS,
  MATRIZ_QUADRANTE_LABELS_GRAFICO,
} from "../../content/matrizImpactoLabels";
import {
  fetchProcessoMatrizImpactoEsforco,
  type MatrizImpactoPonto,
  type ProcessoMatrizMelhoria,
} from "../../data/api/transformometroMatrixApi";
import { exportImpactEffortMatrixPlotPng } from "../../utils/exportImpactEffortMatrixPng";
import { formatCurrency } from "../../utils/format";
import {
  matrizPontoToImpactEffortPoint,
  sortMatrizPontosForRanking,
} from "../../utils/matrizImpactoPoints";
import { matrizSeriesColor } from "../../utils/matrizImpactoSeriesColors";
import { buildProcessoPath } from "../../utils/routeParser";
import { DS_GHOST_BTN } from "../../components/ghostChrome";

type Props = {
  processoId: string;
  processoLabel: string;
  getAccessToken?: () => string | undefined;
  onError: (message: string | null) => void;
  onNavigate?: (path: string) => void;
};

const M = TM_HELP_TOOLTIPS.matriz;
const C = TM_HELP_TOOLTIPS.columns;

function formatScore(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

export function ProcessoMatrizImpactoSection({
  processoId,
  processoLabel,
  getAccessToken,
  onError,
  onNavigate,
}: Props) {
  const plotRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [pontos, setPontos] = useState<MatrizImpactoPonto[]>([]);
  const [melhorias, setMelhorias] = useState<ProcessoMatrizMelhoria[]>([]);
  const [threshold, setThreshold] = useState(50);
  const [activeRevisaoId, setActiveRevisaoId] = useState<string | null>(null);
  const instanciaByRevisao = useMemo(() => {
    const map = new Map<string, string>();
    for (const ponto of pontos) {
      if (ponto.instancia_id) map.set(ponto.revisao_id, ponto.instancia_id);
    }
    return map;
  }, [pontos]);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const response = await fetchProcessoMatrizImpactoEsforco(processoId, getAccessToken, {
        incluir_baseline: true,
      });
      setPontos(response.pontos);
      setMelhorias(response.melhorias);
      setThreshold(response.threshold);
      setActiveRevisaoId(response.ativo?.revisao_id ?? null);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar matriz do processo");
      setPontos([]);
      setMelhorias([]);
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  const scatterPoints = useMemo(
    () => pontos.map((ponto) => matrizPontoToImpactEffortPoint(ponto, { includeMelhoriaInLabel: true })),
    [pontos]
  );

  const rankingRows = useMemo(() => sortMatrizPontosForRanking(pontos), [pontos]);

  const handlePointSelect = useCallback(
    (point: ImpactEffortPoint) => {
      if (!onNavigate) return;
      const instanciaId = instanciaByRevisao.get(point.id);
      if (!instanciaId) return;
      onNavigate(buildProcessoPath(processoId, point.id, instanciaId));
    },
    [instanciaByRevisao, onNavigate, processoId]
  );

  if (!loading && pontos.length === 0) {
    return (
      <section className="tm-processo-matrix-section">
        <ChartCard title="Priorização do processo" titleHint={M.processoPriorizacao} hint={M.semDadosProcesso}>
          <p className="ds-hint">{M.semDadosProcesso}</p>
        </ChartCard>
      </section>
    );
  }

  return (
    <section className="tm-processo-matrix-section">
      <ChartCard
        title={`Priorização do processo — ${processoLabel}`}
        titleHint={M.processoPriorizacao}
        hint="Todas as melhorias e revisões comparáveis no mesmo gráfico impacto × esforço."
        toolbar={
          <button
            type="button"
            className={DS_GHOST_BTN}
            disabled={loading || pontos.length === 0}
            onClick={() =>
              exportImpactEffortMatrixPlotPng(plotRef.current, `matriz-${processoId}`, () =>
                onError("Não foi possível exportar a matriz como PNG.")
              )
            }
          >
            <ImageDown size={16} aria-hidden="true" />
            Exportar PNG
          </button>
        }
      >
        {loading ? (
          <LoadingActivityCard
            title="Carregando priorização"
            description="Montando matriz impacto × esforço de todas as melhorias."
            variant="compact"
          />
        ) : (
          <>
            <div className="tm-impact-effort-section__plot-wrap" ref={plotRef}>
              <ImpactEffortMatrix
                points={scatterPoints}
                activePointId={activeRevisaoId}
                threshold={threshold}
                classNames={impactEffortMatrixTransformometroClasses()}
                quadrantLabels={MATRIZ_QUADRANTE_LABELS_GRAFICO}
                onPointSelect={onNavigate ? handlePointSelect : undefined}
                emptyMessage={M.semDadosProcesso}
                ariaLabel={M.graficoProcessoAria}
              />
            </div>

            {melhorias.length > 1 ? (
              <ul className="tm-processo-matrix-section__series-legend" aria-label="Melhorias no gráfico">
                {melhorias.map((melhoria) => (
                  <li key={melhoria.instancia_id}>
                    <span
                      className="tm-processo-matrix-section__series-swatch"
                      style={{ backgroundColor: matrizSeriesColor(melhoria.color_index) }}
                      aria-hidden="true"
                    />
                    {melhoria.label}
                  </li>
                ))}
              </ul>
            ) : null}

            <div className="tm-impact-effort-section__legend-wrap">
              <FieldLabel
                className="tm-field__label tm-impact-effort-section__legend-label"
                label="Quadrantes"
                hint={M.quadrantes}
              />
              <ImpactEffortMatrixLegend
                className="tm-impact-effort-section__legend"
                quadrantLabels={MATRIZ_QUADRANTE_LABELS}
                quadrantDescriptions={MATRIZ_QUADRANTE_DESCRIPTIONS}
              />
            </div>

            <div className="tm-instancia-matrix-section__table-wrap">
              <FieldLabel
                className="tm-field__label tm-instancia-matrix-section__table-label"
                label="Ranking por prioridade"
                hint={M.rankingTabelaProcesso}
              />
              <table className="tm-instancia-matrix-section__table">
                <thead>
                  <tr>
                    <th scope="col"><TableHeader label="Melhoria" hint={M.melhoriaColuna} /></th>
                    <th scope="col"><TableHeader label="Versão" hint={C.versao} /></th>
                    <th scope="col"><TableHeader label="Cenário" hint={C.cenario} /></th>
                    <th scope="col"><TableHeader label="Impacto" hint={M.impactoScore} /></th>
                    <th scope="col"><TableHeader label="Esforço" hint={M.esforcoScore} /></th>
                    <th scope="col"><TableHeader label="Quadrante" hint={M.quadranteColuna} /></th>
                    <th scope="col"><TableHeader label="Líquida anual" hint={M.liquidaAnualColuna} /></th>
                    <th scope="col"><TableHeader label="Ativa" hint={M.revisaoAtivaColuna} /></th>
                  </tr>
                </thead>
                <tbody>
                  {rankingRows.map((ponto) => {
                    const isBaseline = ponto.cenario_tipo === "baseline";
                    const badgeClass = isBaseline
                      ? "tm-matrix-badge--neutral"
                      : MATRIZ_QUADRANTE_BADGE_CLASS[ponto.quadrante];

                    return (
                      <tr
                        key={ponto.revisao_id}
                        className={
                          ponto.revisao_id === activeRevisaoId
                            ? "tm-instancia-matrix-section__row--active"
                            : undefined
                        }
                      >
                        <td>{ponto.instancia_label ?? "—"}</td>
                        <td>
                          {onNavigate && ponto.instancia_id ? (
                            <button
                              type="button"
                              className="tm-instancia-matrix-section__link"
                              onClick={() =>
                                onNavigate(buildProcessoPath(processoId, ponto.revisao_id, ponto.instancia_id))
                              }
                            >
                              v{ponto.versao_revisao}
                            </button>
                          ) : (
                            `v${ponto.versao_revisao}`
                          )}
                        </td>
                        <td>{cenarioLabel(ponto.cenario_tipo)}</td>
                        <td>{isBaseline || !ponto.incluir_na_matriz ? "—" : formatScore(ponto.impacto)}</td>
                        <td>{isBaseline || !ponto.incluir_na_matriz ? "—" : formatScore(ponto.esforco)}</td>
                        <td>
                          <span className={`tm-matrix-badge ${badgeClass}`}>
                            {isBaseline ? "Ref." : MATRIZ_QUADRANTE_LABELS[ponto.quadrante]}
                          </span>
                        </td>
                        <td>
                          {isBaseline ? "—" : formatCurrency(ponto.metricas.economia_liquida_anual)}
                        </td>
                        <td>{ponto.revisao_ativa ? "●" : "○"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </ChartCard>
    </section>
  );
}
