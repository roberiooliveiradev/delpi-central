import { useEffect, useMemo, useState } from "react";
import { ActionButton, FilePreviewModal, resolveFilePreviewKind } from "@delpi/plugin-ui/index";

import {
  HelpdeskApiError,
  downloadTicketAttachment,
  fetchTicketAttachmentBlob,
  type TicketAttachment,
} from "../api/helpdeskApi";

function previewErrorText(error: unknown): string {
  if (error instanceof HelpdeskApiError) {
    if (error.code === "not_found") return "Este arquivo não está disponível para você.";
    if (error.code === "forbidden" || error.code === "glpi_forbidden") {
      return "O helpdesk recusou este arquivo para o seu usuário.";
    }
  }
  return "Não foi possível abrir o arquivo.";
}
import { HelpdeskAttachmentPreviewStrip } from "../ui/helpdeskUi";

export function TicketAttachmentPreview({
  ticketId,
  attachments,
  onError,
}: {
  ticketId: string;
  attachments: TicketAttachment[];
  onError: (message: string) => void;
}) {
  const [preview, setPreview] = useState<TicketAttachment | null>(null);
  const [thumbs, setThumbs] = useState<Record<number, string>>({});
  const attachmentKey = attachments.map((item) => item.document_id).join(",");

  useEffect(() => {
    let cancelled = false;
    const urls: string[] = [];

    void Promise.all(
      attachments.map(async (file) => {
        if (resolveFilePreviewKind({ fileName: file.filename, mimeType: file.mime }) !== "image") {
          return;
        }
        const blob = await fetchTicketAttachmentBlob(ticketId, file.document_id);
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        urls.push(url);
        setThumbs((current) => ({ ...current, [file.document_id]: url }));
      }),
    ).catch((error) => {
      if (!cancelled) onError(previewErrorText(error));
    });

    return () => {
      cancelled = true;
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [attachmentKey, ticketId]);

  const items = useMemo(
    () =>
      attachments.map((file) => ({
        id: String(file.document_id),
        fileName: file.filename || "anexo",
        contentType: file.mime,
        previewUrl: thumbs[file.document_id] || null,
      })),
    [attachments, thumbs],
  );

  if (attachments.length === 0) return null;

  return (
    <>
      <HelpdeskAttachmentPreviewStrip
        heading="Arquivos do chamado"
        items={items}
        onOpen={(item) => {
          const file = attachments.find((entry) => String(entry.document_id) === item.id);
          if (file) setPreview(file);
        }}
      />
      <FilePreviewModal
        open={Boolean(preview)}
        title={preview?.filename || "Anexo"}
        fileName={preview?.filename}
        mimeType={preview?.mime}
        source={preview ? () => fetchTicketAttachmentBlob(ticketId, preview.document_id) : null}
        portalScopeClassName="dashboard-helpdesk"
        onClose={() => setPreview(null)}
        headerActions={
          preview ? (
            <ActionButton
              onClick={() => {
                void downloadTicketAttachment(ticketId, preview.document_id, preview.filename || "anexo").catch(
                  (error) => onError(previewErrorText(error)),
                );
              }}
            >
              Baixar
            </ActionButton>
          ) : null
        }
      />
    </>
  );
}
