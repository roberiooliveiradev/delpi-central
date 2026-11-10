/** PRC-REF-023 — seção «Documentos de apoio» do detalhe PRC.
 * Lista metadados + download autorizado via Engineering API. */

import { useCallback, useEffect, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringSectionCard,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import {
  downloadPrcAttachment,
  fetchPrcAttachments,
  type PrcAttachment,
} from "../api/productRegistrationApi";
import {
  PRC_ATTACHMENT_MEDIA_LABELS,
  PRC_ATTACHMENT_STATE_LABELS,
  prcFormatSize,
} from "../prcAttachments";

export function PrcAttachmentsSection({
  requestId,
  refreshToken,
}: {
  requestId: string;
  refreshToken?: string;
}) {
  const [items, setItems] = useState<PrcAttachment[]>([]);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const env = await fetchPrcAttachments(requestId);
      setItems(env.data.attachments || []);
      setError("");
    } catch (e) {
      setError((e as Error).message || "Falha ao carregar documentos.");
    } finally {
      setLoaded(true);
    }
  }, [requestId]);

  useEffect(() => {
    setLoaded(false);
    void load();
  }, [load, refreshToken]);

  const download = async (att: PrcAttachment) => {
    setDownloading(att.attachmentId);
    setError("");
    try {
      const blob = await downloadPrcAttachment(requestId, att.attachmentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = att.originalFileName;
      a.rel = "noopener";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message || "Falha ao baixar o documento.");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <EngineeringSectionCard
      title="Documentos de apoio"
      subtitle="Anexos opcionais enviados pelo solicitante"
    >
      {error ? (
        <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
      ) : null}
      {loaded && !items.length && !error ? (
        <p className="engineering-prc__muted">
          Nenhum documento de apoio anexado.
        </p>
      ) : null}
      {items.length ? (
        <ul className="engineering-prc__attach-list">
          {items.map((att) => (
            <li key={att.attachmentId}>
              <span>
                {att.originalFileName} —{" "}
                {PRC_ATTACHMENT_MEDIA_LABELS[att.mediaType] || att.mediaType},{" "}
                {prcFormatSize(att.sizeBytes)} ·{" "}
                {PRC_ATTACHMENT_STATE_LABELS[att.state] || att.state} ·{" "}
                {att.uploadedByDisplayName || att.uploadedBySubject || "—"} ·{" "}
                {new Date(att.createdAt).toLocaleString("pt-BR")}
              </span>
              {att.state === "AVAILABLE" ? (
                <EngineeringActionButton
                  variant="ghost"
                  softDisabled={downloading === att.attachmentId}
                  onClick={() => void download(att)}
                >
                  {downloading === att.attachmentId
                    ? "Baixando…"
                    : "Baixar"}
                </EngineeringActionButton>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </EngineeringSectionCard>
  );
}
