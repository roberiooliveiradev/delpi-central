import { Eye } from "lucide-react";

import type { NcBoardItem } from "../types/ncManagement";
import { shiftLabel } from "../constants/audit5s";
import { formatDisplayDate } from "../utils/dates";
import { useNcBoardItemDetail } from "../hooks/useNcBoardItemDetail";
import { NcBoardFichaView } from "./NcBoardFichaView";
import { NcBoardModalShell } from "./NcBoardModalShell";

type Props = {
  item: NcBoardItem | null;
  open: boolean;
  onClose: () => void;
};

export function NcBoardViewModal({ item, open, onClose }: Props) {
  const { loading, error, treatmentItem, attachmentsByNcId, actions } = useNcBoardItemDetail(
    item,
    open,
  );

  if (!item) return null;

  const meta = `${item.audit_code} · ${item.area_name} · ${shiftLabel(item.shift)} · ${formatDisplayDate(item.audit_date)}`;

  return (
    <NcBoardModalShell
      open={open}
      title="Ficha da não conformidade"
      titleId="a5s-nc-board-view-title"
      meta={meta}
      icon={<Eye size={20} aria-hidden />}
      onClose={onClose}
      dialogClassName="a5s-nc-board-treat-dialog--view"
      footer={
        <button type="button" className="a5s-btn a5s-btn--ghost" onClick={onClose}>
          Fechar
        </button>
      }
    >
      <div className="a5s-nc-board-treat-dialog__body">
        {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}
        {loading ? (
          <p className="a5s-nc-board-treat-dialog__loading">Carregando ficha…</p>
        ) : (
          <NcBoardFichaView
            item={item}
            treatmentItem={treatmentItem}
            attachmentsByNcId={attachmentsByNcId}
            actions={actions}
          />
        )}
      </div>
    </NcBoardModalShell>
  );
}
