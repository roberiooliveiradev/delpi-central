import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, History, RotateCcw } from "lucide-react";
import { createTimeline, type TimelineItemModel } from "@delpi/plugin-ui/index";

import {
  getPlaylistHistorySnapshot,
  type PlaylistHistoryEntry,
  type PlaylistHistorySnapshot,
} from "../../api/tvDashboardApi";
import { useConfirm } from "../../context/ConfirmDialogProvider";
import { useDeckEditorHistoryContext } from "../../context/deckEditorHistoryContext";
import {
  playlistHistoryAuthor,
  playlistHistoryPreview,
  summarizePlaylistHistoryChange,
} from "../../utils/playlistHistoryTimeline";
import { HostContainedDialog } from "../ui/Modal";

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

const TvDashboardTimeline = createTimeline({ prefix: "td" });

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

  const timelineItems: TimelineItemModel[] = (page?.items ?? []).map((item) => {
    const author = playlistHistoryAuthor(item);
    const selected = detail?.snapshotId === item.snapshotId;
    return {
      id: item.snapshotId,
      title: `Revisão ${item.revision}`,
      occurredAt: item.createdAt,
      timeLabel: formatDate(item.createdAt),
      marker: <History size={12} />,
      tone: selected ? "info" : "default",
      detail: summarizePlaylistHistoryChange(item),
      meta: (
        <>
          <span>
            {author.name}
            {author.email ? ` · ${author.email}` : ""}
          </span>
          <br />
          <span>{playlistHistoryPreview(item)}</span>
          <div className="td-history__actions">
            <button
              type="button"
              className="td-btn td-btn--sm"
              onClick={() => void selectRevision(item)}
              aria-label={`Ver detalhes da revisão ${item.revision}`}
              aria-pressed={selected}
            >
              Ver detalhes
            </button>
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={history.restoring}
              onClick={() => void restore(item)}
            >
              <RotateCcw size={14} aria-hidden="true" />
              Restaurar
            </button>
          </div>
        </>
      ),
    };
  });

  return (
    <HostContainedDialog open={open} title="Histórico de revisões" onClose={onClose} className="td-modal--history">
      {history.error ? (
        <div className="td-history__error" role="alert">
          {history.error}
        </div>
      ) : null}
      <div className="td-history__layout">
        <TvDashboardTimeline
          layout="linear"
          aria-label="Revisões da programação"
          items={timelineItems}
          loading={history.loading}
          loadingMessage="Carregando revisões…"
          emptyMessage="Nenhuma revisão registrada."
        />
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
    </HostContainedDialog>
  );
}
