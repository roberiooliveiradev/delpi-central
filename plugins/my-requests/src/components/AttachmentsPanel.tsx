import { useCallback, useEffect, useState } from "react";
import { ActionButton, FieldLabel } from "@delpi/plugin-ui/index";

import {
  attachmentDownloadUrl,
  listAttachments,
  uploadAttachment,
} from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestAttachment } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsFileDropzone,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";

type AttachmentsPanelProps = {
  requestId: string;
  canUpload?: boolean;
};

export function AttachmentsPanel({
  requestId,
  canUpload = false,
}: AttachmentsPanelProps) {
  const [items, setItems] = useState<RequestAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      const next = await listAttachments(requestId, { signal });
      setItems(next);
    },
    [requestId],
  );

  useEffect(() => {
    const ac = new AbortController();
    reload(ac.signal).catch((err: Error) => {
      if (err.name !== "AbortError") setError(err.message);
    });
    return () => ac.abort();
  }, [reload]);

  async function onFilesSelected(files: File[]) {
    if (!canUpload || !files.length || busy) return;
    setBusy(true);
    setError(null);
    try {
      for (const file of files) {
        await uploadAttachment(requestId, file, crypto.randomUUID());
      }
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar documento");
    } finally {
      setBusy(false);
    }
  }

  return (
    <MyRequestsSectionCard
      title="Documentos da solicitação"
      subtitle="Arquivos que ajudam a entender ou complementar o pedido."
      hint={MY_REQUESTS_HELP_TOOLTIPS.attachments.section}
    >
      <div data-help="attachments">
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        {canUpload ? (
          <div className="my-requests-upload-field">
            <FieldLabel
              label="Adicionar documento à solicitação"
              hint={MY_REQUESTS_HELP_TOOLTIPS.attachments.upload}
            />
            <MyRequestsFileDropzone
              multiple
              busy={busy}
              disabled={busy}
              accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
              onFilesSelected={onFilesSelected}
              ariaLabel="Adicionar documento à solicitação"
            />
          </div>
        ) : null}
        {!error && items.length === 0 ? (
          <MyRequestsEmptyState
            message={
              canUpload
                ? "Nenhum documento ainda. Arraste arquivos ou use a área de envio."
                : "Nenhum documento da solicitação."
            }
          />
        ) : null}
        {items.length > 0 ? (
          <ul className="my-requests-domain-list">
            {items.map((item) => (
              <li key={item.id}>
                <ActionButton
                  href={attachmentDownloadUrl(item.id)}
                  title={`Baixar ${item.file_name}`}
                  variant="link"
                >
                  {item.file_name}
                </ActionButton>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </MyRequestsSectionCard>
  );
}
