import { useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { attachmentDownloadUrl, listAttachments } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestAttachment } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";

type AttachmentsPanelProps = {
  requestId: string;
};

export function AttachmentsPanel({ requestId }: AttachmentsPanelProps) {
  const [items, setItems] = useState<RequestAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    listAttachments(requestId, { signal: ac.signal })
      .then(setItems)
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, [requestId]);

  return (
    <MyRequestsSectionCard title="Anexos">
      <div data-help="attachments" title={MY_REQUESTS_HELP_TOOLTIPS.attachments.section}>
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
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
