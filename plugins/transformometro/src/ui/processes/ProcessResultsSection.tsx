import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";

import { DataTable } from "../../components/DataTable";
import { InlineErrorState } from "../../components/ErrorStateBox";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { TmStatusBadge } from "../../components/tmChromeUi";
import { cenarioLabel } from "../../content/cenarioLabels";
import { beneficioCalculoLabel } from "../../content/beneficioCalculoLabels";
import { TransformometroHttpError } from "../../data/api/transformometroHttp";
import {
  fetchInvestimentos,
  fetchMedicao,
  fetchProcessoComparativo,
  fetchRecursos,
  fetchVinculos,
  type Investimento,
  type Medicao,
  type OptionsData,
  type ProcessoComparativoItem,
  type ProcessoInstancia,
  type RecursoCompartilhado,
  type Revisao,
  type VinculoRecurso,
} from "../../data/api/transformometroApi";
import { describeHttpErrorTitle } from "../../utils/apiErrorMessage";
import { buildComparativoColumns, formatProcessoNumber } from "../../utils/processoDetailTables";
import { buildProcessoPath } from "../../utils/routeParser";
import { revisaoDisplayLabel } from "../../utils/revisaoLabels";
import { RevisionInvestmentsSection } from "../revision/registration/RevisionInvestmentsSection";
import { RevisionSharedResourcesSection } from "../revision/registration/RevisionSharedResourcesSection";
import {
  buildMeasurementComparisonRows,
  buildRevisionComparisonView,
  filterComparativoByRevisoes,
  findComparativoItem,
  provenanceForRevisionRole,
} from "./buildRevisionComparisonView";
import { MeasurementComparisonTable } from "./MeasurementComparisonTable";
import { instanciaNavLabel } from "./processWorkspaceNav";
import { RevisionCompareSummary } from "./RevisionCompareSummary";

type Props = {
  processoId: string;
  instancias: ProcessoInstancia[];
  revisoes: Revisao[];
  options: OptionsData;
  getAccessToken?: () => string | undefined;
  onNavigate: (path: string) => void;
  active: boolean;
};

const EMPTY = emptyStateCardBemClasses("ds");

type RevisionBundle = {
  medicao: Medicao | null;
  investimentos: Investimento[];
  vinculos: VinculoRecurso[];
  recursos: RecursoCompartilhado[];
};

/**
 * Resultados — Redesign & Compare V1 (composição frontend).
 * Sem aggregate/DTO/backend novo. Referência = `revisao_referencia_id` do domínio.
 */
