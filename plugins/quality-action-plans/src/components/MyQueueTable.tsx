import { TableHeaderCell } from "./ui/TableHeaderCell";
import { Eye, Paperclip } from "lucide-react";
import { useState } from "react";
import { NativeSelectControl } from "@delpi/plugin-ui/index";

import {
  ACTION_STATUS_OPTIONS,
  actionTypeLabel,
  branchLabel,
  detailPath,
} from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useConfirmDialog } from "../hooks/useConfirmDialog";
import type { MyQueueItem } from "../types/myQueue";
import { formatDate } from "../utils/format";
import {
  queueItemEvidenceLabel,
  queueItemMissingRequiredEvidence,
} from "../utils/myQueueEvidence";
import { MyQueueEvidenceModal } from "./MyQueueEvidenceModal";
import { PAC_TABLE } from "./ui/tableChrome";
import { pacGhostBtn } from "./ui/ghostChrome";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  items: MyQueueItem[];
  loading?: boolean;
  emptyMessage?: string;
  savingActionId?: string | null;
  onNavigate: (path: string) => void;
  onStatusChange: (item: MyQueueItem, status: string) => void | Promise<void>;
  onEvidenceUploaded?: () => void | Promise<void>;
};

function actionStatusLabel(status: string): string {
  return ACTION_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
}

function QueueActionStatusSelect({
  item,
  disabled,
  onStatusChange,
  onRequestStatusChange,
}: {
  item: MyQueueItem;
  disabled: boolean;
  onStatusChange: (item: MyQueueItem, status: string) => void | Promise<void>;
  onRequestStatusChange: (item: MyQueueItem, status: string) => Promise<boolean>;
}) {
  const [resetKey, setResetKey] = useState(0);
  const currentStatus = ACTION_STATUS_OPTIONS.some((option) => option.value === item.action_status)
    ? item.action_status
    : "pending";
  const missingEvidence = queueItemMissingRequiredEvidence(item);

  return (
    <span
      title={
        missingEvidence
          ? "Anexe evidência antes de concluir esta ação."
          : PAC_HELP_TOOLTIPS.tables.actionStatus
      }
    >
      <NativeSelectControl
        key={`${item.action_id}-${currentStatus}-${resetKey}`}
        className="pac-table-select pac-table-select--status"
        value={currentStatus}
        aria-label={`Status da ação ${item.plan_code ?? item.action_id}`}
        options={ACTION_STATUS_OPTIONS.map((option) => ({
          value: option.value,
          label: option.label,
        }))}
        disabled={disabled}
        onChange={(nextStatus) => {
          if (nextStatus === currentStatus) {
            return;
          }
          if (nextStatus === "completed" && missingEvidence) {
            setResetKey((value) => value + 1);
            return;
          }
          void (async () => {
            const confirmed = await onRequestStatusChange(item, nextStatus);
            if (!confirmed) {
              setResetKey((value) => value + 1);
              return;
            }
            await onStatusChange(item, nextStatus);
          })();
        }}
      />
    </span>
  );
}

