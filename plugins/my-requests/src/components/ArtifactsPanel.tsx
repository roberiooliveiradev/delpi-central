import { useCallback, useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import {
  artifactDownloadUrl,
  listArtifacts,
  uploadArtifact,
} from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestArtifact } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsFileDropzone,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SelectField,
} from "../ui/mrUi";

const ARTIFACT_KIND_OPTIONS = [
  { value: "generic", label: "Genérico" },
  { value: "invoice_pdf", label: "PDF da NF" },
] as const;

type ArtifactsPanelProps = {
  requestId: string;
  canUpload?: boolean;
};

export function ArtifactsPanel({ requestId, canUpload = false }: ArtifactsPanelProps) {
  const [items, setItems] = useState<RequestArtifact[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [artifactKind, setArtifactKind] = useState<string>("generic");

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      const next = await listArtifacts(requestId, { signal });
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
        await uploadArtifact(requestId, file, {
          artifactKind,
          idempotencyKey: crypto.randomUUID(),
        });
      }
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar artefato");
    } finally {
      setBusy(false);
    }
  }

  return (
    <MyRequestsSectionCard title="Artefatos">
      <div data-help="artifacts" title={MY_REQUESTS_HELP_TOOLTIPS.artifacts.section}>
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        {canUpload ? (
          <>
            <SelectField
              label="Tipo do artefato"
              value={artifactKind}
              onChange={setArtifactKind}
              options={[...ARTIFACT_KIND_OPTIONS]}
              disabled={busy}
            />
            <MyRequestsFileDropzone
              multiple
              busy={busy}
              disabled={busy}
              accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
              fieldLabel="Enviar artefato"
              onFilesSelected={onFilesSelected}
              ariaLabel="Enviar artefato de processamento"
            />
          </>
        ) : null}
        {!error && items.length === 0 ? (
          <MyRequestsEmptyState
            message={
              canUpload
                ? "Nenhum artefato ainda. Envie evidências do processamento."
                : "Nenhum artefato."
            }
          />
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
