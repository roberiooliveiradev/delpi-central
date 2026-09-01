import { Maximize2 } from "lucide-react";
import { useCallback, useState } from "react";

import { copy } from "../content/copy";
import type { CostCenterRankingItem } from "../types";
import { formatCurrency, formatInteger, formatPercent } from "../utils/formatNumbers";
import { FinBlockState } from "./FinBlockState";
import { FinWideDialog } from "./FinDialog";
import { DataTable, FIN_TABLE_CLASSES, FIN_TABLE_LABELS } from "./dataTableUi";

export const EXPANDED_RANKING_LIMIT = 50;

type RankingVariant = "centers" | "suppliers";

type CostCenterRankingPanelProps = {
  title: string;
  items: CostCenterRankingItem[];
  variant: RankingVariant;
  loading?: boolean;
  loadError?: string | null;
  /** Recorte exibido no cabeçalho — o mês sobrescreve o texto do período. */
  previewHint?: string;
  expandAriaLabel: string;
  modalTitle: string;
  modalSubtitle: string;
  onLoadExpanded: () => Promise<CostCenterRankingItem[]>;
};

function variantKey(item: CostCenterRankingItem): string {
  return item.store ? `${item.code}-${item.store}` : item.code;
}

function RankingBarList({ items }: { items: CostCenterRankingItem[] }) {
  return (
    <ul className="fin-bar-list">
      {items.map((item) => (
        <li key={variantKey(item)}>
          <div className="fin-bar-list__head">
            <strong>{item.label || item.code}</strong>
            <span>{formatCurrency(item.totalAmount)}</span>
          </div>
          <div className="fin-bar-list__track">
            <span
              className="fin-bar-list__fill"
              style={{ width: `${Math.min(Math.max(item.percentage, 0), 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function CostCenterRankingPanel({
  title,
  items,
  variant,
  loading = false,
  loadError = null,
  previewHint = copy.costCenters.rankingPreviewHint,
  expandAriaLabel,
  modalTitle,
  modalSubtitle,
  onLoadExpanded,
}: CostCenterRankingPanelProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<CostCenterRankingItem[]>([]);
  const [expandedLoading, setExpandedLoading] = useState(false);
  const [expandedError, setExpandedError] = useState<string | null>(null);

  const handleExpand = useCallback(async () => {
    setModalOpen(true);
    setExpandedLoading(true);
    setExpandedError(null);

    try {
      const nextItems = await onLoadExpanded();
      setExpandedItems(nextItems);
    } catch (error) {
      setExpandedItems([]);
      setExpandedError(
        error instanceof Error ? error.message : copy.costCenters.rankingExpandedLoadError,
      );
    } finally {
      setExpandedLoading(false);
    }
  }, [onLoadExpanded]);

  const handleClose = useCallback(() => {
    setModalOpen(false);
  }, []);

  const canExpand = !loading && items.length > 0;

  return (
    <>
      <article className="fin-board-list">
        <header className="fin-board-list__head">
          <h2 className="fin-board-list__title">{title}</h2>
          {canExpand ? (
            <button
              type="button"
              className="fin-ranking-expand-btn"
              aria-label={expandAriaLabel}
              title={expandAriaLabel}
              onClick={() => void handleExpand()}
            >
              <Maximize2 size={15} aria-hidden="true" />
              <span>{copy.costCenters.rankingExpand}</span>
            </button>
          ) : null}
          <p className="fin-board-list__hint">{previewHint}</p>
        </header>
        {loading ? (
          <p className="fin-block-state">{copy.costCenters.loading}</p>
        ) : loadError ? (
          <div className="fin-ranking-modal__error">
            <p className="fin-block-state fin-block-state--error" role="alert">
              {loadError}
            </p>
          </div>
        ) : items.length === 0 ? (
          <FinBlockState empty emptyMessage={copy.costCenters.rankingEmpty} block={undefined} />
        ) : (
          <RankingBarList items={items} />
        )}
      </article>

      <FinWideDialog
        open={modalOpen}
        title={modalTitle}
        onClose={handleClose}
        closeAriaLabel={copy.costCenters.detail.close}
      >
        <p className="fin-ranking-modal__subtitle">{modalSubtitle}</p>
        {expandedLoading ? (
          <p className="fin-block-state">{copy.costCenters.loading}</p>
        ) : expandedError ? (
          <div className="fin-ranking-modal__error">
            <p className="fin-block-state fin-block-state--error" role="alert">
              {expandedError}
            </p>
            <button type="button" className="fin-link-btn" onClick={() => void handleExpand()}>
              {copy.retry}
            </button>
          </div>
        ) : expandedItems.length === 0 ? (
          <FinBlockState empty emptyMessage={copy.costCenters.rankingEmpty} block={undefined} />
        ) : (
          <div className="fin-ranking-modal">
            <div className="fin-ranking-modal__bars">
              <RankingBarList items={expandedItems} />
            </div>
            <div className="fin-ranking-modal__detail">
              <h3 className="fin-ranking-modal__detail-title">{copy.costCenters.rankingDetailTitle}</h3>
              <DataTable
                classNames={FIN_TABLE_CLASSES}
                labels={FIN_TABLE_LABELS}
                columns={[
                  {
                    key: "rank",
                    header: copy.costCenters.rankingColumns.rank,
                    render: (row) => {
                      const index = expandedItems.findIndex(
                        (item) => variantKey(item) === variantKey(row),
                      );
                      return String(index + 1);
                    },
                  },
                  {
                    key: "label",
                    header:
                      variant === "centers"
                        ? copy.costCenters.columns.costCenter
                        : copy.costCenters.columns.supplier,
                    render: (row) => row.label || "—",
                  },
                  {
                    key: "code",
                    header:
                      variant === "centers"
                        ? copy.costCenters.rankingColumns.code
                        : copy.costCenters.rankingColumns.store,
                    render: (row) =>
                      variant === "suppliers" && row.store
                        ? `${row.code} / ${row.store}`
                        : row.code || "—",
                  },
                  {
                    key: "totalAmount",
                    header: copy.costCenters.rankingColumns.totalAmount,
                    className: "fin-table__col--numeric",
                    align: "right",
                    render: (row) => formatCurrency(row.totalAmount),
                  },
                  {
                    key: "entryCount",
                    header: copy.costCenters.rankingColumns.entryCount,
                    className: "fin-table__col--numeric",
                    align: "right",
                    render: (row) => formatInteger(row.entryCount),
                  },
                  {
                    key: "percentage",
                    header: copy.costCenters.rankingColumns.percentage,
                    className: "fin-table__col--numeric",
                    align: "right",
                    render: (row) => formatPercent(row.percentage),
                  },
                ]}
                rows={expandedItems}
                rowKey={(row) => variantKey(row)}
              />
            </div>
          </div>
        )}
      </FinWideDialog>
    </>
  );
}