export function MyQueueTable({
  items,
  loading,
  emptyMessage,
  savingActionId,
  onNavigate,
  onStatusChange,
  onEvidenceUploaded,
}: Props) {
  const { confirm, confirmDialog } = useConfirmDialog();
  const [evidenceItem, setEvidenceItem] = useState<MyQueueItem | null>(null);

  async function requestStatusChange(item: MyQueueItem, nextStatus: string) {
    if (nextStatus === "completed" && queueItemMissingRequiredEvidence(item)) {
      await confirm({
        title: "Evidência obrigatória",
        message:
          "Esta ação exige evidência vinculada. Anexe um arquivo antes de marcar como concluída.",
        confirmLabel: "Entendi",
      });
      return false;
    }
    return confirm({
      title: "Alterar status",
      message: `Alterar o status da ação para "${actionStatusLabel(nextStatus)}"?`,
      confirmLabel: "Alterar",
    });
  }

  if (loading) {
    return <p className="pac-muted">Carregando sua fila…</p>;
  }

  if (!items.length) {
    return <p className="pac-muted">{emptyMessage ?? "Nenhuma ação pendente para você."}</p>;
  }

  return (
    <>
      {confirmDialog}
      <MyQueueEvidenceModal
        item={evidenceItem}
        open={evidenceItem != null}
        onClose={() => setEvidenceItem(null)}
        onUploaded={async () => {
          if (onEvidenceUploaded) {
            await onEvidenceUploaded();
          }
        }}
      />
      <div className={PAC_TABLE.wrap}>
      <table className={PAC_TABLE.table}>
        <thead>
          <tr>
            <TableHeaderCell label="Plano" hint={T.plan} />
            <TableHeaderCell label="Ação" hint={T.action} />
            <TableHeaderCell label="Tipo" hint={T.actionType} />
            <TableHeaderCell label="Prazo" hint={T.dueDate} />
            <TableHeaderCell label="Evidência" hint={T.evidenceRequired} />
            <TableHeaderCell label="Status" hint={T.actionStatus} />
            <TableHeaderCell label="Filial" hint={T.branch} />
            <TableHeaderCell label="Cliente" hint={T.customer} />
            <TableHeaderCell
              label="Ações"
              hint={T.rowActions}
              className="pac-table__actions-col pac-table__actions-col--icons"
            />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.action_id}
              className={item.is_overdue ? "pac-table__row--overdue" : undefined}
            >
              <td>
                <strong>{item.plan_code ?? "—"}</strong>
                <p className="pac-muted pac-table__subline">{item.plan_title}</p>
              </td>
              <td>{item.description}</td>
              <td>{actionTypeLabel(item.action_type)}</td>
              <td>
                {item.is_overdue ? (
                  <span className="pac-badge pac-badge--warning pac-table__overdue-badge">Atrasada</span>
                ) : item.completed_late ? (
                  <span className="pac-badge pac-badge--warning pac-table__overdue-badge">
                    Concluída com atraso
                  </span>
                ) : item.is_due_soon ? (
                  <span className="pac-badge pac-badge--sla pac-badge--sla-due-soon pac-table__overdue-badge">
                    Vence em {item.days_until_due ?? 0}d
                  </span>
                ) : null}
                <span>{formatDate(item.due_date)}</span>
                {item.action_status === "completed" && item.completed_at ? (
                  <p className="pac-muted pac-table__subline">
                    Concluída em {formatDate(item.completed_at)}
                  </p>
                ) : null}
              </td>
              <td className="pac-table-cell--evidence">
                <span
                  className={`pac-evidence-chip__label pac-evidence-chip__label--static${
                    item.evidence_required ? " pac-evidence-chip__label--required" : ""
                  }${
                    item.evidence_required && queueItemMissingRequiredEvidence(item)
                      ? " pac-evidence-chip__label--missing"
                      : ""
                  }`}
                >
                  {queueItemEvidenceLabel(item)}
                </span>
              </td>
              <td>
                <QueueActionStatusSelect
                  item={item}
                  disabled={savingActionId === item.action_id}
                  onStatusChange={onStatusChange}
                  onRequestStatusChange={requestStatusChange}
                />
              </td>
              <td>{branchLabel(item.branch_code)}</td>
              <td>{item.customer_name ?? "—"}</td>
              <td className="pac-table__actions-cell">
                <div className="pac-table-actions">
                {item.action_status !== "completed" && item.action_status !== "cancelled" ? (
                  <button
                    type="button"
                    className={pacGhostBtn("icon")}
                    title={
                      item.evidence_required
                        ? "Anexar evidência obrigatória"
                        : "Anexar evidência"
                    }
                    disabled={savingActionId === item.action_id}
                    onClick={() => setEvidenceItem(item)}
                  >
                    <Paperclip size={16} />
                  </button>
                ) : null}
                <button
                  type="button"
                  className="pac-icon-btn"
                  title="Abrir plano"
                  onClick={() => onNavigate(detailPath(item.plan_id))}
                >
                  <Eye size={16} />
                </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </>
  );
}
