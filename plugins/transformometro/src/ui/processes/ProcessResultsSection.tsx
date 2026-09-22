import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";

import { DataTable } from "../../components/DataTable";
import { InlineErrorState } from "../../components/ErrorStateBox";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { cenarioLabel } from "../../content/cenarioLabels";
import { beneficioCalculoLabel } from "../../content/beneficioCalculoLabels";
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
import { buildComparativoColumns, formatProcessoNumber } from "../../utils/processoDetailTables";
import { buildProcessoPath } from "../../utils/routeParser";
import { revisaoDisplayLabel } from "../../utils/revisaoLabels";
import { RevisionInvestmentsSection } from "../revision/registration/RevisionInvestmentsSection";
import { RevisionMeasurementSection } from "../revision/registration/RevisionMeasurementSection";
import { RevisionSharedResourcesSection } from "../revision/registration/RevisionSharedResourcesSection";
import { instanciaNavLabel } from "./processWorkspaceNav";

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
 * Resultados — composição frontend de comparison + medição/investimentos/recursos
 * read-only das capabilities existentes. Sem aggregate/DTO novo.
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
  const [loadedOnce, setLoadedOnce] = useState(false);
  /** Explicit selection only — never silent fallback when multiple instances. */
  const [selectedInstanciaId, setSelectedInstanciaId] = useState<string | null>(null);
  const [selectedRevisaoId, setSelectedRevisaoId] = useState<string | null>(null);
  const [revisionBundle, setRevisionBundle] = useState<RevisionBundle | null>(null);
  const [revisionLoading, setRevisionLoading] = useState(false);
  const [revisionError, setRevisionError] = useState<string | null>(null);

  const requiresInstanceSelection = instancias.length > 1;
  const contextInstanciaId = useMemo(() => {
    if (instancias.length === 1) return instancias[0]!.instancia_id;
    if (requiresInstanceSelection) return selectedInstanciaId;
    return null;
  }, [instancias, requiresInstanceSelection, selectedInstanciaId]);

  const scopedRevisoes = useMemo(() => {
    if (!contextInstanciaId) return [];
    const needle = contextInstanciaId.toLowerCase();
    return revisoes.filter((row) => String(row.instancia_id ?? "").toLowerCase() === needle);
  }, [contextInstanciaId, revisoes]);

  const contextRevisaoId = useMemo(() => {
    if (scopedRevisoes.length === 1) return scopedRevisoes[0]!.revisao_id;
    if (scopedRevisoes.length > 1) return selectedRevisaoId;
    return null;
  }, [scopedRevisoes, selectedRevisaoId]);

  const scopedComparisonItems = useMemo(() => {
    if (!contextInstanciaId) return [];
    const allowed = new Set(scopedRevisoes.map((row) => row.revisao_id));
    return items.filter((row) => allowed.has(row.revisao_id));
  }, [contextInstanciaId, items, scopedRevisoes]);

  const selectedComparison = useMemo(
    () => scopedComparisonItems.find((row) => row.revisao_id === contextRevisaoId) ?? null,
    [contextRevisaoId, scopedComparisonItems],
  );

  const loadComparison = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProcessoComparativo(processoId, getAccessToken);
      setItems(data.items ?? []);
      setLoadedOnce(true);
    } catch (reason) {
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
    setRevisionBundle(null);
    setRevisionError(null);
  }, [contextInstanciaId]);

  const loadRevisionBundle = useCallback(
    async (revisaoId: string) => {
      setRevisionLoading(true);
      setRevisionError(null);
      try {
        const [medicao, investimentos, vinculos, recursos] = await Promise.all([
          fetchMedicao(revisaoId, getAccessToken),
          fetchInvestimentos(revisaoId, getAccessToken),
          fetchVinculos(revisaoId, getAccessToken),
          fetchRecursos(getAccessToken),
        ]);
        setRevisionBundle({
          medicao,
          investimentos: investimentos.items ?? [],
          vinculos: vinculos.items ?? [],
          recursos: recursos.items ?? [],
        });
      } catch (reason) {
        setRevisionBundle(null);
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

  useEffect(() => {
    if (!active || !contextRevisaoId) {
      setRevisionBundle(null);
      return;
    }
    void loadRevisionBundle(contextRevisaoId);
  }, [active, contextRevisaoId, loadRevisionBundle]);

  const columns = useMemo(() => buildComparativoColumns(), []);
  const activeRevisao = scopedRevisoes.find((row) => row.revisao_id === contextRevisaoId) ?? null;

  const openRevisionSection = (section: "medicao" | "investimentos" | "recursos") => {
    if (!contextInstanciaId || !contextRevisaoId) return;
    onNavigate(
      `${buildProcessoPath(processoId, contextRevisaoId, contextInstanciaId)}#${section}`,
    );
  };

  return (
    <section
      className="ds-card tm-processo-workspace-panel tm-processo-results"
      aria-labelledby="tm-process-resultados-title"
    >
      <h2 id="tm-process-resultados-title" className="ds-section-title">
        Resultados
      </h2>
      <p className="ds-hint">
        Comparação e benefícios <strong>calculados</strong> a partir das medições informadas nas
        revisões. Não confundir com resultado observado em campo.
      </p>

      {instancias.length === 0 ? (
        <EmptyState
          classNames={EMPTY}
          title="Sem melhorias"
          defaultMessage="Nenhuma melhoria operacional registrada."
        />
      ) : null}

      {requiresInstanceSelection && !selectedInstanciaId ? (
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

      {contextInstanciaId ? (
        <div
          className="tm-processo-results-scoped"
          data-selected-instancia={contextInstanciaId}
          data-selected-revisao={contextRevisaoId ?? undefined}
        >
          <p className="ds-hint">
            Melhoria:{" "}
            {instanciaNavLabel(
              instancias.find((row) => row.instancia_id === contextInstanciaId)!,
            )}
            {requiresInstanceSelection ? (
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
          </p>

          {scopedRevisoes.length > 1 ? (
            <div className="tm-processo-results-revisao-picker" role="group" aria-label="Revisão">
              <p className="ds-hint">Selecione a revisão (baseline/cenário) neste contexto:</p>
              <ul className="tm-processo-results-instance-picker">
                {scopedRevisoes.map((revisao) => (
                  <li key={revisao.revisao_id}>
                    <button
                      type="button"
                      className={DS_GHOST_BTN}
                      aria-pressed={contextRevisaoId === revisao.revisao_id}
                      onClick={() => setSelectedRevisaoId(revisao.revisao_id)}
                    >
                      {revisaoDisplayLabel(revisao)} · {cenarioLabel(revisao.cenario_tipo)}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {scopedRevisoes.length === 0 ? (
            <EmptyState
              classNames={EMPTY}
              title="Sem revisões"
              defaultMessage="Ainda não há baseline/medição comparável."
            />
          ) : null}

          {loading && scopedComparisonItems.length === 0 ? (
            <LoadingActivityCard
              title="Carregando comparação calculada"
              description="Buscando totais calculados das revisões deste contexto."
            />
          ) : null}

          {error ? (
            <InlineErrorState
              title="Falha ao carregar comparação calculada"
              message={error}
              onAction={() => void loadComparison()}
            />
          ) : null}

          {!loading && !error && loadedOnce && scopedComparisonItems.length === 0 && scopedRevisoes.length > 0 ? (
            <EmptyState
              classNames={EMPTY}
              title="Sem comparação"
              defaultMessage="Ainda não há baseline/medição comparável."
            />
          ) : null}

          {scopedComparisonItems.length > 0 ? (
            <div className="tm-processo-results-comparison">
              <h3 className="ds-subsection-title">Comparação calculada</h3>
              <p className="ds-hint">
                Totais e breakdowns são <strong>calculados</strong> — não são economia realizada
                observada.
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

          {contextRevisaoId && activeRevisao ? (
            <>
              {revisionLoading ? (
                <LoadingActivityCard
                  title="Carregando capacidade da revisão"
                  description="Medição, investimentos e recursos do mesmo contexto selecionado."
                />
              ) : null}

              {revisionError ? (
                <InlineErrorState
                  title="Falha ao carregar dados da revisão"
                  message={revisionError}
                  onAction={() => void loadRevisionBundle(contextRevisaoId)}
                />
              ) : null}

              {!revisionLoading && !revisionError && revisionBundle ? (
                <>
                  <div className="tm-processo-results-block" data-results-block="medicoes">
                    <div className="tm-processo-results-block__head">
                      <h3 className="ds-subsection-title">Medições</h3>
                      <button
                        type="button"
                        className="ds-link"
                        onClick={() => openRevisionSection("medicao")}
                      >
                        Abrir na revisão
                      </button>
                    </div>
                    {revisionBundle.medicao ? (
                      <RevisionMeasurementSection
                        embeddedInCard
                        readOnly
                        medicao={revisionBundle.medicao}
                        beneficioCalculoCategoria={
                          activeRevisao.beneficio_calculo_categoria ??
                          selectedComparison?.beneficio_calculo_categoria
                        }
                        onChange={() => undefined}
                        onSubmit={(event) => event.preventDefault()}
                      />
                    ) : (
                      <EmptyState
                        classNames={EMPTY}
                        title="Sem medição"
                        defaultMessage="Ainda não há baseline/medição comparável."
                      />
                    )}
                  </div>

                  <div className="tm-processo-results-block" data-results-block="investimentos">
                    <div className="tm-processo-results-block__head">
                      <h3 className="ds-subsection-title">Investimentos</h3>
                      <button
                        type="button"
                        className="ds-link"
                        onClick={() => openRevisionSection("investimentos")}
                      >
                        Abrir na revisão
                      </button>
                    </div>
                    <RevisionInvestmentsSection
                      embeddedInCard
                      readOnly
                      revisaoId={contextRevisaoId}
                      options={options}
                      investimentos={revisionBundle.investimentos}
                      getAccessToken={getAccessToken}
                      onError={setRevisionError}
                      onReload={async () => {
                        await loadRevisionBundle(contextRevisaoId);
                      }}
                    />
                  </div>

                  <div className="tm-processo-results-block" data-results-block="recursos">
                    <div className="tm-processo-results-block__head">
                      <h3 className="ds-subsection-title">Recursos e custos</h3>
                      <button
                        type="button"
                        className="ds-link"
                        onClick={() => openRevisionSection("recursos")}
                      >
                        Abrir na revisão
                      </button>
                    </div>
                    <p className="ds-hint">
                      Vínculos e rateio desta revisão. Histórico de custos unitários do recurso
                      permanece em Configurações → Recursos compartilhados (owner do catálogo).
                    </p>
                    <RevisionSharedResourcesSection
                      embeddedInCard
                      readOnly
                      revisaoId={contextRevisaoId}
                      options={options}
                      recursos={revisionBundle.recursos}
                      vinculos={revisionBundle.vinculos}
                      getAccessToken={getAccessToken}
                      onError={setRevisionError}
                      onReload={async () => {
                        await loadRevisionBundle(contextRevisaoId);
                      }}
                    />
                  </div>

                  <div className="tm-processo-results-block" data-results-block="beneficios">
                    <h3 className="ds-subsection-title">Benefícios calculados</h3>
                    {selectedComparison ? (
                      <dl className="ds-dl-grid">
                        <div>
                          <dt>Categoria de cálculo</dt>
                          <dd>
                            {beneficioCalculoLabel(selectedComparison.beneficio_calculo_categoria)}
                          </dd>
                        </div>
                        <div>
                          <dt>Economia bruta (calc.)</dt>
                          <dd>{formatProcessoNumber(selectedComparison.totais.economia_bruta)}</dd>
                        </div>
                        <div>
                          <dt>Economia líquida/mês (calc.)</dt>
                          <dd>
                            {formatProcessoNumber(selectedComparison.totais.economia_liquida_mes)}
                          </dd>
                        </div>
                        <div>
                          <dt>Horas economizadas/mês (calc.)</dt>
                          <dd>
                            {formatProcessoNumber(selectedComparison.totais.horas_economizadas_mes)}
                          </dd>
                        </div>
                        <div>
                          <dt>Ganho de capacidade (calc.)</dt>
                          <dd>{formatProcessoNumber(selectedComparison.totais.ganho_capacidade)}</dd>
                        </div>
                        <div>
                          <dt>Investimento total/mês (calc.)</dt>
                          <dd>
                            {formatProcessoNumber(
                              selectedComparison.totais.investimento_total_mes,
                            )}
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
                </>
              ) : null}
            </>
          ) : null}

          {scopedRevisoes.length > 1 && !selectedRevisaoId ? (
            <EmptyState
              classNames={EMPTY}
              title="Revisão necessária"
              defaultMessage="Selecione uma revisão para visualizar medição, investimentos e recursos."
            />
          ) : null}
        </div>
      ) : null}

      {contextInstanciaId ? (
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
