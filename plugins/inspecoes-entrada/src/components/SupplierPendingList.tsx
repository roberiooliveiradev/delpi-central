import { IE_STATE_BOX_COMPACT } from "../ui/stateChrome";
import type { InspecoesEntradaPendenteFornecedor } from "../types/inspecoesEntradaDashboard";
import { formatText } from "../utils/format";

type SupplierPendingListProps = {
  items: InspecoesEntradaPendenteFornecedor[];
  loading: boolean;
  error: string | null;
  totalPending?: number;
};

export function SupplierPendingList({
  items,
  loading,
  error,
  totalPending,
}: SupplierPendingListProps) {
  if (loading) {
    return <div className={IE_STATE_BOX_COMPACT}>Carregando gargalos…</div>;
  }

  if (error) {
    return (
      <div className="ie-alert ie-alert--error" role="alert">
        <p>{error}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return <div className={IE_STATE_BOX_COMPACT}>Nenhum fornecedor com pendência encontrado.</div>;
  }

  const maxCount = Math.max(...items.map((item) => item.pending_count), 1);

  return (
    <ul className="ie-bar-list ie-bar-list--stacked">
      {items.map((item, index) => {
        const width = Math.max((item.pending_count / maxCount) * 100, 6);
        return (
          <li key={`${item.branch}-${item.supplier_name}`} className="ie-bar-list__item">
            <div className="ie-bar-list__row">
              <span className="ie-bar-list__rank">{index + 1}</span>
              <div className="ie-bar-list__content">
                <div className="ie-bar-list__header">
                  <span className="ie-bar-list__label" title={item.supplier_name}>
                    {formatText(item.supplier_name)}
                  </span>
                  <span className="ie-bar-list__value">{item.pending_count.toLocaleString("pt-BR")}</span>
                </div>
                <div className="ie-bar-list__track" aria-hidden="true">
                  <span className="ie-bar-list__fill" style={{ width: `${width}%` }} />
                </div>
              </div>
            </div>
          </li>
        );
      })}
      {totalPending !== undefined ? (
        <li className="ie-bar-list__total" aria-hidden="true">
          Total: {totalPending.toLocaleString("pt-BR")} pendência(s)
        </li>
      ) : null}
    </ul>
  );
}
