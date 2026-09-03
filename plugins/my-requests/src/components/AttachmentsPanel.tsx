import { useEffect, useState } from "react";

import { attachmentDownloadUrl, listAttachments } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestAttachment } from "../types/requests";

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
    <section
      className="dashboard-my-requests__panel"
      data-help="attachments"
      title={MY_REQUESTS_HELP_TOOLTIPS.attachments.section}
    >
      <h2>Anexos</h2>
      {error ? <p className="dashboard-my-requests__error">{error}</p> : null}
      {!error && items.length === 0 ? (
        <p className="dashboard-my-requests__muted">Nenhum anexo.</p>
      ) : null}
      <ul className="dashboard-my-requests__list">
        {items.map((item) => (
          <li key={item.id}>
            <a href={attachmentDownloadUrl(item.id)}>{item.file_name}</a>
          </li>
        ))}
      </ul>
    </section>
  );
}
