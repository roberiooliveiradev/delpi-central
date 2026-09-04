import { useCallback, useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

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
};

export function AttachmentsPanel({ requestId }: AttachmentsPanelProps) {
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
    if (!files.length || busy) return;
    setBusy(true);
    setError(null);
    try {
      for (const file of files) {
        await uploadAttachment(requestId, file, crypto.randomUUID());
      }
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar anexo");
    } finally {
      setBusy(false);
    }
  }

  return (
    <MyRequestsSectionCard title="Anexos">
      <div data-help="attachments" title={MY_REQUESTS_HELP_TOOLTIPS.attachments.section}>
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        <MyRequestsFileDropzone
          multiple
          busy={busy}
          disabled={busy}
          accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
          fieldLabel="Enviar anexo"
          onFilesSelected={onFilesSelected}
          ariaLabel="Enviar anexo da solicitação"
        />
        {!error && items.length === 0 ? (
          <MyRequestsEmptyState message="Nenhum anexo." />
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
