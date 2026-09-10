import { useCallback, useEffect, useState } from "react";
import { ActionButton, FieldLabel } from "@delpi/plugin-ui/index";

import {
  artifactDownloadUrl,
  listArtifacts,
  uploadArtifact,
} from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  ARTIFACT_KIND_OPTIONS,
  artifactKindLabel,
} from "../content/presentationLabels";
import type { RequestArtifact } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsFileDropzone,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SelectField,
} from "../ui/mrUi";

type ArtifactsPanelProps = {
  requestId: string;
  canUpload?: boolean;
  refreshKey?: number;
};

export function ArtifactsPanel({
  requestId,
  canUpload = false,
  refreshKey = 0,
}: ArtifactsPanelProps) {
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
  }, [reload, refreshKey]);

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
      setError(err instanceof Error ? err.message : "Não foi possível enviar o documento.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <MyRequestsSectionCard
      title="Documentos gerados no atendimento"
      subtitle="Arquivos produzidos como resultado do atendimento."
      hint={MY_REQUESTS_HELP_TOOLTIPS.artifacts.section}
    >
      <div data-help="artifacts">
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        {canUpload ? (
          <>
            <SelectField
              label="Tipo de documento"
              hint={MY_REQUESTS_HELP_TOOLTIPS.artifacts.kind}
              value={artifactKind}
              onChange={setArtifactKind}
              options={[...ARTIFACT_KIND_OPTIONS]}
              disabled={busy}
            />
            <div className="my-requests-upload-field">
              <FieldLabel
                label="Adicionar documento do atendimento"
                hint={MY_REQUESTS_HELP_TOOLTIPS.artifacts.upload}
              />
              <MyRequestsFileDropzone
                multiple
                busy={busy}
                disabled={busy}
                accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
                onFilesSelected={onFilesSelected}
                ariaLabel="Adicionar documento do atendimento"
              />
            </div>
          </>
        ) : null}
        {!error && items.length === 0 ? (
          <MyRequestsEmptyState
            message={
              canUpload
                ? "Nenhum documento ainda. Envie evidências do atendimento (ex.: nota fiscal em PDF)."
                : "Nenhum documento gerado no atendimento."
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
                {item.kind ? ` (${artifactKindLabel(item.kind)})` : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </MyRequestsSectionCard>
  );
}
