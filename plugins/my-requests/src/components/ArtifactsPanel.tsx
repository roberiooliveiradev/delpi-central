import { useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { artifactDownloadUrl, listArtifacts } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestArtifact } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";

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
    <MyRequestsSectionCard title="Artefatos">
      <div data-help="artifacts" title={MY_REQUESTS_HELP_TOOLTIPS.artifacts.section}>
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        {!error && items.length === 0 ? (
          <MyRequestsEmptyState message="Nenhum artefato." />
        ) : null}
        {items.length > 0 ? (
          <ul className="my-requests-domain-list">
            {items.map((item) => (
              <li key={item.id}>
                <ActionButton
                  href={artifactDownloadUrl(item.id)}
                  title={`Baixar ${item.file_name}`}
                  variant="link"
                >
                  {item.file_name}
                </ActionButton>
                {item.kind ? ` (${item.kind})` : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </MyRequestsSectionCard>
  );
}
