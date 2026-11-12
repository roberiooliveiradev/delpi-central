/** PRC-REF-023 — seção «Documentos de apoio» do detalhe PRC.
 * Miniaturas oficiais (imagem=thumb real, PDF=ícone) + modal de
 * pré-visualização; bytes sempre via endpoint autenticado da
 * Engineering API — nunca URL pública nem chave de storage. */

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringAttachmentPreviewStrip,
  EngineeringFilePreviewModal,
  EngineeringSectionCard,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import {
  downloadPrcAttachment,
  fetchPrcAttachments,
  type PrcAttachment,
} from "../api/productRegistrationApi";
import {
  PRC_ATTACHMENT_MEDIA_LABELS,
  PRC_ATTACHMENT_STATE_LABELS,
  prcFormatSize,
} from "../prcAttachments";

export function PrcAttachmentsSection({
  requestId,
  refreshToken,
}: {
  requestId: string;
  refreshToken?: string;
}) {
  const [items, setItems] = useState<PrcAttachment[]>([]);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [preview, setPreview] = useState<PrcAttachment | null>(null);

  const load = useCallback(async () => {
    try {
      const env = await fetchPrcAttachments(requestId);
      setItems(env.data.attachments || []);
      setError("");
    } catch (e) {
      setError((e as Error).message || "Falha ao carregar documentos.");
    } finally {
      setLoaded(true);
    }
  }, [requestId]);

  useEffect(() => {
    setLoaded(false);
    void load();
  }, [load, refreshToken]);

  /* Miniaturas de imagens persistidas: blob autenticado → object URL;
   * revogado na troca de itens/desmontagem. PDF usa ícone oficial. */
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  useEffect(() => {
    let cancelled = false;
    const created: Record<string, string> = {};
    const images = items.filter(
      (i) => i.state === "AVAILABLE" && i.mediaType.startsWith("image/"),
    );
    if (!images.length) {
      setThumbUrls({});
      return undefined;
    }
    void (async () => {
      for (const att of images) {
        try {
          const blob = await downloadPrcAttachment(
            requestId,
            att.attachmentId,
          );
          if (cancelled) return;
          created[att.attachmentId] = URL.createObjectURL(blob);
        } catch {
          /* thumb indisponível → cai no ícone por tipo */
        }
      }
      if (!cancelled) setThumbUrls(created);
    })();
    return () => {
      cancelled = true;
      Object.values(created).forEach((u) => URL.revokeObjectURL(u));
    };
  }, [items, requestId]);

  const download = useCallback(
    async (att: PrcAttachment) => {
      setDownloading(att.attachmentId);
      setError("");
      try {
        const blob = await downloadPrcAttachment(requestId, att.attachmentId);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = att.originalFileName;
        a.rel = "noopener";
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 5000);
      } catch (e) {
        setError((e as Error).message || "Falha ao baixar o documento.");
      } finally {
        setDownloading(null);
      }
    },
    [requestId],
  );

  /* Modal usa loader do kit com fetch lazy autenticado — o blob só é
   * buscado quando o usuário abre a pré-visualização. */
  const previewSource = useMemo(
    () =>
      preview
        ? () => downloadPrcAttachment(requestId, preview.attachmentId)
        : null,
    [preview, requestId],
  );

  /* PRC-UX-CHANGE-01 — sem anexos, sem card: só renderiza quando há
   * documentos ou uma falha a reportar (estado de carregamento não
   * exibe shell vazio). */
  if (loaded && !items.length && !error) return null;

  return (
    <EngineeringSectionCard
      title="Documentos de apoio"
      subtitle="Anexos opcionais enviados pelo solicitante"
    >
      {error ? (
        <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
      ) : null}
      {items.length ? (
        <EngineeringAttachmentPreviewStrip
          mode="preview"
          items={items.map((att) => ({
            id: att.attachmentId,
            fileName: att.originalFileName,
            contentType: att.mediaType,
            previewUrl: thumbUrls[att.attachmentId] ?? null,
            detail: `${PRC_ATTACHMENT_MEDIA_LABELS[att.mediaType] || att.mediaType} · ${prcFormatSize(att.sizeBytes)} · ${PRC_ATTACHMENT_STATE_LABELS[att.state] || att.state} · ${att.uploadedByDisplayName || att.uploadedBySubject || "—"} · ${new Date(att.createdAt).toLocaleString("pt-BR")}`,
            busy: false,
            removable: false,
          }))}
          onOpen={(item) => {
            const att = items.find((i) => i.attachmentId === item.id);
            if (att && att.state === "AVAILABLE") setPreview(att);
          }}
        />
      ) : null}
      <EngineeringFilePreviewModal
        open={preview != null}
        title={preview?.originalFileName || "Documento"}
        source={previewSource}
        mimeType={preview?.mediaType || null}
        fileName={preview?.originalFileName || null}
        metaItems={
          preview
            ? [
                PRC_ATTACHMENT_MEDIA_LABELS[preview.mediaType] ||
                  preview.mediaType,
                prcFormatSize(preview.sizeBytes),
                preview.uploadedByDisplayName || preview.uploadedBySubject,
                new Date(preview.createdAt).toLocaleString("pt-BR"),
              ]
            : []
        }
        headerActions={
          preview ? (
            <EngineeringActionButton
              variant="ghost"
              softDisabled={downloading === preview.attachmentId}
              onClick={() => preview && void download(preview)}
            >
              {downloading === preview.attachmentId
                ? "Baixando…"
                : "Baixar"}
            </EngineeringActionButton>
          ) : null
        }
        onClose={() => setPreview(null)}
      />
    </EngineeringSectionCard>
  );
}