export function ProcessResultsSection({
  processoId,
  instancias,
  revisoes,
  options,
  getAccessToken,
  onNavigate,
  active,
}: Props) {
  const [items, setItems] = useState<ProcessoComparativoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [selectedInstanciaId, setSelectedInstanciaId] = useState<string | null>(null);
  const [selectedRevisaoId, setSelectedRevisaoId] = useState<string | null>(null);
  const [toBeBundle, setToBeBundle] = useState<RevisionBundle | null>(null);
  const [asIsMedicao, setAsIsMedicao] = useState<Medicao | null>(null);
  const [revisionLoading, setRevisionLoading] = useState(false);
  const [asIsLoading, setAsIsLoading] = useState(false);
  const [revisionError, setRevisionError] = useState<string | null>(null);
  const [revisionErrorStatus, setRevisionErrorStatus] = useState<number | null>(null);
  const [showHeavyStructure, setShowHeavyStructure] = useState(false);

  const comparison = useMemo(
    () =>
      buildRevisionComparisonView({
        processId: processoId,
        instancias,
        revisoes,
        selectedInstanciaId,
        selectedRevisaoId,
      }),
    [instancias, processoId, revisoes, selectedInstanciaId, selectedRevisaoId],
  );

  const scopedComparisonItems = useMemo(
    () => filterComparativoByRevisoes(items, comparison.scopedRevisoes),
    [comparison.scopedRevisoes, items],
  );

  const toBeComparison = useMemo(
    () => findComparativoItem(scopedComparisonItems, comparison.selectedRevisionId),
    [comparison.selectedRevisionId, scopedComparisonItems],
  );
  const asIsComparison = useMemo(
    () => findComparativoItem(scopedComparisonItems, comparison.asIs?.revisao_id ?? null),
    [comparison.asIs?.revisao_id, scopedComparisonItems],
  );

  const loadComparison = useCallback(async () => {
    setLoading(true);
    setError(null);
    setErrorStatus(null);
    try {
      const data = await fetchProcessoComparativo(processoId, getAccessToken);
      setItems(data.items ?? []);
      setLoadedOnce(true);
    } catch (reason) {
      const status = reason instanceof TransformometroHttpError ? reason.status : null;
      setErrorStatus(status);
      setError(
        reason instanceof Error
          ? reason.message
          : "Não foi possível carregar a comparação de resultados.",
      );
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, processoId]);

  useEffect(() => {
    if (!active) return;
    if (loadedOnce && !error) return;
    void loadComparison();
  }, [active, error, loadComparison, loadedOnce]);

  useEffect(() => {
    setSelectedRevisaoId(null);
    setToBeBundle(null);
    setAsIsMedicao(null);
    setRevisionError(null);
    setRevisionErrorStatus(null);
    setShowHeavyStructure(false);
  }, [comparison.instanceId]);

  const loadToBeBundle = useCallback(
    async (revisaoId: string) => {
      setRevisionLoading(true);
      setRevisionError(null);
      setRevisionErrorStatus(null);
      try {
        const [medicao, investimentos, vinculos, recursos] = await Promise.all([
          fetchMedicao(revisaoId, getAccessToken),
          fetchInvestimentos(revisaoId, getAccessToken),
          fetchVinculos(revisaoId, getAccessToken),
          fetchRecursos(getAccessToken),
        ]);
        setToBeBundle({
          medicao,
          investimentos: investimentos.items ?? [],
          vinculos: vinculos.items ?? [],
          recursos: recursos.items ?? [],
        });
      } catch (reason) {
        setToBeBundle(null);
        const status = reason instanceof TransformometroHttpError ? reason.status : null;
        setRevisionErrorStatus(status);
        setRevisionError(
          reason instanceof Error
            ? reason.message
            : "Não foi possível carregar medição/investimentos/recursos desta revisão.",
        );
      } finally {
        setRevisionLoading(false);
      }
    },
    [getAccessToken],
  );

  const loadAsIsMedicao = useCallback(
    async (revisaoId: string) => {
      setAsIsLoading(true);
      try {
        const medicao = await fetchMedicao(revisaoId, getAccessToken);
        setAsIsMedicao(medicao);
      } catch {
        setAsIsMedicao(null);
      } finally {
        setAsIsLoading(false);
      }
    },
    [getAccessToken],
  );

  useEffect(() => {
    if (!active || !comparison.selectedRevisionId) {
      setToBeBundle(null);
      return;
    }
    if (
      comparison.mode === "pair" ||
      comparison.mode === "baseline_only" ||
      comparison.mode === "legacy_reference_missing"
    ) {
      void loadToBeBundle(comparison.selectedRevisionId);
    }
  }, [active, comparison.mode, comparison.selectedRevisionId, loadToBeBundle]);

  useEffect(() => {
    if (!active || comparison.mode !== "pair" || !comparison.asIs) {
      setAsIsMedicao(null);
      return;
    }
    void loadAsIsMedicao(comparison.asIs.revisao_id);
  }, [active, comparison.asIs, comparison.mode, loadAsIsMedicao]);

  const measurementRows = useMemo(
    () =>
      buildMeasurementComparisonRows(
        comparison.mode === "pair" ? asIsMedicao : comparison.mode === "baseline_only" ? toBeBundle?.medicao ?? null : null,
        comparison.mode === "pair" ? toBeBundle?.medicao ?? null : null,
      ),
    [asIsMedicao, comparison.mode, toBeBundle?.medicao],
  );

  const columns = useMemo(() => buildComparativoColumns(), []);

  const openRevisionSection = (
    revisaoId: string,
    section: "medicao" | "investimentos" | "recursos" | "mapeamento" | "diagrama",
  ) => {
    if (!comparison.instanceId) return;
    onNavigate(`${buildProcessoPath(processoId, revisaoId, comparison.instanceId)}#${section}`);
  };

  const calculatedSummary =
    comparison.mode === "pair"
      ? {
          asIsEconomy: asIsComparison?.totais.economia_liquida_mes ?? null,
          toBeEconomy: toBeComparison?.totais.economia_liquida_mes ?? null,
          deltaEconomy:
            asIsComparison != null && toBeComparison != null
              ? (toBeComparison.totais.economia_liquida_mes ?? 0) -
                (asIsComparison.totais.economia_liquida_mes ?? 0)
              : null,
        }
      : undefined;

  return (
    <section
      className="ds-card tm-processo-workspace-panel tm-processo-results"
      aria-labelledby="tm-process-resultados-title"
      data-results-mode={comparison.mode}
    >
      <h2 id="tm-process-resultados-title" className="ds-section-title">
        Resultados
      </h2>
      <p className="ds-hint">
        Redesign &amp; Compare: AS-IS é a revisão de referência do domínio; TO-BE é o cenário
        selecionado. Benefícios e totais do comparativo são <strong>calculados</strong> — não
        confundir com resultado observado em campo.
      </p>

      {comparison.mode === "no_instance" ? (
        <EmptyState
          classNames={EMPTY}
          title="Sem melhorias"
          defaultMessage="Nenhuma melhoria operacional registrada."
        />
      ) : null}

      {comparison.mode === "needs_instance_selection" ? (
        <EmptyState
          classNames={EMPTY}
          title="Contexto necessário"
          defaultMessage="Selecione uma melhoria para visualizar este conteúdo."
        >
          <ul className="tm-processo-results-instance-picker">
            {instancias.map((instancia) => (
              <li key={instancia.instancia_id}>
                <button
                  type="button"
                  className={DS_GHOST_BTN}
                  onClick={() => setSelectedInstanciaId(instancia.instancia_id)}
                >
                  {instanciaNavLabel(instancia)}
                </button>
              </li>
            ))}
          </ul>
        </EmptyState>
      ) : null}

      {comparison.instanceId && comparison.instance ? (
        <div
          className="tm-processo-results-scoped"
          data-selected-instancia={comparison.instanceId}
          data-selected-revisao={comparison.selectedRevisionId ?? undefined}
          data-reference-revisao={comparison.referenceRevisionId ?? undefined}
        >
          <header className="tm-processo-results-context" aria-label="Contexto da comparação">
            <dl className="tm-processo-results-context__grid">
              <div>
                <dt>Melhoria</dt>
                <dd>
                  {instanciaNavLabel(comparison.instance)}
                  {instancias.length > 1 ? (
                    <>
                      {" · "}
                      <button
                        type="button"
                        className="ds-link"
                        onClick={() => setSelectedInstanciaId(null)}
                      >
                        Trocar
                      </button>
                    </>
                  ) : null}
                </dd>
              </div>
              <div>
                <dt>Cenário</dt>
                <dd>
                  {comparison.toBe
                    ? `${revisaoDisplayLabel(comparison.toBe)} · ${cenarioLabel(comparison.toBe.cenario_tipo)}`
                    : "—"}
                  {comparison.toBe && !comparison.toBe.revisao_ativa ? (
                    <>
                      {" "}
                      <TmStatusBadge label="inativa" variant="neutral" />
                    </>
                  ) : null}
                  {comparison.toBe?.revisao_ativa ? (
                    <>
                      {" "}
                      <TmStatusBadge label="ativa" variant="success" />
                    </>
                  ) : null}
                </dd>
              </div>
              <div>
                <dt>Referência</dt>
                <dd>
                  {comparison.mode === "legacy_reference_missing"
                    ? "Não definida"
                    : comparison.asIs
                      ? `${revisaoDisplayLabel(comparison.asIs)} · ${cenarioLabel(comparison.asIs.cenario_tipo)}`
                      : comparison.mode === "baseline_only"
                        ? "Linha de base (própria)"
                        : "—"}
                </dd>
              </div>
            </dl>
          </header>

          {comparison.scopedRevisoes.length > 1 ? (
            <div className="tm-processo-results-revisao-picker" role="group" aria-label="Cenário (TO-BE)">
              <p className="ds-hint">Selecione o cenário (revisão TO-BE) neste contexto:</p>
              <ul className="tm-processo-results-instance-picker">
                {comparison.scopedRevisoes.map((revisao) => (
                  <li key={revisao.revisao_id}>
                    <button
                      type="button"
                      className={DS_GHOST_BTN}
                      aria-pressed={comparison.selectedRevisionId === revisao.revisao_id}
                      onClick={() => setSelectedRevisaoId(revisao.revisao_id)}
                    >
                      {revisaoDisplayLabel(revisao)} · {cenarioLabel(revisao.cenario_tipo)}
                      {!revisao.revisao_ativa ? " · inativa" : ""}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {comparison.mode === "no_revision" ? (
            <EmptyState
              classNames={EMPTY}
              title="Sem revisões"
              defaultMessage="Ainda não há cenário para comparação."
            />
          ) : null}

          {comparison.mode === "needs_revision_selection" ? (
            <EmptyState
              classNames={EMPTY}
              title="Revisão necessária"
              defaultMessage="Selecione uma revisão para visualizar medição, investimentos e recursos."
            />
          ) : null}

          {comparison.mode === "legacy_reference_missing" ? (
            <EmptyState
              classNames={EMPTY}
              title="Referência ausente"
              defaultMessage="Esta revisão não possui referência de comparação definida."
            />
          ) : null}

          {comparison.mode === "reference_not_in_scope" ? (
            <EmptyState
              classNames={EMPTY}
              title="Referência fora do contexto"
              defaultMessage="Esta revisão não possui referência de comparação definida."
            />
          ) : null}

          {(comparison.mode === "pair" || comparison.mode === "baseline_only") && comparison.toBe ? (
            <div className="tm-processo-results-block" data-results-block="compare-summary">
              <h3 className="ds-subsection-title">Comparação</h3>
              <RevisionCompareSummary
                mode={comparison.mode === "pair" ? "pair" : "baseline_only"}
                asIsLabel={
                  comparison.asIs
                    ? `${revisaoDisplayLabel(comparison.asIs)} · ${cenarioLabel(comparison.asIs.cenario_tipo)}`
                    : "—"
                }
                toBeLabel={
                  comparison.mode === "baseline_only"
                    ? null
                    : `${revisaoDisplayLabel(comparison.toBe)} · ${cenarioLabel(comparison.toBe.cenario_tipo)}`
                }
                asIsProvenance={provenanceForRevisionRole("as_is", comparison.asIs)}
                toBeProvenance={
                  comparison.mode === "pair"
                    ? provenanceForRevisionRole("to_be", comparison.toBe)
                    : null
                }
                calculatedSummary={calculatedSummary}
              />
            </div>
          ) : null}

          {loading && scopedComparisonItems.length === 0 ? (
            <LoadingActivityCard
              title="Carregando comparação calculada"
              description="Buscando totais calculados das revisões deste contexto."
            />
          ) : null}

          {error ? (
            <InlineErrorState
              title={
                errorStatus === 403 || errorStatus === 401
                  ? describeHttpErrorTitle(errorStatus)
                  : "Falha ao carregar comparação calculada"
              }
              message={error}
              onAction={errorStatus === 403 ? undefined : () => void loadComparison()}
            />
          ) : null}

          {!loading &&
          !error &&
          loadedOnce &&
          scopedComparisonItems.length === 0 &&
          comparison.scopedRevisoes.length > 0 ? (
            <EmptyState
              classNames={EMPTY}
              title="Sem comparação"
              defaultMessage="Ainda não há baseline/medição comparável."
            />
          ) : null}

          {scopedComparisonItems.length > 0 ? (
            <div className="tm-processo-results-comparison" data-results-block="comparativo-tabela">
              <h3 className="ds-subsection-title">Comparação calculada</h3>
              <p className="ds-hint">
                Totais e breakdowns são <strong>CALCULADOS</strong> pelo contrato de comparação —
                não são economia realizada observada.
              </p>
              <div className="tm-processo-results-table-scroll">
                <DataTable
                  columns={columns}
                  rows={scopedComparisonItems}
                  rowKey={(row) => row.revisao_id}
                />
              </div>
            </div>
          ) : null}

          {comparison.selectedRevisionId &&
          (comparison.mode === "pair" ||
            comparison.mode === "baseline_only" ||
            comparison.mode === "legacy_reference_missing") ? (
            <>
              {(revisionLoading || asIsLoading) && !toBeBundle ? (
                <LoadingActivityCard
                  title="Carregando indicadores da revisão"
                  description="Medição, investimentos e recursos do mesmo contexto selecionado."
                />
              ) : null}

              {revisionError ? (
                <InlineErrorState
                  title={
                    revisionErrorStatus === 403 || revisionErrorStatus === 401
                      ? describeHttpErrorTitle(revisionErrorStatus)
                      : "Falha ao carregar dados da revisão"
                  }
                  message={revisionError}
                  onAction={
                    revisionErrorStatus === 403
                      ? undefined
                      : () => void loadToBeBundle(comparison.selectedRevisionId!)
                  }
                />
              ) : null}

              {!revisionLoading && !revisionError && toBeBundle ? (
                <>
                  <div className="tm-processo-results-block" data-results-block="medicoes">
                    <div className="tm-processo-results-block__head">
                      <h3 className="ds-subsection-title">Indicadores operacionais</h3>
                      <button
                        type="button"
                        className="ds-link"
                        onClick={() =>
                          openRevisionSection(comparison.selectedRevisionId!, "medicao")
                        }
                      >
                        Abrir na revisão
                      </button>
                    </div>
                    {comparison.mode === "pair" ? (
                      <MeasurementComparisonTable
                        rows={measurementRows}
                        hasAsIsMeasurement={Boolean(asIsMedicao)}
                        hasToBeMeasurement={Boolean(toBeBundle.medicao)}
                        pairMode
                      />
                    ) : toBeBundle.medicao ? (
                      <MeasurementComparisonTable
                        rows={buildMeasurementComparisonRows(toBeBundle.medicao, null)}
                        hasAsIsMeasurement
                        hasToBeMeasurement={false}
                        pairMode={false}
                      />
                    ) : (
                      <EmptyState
                        classNames={EMPTY}
                        title="Sem medição"
                        defaultMessage="Sem medição informada para este cenário."
                      />
                    )}
                  </div>

                  <div className="tm-processo-results-block" data-results-block="investimentos">
                    <div className="tm-processo-results-block__head">
                      <h3 className="ds-subsection-title">Investimentos</h3>
                      <button
                        type="button"
                        className="ds-link"
                        onClick={() =>
                          openRevisionSection(comparison.selectedRevisionId!, "investimentos")
                        }
                      >
                        Abrir na revisão
                      </button>
                    </div>
                    <p className="ds-hint">
                      Investimento do cenário selecionado
                      {comparison.mode === "pair" ? " (TO-BE / PROPOSTO)" : ""}. Sem fabricar
                      investimento AS-IS.
                    </p>
                    {toBeBundle.investimentos.length === 0 ? (
                      <EmptyState
                        classNames={EMPTY}
                        title="Sem investimentos"
                        defaultMessage="Nenhum investimento registrado para este cenário."
                      />
                    ) : (
                      <RevisionInvestmentsSection
                        embeddedInCard
                        readOnly
                        revisaoId={comparison.selectedRevisionId}
                        options={options}
                        investimentos={toBeBundle.investimentos}
                        getAccessToken={getAccessToken}
                        onError={setRevisionError}
                        onReload={async () => {
                          await loadToBeBundle(comparison.selectedRevisionId!);
                        }}
                      />
                    )}
                  </div>

                  <div className="tm-processo-results-block" data-results-block="recursos">
                    <div className="tm-processo-results-block__head">
                      <h3 className="ds-subsection-title">Recursos e custos</h3>
                      <button
                        type="button"
                        className="ds-link"
                        onClick={() =>
                          openRevisionSection(comparison.selectedRevisionId!, "recursos")
                        }
                      >
                        Abrir na revisão
                      </button>
                    </div>
                    <p className="ds-hint">
                      Vínculos desta revisão. Custos unitários do catálogo permanecem em
                      Configurações → Recursos compartilhados.
                    </p>
                    {toBeBundle.vinculos.length === 0 ? (
                      <EmptyState
                        classNames={EMPTY}
                        title="Sem recursos"
                        defaultMessage="Nenhum recurso vinculado a este cenário."
                      />
                    ) : (
                      <RevisionSharedResourcesSection
                        embeddedInCard
                        readOnly
                        revisaoId={comparison.selectedRevisionId}
                        options={options}
                        recursos={toBeBundle.recursos}
                        vinculos={toBeBundle.vinculos}
                        getAccessToken={getAccessToken}
                        onError={setRevisionError}
                        onReload={async () => {
                          await loadToBeBundle(comparison.selectedRevisionId!);
                        }}
                      />
                    )}
                  </div>

                  <div className="tm-processo-results-block" data-results-block="beneficios">
                    <h3 className="ds-subsection-title">Benefícios calculados</h3>
                    {toBeComparison ? (
                      <dl className="ds-dl-grid">
                        <div>
                          <dt>Categoria de cálculo</dt>
                          <dd>
                            {beneficioCalculoLabel(toBeComparison.beneficio_calculo_categoria)}
                          </dd>
                        </div>
                        <div>
                          <dt>Economia bruta (CALCULADO)</dt>
                          <dd>{formatProcessoNumber(toBeComparison.totais.economia_bruta)}</dd>
                        </div>
                        <div>
                          <dt>Economia líquida/mês (CALCULADO)</dt>
                          <dd>
                            {formatProcessoNumber(toBeComparison.totais.economia_liquida_mes)}
                          </dd>
                        </div>
                        <div>
                          <dt>Horas economizadas/mês (CALCULADO)</dt>
                          <dd>
                            {formatProcessoNumber(toBeComparison.totais.horas_economizadas_mes)}
                          </dd>
                        </div>
                        <div>
                          <dt>Ganho de capacidade (CALCULADO)</dt>
                          <dd>{formatProcessoNumber(toBeComparison.totais.ganho_capacidade)}</dd>
                        </div>
                        <div>
                          <dt>Investimento total/mês (CALCULADO)</dt>
                          <dd>
                            {formatProcessoNumber(toBeComparison.totais.investimento_total_mes)}
                          </dd>
                        </div>
                      </dl>
                    ) : (
                      <EmptyState
                        classNames={EMPTY}
                        title="Sem benefício calculado"
                        defaultMessage="Ainda não há baseline/medição comparável."
                      />
                    )}
                  </div>

                  <div className="tm-processo-results-block" data-results-block="estrutura-fluxo">
                    <h3 className="ds-subsection-title">Mapeamento e fluxo alterados</h3>
                    <p className="ds-hint">
                      Diff estrutural de nós (mantido/alterado/incluído/removido) depende do overlay
                      da revisão. Nesta V1 a comparação detalhada abre nas seções canônicas —
                      sem inventar graph-diff no frontend.
                    </p>
                    {!showHeavyStructure ? (
                      <button
                        type="button"
                        className={DS_GHOST_BTN}
                        onClick={() => setShowHeavyStructure(true)}
                      >
                        Mostrar atalhos de mapeamento e fluxo
                      </button>
                    ) : (
                      <ul className="tm-processo-results-structure-links">
                        {comparison.asIs && comparison.mode === "pair" ? (
                          <>
                            <li>
                              <button
                                type="button"
                                className="ds-link"
                                onClick={() =>
                                  openRevisionSection(comparison.asIs!.revisao_id, "mapeamento")
                                }
                              >
                                Mapeamento AS-IS ({revisaoDisplayLabel(comparison.asIs)})
                              </button>
                            </li>
                            <li>
                              <button
                                type="button"
                                className="ds-link"
                                onClick={() =>
                                  openRevisionSection(comparison.asIs!.revisao_id, "diagrama")
                                }
                              >
                                Fluxo AS-IS ({revisaoDisplayLabel(comparison.asIs)})
                              </button>
                            </li>
                          </>
                        ) : null}
                        <li>
                          <button
                            type="button"
                            className="ds-link"
                            onClick={() =>
                              openRevisionSection(comparison.selectedRevisionId!, "mapeamento")
                            }
                          >
                            Mapeamento do cenário (TO-BE)
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            className="ds-link"
                            onClick={() =>
                              openRevisionSection(comparison.selectedRevisionId!, "diagrama")
                            }
                          >
                            Fluxo do cenário (TO-BE)
                          </button>
                        </li>
                      </ul>
                    )}
                  </div>
                </>
              ) : null}
            </>
          ) : null}
        </div>
      ) : null}

      {comparison.instanceId ? (
        <div className="tm-processo-workspace-overview__actions">
          <button
            type="button"
            className={DS_GHOST_BTN}
            disabled={loading}
            onClick={() => void loadComparison()}
          >
            {loading ? "Atualizando…" : "Atualizar comparação"}
          </button>
        </div>
      ) : null}
    </section>
  );
}
