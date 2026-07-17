import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";

import {
  getPlaylistHistorySnapshot,
  type PlaylistHistoryEntry,
  type PlaylistHistorySnapshot,
} from "../../api/tvDashboardApi";
import { useConfirm } from "../../context/ConfirmDialogProvider";
import { useDeckEditorHistoryContext } from "../../context/deckEditorHistoryContext";
import { Modal } from "../ui/Modal";

type Props = {
  open: boolean;
  playlistId: string;
  onClose: () => void;
};

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function authorLabel(item: PlaylistHistoryEntry): string {
  return item.authorName?.trim() || item.authorId?.trim() || "Sistema";
}

function previewLabel(item: PlaylistHistoryEntry): string {
  const preview = item.preview;
  if (!preview) return "Prévia disponível ao selecionar a revisão.";
  const slides =
    preview.slideTitles?.filter(Boolean).slice(0, 3).join(", ") ||
    `${preview.slideCount ?? 0} tela(s)`;
  return [preview.playlistName, slides].filter(Boolean).join(" · ");
}

function reasonLabel(reason?: string | null): string {
  if (!reason?.trim()) return "Alteração da programação";
  return reason.replaceAll("_", " ");
}

export function DeckRevisionHistoryPanel({ open, playlistId, onClose }: Props) {
  const history = useDeckEditorHistoryContext();
  const loadHistory = history?.loadHistory;
  const restoreRevision = history?.restoreRevision;
  const confirm = useConfirm();
  const [detail, setDetail] = useState<PlaylistHistorySnapshot | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !loadHistory) return;
    void loadHistory(1);
  }, [loadHistory, open]);

  if (!history) return null;
  const page = history.historyPage;

  async function selectRevision(item: PlaylistHistoryEntry) {
    setDetailLoading(true);
    setDetailError(null);
    try {
      setDetail(await getPlaylistHistorySnapshot(playlistId, item.snapshotId));
    } catch (caught) {
      setDetailError(caught instanceof Error ? caught.message : "Erro ao carregar prévia.");
    } finally {
      setDetailLoading(false);
    }
  }

  async function restore(item: PlaylistHistoryEntry) {
    const accepted = await confirm({
      title: "Restaurar revisão",
      message: `Restaurar a revisão ${item.revision}? A versão atual continuará disponível no histórico.`,
      confirmLabel: "Restaurar",
      variant: "danger",
    });
    if (!accepted) return;
    await restoreRevision?.(item.snapshotId, item.revision);
  }

  return (
    <Modal open={open} title="Histórico de revisões" onClose={onClose} className="td-modal--history">
      {history.error ? (
        <div className="td-history__error" role="alert">
          {history.error}
        </div>
      ) : null}
      {history.loading && !page ? <div className="td-history__state">Carregando revisões…</div> : null}
      {!history.loading && page?.items.length === 0 ? (
        <div className="td-history__state">Nenhuma revisão registrada.</div>
      ) : null}
      <div className="td-history__layout">
        <ol className="td-history__list" aria-label="Revisões da programação">
          {page?.items.map((item) => (
            <li key={item.snapshotId} className="td-history__item">
              <button
                type="button"
                className="td-history__summary"
                onClick={() => void selectRevision(item)}
                aria-label={`Ver prévia da revisão ${item.revision}`}
              >
                <strong>Revisão {item.revision}</strong>
                <span>{formatDate(item.createdAt)} · {authorLabel(item)}</span>
                <span>{reasonLabel(item.reason)}</span>
                <small>{previewLabel(item)}</small>
              </button>
              <button
                type="button"
                className="td-btn td-btn--sm td-history__restore"
                disabled={history.restoring}
                onClick={() => void restore(item)}
              >
                <RotateCcw size={14} aria-hidden="true" />
                Restaurar
              </button>
            </li>
          ))}
        </ol>
        <aside className="td-history__preview" aria-label="Prévia da revisão">
          {detailLoading ? <p>Carregando prévia…</p> : null}
          {detailError ? <p role="alert">{detailError}</p> : null}
          {!detailLoading && !detailError && detail ? (
            <>
              <strong>{detail.snapshot.playlist.name ?? "Programação"}</strong>
              <span>Revisão {detail.revision} · {formatDate(detail.createdAt)}</span>
              <span>{detail.snapshot.slides.length} tela(s)</span>
              <ul>
                {detail.snapshot.slides.slice(0, 6).map((slide) => (
                  <li key={slide.id}>{slide.title}</li>
                ))}
              </ul>
            </>
          ) : null}
          {!detail && !detailLoading && !detailError ? <p>Selecione uma revisão para ver a prévia.</p> : null}
        </aside>
      </div>
      {page && (page.page > 1 || page.hasNext) ? (
        <div className="td-history__pagination" aria-label="Paginação do histórico">
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={page.page <= 1 || history.loading}
            onClick={() => void history.loadHistory(page.page - 1)}
          >
            <ChevronLeft size={14} aria-hidden="true" /> Anterior
          </button>
          <span>Página {page.page}</span>
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={!page.hasNext || history.loading}
            onClick={() => void history.loadHistory(page.page + 1)}
          >
            Próxima <ChevronRight size={14} aria-hidden="true" />
          </button>
        </div>
      ) : null}
    </Modal>
  );
}
