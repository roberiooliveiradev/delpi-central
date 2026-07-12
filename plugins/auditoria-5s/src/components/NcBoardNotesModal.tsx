import { useState } from "react";
import { MessageSquarePlus } from "lucide-react";

import { addNcAction } from "../api/audit5sApi";
import type { NcBoardItem } from "../types/ncManagement";
import { shiftLabel } from "../constants/audit5s";
import { formatDisplayDate } from "../utils/dates";
import { formatPersonName } from "../utils/formatPersonName";
import { useNcBoardItemDetail } from "../hooks/useNcBoardItemDetail";
import { NcBoardModalShell } from "./NcBoardModalShell";

type Props = {
  item: NcBoardItem | null;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
};

function formatActionTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NcBoardNotesModal({ item, open, onClose, onSaved }: Props) {
  const { loading, error, actions, reload } = useNcBoardItemDetail(item, open);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const canAddNote = Boolean(item?.is_registered);
  const trimmedNote = note.trim();

  const handleSubmit = async () => {
    if (!item?.is_registered || trimmedNote.length < 3) return;

    setSaving(true);
    setSubmitError(null);
    try {
      await addNcAction(item.id, trimmedNote);
      setNote("");
      await reload();
      onSaved();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Erro ao registrar observação.");
    } finally {
      setSaving(false);
    }
  };

  if (!item) return null;

  const meta = `${item.audit_code} · ${item.area_name} · ${shiftLabel(item.shift)} · ${formatDisplayDate(item.audit_date)}`;

  return (
    <NcBoardModalShell
      open={open}
      title="Notas da NC"
      titleId="a5s-nc-board-notes-title"
      meta={meta}
      icon={<MessageSquarePlus size={20} aria-hidden />}
      onClose={onClose}
      dialogClassName="a5s-nc-board-treat-dialog--notes"
      footer={
        <>
          <button type="button" className="a5s-btn a5s-btn--ghost" onClick={onClose}>
            Fechar
          </button>
          <button
            type="button"
            className="a5s-btn"
            disabled={!canAddNote || saving || trimmedNote.length < 3}
            onClick={() => {
              void handleSubmit();
            }}
          >
            {saving ? "Salvando…" : "Registrar nota"}
          </button>
        </>
      }
    >
      <div className="a5s-nc-board-treat-dialog__body">
        {!canAddNote ? (
          <div className="a5s-alert a5s-alert--warning">
            Registre o plano de ação em <strong>Atualizar</strong> antes de incluir observações no
            histórico.
          </div>
        ) : null}

        {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}
        {submitError ? <div className="a5s-alert a5s-alert--error">{submitError}</div> : null}

        <label className="a5s-nc-notes__composer">
          <span className="a5s-nc-notes__composer-label">Nova observação</span>
          <textarea
            value={note}
            rows={4}
            disabled={!canAddNote || saving}
            placeholder="Descreva o andamento, decisão ou contexto que deve ficar no histórico da ficha…"
            onChange={(event) => setNote(event.target.value)}
          />
        </label>

        <section className="a5s-nc-notes__history">
          <h3>Histórico</h3>
          {loading ? (
            <p className="a5s-nc-board-treat-dialog__loading">Carregando histórico…</p>
          ) : actions.length === 0 ? (
            <p className="a5s-nc-ficha__empty">Nenhuma observação registrada ainda.</p>
          ) : (
            <ol className="a5s-nc-ficha__history">
              {actions.map((action) => (
                <li key={action.id} className="a5s-nc-ficha__history-item">
                  <div className="a5s-nc-ficha__history-head">
                    <strong>
                      {formatPersonName(action.actor_display_name) || action.actor_display_name}
                    </strong>
                    <time dateTime={action.created_at}>{formatActionTimestamp(action.created_at)}</time>
                  </div>
                  <p>{action.description}</p>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </NcBoardModalShell>
  );
}
