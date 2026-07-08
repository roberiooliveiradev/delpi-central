import { useCallback, useEffect, useMemo, useState } from "react";

import {
  ImpactEffortMatrix,
  ImpactEffortMatrixLegend,
  impactEffortMatrixTransformometroClasses,
  type ImpactEffortPoint,
} from "@delpi/plugin-ui";

import { ChartCard } from "../../components/ChartCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { cenarioLabel } from "../../content/cenarioLabels";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  MATRIZ_QUADRANTE_BADGE_CLASS,
  MATRIZ_QUADRANTE_LABELS,
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
      <ChartCard title={`Priorização das revisões — ${instanciaLabel}`} hint={M.instanciaPriorizacao}>
        {loading ? (
          <LoadingActivityCard
            title="Carregando priorização"
            description="Montando matriz impacto × esforço da melhoria."
            variant="compact"
          />
        ) : (
          <>
            <ImpactEffortMatrix
              points={scatterPoints}
              activePointId={activeRevisaoId}
              threshold={threshold}
              classNames={impactEffortMatrixTransformometroClasses()}
              onPointSelect={onNavigateToRevisao ? handlePointSelect : undefined}
              emptyMessage={M.semDados}
              ariaLabel={M.graficoInstanciaAria}
            />
            <ImpactEffortMatrixLegend quadrantLabels={MATRIZ_QUADRANTE_LABELS} />

            <div className="tm-instancia-matrix-section__table-wrap">
              <table className="tm-instancia-matrix-section__table">
                <thead>
                  <tr>
                    <th scope="col">Versão</th>
                    <th scope="col">Cenário</th>
                    <th scope="col">Impacto</th>
                    <th scope="col">Esforço</th>
                    <th scope="col">Quadrante</th>
                    <th scope="col">Líquida anual</th>
                    <th scope="col">Ativa</th>
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
                                ? "Referência (baseline)"
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
