import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";

import { DataTable } from "../../components/DataTable";
import { InlineErrorState } from "../../components/ErrorStateBox";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { cenarioLabel } from "../../content/cenarioLabels";
import {
  fetchProcessoComparativo,
  type ProcessoComparativoItem,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import { buildComparativoColumns } from "../../utils/processoDetailTables";
import { buildProcessoPath } from "../../utils/routeParser";
import { instanciaNavLabel } from "./processWorkspaceNav";

type Props = {
  processoId: string;
  instancias: ProcessoInstancia[];
  revisoes: Revisao[];
  getAccessToken?: () => string | undefined;
  onNavigate: (path: string) => void;
  active: boolean;
};

const EMPTY = emptyStateCardBemClasses("ds");

/**
 * Resultados — composição frontend de comparison + atalhos para medição/investimentos.
 * Não cria aggregate/DTO; preserva natureza CALCULATED via labels de cenário/categoria.
 */
export function ProcessResultsSection({
  processoId,
  instancias,
  revisoes,
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

  const requiresInstanceSelection = instancias.length > 1;
  const resolvedInstanciaId = useMemo(() => {
    if (instancias.length === 1) return instancias[0]!.instancia_id;
    if (requiresInstanceSelection) return selectedInstanciaId;
    return null;
  }, [instancias, requiresInstanceSelection, selectedInstanciaId]);

  const load = useCallback(async () => {
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
    void load();
  }, [active, error, load, loadedOnce]);

  const columns = useMemo(() => buildComparativoColumns(), []);

  const scopedRevisoes = useMemo(() => {
    if (!resolvedInstanciaId) return [];
    const needle = resolvedInstanciaId.toLowerCase();
    return revisoes.filter((row) => String(row.instancia_id ?? "").toLowerCase() === needle);
  }, [resolvedInstanciaId, revisoes]);

  /** Same selected context for baseline + scenario links — never mix instances. */
  const contextInstanciaId = resolvedInstanciaId;

  return (
    <section className="ds-card tm-processo-workspace-panel" aria-labelledby="tm-process-resultados-title">
      <h2 id="tm-process-resultados-title" className="ds-section-title">
        Resultados
      </h2>
      <p className="ds-hint">
        Comparação e benefícios calculados a partir das revisões existentes. Valores de cenário
        (baseline/melhoria) e categoria de cálculo não são resultado realizado observado — use as
        medições na revisão para o detalhe operacional.
      </p>

      {loading && items.length === 0 ? (
        <LoadingActivityCard
          title="Carregando resultados"
          description="Buscando comparação e totais calculados das revisões."
        />
      ) : null}

      {error ? (
        <InlineErrorState
          title="Falha ao carregar resultados"
          message={error}
          onAction={() => void load()}
        />
      ) : null}

      {!loading && !error && loadedOnce && items.length === 0 ? (
        <EmptyState
          classNames={EMPTY}
          title="Sem comparação"
          defaultMessage="Ainda não há baseline/medição comparável."
        />
      ) : null}

      {items.length > 0 ? (
        <div className="tm-processo-results-comparison">
          <h3 className="ds-subsection-title">Comparação (calculado)</h3>
          <p className="ds-hint">
            Totais e breakdowns são <strong>calculados</strong> a partir das medições informadas —
            não confundir com resultado observado em campo.
          </p>
          <DataTable columns={columns} rows={items} rowKey={(row) => row.revisao_id} />
        </div>
      ) : null}

      <div className="tm-processo-results-detail" data-testid="tm-process-results-instance-scope">
        <h3 className="ds-subsection-title">Medições, investimentos e recursos</h3>
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
          >
            {requiresInstanceSelection ? (
              <p className="ds-hint">
                Melhoria selecionada:{" "}
                {instanciaNavLabel(
                  instancias.find((row) => row.instancia_id === contextInstanciaId)!,
                )}
                {" · "}
                <button
                  type="button"
                  className="ds-link"
                  onClick={() => setSelectedInstanciaId(null)}
                >
                  Trocar
                </button>
              </p>
            ) : null}
            {scopedRevisoes.length === 0 ? (
              <EmptyState
                classNames={EMPTY}
                title="Sem revisões"
                defaultMessage="Ainda não há baseline/medição comparável."
              />
            ) : (
              <ul className="tm-processo-results-revisao-links">
                {scopedRevisoes.map((revisao) => (
                  <li key={revisao.revisao_id}>
                    <button
                      type="button"
                      className="ds-link"
                      onClick={() =>
                        onNavigate(
                          `${buildProcessoPath(processoId, revisao.revisao_id, contextInstanciaId)}#medicao`,
                        )
                      }
                    >
                      {revisao.versao_revisao ?? revisao.revisao_id} · {cenarioLabel(revisao.cenario_tipo)}{" "}
                      — medição / investimentos / recursos
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
      </div>

      <div className="tm-processo-workspace-overview__actions">
        <button
          type="button"
          className={DS_GHOST_BTN}
          disabled={loading}
          onClick={() => void load()}
        >
          {loading ? "Atualizando…" : "Atualizar comparação"}
        </button>
      </div>
    </section>
  );
}
