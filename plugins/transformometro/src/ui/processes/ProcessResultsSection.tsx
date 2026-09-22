import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { EmptyState, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";

import { DataTable } from "../../components/DataTable";
import { InlineErrorState } from "../../components/ErrorStateBox";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { TmStatusBadge } from "../../components/tmChromeUi";
import { cenarioLabel } from "../../content/cenarioLabels";
import { beneficioCalculoLabel } from "../../content/beneficioCalculoLabels";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
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
import { ResultsContextHeader } from "./ResultsContextHeader";
import { ResultsProvenanceLegend } from "./ResultsProvenanceLegend";
import { ResultsSectionBlock } from "./ResultsSectionBlock";
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
const H = TM_HELP_TOOLTIPS.resultados;
const SCENARIO_SELECT_THRESHOLD = 5;

type RevisionBundle = {
  medicao: Medicao | null;
  investimentos: Investimento[];
  vinculos: VinculoRecurso[];
  recursos: RecursoCompartilhado[];
};

/**
 * Resultados — Redesign & Compare V1 (composição frontend).
 * Sem aggregate/DTO/backend novo. Referência vem do domínio (campo canônico na revisão).
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
        comparison.mode === "pair"
          ? asIsMedicao
          : comparison.mode === "baseline_only"
            ? toBeBundle?.medicao ?? null
            : null,
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

  const tertiaryOpenLink = (label: string, onClick: () => void) => (
    <button type="button" className="ds-link tm-processo-results-tertiary" onClick={onClick}>
      {label}
    </button>
  );

  const scenarioPicker: ReactNode =
    comparison.scopedRevisoes.length > 1 ? (
      <div
        className="tm-processo-results-revisao-picker"
        role="group"
        aria-label="Trocar cenário"
      >
        <p className="tm-processo-results-block__helper">Trocar cenário</p>
        {comparison.scopedRevisoes.length >= SCENARIO_SELECT_THRESHOLD ? (
          <label className="tm-processo-results-revisao-select">
            <span className="sr-only">Cenário proposto</span>
            <select
              value={comparison.selectedRevisionId ?? ""}
              onChange={(event) => setSelectedRevisaoId(event.target.value || null)}
            >
              <option value="">Selecione um cenário…</option>
              {comparison.scopedRevisoes.map((revisao) => (
                <option key={revisao.revisao_id} value={revisao.revisao_id}>
                  {revisaoDisplayLabel(revisao)} · {cenarioLabel(revisao.cenario_tipo)}
                  {!revisao.revisao_ativa ? " · inativa" : ""}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <ul className="tm-processo-results-scenario-list" role="listbox" aria-label="Cenários">
            {comparison.scopedRevisoes.map((revisao) => {
              const selected = comparison.selectedRevisionId === revisao.revisao_id;
              return (
                <li key={revisao.revisao_id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={selected}
                    className={
                      selected
                        ? "tm-processo-results-scenario tm-processo-results-scenario--selected"
                        : "tm-processo-results-scenario"
                    }
                    onClick={() => setSelectedRevisaoId(revisao.revisao_id)}
                  >
                    <span className="tm-processo-results-scenario__label">
                      {revisaoDisplayLabel(revisao)}
                    </span>
                    <span className="tm-processo-results-scenario__meta">
                      {cenarioLabel(revisao.cenario_tipo)}
                      {!revisao.revisao_ativa ? " · inativa" : ""}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    ) : null;

  return (
    <section
      className="ds-card tm-processo-workspace-panel tm-processo-results"
      aria-labelledby="tm-process-resultados-title"
      data-results-mode={comparison.mode}
    >
      <div className="tm-processo-results__intro">
        <h2 id="tm-process-resultados-title" className="ds-section-title">
          Resultados
        </h2>
        <p className="tm-processo-results__lede">{H.intro}</p>
        <ResultsProvenanceLegend />
      </div>

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
          <ResultsContextHeader
            instance={comparison.instance}
            toBe={comparison.toBe}
            asIs={comparison.asIs}
            mode={comparison.mode}
            canChangeInstance={instancias.length > 1}
            onChangeInstance={() => setSelectedInstanciaId(null)}
            onOpenRevision={
              comparison.selectedRevisionId
                ? () => openRevisionSection(comparison.selectedRevisionId!, "medicao")
                : undefined
            }
            scenarioPicker={scenarioPicker}
          />

          {comparison.mode === "no_revision" ? (
            <EmptyState
              classNames={EMPTY}
              title="Sem cenário"
              defaultMessage="Ainda não há cenário para comparação."
            />
          ) : null}

          {comparison.mode === "needs_revision_selection" ? (
            <EmptyState
              classNames={EMPTY}
              title="Cenário necessário"
              defaultMessage="Selecione um cenário para visualizar a comparação."
            />
          ) : null}

          {comparison.mode === "legacy_reference_missing" ||
          comparison.mode === "reference_not_in_scope" ? (
            <EmptyState
              classNames={EMPTY}
              title="Referência ausente"
              defaultMessage="Este cenário não possui uma referência de comparação definida."
            />
          ) : null}

          {(comparison.mode === "pair" || comparison.mode === "baseline_only") && comparison.toBe ? (
            <ResultsSectionBlock
              id="compare-summary"
              title="Resumo da comparação"
              helper="AS-IS é a referência; TO-BE é o cenário proposto; DELTA é a diferença calculada."
            >
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
            </ResultsSectionBlock>
          ) : null}

          {loading && scopedComparisonItems.length === 0 ? (
            <LoadingActivityCard
              title="Carregando comparação"
              description="Buscando totais calculados deste contexto."
            />
          ) : null}

          {error ? (
            <InlineErrorState
              title={
                errorStatus === 403 || errorStatus === 401
                  ? describeHttpErrorTitle(errorStatus)
                  : "Falha ao carregar comparação"
              }
              message={error}
              onAction={errorStatus === 403 ? undefined : () => void loadComparison()}
            />
          ) : null}

          {comparison.selectedRevisionId &&
          (comparison.mode === "pair" ||
            comparison.mode === "baseline_only" ||
            comparison.mode === "legacy_reference_missing") ? (
            <>
              {(revisionLoading || asIsLoading) && !toBeBundle ? (
                <LoadingActivityCard
                  title="Carregando indicadores"
                  description="Medição, investimentos e recursos do cenário selecionado."
                />
              ) : null}

              {revisionError ? (
                <InlineErrorState
                  title={
                    revisionErrorStatus === 403 || revisionErrorStatus === 401
                      ? describeHttpErrorTitle(revisionErrorStatus)
                      : "Falha ao carregar dados do cenário"
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
                  <ResultsSectionBlock
                    id="medicoes"
                    title="Indicadores operacionais"
                    help={H.indicadores}
                    helper="Compare referência e cenário. Δ é CALCULADO — AS-IS e TO-BE vêm das revisões."
                    action={tertiaryOpenLink("Ver medição", () =>
                      openRevisionSection(comparison.selectedRevisionId!, "medicao"),
                    )}
                  >
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
                        title="Sem indicadores"
                        defaultMessage="Não há indicadores informados para este cenário."
                      />
                    )}
                  </ResultsSectionBlock>

                  <ResultsSectionBlock
                    id="beneficios"
                    title="Benefícios calculados"
                    help={H.beneficios}
                    helper="Estimativas derivadas da comparação — não são benefícios já obtidos em campo."
                  >
                    {toBeComparison ? (
                      <div className="tm-processo-results-benefits">
                        <p className="tm-processo-results-benefits__meta">
                          Categoria:{" "}
                          {beneficioCalculoLabel(toBeComparison.beneficio_calculo_categoria)}
                        </p>
                        <ul className="tm-processo-results-benefits__grid">
                          <BenefitKpi
                            label="Economia líquida/mês"
                            value={formatProcessoNumber(
                              toBeComparison.totais.economia_liquida_mes,
                            )}
                            emphasis
                          />
                          <BenefitKpi
                            label="Economia bruta"
                            value={formatProcessoNumber(toBeComparison.totais.economia_bruta)}
                          />
                          <BenefitKpi
                            label="Horas economizadas/mês"
                            value={formatProcessoNumber(
                              toBeComparison.totais.horas_economizadas_mes,
                            )}
                            emphasis
                          />
                          <BenefitKpi
                            label="Investimento total/mês"
                            value={formatProcessoNumber(
                              toBeComparison.totais.investimento_total_mes,
                            )}
                            emphasis
                          />
                          <BenefitKpi
                            label="Ganho de capacidade"
                            value={formatProcessoNumber(toBeComparison.totais.ganho_capacidade)}
                          />
                        </ul>
                      </div>
                    ) : (
                      <EmptyState
                        classNames={EMPTY}
                        title="Sem benefício calculado"
                        defaultMessage="Ainda não há baseline/medição comparável."
                      />
                    )}
                  </ResultsSectionBlock>

                  <ResultsSectionBlock
                    id="investimentos"
                    title="Investimentos"
                    help={H.investimentos}
                    helper="Valores necessários para viabilizar o cenário proposto. Sem fabricar investimento da referência."
                    action={tertiaryOpenLink("Ver investimentos", () =>
                      openRevisionSection(comparison.selectedRevisionId!, "investimentos"),
                    )}
                  >
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
                  </ResultsSectionBlock>

                  <ResultsSectionBlock
                    id="recursos"
                    title="Recursos e custos"
                    help={H.recursos}
                    helper="Recursos associados ao cenário selecionado. Custos unitários do catálogo continuam em Configurações → Recursos compartilhados."
                    action={tertiaryOpenLink("Ver recursos", () =>
                      openRevisionSection(comparison.selectedRevisionId!, "recursos"),
                    )}
                  >
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
                  </ResultsSectionBlock>

                  <ResultsSectionBlock
                    id="estrutura-fluxo"
                    title="Impacto no processo"
                    helper="Consulte onde a estrutura e o fluxo do processo foram alterados neste cenário."
                  >
                    {!showHeavyStructure ? (
                      <button
                        type="button"
                        className={DS_GHOST_BTN}
                        onClick={() => setShowHeavyStructure(true)}
                      >
                        Ver mapeamento e fluxo
                      </button>
                    ) : (
                      <div className="tm-processo-results-structure">
                        <p className="tm-processo-results-block__helper">
                          Consulte o mapeamento da revisão para visualizar as alterações
                          disponíveis.
                        </p>
                        <ul className="tm-processo-results-structure-links">
                          {comparison.asIs && comparison.mode === "pair" ? (
                            <>
                              <li>
                                <button
                                  type="button"
                                  className="ds-link"
                                  onClick={() =>
                                    openRevisionSection(
                                      comparison.asIs!.revisao_id,
                                      "mapeamento",
                                    )
                                  }
                                >
                                  Ver estrutura (referência)
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
                                  Ver fluxo (referência)
                                </button>
                              </li>
                            </>
                          ) : null}
                          <li>
                            <button
                              type="button"
                              className="ds-link"
                              onClick={() =>
                                openRevisionSection(
                                  comparison.selectedRevisionId!,
                                  "mapeamento",
                                )
                              }
                            >
                              Ver estrutura do cenário
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
                              Ver fluxo do cenário
                            </button>
                          </li>
                        </ul>
                      </div>
                    )}
                  </ResultsSectionBlock>

                  {!loading &&
                  !error &&
                  loadedOnce &&
                  scopedComparisonItems.length === 0 &&
                  comparison.scopedRevisoes.length > 0 ? (
                    <EmptyState
                      classNames={EMPTY}
                      title="Sem comparação detalhada"
                      defaultMessage="Ainda não há baseline/medição comparável."
                    />
                  ) : null}

                  {scopedComparisonItems.length > 0 ? (
                    <details
                      className="tm-processo-results-detail-disclosure"
                      data-results-block="comparativo-tabela"
                    >
                      <summary className="tm-processo-results-detail-disclosure__summary">
                        Ver comparação detalhada
                      </summary>
                      <div className="tm-processo-results-detail-disclosure__body">
                        <p className="tm-processo-results-block__helper">
                          Totais e breakdowns calculados — aprofundamento técnico do resumo.
                        </p>
                        <div className="tm-processo-results-table-scroll tm-processo-results-table-scroll--detail">
                          <DataTable
                            columns={columns}
                            rows={scopedComparisonItems}
                            rowKey={(row) => row.revisao_id}
                          />
                        </div>
                      </div>
                    </details>
                  ) : null}
                </>
              ) : null}
            </>
          ) : null}
        </div>
      ) : null}

      {comparison.instanceId ? (
        <div className="tm-processo-results__utility">
          <button
            type="button"
            className="tm-processo-results-refresh"
            disabled={loading}
            title={H.atualizar}
            aria-label={H.atualizar}
            onClick={() => void loadComparison()}
          >
            <RefreshCw size={14} aria-hidden />
            <span>{loading ? "Atualizando…" : "Atualizar comparação"}</span>
          </button>
        </div>
      ) : null}
    </section>
  );
}

function BenefitKpi({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <li
      className={
        emphasis
          ? "tm-processo-results-benefit-kpi tm-processo-results-benefit-kpi--emphasis"
          : "tm-processo-results-benefit-kpi"
      }
    >
      <span className="tm-processo-results-benefit-kpi__label">{label}</span>
      <strong className="tm-processo-results-benefit-kpi__value">{value}</strong>
      <TmStatusBadge label="CALCULADO" variant="neutral" />
    </li>
  );
}
