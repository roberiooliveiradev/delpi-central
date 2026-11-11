/** PRC-REF-023-F04 — acompanhamento do caso PRC pelo solicitante.
 *
 * Status, histórico, anexos privados e correção de campos devolvidos —
 * sempre sobre o mesmo ``requestId`` da Engineering API. Correção só
 * edita os alvos devolvidos pelo analista (contrato REF-022); o backend
 * valida escopo de objeto, estado, versão e idempotência.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  PRC_ATTACHMENT_MAX_MB,
  PRC_ATTACHMENT_STATE_LABELS,
  PRC_FIELD_LABELS,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  addSupportFiles,
  prcFormatSize,
  prcTimelineItemViews,
  type PrcSupportFile,
} from "@delpi/plugin-ui/index";

import { AppShell } from "../../components/AppShell";
import {
  downloadPrcAttachment,
  fetchPrcAttachments,
  fetchPrcRequest,
  fetchPrcTimeline,
  resubmitPrcCorrection,
  savePrcReturnedFields,
  uploadPrcAttachment,
  type PrcAttachment,
  type PrcRequestDetail,
  type PrcTimelineEvent,
} from "./prcApi";
import { RequestHistoryTimeline } from "../../components/RequestHistoryTimeline";
import { useParticipantAvatarUrls } from "../../hooks/useParticipantAvatarUrls";
import {
  MyRequestsAttachmentPreviewStrip,
  MyRequestsFileDropzone,
  MyRequestsFormActions,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  MyRequestsStatusBadge,
  TextField,
} from "../../ui/mrUi";

type Props = {
  requestId: string;
  onBack: () => void;
};

export function PrcCasePage({ requestId, onBack }: Props) {
  const [detail, setDetail] = useState<PrcRequestDetail | null>(null);
  const [timeline, setTimeline] = useState<PrcTimelineEvent[]>([]);
  const [attachments, setAttachments] = useState<PrcAttachment[]>([]);
  const [canUpload, setCanUpload] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [changes, setChanges] = useState<
    Record<string, { value: string; reason: string; mode: "changed" | "confirmed" }>
  >({});
  const [newFiles, setNewFiles] = useState<PrcSupportFile[]>([]);
  const [fileError, setFileError] = useState("");

  const load = useCallback(() => {
    const ac = new AbortController();
    setError("");
    Promise.all([
      fetchPrcRequest(requestId, ac.signal),
      fetchPrcTimeline(requestId, ac.signal).catch(() => []),
      fetchPrcAttachments(requestId, ac.signal).catch(() => ({
        attachments: [],
        canUpload: false,
      })),
    ])
      .then(([d, t, a]) => {
        setDetail(d);
        setTimeline(t);
        setAttachments(a.attachments);
        setCanUpload(a.canUpload);
      })
      .catch((e: Error) => setError(e.message));
    return () => ac.abort();
  }, [requestId]);

  useEffect(() => load(), [load]);

  const historyViews = useMemo(() => prcTimelineItemViews(timeline), [timeline]);
  const avatarByUserId = useParticipantAvatarUrls(
    historyViews.map((v) => v.actorUserId),
  );

  const openTargets = useMemo(
    () => detail?.correctionExchange?.openReturn?.targets || [],
    [detail],
  );
  const canCorrect =
    detail?.status === "needs_correction" &&
    detail?.correctionExchange?.canCorrect === true;

  const saveAndResubmit = async () => {
    if (!detail || busy) return;
    setBusy(true);
    setError("");
    try {
      const payload = openTargets
        .filter((t) => t.targetPath)
        .map((t) => {
          const c = changes[t.targetPath!] || {
            value: "",
            reason: "",
            mode: "changed" as const,
          };
          return {
            path: t.targetPath!,
            proposedValue: c.value,
            reason: c.reason || "Correção do solicitante.",
            mode: c.mode,
          };
        });
      let version = detail.caseVersion;
      if (payload.length) {
        const saved = await savePrcReturnedFields(
          requestId,
          version,
          payload,
          `mr-save-${Date.now()}`,
        );
        version = saved.caseVersion;
      }
      await resubmitPrcCorrection(
        requestId,
        version,
        `mr-resub-${Date.now()}`,
      );
      setChanges({});
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const uploadNew = async () => {
    if (!detail || !newFiles.length || busy) return;
    setBusy(true);
    setFileError("");
    try {
      for (const entry of newFiles) {
        await uploadPrcAttachment(requestId, entry.file);
      }
      setNewFiles([]);
      load();
    } catch (e) {
      setFileError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const download = async (att: PrcAttachment) => {
    try {
      const blob = await downloadPrcAttachment(
        requestId,
        att.attachmentId,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = att.originalFileName;
      a.rel = "noopener";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  if (!detail && !error) {
    return (
      <AppShell title="Acompanhamento">
        <MyRequestsLoadingState message="Carregando solicitação…" />
      </AppShell>
    );
  }

  return (
    <AppShell title="Acompanhamento da solicitação">
      {error ? (
        <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
      ) : null}
      {detail ? (
        <>
          <MyRequestsSectionCard
            title={`${PRC_TYPE_LABELS[detail.requestType] || "Solicitação"} — ${detail.id.slice(0, 8)}`}
            hint={`Criada em ${new Date(detail.createdAt).toLocaleString("pt-BR")}`}
          >
            <MyRequestsStatusBadge
              label={PRC_STATUS_LABELS[detail.status] || detail.status}
              variant={
                detail.status === "completed"
                  ? "success"
                  : detail.status === "rejected"
                    ? "danger"
                    : detail.status === "needs_correction"
                      ? "warning"
                      : "info"
              }
            />
            {detail.officialCode ? (
              <p>Código oficial: {detail.officialCode}</p>
            ) : null}
          </MyRequestsSectionCard>

          {canCorrect ? (
            <MyRequestsSectionCard
              title="Correção solicitada pela Engenharia"
              hint="Ajuste somente os campos devolvidos e reenvie o mesmo chamado."
            >
              {detail.correctionExchange?.openReturn?.reason ? (
                <p>
                  <strong>Motivo:</strong>{" "}
                  {detail.correctionExchange.openReturn.reason}
                </p>
              ) : null}
              {openTargets
                .filter((t) => t.targetPath)
                .map((t) => {
                  const path = t.targetPath!;
                  const label = PRC_FIELD_LABELS[path] || path;
                  const entry = changes[path] || {
                    value: "",
                    reason: "",
                    mode: "changed" as const,
                  };
                  return (
                    <div key={path}>
                      <p>
                        <strong>{label}:</strong> {t.reason}
                      </p>
                      <TextField
                        label={`Novo valor — ${label}`}
                        value={entry.value}
                        onChange={(v) =>
                          setChanges((s) => ({
                            ...s,
                            [path]: {
                              ...entry,
                              value: v,
                              mode: "changed" as const,
                            },
                          }))
                        }
                      />
                      <TextField
                        label="Justificativa (opcional)"
                        value={entry.reason}
                        onChange={(v) =>
                          setChanges((s) => ({
                            ...s,
                            [path]: { ...entry, reason: v },
                          }))
                        }
                      />
                    </div>
                  );
                })}
              <MyRequestsFormActions>
                <ActionButton
                  variant="primary"
                  disabled={busy}
                  onClick={() => void saveAndResubmit()}
                >
                  Salvar correções e reenviar
                </ActionButton>
              </MyRequestsFormActions>
            </MyRequestsSectionCard>
          ) : null}

          <MyRequestsSectionCard title="Documentos">
            {attachments.length ? (
              <MyRequestsAttachmentPreviewStrip
                mode="preview"
                items={attachments.map((att) => ({
                  id: att.attachmentId,
                  fileName: att.originalFileName,
                  contentType: att.mediaType || null,
                  detail: `${prcFormatSize(att.sizeBytes || 0)} · ${
                    PRC_ATTACHMENT_STATE_LABELS[att.state] || att.state
                  }`,
                }))}
                onOpen={(item) => {
                  const att = attachments.find(
                    (a) => a.attachmentId === item.id,
                  );
                  if (att) void download(att);
                }}
              />
            ) : (
              <p>Nenhum documento anexado.</p>
            )}
            {canUpload ? (
              <>
                <MyRequestsFileDropzone
                  multiple
                  ariaLabel="Anexar documentos"
                  onFilesSelected={(list) => {
                    const { files, errors } = addSupportFiles(
                      newFiles,
                      Array.from(list ?? []),
                      10,
                    );
                    setNewFiles(files);
                    setFileError(Object.values(errors)[0] || "");
                  }}
                  labels={{
                    title: `Anexar documento (até ${PRC_ATTACHMENT_MAX_MB} MB)`,
                    hint: "PDF ou imagens",
                  }}
                />
                {newFiles.length ? (
                  <MyRequestsFormActions>
                    <ActionButton
                      variant="primary"
                      disabled={busy}
                      onClick={() => void uploadNew()}
                    >
                      Enviar {newFiles.length} documento(s)
                    </ActionButton>
                  </MyRequestsFormActions>
                ) : null}
                {fileError ? (
                  <MyRequestsStateBanner variant="error">
                    {fileError}
                  </MyRequestsStateBanner>
                ) : null}
              </>
            ) : null}
          </MyRequestsSectionCard>

          <MyRequestsSectionCard title="Linha do tempo">
            <RequestHistoryTimeline
              items={historyViews.map((v) => ({
                id: v.id,
                title: v.title,
                occurredAt: v.occurredAt,
                timeLabel: v.timeLabel,
                actorName: v.actorLabel || null,
                actorUserId: v.actorUserId,
                transition: v.transition,
                detailText: v.reasonText,
                metaText: v.metaText,
              }))}
              avatarByUserId={avatarByUserId}
            />
          </MyRequestsSectionCard>
        </>
      ) : null}
      <MyRequestsFormActions>
        <ActionButton variant="ghost" onClick={onBack}>
          Voltar
        </ActionButton>
      </MyRequestsFormActions>
    </AppShell>
  );
}
