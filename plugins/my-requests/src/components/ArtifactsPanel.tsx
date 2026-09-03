import { useEffect, useState } from "react";

import { artifactDownloadUrl, listArtifacts } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestArtifact } from "../types/requests";

type ArtifactsPanelProps = {
  requestId: string;
};

export function ArtifactsPanel({ requestId }: ArtifactsPanelProps) {
  const [items, setItems] = useState<RequestArtifact[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    listArtifacts(requestId, { signal: ac.signal })
      .then(setItems)
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, [requestId]);

  return (
    <section
      className="dashboard-my-requests__panel"
      data-help="artifacts"
      title={MY_REQUESTS_HELP_TOOLTIPS.artifacts.section}
    >
      <h2>Artefatos</h2>
      {error ? <p className="dashboard-my-requests__error">{error}</p> : null}
      {!error && items.length === 0 ? (
        <p className="dashboard-my-requests__muted">Nenhum artefato.</p>
      ) : null}
      <ul className="dashboard-my-requests__list">
        {items.map((item) => (
          <li key={item.id}>
            <a href={artifactDownloadUrl(item.id)}>{item.file_name}</a>
            {item.kind ? (
              <span className="dashboard-my-requests__muted"> ({item.kind})</span>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
