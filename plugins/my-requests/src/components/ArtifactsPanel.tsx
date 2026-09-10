import { FieldLabel } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  artifactDownloadUrl,
  downloadArtifactBlob,
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
  MyRequestsAttachmentPreviewStrip,
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

function isImageArtifact(item: RequestArtifact): boolean {
  const ct = (item.content_type || "").toLowerCase();
  if (ct.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(item.file_name || "");
}

function formatBytes(value: number | null | undefined): string | undefined {
  if (value == null || value <= 0) return undefined;
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function ArtifactsPanel({
  requestId,
  canUpload = false,
  refreshKey = 0,
}: ArtifactsPanelProps) {
  const [items, setItems] = useState<RequestArtifact[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [artifactKind, setArtifactKind] = useState<string>("generic");
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  const thumbUrlsRef = useRef<Record<string, string>>({});

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

  useEffect(() => {
    let cancelled = false;
    const clearThumbs = () => {
      for (const url of Object.values(thumbUrlsRef.current)) {
        URL.revokeObjectURL(url);
      }
      thumbUrlsRef.current = {};
      setThumbUrls({});
    };

    if (items.length === 0) {
      clearThumbs();
      return () => {
        cancelled = true;
      };
    }

    void (async () => {
      const next: Record<string, string> = {};
      for (const item of items) {
        if (!isImageArtifact(item)) continue;
        try {
          const blob = await downloadArtifactBlob(item.id);
          if (cancelled) return;
          next[item.id] = URL.createObjectURL(blob);
        } catch {
          // icon fallback
        }
      }
      if (cancelled) {
        for (const url of Object.values(next)) URL.revokeObjectURL(url);
        return;
      }
      clearThumbs();
      thumbUrlsRef.current = next;
      setThumbUrls(next);
    })();

    return () => {
      cancelled = true;
      clearThumbs();
    };
  }, [items]);

  const stripItems = useMemo(
    () =>
      items.map((item) => ({
        id: item.id,
        fileName: item.file_name,
        contentType: item.content_type,
        previewUrl: thumbUrls[item.id] || null,
        detail: [item.kind ? artifactKindLabel(item.kind) : null, formatBytes(item.size_bytes)]
          .filter(Boolean)
          .join(" · "),
      })),
    [items, thumbUrls],
  );

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
          <MyRequestsAttachmentPreviewStrip
            mode="preview"
            items={stripItems}
            onOpen={(item) => {
              window.open(artifactDownloadUrl(item.id), "_blank", "noopener,noreferrer");
            }}
          />
        ) : null}
      </div>
    </MyRequestsSectionCard>
  );
}
