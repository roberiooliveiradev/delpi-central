import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  closeAudit,
  completeNcAction,
  createNonconformity,
  fetchAuditNcAttachments,
  fetchNcCandidates,
  fetchNonconformities,
  updateNonconformity,
  uploadNcAttachment,
  type AuditDetail,
  type NcAttachmentMap,
  type NcAttachmentType,
  type Nonconformity,
} from "../api/audit5sApi";
import { isAuditClosed } from "../constants/audit5s";
import { AuditNcItemCard } from "./AuditNcItemCard";
import {
  buildNcTreatmentItems,
  canCreateNc,
  computeNcTreatmentStats,
  emptyNcForm,
  formFromNonconformity,
  formsEqual,
  normalizeOptionalText,
  type NcFormState,
  type NcTreatmentItem,
} from "../utils/auditNc";
import { groupAttachmentsByResponse } from "../utils/ncAttachments";

type Props = {
  audit: AuditDetail;
  onAuditUpdated: (audit: AuditDetail) => void;
  onClosed: () => void;
  onStatsChange?: (stats: ReturnType<typeof computeNcTreatmentStats>) => void;
  onLastSavedChange?: (timestamp: number) => void;
  closeSignal?: number;
};

export function AuditNcPanel({
  audit,
  onAuditUpdated,
  onClosed,
  onStatsChange,
  onLastSavedChange,
  closeSignal = 0,
}: Props) {
  const [items, setItems] = useState<NcTreatmentItem[]>([]);
  const [forms, setForms] = useState<Record<string, NcFormState>>({});
  const [attachmentsByNcId, setAttachmentsByNcId] = useState<NcAttachmentMap>({});
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingIds, setSavingIds] = useState<Set<string>>(new Set());
  const [savedFlashIds, setSavedFlashIds] = useState<Set<string>>(new Set());
  const [finalizingIds, setFinalizingIds] = useState<Set<string>>(new Set());
  const [uploadingByResponse, setUploadingByResponse] = useState<
    Record<string, NcAttachmentType | null>
  >({});
  const persistedFormsRef = useRef<Record<string, NcFormState>>({});

  const readOnly = isAuditClosed(audit.status);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [candidateItems, ncItems, attachmentItems] = await Promise.all([
        fetchNcCandidates(audit.id),
        fetchNonconformities(audit.id),
        fetchAuditNcAttachments(audit.id),
      ]);
      const nextItems = buildNcTreatmentItems(candidateItems, ncItems);
      setItems(nextItems);
      setAttachmentsByNcId(groupAttachmentsByResponse(attachmentItems));

      const nextForms: Record<string, NcFormState> = {};
      for (const item of nextItems) {
        nextForms[item.responseId] = item.nc
          ? formFromNonconformity(item.nc)
          : emptyNcForm();
      }
      setForms(nextForms);
      persistedFormsRef.current = nextForms;

      setExpandedIds((prev) => {
        if (prev.size > 0) return prev;
        const firstPending = nextItems.find((item) => item.nc?.status !== "closed")?.responseId;
        return new Set(
          firstPending ? [firstPending] : nextItems.slice(0, 1).map((item) => item.responseId),
        );
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar não conformidades.");
    } finally {
      setLoading(false);
    }
  }, [audit.id]);

  useEffect(() => {
    void load();
  }, [load]);

  const stats = useMemo(() => computeNcTreatmentStats(items, forms), [items, forms]);

  useEffect(() => {
    onStatsChange?.(stats);
  }, [onStatsChange, stats]);

  const upsertItemNc = (responseId: string, nc: Nonconformity) => {
    setItems((prev) =>
      prev.map((item) => (item.responseId === responseId ? { ...item, nc } : item)),
    );
    const nextForm = formFromNonconformity(nc);
    setForms((prev) => ({ ...prev, [responseId]: nextForm }));
    persistedFormsRef.current = { ...persistedFormsRef.current, [responseId]: nextForm };
  };

  const flashSaved = (responseId: string) => {
    setSavedFlashIds((prev) => new Set(prev).add(responseId));
    window.setTimeout(() => {
      setSavedFlashIds((prev) => {
        const next = new Set(prev);
        next.delete(responseId);
        return next;
      });
    }, 1800);
  };

  const handleSave = async (
    responseId: string,
    override?: Partial<NcFormState>,
  ) => {
    if (readOnly) return;

    const item = items.find((entry) => entry.responseId === responseId);
    const baseForm = forms[responseId];
    if (!item || !baseForm) return;

    const form: NcFormState = { ...baseForm, ...override };
    if (override) {
      setForms((prev) => ({ ...prev, [responseId]: form }));
    }

    const persisted = persistedFormsRef.current[responseId];
    if (!persisted || formsEqual(form, persisted)) {
      return;
    }
    if (item.nc?.status === "closed") return;

    setSavingIds((prev) => new Set(prev).add(responseId));
    setError(null);

    try {
      if (!item.nc) {
        if (!canCreateNc(form)) {
          return;
        }

        const created = await createNonconformity(audit.id, {
          response_id: responseId,
          description: form.description.trim(),
          responsible_name: form.responsible_name.trim(),
          responsible_user_id: form.responsible_user_id,
          due_date: form.due_date,
          root_cause: normalizeOptionalText(form.root_cause),
          corrective_action: normalizeOptionalText(form.corrective_action),
          priority: form.priority || null,
        });

        upsertItemNc(responseId, created);
        onAuditUpdated({ ...audit, status: "nc_in_progress" });
        try {
          const attachmentItems = await fetchAuditNcAttachments(audit.id);
          setAttachmentsByNcId(groupAttachmentsByResponse(attachmentItems));
        } catch {
          // Plano já salvo; anexos podem ser atualizados no próximo refresh.
        }
      } else {
        if (!form.responsible_name.trim() || !form.responsible_user_id?.trim()) {
          setForms((prev) => ({ ...prev, [responseId]: form }));
          return;
        }

        const updated = await updateNonconformity(item.nc.id, {
          description: form.description.trim(),
          root_cause: normalizeOptionalText(form.root_cause),
          corrective_action: normalizeOptionalText(form.corrective_action),
          responsible_name: form.responsible_name.trim(),
          responsible_user_id: form.responsible_user_id,
          due_date: form.due_date,
          priority: form.priority || null,
        });
        upsertItemNc(responseId, { ...item.nc, ...updated });
      }

      onLastSavedChange?.(Date.now());
      flashSaved(responseId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar não conformidade.");
    } finally {
      setSavingIds((prev) => {
        const next = new Set(prev);
        next.delete(responseId);
        return next;
      });
    }
  };

  const handleUpload = async (responseId: string, type: NcAttachmentType, file: File) => {
    const item = items.find((entry) => entry.responseId === responseId);
    if (!item?.nc) {
      throw new Error("Salve o plano da NC antes de anexar evidências.");
    }

    setUploadingByResponse((prev) => ({ ...prev, [responseId]: type }));
    setError(null);
    try {
      const attachment = await uploadNcAttachment(item.nc.id, type, file);
      setAttachmentsByNcId((prev) => ({
        ...prev,
        [item.nc!.id]: {
          ...(prev[item.nc!.id] ?? {}),
          [type]: attachment,
        },
      }));
      onLastSavedChange?.(Date.now());
    } finally {
      setUploadingByResponse((prev) => ({ ...prev, [responseId]: null }));
    }
  };

  const handleFinalize = async (responseId: string) => {
    const item = items.find((entry) => entry.responseId === responseId);
    if (!item?.nc) return;

    setFinalizingIds((prev) => new Set(prev).add(responseId));
    setError(null);
    try {
      const finalized = await completeNcAction(item.nc.id);
      upsertItemNc(responseId, finalized);
      onAuditUpdated({ ...audit, status: "nc_in_progress" });
      onLastSavedChange?.(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao finalizar ação.");
    } finally {
      setFinalizingIds((prev) => {
        const next = new Set(prev);
        next.delete(responseId);
        return next;
      });
    }
  };

  const handleClose = async () => {
    setError(null);
    try {
      const closed = await closeAudit(audit.id);
      onAuditUpdated(closed);
      onClosed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao concluir tratamento.");
    }
  };

  useEffect(() => {
    if (closeSignal <= 0) return;
    void handleClose();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [closeSignal]);

  if (loading) {
    return <p className="a5s-nc-loading">Carregando não conformidades...</p>;
  }

  if (items.length === 0) {
    return (
      <div className="a5s-nc-panel">
        <div className="a5s-alert a5s-alert--success">
          Nenhum critério abaixo da nota máxima. Você pode concluir o tratamento desta auditoria.
        </div>
        {!readOnly ? (
          <div className="a5s-panel__actions">
            <button type="button" className="a5s-btn" onClick={() => void handleClose()}>
              Concluir tratamento
            </button>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="a5s-nc-panel">
      {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}

      <div className="a5s-nc-panel__head">
        <h2>Não conformidades a tratar ({items.length})</h2>
        <p className="a5s-nc-panel__intro">
          1) Registre o plano · 2) Anexe fotos do antes e depois · 3) Finalize cada ação · 4)
          Conclua o tratamento da auditoria
        </p>
      </div>

      <div className="a5s-nc-panel__list">
        {items.map((item) => (
          <AuditNcItemCard
            key={item.responseId}
            auditId={audit.id}
            item={item}
            form={forms[item.responseId] ?? emptyNcForm()}
            attachmentsByNcId={attachmentsByNcId}
            disabled={readOnly}
            expanded={expandedIds.has(item.responseId)}
            saving={savingIds.has(item.responseId)}
            savedFlash={savedFlashIds.has(item.responseId)}
            finalizing={finalizingIds.has(item.responseId)}
            uploadingType={uploadingByResponse[item.responseId] ?? null}
            onToggle={() =>
              setExpandedIds((prev) => {
                const next = new Set(prev);
                if (next.has(item.responseId)) {
                  next.delete(item.responseId);
                } else {
                  next.add(item.responseId);
                }
                return next;
              })
            }
            onChange={(patch) =>
              setForms((prev) => ({
                ...prev,
                [item.responseId]: { ...(prev[item.responseId] ?? emptyNcForm()), ...patch },
              }))
            }
            onBlurSave={(patch) => {
              void handleSave(item.responseId, patch);
            }}
            onUpload={(type, file) => handleUpload(item.responseId, type, file)}
            onFinalize={() => {
              void handleFinalize(item.responseId);
            }}
          />
        ))}
      </div>

      {!readOnly && stats.pending > 0 ? (
        <p className="a5s-nc-panel__hint">
          Finalize todas as ações com evidências (foto do antes e depois) para concluir o
          tratamento da auditoria.
        </p>
      ) : null}
    </div>
  );
}
