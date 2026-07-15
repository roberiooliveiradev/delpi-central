import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveMedia,
  createExternalVideo,
  listAdminProcedureMedia,
  updateMediaMetadata,
  uploadProcedureImage,
  uploadProcedureVideo,
  type ProcedureMedia,
} from "../api/guiasProcedimentosApi";
import { HttpRequestError } from "../api/httpClient";
import { formatBytes } from "../utils/formatBytes";
import { parseExternalVideoUrl } from "../utils/externalVideo";
import {
  appendHtmlBlock,
  buildExternalVideoInsertHtml,
  buildImageInsertHtml,
  buildVideoFileInsertHtml,
} from "../utils/guideMediaInsert";
import { GuiasConfirmDialog } from "./GuiasConfirmDialog";
import { GuiasFormDialog } from "./GuiasFormDialog";
import { MediaPreviewPlayer, ProtectedMediaThumb } from "./ProtectedMediaThumb";

const IMAGE_MAX = 5 * 1024 * 1024;
const VIDEO_MAX = 20 * 1024 * 1024;
const IMAGE_EXT = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif"]);
const VIDEO_EXT = new Set([".mp4", ".webm", ".mov"]);
const IMAGE_MIME = new Set([
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
  "image/gif",
]);
const VIDEO_MIME = new Set([
  "video/mp4",
  "video/webm",
  "video/quicktime",
]);

type ProcedureMediaManagerProps = {
  procedureId: string | null;
  contentHtml: string;
  onContentHtmlChange: (next: string) => void;
  disabled?: boolean;
};

type UploadMode = "image" | "video" | "external" | null;
type EditState = {
  id: string;
  title: string;
  alt_text: string;
  order_index: number;
} | null;

function extensionOf(name: string): string {
  const idx = name.lastIndexOf(".");
  return idx >= 0 ? name.slice(idx).toLowerCase() : "";
}

function kindLabel(
  kind: ProcedureMedia["media_kind"],
  provider?: string | null,
): string {
  switch (kind) {
    case "image":
      return "Imagem";
    case "video_file":
      return "Vídeo";
    case "video_external":
      if (provider === "google_drive") return "Google Drive";
      if (provider === "vimeo") return "Vimeo";
      if (provider === "youtube") return "YouTube";
      return "Vídeo externo";
    default:
      return kind;
  }
}

