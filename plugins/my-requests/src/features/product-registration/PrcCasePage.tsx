/** PRC-REF-023-F04/UI-FIX-07 — acompanhamento do caso PRC pelo
 * solicitante.
 *
 * Hero consolidado + duas abas (Ficha técnica · Histórico) sobre o
 * mesmo ``requestId`` da Engineering API. A ficha técnica é a
 * composição única `PrcTechnicalSheetView` do kit — mesma leitura do
 * Portal Engenharia — e os documentos de apoio vivem dentro dela.
 * Correção só edita os alvos devolvidos pelo analista (REF-022),
 * contextual na própria ficha; o backend valida escopo de objeto,
 * estado, versão e idempotência. */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  PRC_ATTACHMENT_MAX_MB,
  PRC_ATTACHMENT_STATE_LABELS,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  PrcRequestForm,
  PrcReturnedFieldsEditor,
  PrcTechnicalSheetView,
  PrcWorkflowProgress,
  addSupportFiles,
  prcFormatSize,
  prcRequesterLabel,
  prcTimelineItemViews,
  type PrcFieldSpec,
  type PrcFormDataProvider,
  type PrcReturnedFieldChange,
  type PrcSupportFile,
} from "@delpi/plugin-ui/index";

import { AppShell } from "../../components/AppShell";
import {
  downloadPrcAttachment,
  fetchPrcAttachments,
  fetchPrcCatalog,
  fetchPrcEditContext,
  fetchPrcReferenceData,
  fetchPrcRequest,
  fetchPrcTimeline,
  prcIntakeSubmit,
  resubmitPrcCorrection,
  savePrcReturnedFields,
  searchPrcSuppliers,
  updatePrcDraft,
  uploadPrcAttachment,
  type PrcAttachment,
  type PrcRequestDetail,
  type PrcTimelineEvent,
} from "./prcApi";
import { RequestHistoryTimeline } from "../../components/RequestHistoryTimeline";
import { useParticipantAvatarUrls } from "../../hooks/useParticipantAvatarUrls";
import {
  DetailFields,
  MR_PORTAL_SCOPE,
  MyRequestsAttachmentPreviewStrip,
  MyRequestsFileDropzone,
  MyRequestsFormActions,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  MyRequestsStatusBadge,
  MyRequestsUnderlineNav,
} from "../../ui/mrUi";

type Props = {
  requestId: string;
  onBack: () => void;
};

type CaseTab = "sheet" | "history";

const CASE_TABS: { key: CaseTab; label: string }[] = [
  { key: "sheet", label: "Ficha técnica" },
  { key: "history", label: "Histórico" },
];

const PRC_SOURCE = "my-requests";

