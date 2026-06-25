import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchMyQueue } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { MyQueueTable } from "../components/MyQueueTable";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import { FilterBar } from "../components/ui/FilterBar";
import { MultiSelectField } from "../components/ui/MultiSelectField";
import { PAC_BRANCH_OPTIONS } from "../constants/actionPlans";
import type { MyQueueItem, MyQueueSummary } from "../types/myQueue";

type Props = {
  onNavigate: (path: string) => void;
};

export function MyQueuePage({ onNavigate }: Props) {
  const [items, setItems] = useState<MyQueueItem[]>([]);
  const [summary, setSummary] = useState<MyQueueSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branches, setBranches] = useState<string[]>([]);
  const [overdueOnly, setOverdueOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyQueue({
        branch_code: branches.length === 1 ? branches[0] : undefined,
        overdue_only: overdueOnly || undefined,
        page_size: 200,
      });
      setItems(data.items);
      setSummary(data.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar sua fila.");
    } finally {
      setLoading(false);
    }
  }, [branches, overdueOnly]);

  useEffect(() => {
    void load();
  }, [load]);

  const visibleItems = useMemo(() => {
    if (branches.length <= 1) return items;
    return items.filter((item) => branches.includes(item.branch_code ?? ""));
  }, [branches, items]);

  return (
    <>
      <PageHeader
        title="Minha fila"
        subtitle="Ações atribuídas a você em planos abertos."
      />
      <AppNav active="my-queue" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <div className="pac-page-stack">
        {summary ? (
          <div className="pac-dashboard-grid pac-dashboard-grid--queue-summary">
            <article className="pac-metric-card">
              <p className="pac-metric-card__label">Ações abertas</p>
              <p className="pac-metric-card__value">{summary.open_actions}</p>
            </article>
            <article className="pac-metric-card pac-metric-card--danger">
              <p className="pac-metric-card__label">Atrasadas</p>
              <p className="pac-metric-card__value">{summary.overdue_actions}</p>
            </article>
          </div>
        ) : null}

        <FilterBar compact>
        <MultiSelectField
          id="pac-queue-branch"
          label="Filial"
          options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
          selectedValues={branches}
          onChange={setBranches}
          emptyLabel="Todas"
          searchable={false}
        />
        <label className="pac-checkbox pac-filter-checkbox" htmlFor="pac-queue-overdue">
          <input
            id="pac-queue-overdue"
            type="checkbox"
            checked={overdueOnly}
            onChange={(event) => setOverdueOnly(event.target.checked)}
          />
          Somente atrasadas
        </label>
        </FilterBar>

        <section className="pac-card">
          <div className="pac-section-card__header pac-table-header">
            <h2 className="pac-section-title">Suas ações</h2>
            <span className="pac-muted pac-table-header__count">
              {visibleItems.length} ação(ões)
            </span>
          </div>
          <MyQueueTable
            items={visibleItems}
            loading={loading}
            emptyMessage={
              overdueOnly
                ? "Nenhuma ação atrasada atribuída a você."
                : "Nenhuma ação pendente atribuída a você."
            }
            onNavigate={onNavigate}
          />
        </section>
      </div>
    </>
  );
}
