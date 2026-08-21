import { FileUp, FileText, Link2 } from "lucide-react";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

import {
  downloadRoomMessageAttachmentBlob,
  listRoomSharedItems,
  postInteractionMessage,
  uploadRoomMessageAttachment,
  type InteractionRoomSharedItemDto,
} from "../../api/interactionRoomsApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialTextField,
  CommercialUnderlineNav,
} from "../../app/commercialUi";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { formatInteractionMessageTime } from "./interactionRoomMessageTime";
import { ROOM_ATTACH_ACCEPT } from "./InteractionRoomMessageComposer";

type SharedKindTab = "all" | "file" | "link";

type Props = {
  roomId: string;
  onError?: (message: string) => void;
  onUploaded?: () => void;
};

export function InteractionRoomSharedView({ roomId, onError, onUploaded }: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const filterId = useId();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [kind, setKind] = useState<SharedKindTab>("all");
  const [filter, setFilter] = useState("");
  const [debouncedFilter, setDebouncedFilter] = useState("");
  const [items, setItems] = useState<InteractionRoomSharedItemDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedFilter(filter.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [filter]);

  useEffect(() => {
    const id = roomId.trim();
    if (!id) return;
    const controller = new AbortController();
    setLoading(true);
    void (async () => {
      try {
        const rows = await listRoomSharedItems(id, {
          kind,
          q: debouncedFilter || null,
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setItems(rows);
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setItems([]);
        onError?.(
          err instanceof Error ? err.message : content.sharedLoadError,
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [roomId, kind, debouncedFilter, reloadToken, content.sharedLoadError, onError]);

  const authorIds = useMemo(
    () =>
      [
        ...new Set(
          items
            .map((item) => (item.shared_by || "").trim())
            .filter(Boolean),
        ),
      ],
    [items],
  );
  const { nameFor } = useDirectoryUserLabels(authorIds);

  const openItem = useCallback(
    async (item: InteractionRoomSharedItemDto) => {
      if (item.kind === "link" && item.href) {
        window.open(item.href, "_blank", "noopener,noreferrer");
        return;
      }
      const attachmentId = (item.attachment_id || "").trim();
      if (!attachmentId) return;
      try {
        const blob = await downloadRoomMessageAttachmentBlob(attachmentId);
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = item.title || "attachment";
        anchor.rel = "noopener";
        anchor.click();
        URL.revokeObjectURL(url);
      } catch (err: unknown) {
        onError?.(err instanceof Error ? err.message : content.sharedLoadError);
      }
    },
    [content.sharedLoadError, onError],
  );

  const onUploadFiles = useCallback(
    async (fileList: FileList | null) => {
      const files = fileList ? Array.from(fileList) : [];
      if (files.length === 0) return;
      const id = roomId.trim();
      if (!id) return;
      setUploading(true);
      try {
        for (const file of files) {
          const message = await postInteractionMessage(id, {
            body_text: file.name || "attachment",
          });
          await uploadRoomMessageAttachment(message.id, file);
        }
        setReloadToken((token) => token + 1);
        onUploaded?.();
      } catch (err: unknown) {
        onError?.(
          err instanceof Error ? err.message : content.attachUploadError,
        );
      } finally {
        setUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [content.attachUploadError, onError, onUploaded, roomId],
  );

  return (
    <div className="cm-room-shared">
      <div className="cm-room-shared__toolbar">
        <CommercialUnderlineNav
          mode="tabs"
          aria-label={content.roomViewShared}
          activeId={kind}
          items={[
            {
              id: "all",
              label: content.sharedKindRecent,
              onSelect: () => setKind("all"),
            },
            {
              id: "file",
              label: content.sharedKindFiles,
              onSelect: () => setKind("file"),
            },
            {
              id: "link",
              label: content.sharedKindLinks,
              onSelect: () => setKind("link"),
            },
          ]}
        />
        <div className="cm-room-shared__toolbar-actions">
          <CommercialTextField
            id={filterId}
            label={content.sharedFilterPlaceholder}
            value={filter}
            onChange={setFilter}
            placeholder={content.sharedFilterPlaceholder}
            fullWidth
          />
          <CommercialActionButton
            variant="secondary"
            aria-label={content.sharedUploadAriaLabel}
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            <FileUp size={16} aria-hidden />
            {content.sharedUploadLabel}
          </CommercialActionButton>
          <input
            ref={fileInputRef}
            type="file"
            accept={ROOM_ATTACH_ACCEPT}
            multiple
            hidden
            onChange={(event) => void onUploadFiles(event.target.files)}
          />
        </div>
      </div>
      {loading || uploading ? (
        <CommercialLoadingCard
          title={uploading ? content.dropzoneBusyTitle : content.sharedLoadingLabel}
          variant="panel"
        />
      ) : null}
      {!loading && !uploading && items.length === 0 ? (
        <CommercialEmptyState
          title={content.sharedEmptyTitle}
          message={content.sharedEmptyDescription}
        />
      ) : null}
      {!loading && !uploading && items.length > 0 ? (
        <ul className="cm-room-shared__list">
          {items.map((item) => {
            const Icon = item.kind === "link" ? Link2 : FileText;
            const sharedBy = item.shared_by
              ? nameFor(item.shared_by)
              : "—";
            const aria =
              item.kind === "link"
                ? content.sharedOpenLinkAriaLabel
                : content.sharedOpenFileAriaLabel.replace(
                    "{fileName}",
                    item.title || "file",
                  );
            return (
              <li key={item.id}>
                <button
                  type="button"
                  className="cm-room-shared__row"
                  aria-label={aria}
                  onClick={() => void openItem(item)}
                >
                  <span className="cm-room-shared__icon" aria-hidden>
                    <Icon size={18} />
                  </span>
                  <span className="cm-room-shared__meta">
                    <span className="cm-room-shared__title">{item.title}</span>
                    {item.subtitle ? (
                      <span className="cm-room-shared__subtitle">{item.subtitle}</span>
                    ) : null}
                  </span>
                  <span className="cm-room-shared__when">
                    {formatInteractionMessageTime(item.shared_at)}
                  </span>
                  <span className="cm-room-shared__who">{sharedBy}</span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