export function PrcCasePage({ requestId, onBack }: Props) {
  const [detail, setDetail] = useState<PrcRequestDetail | null>(null);
  const [timeline, setTimeline] = useState<PrcTimelineEvent[]>([]);
  const [attachments, setAttachments] = useState<PrcAttachment[]>([]);
  const [canUpload, setCanUpload] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<CaseTab>("sheet");
  const [newFiles, setNewFiles] = useState<PrcSupportFile[]>([]);
  const [fileError, setFileError] = useState("");
  /* FIX-08 — edição livre pré-atendimento: o backend só emite
   * `edit_draft` ao criador em ``submitted`` (allowedActions). */
  const [editing, setEditing] = useState(false);
  /* CORRECTION-09 — specs dos campos para o editor granular usar os
   * controles oficiais (select de catálogo, nunca caixa genérica). */
  const [fieldSpecs, setFieldSpecs] = useState<PrcFieldSpec[]>([]);

  const dataProvider = useMemo<PrcFormDataProvider>(
    () => ({
      fetchReferenceData: (signal) => fetchPrcReferenceData(signal),
      fetchCatalog: (kind, query, signal, limit) =>
        fetchPrcCatalog(kind, query, signal, limit).then((data) => ({
          data,
        })),
      searchSuppliers: searchPrcSuppliers,
      fetchEditContext: fetchPrcEditContext,
      submitIntake: (body, idempotencyKey) =>
        prcIntakeSubmit(body, idempotencyKey).then((result) => ({
          requestId: result.requestId,
        })),
      uploadAttachment: (caseId, file) =>
        uploadPrcAttachment(caseId, file).then(() => undefined),
      saveDraft: (caseId, expectedVersion, changes, idempotencyKey) =>
        updatePrcDraft(
          caseId,
          expectedVersion,
          changes,
          idempotencyKey,
        ).then(() => undefined),
    }),
    [],
  );

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

  /* CORRECTION-09 — specs carregados sob demanda: o editor granular
   * usa os controles oficiais (enum vira select) por campo devolvido. */
  useEffect(() => {
    if (!canCorrect || fieldSpecs.length) return;
    const ac = new AbortController();
    fetchPrcReferenceData(ac.signal)
      .then((ref) => setFieldSpecs(ref.fields || []))
      .catch(() => setFieldSpecs([]));
    return () => ac.abort();
  }, [canCorrect, fieldSpecs.length]);

  /** Reenvio do mesmo requestId: PATCH /returned-fields (CAS +
   * idempotência) e depois POST resubmit-correction. O editor
   * compartilhado já cobre todos os alvos (changed/confirmed) —
   * o backend revalida a allowlist granular por vínculo+atributo. */
  const saveAndResubmit = async (changes: PrcReturnedFieldChange[]) => {
    if (!detail || busy || !changes.length) return;
    setBusy(true);
    setError("");
    try {
      const saved = await savePrcReturnedFields(
        requestId,
        detail.caseVersion,
        changes,
        `mr-save-${Date.now()}`,
      );
      await resubmitPrcCorrection(
        requestId,
        saved.caseVersion,
        `mr-resub-${Date.now()}`,
      );
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

  /* FIX-08 — modo de edição do caso enviado: mesmo wizard
   * compartilhado, sem etapa de identificação; salva PATCH /draft
   * com CAS + idempotência no mesmo requestId. */
  if (editing && detail) {
    return (
      <AppShell title="Editar solicitação">
        <PrcRequestForm
          source={PRC_SOURCE}
          dataProvider={dataProvider}
          portalScopeClassName={MR_PORTAL_SCOPE}
          editCase={{
            requestId,
            expectedVersion: detail.caseVersion,
            requestType:
              detail.requestType === "update" ? "update" : "create",
            draft: detail.technicalDraft || {},
            changedPaths: detail.changedPaths || [],
          }}
          onCancel={() => setEditing(false)}
          onCompleted={() => {
            setEditing(false);
            load();
          }}
        />
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
            hint="Acompanhamento do caso PRC na Engineering API."
            actions={
              <>
                {detail.allowedActions?.includes("edit_draft") ? (
                  <ActionButton
                    variant="ghost"
                    onClick={() => setEditing(true)}
                  >
                    Editar solicitação
                  </ActionButton>
                ) : null}
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
              </>
            }
          >
            <DetailFields
              fields={[
                {
                  label: "Código oficial",
                  value: detail.officialCode || "Aguardando cadastro",
                },
                {
                  label: "Solicitante",
                  value: prcRequesterLabel(detail.requester),
                },
                {
                  label: "Abertura",
                  value: new Date(detail.createdAt).toLocaleString("pt-BR"),
                },
                {
                  label: "Última atualização",
                  value: detail.updatedAt
                    ? new Date(detail.updatedAt).toLocaleString("pt-BR")
                    : "—",
                },
              ]}
            />
            <PrcWorkflowProgress status={detail.status} />
          </MyRequestsSectionCard>

          <MyRequestsUnderlineNav
            mode="tabs"
            aria-label="Seções do acompanhamento"
            activeId={tab}
            items={CASE_TABS.map((t) => ({
              id: t.key,
              label: t.label,
              controlId: `prc-case-panel-${t.key}`,
              tabId: `prc-case-tab-${t.key}`,
              onSelect: () => setTab(t.key),
            }))}
          />

          <div
            role="tabpanel"
            id={`prc-case-panel-${tab}`}
            aria-labelledby={`prc-case-tab-${tab}`}
            className="delpi-prc"
          >
            {tab === "sheet" ? (
              <>
                {canCorrect ? (
                  <MyRequestsSectionCard
                    title="Corrigir campos devolvidos"
                    hint="Apenas os campos indicados pela Engenharia podem ser modificados."
                  >
                    {detail.correctionExchange?.openReturn?.reason ? (
                      <p>
                        <strong>Motivo:</strong>{" "}
                        {detail.correctionExchange.openReturn.reason}
                      </p>
                    ) : null}
                    <PrcReturnedFieldsEditor
                      targets={openTargets}
                      fieldSpecs={fieldSpecs}
                      draft={detail.technicalDraft || {}}
                      busy={busy}
                      idPrefix="mr-prc-correct"
                      onSubmit={(changes) => void saveAndResubmit(changes)}
                    />
                  </MyRequestsSectionCard>
                ) : null}

                <PrcTechnicalSheetView
                  draft={detail.technicalDraft}
                  changedPaths={detail.changedPaths || []}
                  baselineFields={detail.officialBaseline?.fields || null}
                />

                <MyRequestsSectionCard title="Documentos de apoio">
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
              </>
            ) : null}

            {tab === "history" ? (
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
            ) : null}
          </div>
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