export function ProcedureMediaManager({
  procedureId,
  contentHtml,
  onContentHtmlChange,
  disabled = false,
}: ProcedureMediaManagerProps) {
  const [items, setItems] = useState<ProcedureMedia[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [uploadMode, setUploadMode] = useState<UploadMode>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [altText, setAltText] = useState("");
  const [orderIndex, setOrderIndex] = useState(0);
  const [externalUrl, setExternalUrl] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [edit, setEdit] = useState<EditState>(null);
  const [archiveId, setArchiveId] = useState<string | null>(null);
  const [preview, setPreview] = useState<ProcedureMedia | null>(null);

  const reload = useCallback(async () => {
    if (!procedureId) return;
    setLoading(true);
    setError(null);
    try {
      const rows = await listAdminProcedureMedia(procedureId);
      setItems(rows);
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível carregar as mídias.",
      );
    } finally {
      setLoading(false);
    }
  }, [procedureId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const nextOrder = useMemo(
    () => (items.length ? Math.max(...items.map((m) => m.order_index)) + 1 : 0),
    [items],
  );

  function openUpload(mode: UploadMode) {
    setUploadMode(mode);
    setFile(null);
    setTitle("");
    setAltText("");
    setExternalUrl("");
    setOrderIndex(nextOrder);
    setProgress(null);
    setError(null);
  }

  function closeUpload() {
    if (busy) return;
    setUploadMode(null);
    setFile(null);
    setProgress(null);
  }

  async function submitUpload() {
    if (!procedureId || !uploadMode) return;
    setBusy(true);
    setError(null);
    setFeedback(null);
    try {
      if (uploadMode === "external") {
        const parsed = parseExternalVideoUrl(externalUrl);
        if (!parsed.ok) {
          setError(parsed.reason);
          setBusy(false);
          return;
        }
        await createExternalVideo(procedureId, {
          url: parsed.url,
          title: title.trim(),
          order_index: Number(orderIndex) || 0,
        });
        setFeedback("Vídeo externo cadastrado.");
      } else if (uploadMode === "image") {
        if (!file) {
          setError("Selecione uma imagem.");
          setBusy(false);
          return;
        }
        const ext = extensionOf(file.name);
        if (ext === ".svg" || (!IMAGE_EXT.has(ext) && file.type && !IMAGE_MIME.has(file.type))) {
          setError("Formato inválido. Use JPEG, PNG, WebP ou GIF (sem SVG).");
          setBusy(false);
          return;
        }
        if (file.size > IMAGE_MAX) {
          setError("Imagem excede o limite de 5 MB.");
          setBusy(false);
          return;
        }
        setProgress(0);
        await uploadProcedureImage(
          procedureId,
          file,
          {
            title: title.trim() || file.name,
            alt_text: altText.trim(),
            order_index: Number(orderIndex) || 0,
          },
          (ratio) => setProgress(ratio),
        );
        setFeedback("Imagem enviada.");
      } else {
        if (!file) {
          setError("Selecione um vídeo.");
          setBusy(false);
          return;
        }
        const ext = extensionOf(file.name);
        if (!VIDEO_EXT.has(ext) && file.type && !VIDEO_MIME.has(file.type)) {
          setError("Formato inválido. Use MP4, WebM ou MOV.");
          setBusy(false);
          return;
        }
        if (file.size > VIDEO_MAX) {
          setError("Vídeos maiores que 20 MB não podem ser enviados nesta versão.");
          setBusy(false);
          return;
        }
        setProgress(0);
        await uploadProcedureVideo(
          procedureId,
          file,
          {
            title: title.trim() || file.name,
            order_index: Number(orderIndex) || 0,
          },
          (ratio) => setProgress(ratio),
        );
        setFeedback("Vídeo enviado.");
      }
      setUploadMode(null);
      setFile(null);
      await reload();
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível concluir o envio.",
      );
    } finally {
      setBusy(false);
      setProgress(null);
    }
  }

  async function submitEdit() {
    if (!edit) return;
    setBusy(true);
    setError(null);
    try {
      await updateMediaMetadata(edit.id, {
        title: edit.title.trim(),
        alt_text: edit.alt_text.trim(),
        order_index: Number(edit.order_index) || 0,
      });
      setFeedback("Metadados atualizados.");
      setEdit(null);
      await reload();
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível atualizar.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirmArchive() {
    if (!archiveId) return;
    setBusy(true);
    setError(null);
    try {
      await archiveMedia(archiveId);
      setFeedback("Mídia arquivada.");
      setArchiveId(null);
      await reload();
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível arquivar.",
      );
      setArchiveId(null);
    } finally {
      setBusy(false);
    }
  }

  function insertMedia(media: ProcedureMedia) {
    let block = "";
    if (media.media_kind === "image") {
      block = buildImageInsertHtml(media);
    } else if (media.media_kind === "video_file") {
      block = buildVideoFileInsertHtml(media);
    } else if (media.external_url) {
      block = buildExternalVideoInsertHtml({
        title: media.title,
        external_url: media.external_url,
        external_provider: media.external_provider,
      });
    }
    if (!block) return;
    onContentHtmlChange(appendHtmlBlock(contentHtml, block));
    setFeedback("Referência inserida no artigo. Confira na aba Conteúdo.");
  }

  async function copyRef(media: ProcedureMedia) {
    let block = "";
    if (media.media_kind === "image") block = buildImageInsertHtml(media);
    else if (media.media_kind === "video_file") {
      block = buildVideoFileInsertHtml(media);
    } else if (media.external_url) {
      block = buildExternalVideoInsertHtml({
        title: media.title,
        external_url: media.external_url,
        external_provider: media.external_provider,
      });
    }
    if (!block) return;
    try {
      await navigator.clipboard.writeText(block);
      setFeedback("HTML copiado.");
    } catch {
      setFeedback("Não foi possível copiar. Use «Inserir no artigo».");
    }
  }

  if (!procedureId) {
    return (
      <div className="gp-asset-panel">
        <p className="gp-intro">
          Salve o rascunho do procedimento antes de enviar imagens ou vídeos.
        </p>
      </div>
    );
  }

  return (
    <div className="gp-asset-panel">
      <div className="gp-asset-panel__toolbar">
        <button
          type="button"
          className="gp-btn gp-btn--secondary gp-btn--compact"
          disabled={disabled || busy}
          onClick={() => openUpload("image")}
        >
          Enviar imagem
        </button>
        <button
          type="button"
          className="gp-btn gp-btn--secondary gp-btn--compact"
          disabled={disabled || busy}
          onClick={() => openUpload("video")}
        >
          Enviar vídeo
        </button>
        <button
          type="button"
          className="gp-btn gp-btn--ghost gp-btn--compact"
          disabled={disabled || busy}
          onClick={() => openUpload("external")}
        >
          Vídeo externo
        </button>
      </div>
      <p className="gp-field__hint">
        Imagens até 5 MB (JPEG, PNG, WebP, GIF — sem SVG). Vídeos de arquivo até
        20 MB (MP4, WebM, MOV).{" "}
        <strong>Vídeos maiores que 20 MB não podem ser enviados nesta versão.</strong>
      </p>

      {feedback ? (
        <p className="gp-feedback gp-feedback--ok">{feedback}</p>
      ) : null}
      {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}
      {loading ? <p className="gp-intro">Carregando mídias…</p> : null}

      {!loading && items.length === 0 ? (
        <p className="gp-intro">Nenhuma mídia cadastrada.</p>
      ) : null}

      {items.length > 0 ? (
        <div className="gp-admin-table-wrap">
          <table className="gp-admin-table">
            <thead>
              <tr>
                <th scope="col">Prévia</th>
                <th scope="col">Título</th>
                <th scope="col">Tipo</th>
                <th scope="col">Tamanho</th>
                <th scope="col">Ordem</th>
                <th scope="col">Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((media) => (
                <tr key={media.id}>
                  <td>
                    <ProtectedMediaThumb media={media} />
                  </td>
                  <td>
                    <div className="gp-asset-title">
                      {media.title || media.original_filename || "Sem título"}
                    </div>
                    {media.original_filename ? (
                      <div className="gp-field__hint">{media.original_filename}</div>
                    ) : null}
                  </td>
                  <td>
                    {kindLabel(media.media_kind, media.external_provider)}
                  </td>
                  <td>
                    {media.media_kind === "video_external"
                      ? "—"
                      : formatBytes(media.size_bytes)}
                  </td>
                  <td>{media.order_index}</td>
                  <td>
                    <div className="gp-admin-row-actions">
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        onClick={() => setPreview(media)}
                      >
                        Prévia
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        disabled={disabled}
                        onClick={() =>
                          setEdit({
                            id: media.id,
                            title: media.title,
                            alt_text: media.alt_text,
                            order_index: media.order_index,
                          })
                        }
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--secondary gp-btn--compact"
                        disabled={disabled}
                        onClick={() => insertMedia(media)}
                      >
                        Inserir no artigo
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        onClick={() => void copyRef(media)}
                      >
                        Copiar HTML
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        disabled={disabled || busy}
                        onClick={() => setArchiveId(media.id)}
                      >
                        Arquivar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <GuiasFormDialog
        open={uploadMode != null}
        title={
          uploadMode === "image"
            ? "Enviar imagem"
            : uploadMode === "video"
              ? "Enviar vídeo"
              : "Cadastrar vídeo externo"
        }
        busy={busy}
        confirmLabel={uploadMode === "external" ? "Cadastrar" : "Enviar"}
        confirmDisabled={
          uploadMode === "external" ? !externalUrl.trim() : !file
        }
        onCancel={closeUpload}
        onConfirm={() => void submitUpload()}
      >
        {uploadMode === "external" ? (
          <>
            <label className="gp-field">
              <span>URL</span>
              <input
                className="gp-input"
                value={externalUrl}
                onChange={(event) => setExternalUrl(event.target.value)}
                placeholder="https://drive.google.com/file/d/…/view"
                disabled={busy}
              />
              <span className="gp-field__hint">
                Informe uma URL HTTPS pública do YouTube, Vimeo ou Google Drive
                (compartilhamento do arquivo, não da pasta).
              </span>
            </label>
            <label className="gp-field">
              <span>Título</span>
              <input
                className="gp-input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                disabled={busy}
              />
            </label>
            <label className="gp-field">
              <span>Ordem</span>
              <input
                className="gp-input"
                type="number"
                min={0}
                value={orderIndex}
                onChange={(event) => setOrderIndex(Number(event.target.value))}
                disabled={busy}
              />
            </label>
          </>
        ) : (
          <>
            <label className="gp-field">
              <span>Arquivo</span>
              <input
                className="gp-input"
                type="file"
                accept={
                  uploadMode === "image"
                    ? "image/jpeg,image/png,image/webp,image/gif,.jpg,.jpeg,.png,.webp,.gif"
                    : "video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov"
                }
                disabled={busy}
                onChange={(event) => {
                  const next = event.target.files?.[0] ?? null;
                  setFile(next);
                  if (next && !title.trim()) setTitle(next.name);
                }}
              />
              {file ? (
                <span className="gp-field__hint">
                  {file.name} · {formatBytes(file.size)}
                </span>
              ) : null}
              {uploadMode === "video" ? (
                <span className="gp-field__hint">
                  Vídeos maiores que 20 MB não podem ser enviados nesta versão.
                </span>
              ) : null}
            </label>
            <label className="gp-field">
              <span>Título</span>
              <input
                className="gp-input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                disabled={busy}
              />
            </label>
            {uploadMode === "image" ? (
              <label className="gp-field">
                <span>Texto alternativo (alt)</span>
                <input
                  className="gp-input"
                  value={altText}
                  onChange={(event) => setAltText(event.target.value)}
                  disabled={busy}
                />
              </label>
            ) : null}
            <label className="gp-field">
              <span>Ordem</span>
              <input
                className="gp-input"
                type="number"
                min={0}
                value={orderIndex}
                onChange={(event) => setOrderIndex(Number(event.target.value))}
                disabled={busy}
              />
            </label>
            {progress != null ? (
              <p className="gp-field__hint">
                Envio: {Math.round(progress * 100)}%
              </p>
            ) : null}
          </>
        )}
      </GuiasFormDialog>

      <GuiasFormDialog
        open={edit != null}
        title="Editar metadados da mídia"
        busy={busy}
        onCancel={() => !busy && setEdit(null)}
        onConfirm={() => void submitEdit()}
      >
        {edit ? (
          <>
            <p className="gp-field__hint">
              Para substituir o arquivo, envie um novo e arquive o anterior.
            </p>
            <label className="gp-field">
              <span>Título</span>
              <input
                className="gp-input"
                value={edit.title}
                onChange={(event) =>
                  setEdit({ ...edit, title: event.target.value })
                }
                disabled={busy}
              />
            </label>
            <label className="gp-field">
              <span>Texto alternativo (alt)</span>
              <input
                className="gp-input"
                value={edit.alt_text}
                onChange={(event) =>
                  setEdit({ ...edit, alt_text: event.target.value })
                }
                disabled={busy}
              />
            </label>
            <label className="gp-field">
              <span>Ordem</span>
              <input
                className="gp-input"
                type="number"
                min={0}
                value={edit.order_index}
                onChange={(event) =>
                  setEdit({
                    ...edit,
                    order_index: Number(event.target.value),
                  })
                }
                disabled={busy}
              />
            </label>
          </>
        ) : null}
      </GuiasFormDialog>

      <GuiasFormDialog
        open={preview != null}
        title={preview?.title || "Prévia"}
        busy={false}
        confirmLabel="Fechar"
        cancelLabel="Fechar"
        onCancel={() => setPreview(null)}
        onConfirm={() => setPreview(null)}
      >
        {preview ? <MediaPreviewPlayer media={preview} /> : null}
      </GuiasFormDialog>

      <GuiasConfirmDialog
        open={archiveId != null}
        title="Arquivar mídia"
        message="A mídia deixará de aparecer publicamente e nas listagens ativas. O arquivo permanece no armazenamento (sem exclusão física)."
        confirmLabel="Arquivar"
        busy={busy}
        variant="danger"
        onCancel={() => !busy && setArchiveId(null)}
        onConfirm={() => void confirmArchive()}
      />
    </div>
  );
}
