import { useCallback, useEffect, useMemo, useState } from "react";

import {
  FieldLabel,
  ImpactEffortMatrix,
  ImpactEffortMatrixLegend,
  impactEffortMatrixTransformometroClasses,
  type ImpactEffortPoint,
} from "@delpi/plugin-ui";

import { ChartCard } from "../../components/ChartCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { TableHeader } from "../../components/TableHeader";
import { cenarioLabel } from "../../content/cenarioLabels";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  MATRIZ_QUADRANTE_BADGE_CLASS,
  MATRIZ_QUADRANTE_LABELS,
  MATRIZ_QUADRANTE_LABELS_GRAFICO,
} from "../../content/matrizImpactoLabels";
import {
  fetchInstanciaMatrizImpactoEsforco,
  type MatrizImpactoPonto,
} from "../../data/api/transformometroMatrixApi";
import { formatCurrency } from "../../utils/format";
import {
  matrizPontoToImpactEffortPoint,
  sortMatrizPontosForRanking,
} from "../../utils/matrizImpactoPoints";

type Props = {
  instanciaId: string;
  instanciaLabel: string;
  getAccessToken?: () => string | undefined;
  onError: (message: string | null) => void;
  onNavigateToRevisao?: (revisaoId: string) => void;
};

const M = TM_HELP_TOOLTIPS.matriz;
const C = TM_HELP_TOOLTIPS.columns;

function formatScore(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

export function InstanciaMatrizRevisoesSection({
  instanciaId,
  instanciaLabel,
  getAccessToken,
  onError,
  onNavigateToRevisao,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [pontos, setPontos] = useState<MatrizImpactoPonto[]>([]);
  const [threshold, setThreshold] = useState(50);
  const [activeRevisaoId, setActiveRevisaoId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const response = await fetchInstanciaMatrizImpactoEsforco(instanciaId, getAccessToken, {
        incluir_baseline: true,
      });
      setPontos(response.pontos);
      setThreshold(response.threshold);
      setActiveRevisaoId(response.ativo?.revisao_id ?? null);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar matriz da melhoria");
      setPontos([]);
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, onError]);

  useEffect(() => {
    void load();
  }, [load]);

  const scatterPoints = useMemo(
    () => pontos.map((ponto) => matrizPontoToImpactEffortPoint(ponto)),
    [pontos]
  );

  const rankingRows = useMemo(() => sortMatrizPontosForRanking(pontos), [pontos]);

  const handlePointSelect = useCallback(
    (point: ImpactEffortPoint) => {
      if (!onNavigateToRevisao) return;
      onNavigateToRevisao(point.id);
    },
    [onNavigateToRevisao]
  );

  if (!loading && pontos.length === 0) {
    return null;
  }

  return (
    <section className="tm-instancia-matrix-section">
      <ChartCard
        title={`Priorização das revisões — ${instanciaLabel}`}
        titleHint={M.instanciaPriorizacao}
        hint="Ranking e posicionamento de todas as revisões desta melhoria."
      >
        {loading ? (
          <LoadingActivityCard
            title="Carregando priorização"
            description="Montando matriz impacto × esforço da melhoria."
            variant="compact"
          />
        ) : (
          <>
            <div className="tm-impact-effort-section__plot-wrap">
              <ImpactEffortMatrix
                points={scatterPoints}
                activePointId={activeRevisaoId}
                threshold={threshold}
                classNames={impactEffortMatrixTransformometroClasses()}
                quadrantLabels={MATRIZ_QUADRANTE_LABELS_GRAFICO}
                onPointSelect={onNavigateToRevisao ? handlePointSelect : undefined}
                emptyMessage={M.semDados}
                ariaLabel={M.graficoInstanciaAria}
              />
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

            <div className="tm-instancia-matrix-section__table-wrap">
              <FieldLabel
                className="tm-field__label tm-instancia-matrix-section__table-label"
                label="Ranking por prioridade"
                hint={M.rankingTabela}
              />
              <table className="tm-instancia-matrix-section__table">
                <thead>
                  <tr>
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
                        <td>
                          {onNavigateToRevisao ? (
                            <button
                              type="button"
                              className="tm-instancia-matrix-section__link"
                              onClick={() => onNavigateToRevisao(ponto.revisao_id)}
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
                          <span
                            className={`tm-matrix-badge ${badgeClass}`}
                            title={
                              isBaseline
                                ? "Referência (linha de base)"
                                : `Impacto ${formatScore(ponto.impacto)} · Esforço ${formatScore(ponto.esforco)} · ${MATRIZ_QUADRANTE_LABELS[ponto.quadrante]}`
                            }
                          >
                            {isBaseline ? "Ref." : MATRIZ_QUADRANTE_LABELS[ponto.quadrante]}
                          </span>
                        </td>
                        <td>
                          {isBaseline
                            ? "—"
                            : formatCurrency(ponto.metricas.economia_liquida_anual)}
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
