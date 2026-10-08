import { useState } from "react";
import { CircleAlert, Hourglass, MapPin, MessagesSquare } from "lucide-react";

import { HostContainedDialog, HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { MachineLoadOperation, PcpOperatorFeedback } from "../types";
import {
  feedbackReasonLabel,
  feedbackStatusLabel,
  feedbackTypeLabel,
} from "../utils/operatorFeedback";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";

const RESOLUTION_NOTE_MAX = 500;

type Props = {
  open: boolean;
  items: PcpOperatorFeedback[];
  summary: { total: number; open: number; acknowledged: number };
  loading: boolean;
  error: string | null;
  notice: string | null;
  actingId: string | null;
  /** Localiza a operacao na fila atual (qualquer CT); null = fora da fila. */
  findInQueue: (feedback: PcpOperatorFeedback) => MachineLoadOperation | null;
  onAcknowledge: (feedbackId: string) => Promise<boolean>;
  onResolve: (feedbackId: string, note: string | null) => Promise<boolean>;
  onGoToQueue: (operation: MachineLoadOperation) => void;
  onClose: () => void;
};

function FeedbackItem({
  item,
  acting,
  queueTarget,
  onAcknowledge,
  onAskResolve,
  onGoToQueue,
}: {
  item: PcpOperatorFeedback;
  acting: boolean;
  queueTarget: MachineLoadOperation | null;
  onAcknowledge: (id: string) => void;
  onAskResolve: (item: PcpOperatorFeedback) => void;
  onGoToQueue: (operation: MachineLoadOperation) => void;
}) {
  const labels = copy.machineLoad.feedback;
  const isOpen = item.status === "open";
  return (
    <li
      className={
        isOpen
          ? "ppc-feedback__item ppc-feedback__item--open"
          : "ppc-feedback__item ppc-feedback__item--acknowledged"
      }
    >
      <div className="ppc-feedback__body">
        <p className="ppc-feedback__title">
          <span
            className={
              isOpen
                ? "ppc-feedback__status ppc-feedback__status--open"
                : "ppc-feedback__status ppc-feedback__status--acknowledged"
            }
          >
            {isOpen ? (
              <CircleAlert size={14} strokeWidth={2} aria-hidden />
            ) : (
              <Hourglass size={14} strokeWidth={2} aria-hidden />
            )}
            {feedbackStatusLabel(item.status)}
          </span>
          <strong>{item.productionOrder}</strong>
          <span>{"Op. " + item.operationCode}</span>
        </p>
        <p className="ppc-feedback__meta">
          <span>{feedbackReasonLabel(item.reasonCode)}</span>
          <span className="ppc-feedback__muted">
            {feedbackTypeLabel(item.feedbackType)}
          </span>
        </p>
        <p className="ppc-feedback__meta">
          {item.paProductCode || item.productCode ? (
            <span>
              {item.paProductCode ?? item.productCode}
              {item.productDescription ? " — " + item.productDescription : null}
            </span>
          ) : null}
          {item.dueDate ? <span>{formatIsoDate(item.dueDate)}</span> : null}
        </p>
        <p className="ppc-feedback__meta">
          <span>{labels.reportedCenter(item.reportedWorkCenter)}</span>
          <span>{labels.reportedBy(item.operatorName, item.operatorCode)}</span>
          <span>{labels.reportedAt(formatRefreshedAt(item.createdAt))}</span>
        </p>
        {item.note ? (
          <p className="ppc-feedback__note">
            <strong>{labels.noteLabel}: </strong>
            {item.note}
          </p>
        ) : null}
        {item.status === "acknowledged" ? (
          <p className="ppc-feedback__meta">
            <span>{labels.acknowledgedBy(item.acknowledgedBy)}</span>
          </p>
        ) : null}
      </div>
      <div className="ppc-feedback__actions">
        {queueTarget ? (
          <button
            type="button"
            className="ppc-feedback__go"
            onClick={() => onGoToQueue(queueTarget)}
          >
            <MapPin size={13} strokeWidth={1.9} aria-hidden />
            {labels.goToQueue}
          </button>
        ) : (
          <span className="ppc-feedback__out">{labels.outOfQueue}</span>
        )}
        {isOpen ? (
          <button
            type="button"
            className="ppc-feedback__ack"
            disabled={acting}
            aria-busy={acting}
            onClick={() => onAcknowledge(item.id)}
          >
            {acting ? labels.acknowledgeBusy : labels.acknowledge}
          </button>
        ) : null}
        <button
          type="button"
          className={
            isOpen ? "ppc-feedback__resolve" : "ppc-feedback__ack"
          }
          disabled={acting}
          onClick={() => onAskResolve(item)}
        >
          {isOpen ? labels.resolve : copy.machineLoad.feedback.resolveConfirm}
        </button>
      </div>
    </li>
  );
}

function ResolveFeedbackDialog({
  item,
  busy,
  onCancel,
  onConfirm,
}: {
  item: PcpOperatorFeedback;
  busy: boolean;
  onCancel: () => void;
  onConfirm: (note: string | null) => void;
}) {
  const labels = copy.machineLoad.feedback;
  const [note, setNote] = useState("");
  return (
    <HostContainedDialog
      open
      title={labels.resolveModalTitle}
      onClose={busy ? () => undefined : onCancel}
    >
      <div className="ppc-feedback-resolve">
        <p className="ppc-feedback-resolve__context">
          <strong>{item.productionOrder}</strong>
          <span>{"Op. " + item.operationCode}</span>
          <span>{feedbackReasonLabel(item.reasonCode)}</span>
        </p>
        {item.note ? (
          <p className="ppc-feedback__note">
            <strong>{labels.noteLabel}: </strong>
            {item.note}
          </p>
        ) : null}
        <label className="ppc-feedback-resolve__field">
          <span>{labels.resolveNoteLabel}</span>
          <textarea
            value={note}
            maxLength={RESOLUTION_NOTE_MAX}
            rows={3}
            disabled={busy}
            placeholder={labels.resolveNotePlaceholder}
            onChange={(event) => setNote(event.target.value)}
          />
          <em>{labels.resolveNoteHint}</em>
        </label>
        <div className="ppc-feedback-resolve__actions">
          <button
            type="button"
            className="ppc-feedback__resolve"
            disabled={busy}
            onClick={onCancel}
          >
            {labels.cancel}
          </button>
          <button
            type="button"
            className="ppc-feedback__ack"
            disabled={busy}
            aria-busy={busy}
            onClick={() => onConfirm(note.trim() || null)}
          >
            {busy ? labels.resolveBusy : labels.resolveConfirm}
          </button>
        </div>
      </div>
    </HostContainedDialog>
  );
}

/** Inbox de impedimentos do PCP — dominio separado do status MES da fila. */
export function OperatorFeedbackInbox({
  open,
  items,
  summary,
  loading,
  error,
  notice,
  actingId,
  findInQueue,
  onAcknowledge,
  onResolve,
  onGoToQueue,
  onClose,
}: Props) {
  const labels = copy.machineLoad.feedback;
  const [resolving, setResolving] = useState<PcpOperatorFeedback | null>(null);

  return (
    <HostContainedWideDialog open={open} title={labels.modalTitle} onClose={onClose}>
      <div className="ppc-feedback">
        <p className="ppc-feedback__lead">{labels.lead}</p>
        {summary.total > 0 ? (
          <p className="ppc-feedback__summary" role="status">
            <MessagesSquare size={14} strokeWidth={1.9} aria-hidden />
            {labels.summaryLine(summary.total, summary.open, summary.acknowledged)}
          </p>
        ) : null}
        {notice ? (
          <p className="ppc-feedback__notice" role="status">
            {notice}
          </p>
        ) : null}
        {error ? (
          <p className="ppc-feedback__error" role="alert">
            {error}
          </p>
        ) : null}
        {loading && items.length === 0 ? (
          <p className="ppc-feedback__empty">{labels.loading}</p>
        ) : items.length === 0 ? (
          <p className="ppc-feedback__empty">{labels.empty}</p>
        ) : (
          <ul className="ppc-feedback__list">
            {items.map((item) => (
              <FeedbackItem
                key={item.id}
                item={item}
                acting={actingId === item.id}
                queueTarget={findInQueue(item)}
                onAcknowledge={(id) => void onAcknowledge(id)}
                onAskResolve={setResolving}
                onGoToQueue={onGoToQueue}
              />
            ))}
          </ul>
        )}
      </div>
      {resolving ? (
        <ResolveFeedbackDialog
          item={resolving}
          busy={actingId === resolving.id}
          onCancel={() => setResolving(null)}
          onConfirm={(note) => {
            void onResolve(resolving.id, note).then((done) => {
              if (done) setResolving(null);
            });
          }}
        />
      ) : null}
    </HostContainedWideDialog>
  );
}
