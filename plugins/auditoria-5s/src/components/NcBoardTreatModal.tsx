import { useCallback, useEffect, useRef, useState } from "react";
import { ClipboardList, X } from "lucide-react";

import {
  completeNcAction,
  createNonconformity,
  fetchAuditNcAttachments,
  fetchNcCandidates,
  updateNonconformity,
  uploadNcAttachment,
  type NcAttachmentMap,
  type NcAttachmentType,
  type Nonconformity,
} from "../api/audit5sApi";
import { shiftLabel } from "../constants/audit5s";
import type { NcBoardItem } from "../types/ncManagement";
import {
  canCreateNc,
  formFromNonconformity,
  formsEqual,
  normalizeOptionalText,
  type NcFormState,
  type NcTreatmentItem,
} from "../utils/auditNc";
import {
  buildBoardTreatmentItem,
  formFromNcBoardItem,
} from "../utils/ncBoardTreat";
import { groupAttachmentsByResponse } from "../utils/ncAttachments";
import { formatDisplayDate } from "../utils/dates";
import { AuditNcItemEditor } from "./AuditNcItemEditor";

type Props = {
  item: NcBoardItem | null;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
};

export function NcBoardTreatModal({ item, open, onClose, onSaved }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [treatmentItem, setTreatmentItem] = useState<NcTreatmentItem | null>(null);
  const [form, setForm] = useState<NcFormState | null>(null);
  const [attachmentsByNcId, setAttachmentsByNcId] = useState<NcAttachmentMap>({});
  const [saving, setSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [uploadingType, setUploadingType] = useState<NcAttachmentType | null>(null);
  const persistedFormRef = useRef<NcFormState | null>(null);
  const readOnly = item?.status === "closed" || item?.status === "cancelled";

  const loadContext = useCallback(async (boardItem: NcBoardItem) => {
    setLoading(true);
    setError(null);
    try {
      const [candidates, attachmentItems] = await Promise.all([
        fetchNcCandidates(boardItem.audit_id),
        boardItem.is_registered ? fetchAuditNcAttachments(boardItem.audit_id) : Promise.resolve([]),
      ]);

      const candidate =
        candidates.find((entry) => entry.response.id === boardItem.response_id) ?? null;
      const nextItem = buildBoardTreatmentItem(boardItem, candidate);
      const nextForm = formFromNcBoardItem(boardItem);

      setTreatmentItem(nextItem);
      setForm(nextForm);
      persistedFormRef.current = nextForm;
      setAttachmentsByNcId(groupAttachmentsByResponse(attachmentItems));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar plano de ação.");
      setTreatmentItem(null);
      setForm(null);
      persistedFormRef.current = null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open || !item) {
      setTreatmentItem(null);
      setForm(null);
      setError(null);
      setSavedFlash(false);
      persistedFormRef.current = null;
      return;
    }

    void loadContext(item);
  }, [item, open, loadContext]);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  const flashSaved = () => {
    setSavedFlash(true);
    window.setTimeout(() => setSavedFlash(false), 1800);
  };

  const upsertNc = (nc: Nonconformity) => {
    setTreatmentItem((prev) => (prev ? { ...prev, nc } : prev));
    const nextForm = formFromNonconformity(nc);
    setForm(nextForm);
    persistedFormRef.current = nextForm;
  };

  const handleSave = async (override?: Partial<NcFormState>) => {
    if (!item || !treatmentItem || !form || readOnly) return;

    const currentForm: NcFormState = { ...form, ...override };
    if (override) {
      setForm(currentForm);
    }

    const persisted = persistedFormRef.current;
    if (!persisted || formsEqual(currentForm, persisted)) return;
    if (treatmentItem.nc?.status === "closed") return;

    setSaving(true);
    setError(null);

    try {
      if (!treatmentItem.nc) {
        if (!canCreateNc(currentForm)) return;

        const created = await createNonconformity(item.audit_id, {
          response_id: treatmentItem.responseId,
          description: currentForm.description.trim(),
          responsible_name: currentForm.responsible_name.trim(),
          responsible_user_id: currentForm.responsible_user_id,
          due_date: currentForm.due_date,
          root_cause: normalizeOptionalText(currentForm.root_cause),
          corrective_action: normalizeOptionalText(currentForm.corrective_action),
          priority: currentForm.priority || null,
        });

        upsertNc(created);
        try {
          const attachmentItems = await fetchAuditNcAttachments(item.audit_id);
          setAttachmentsByNcId(groupAttachmentsByResponse(attachmentItems));
        } catch {
          // Plano salvo; anexos podem ser recarregados depois.
        }
      } else {
        if (!currentForm.responsible_name.trim() || !currentForm.responsible_user_id?.trim()) {
          // Evita PATCH inválido ao limpar responsável; só persiste seleção completa.
          setForm(currentForm);
          return;
        }

        const updated = await updateNonconformity(treatmentItem.nc.id, {
          description: currentForm.description.trim(),
          root_cause: normalizeOptionalText(currentForm.root_cause),
          corrective_action: normalizeOptionalText(currentForm.corrective_action),
          responsible_name: currentForm.responsible_name.trim(),
          responsible_user_id: currentForm.responsible_user_id,
          due_date: currentForm.due_date,
          priority: currentForm.priority || null,
        });
        upsertNc({ ...treatmentItem.nc, ...updated });
      }

      flashSaved();
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar não conformidade.");
    } finally {
      setSaving(false);
    }
  };

  const handleUpload = async (type: NcAttachmentType, file: File) => {
    if (!item || !treatmentItem?.nc) {
      throw new Error("Salve o plano da NC antes de anexar evidências.");
    }

    setUploadingType(type);
    setError(null);
    try {
      const attachment = await uploadNcAttachment(treatmentItem.nc.id, type, file);
      setAttachmentsByNcId((prev) => ({
        ...prev,
        [treatmentItem.nc!.id]: {
          ...(prev[treatmentItem.nc!.id] ?? {}),
          [type]: attachment,
        },
      }));
      onSaved();
    } finally {
      setUploadingType(null);
    }
  };

  const handleFinalize = async () => {
    if (!treatmentItem?.nc) return;

    setFinalizing(true);
    setError(null);
    try {
      const finalized = await completeNcAction(treatmentItem.nc.id);
      upsertNc(finalized);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao finalizar ação.");
    } finally {
      setFinalizing(false);
    }
  };

  if (!open || !item) return null;

  const modalTitle = item.is_registered
    ? "Editar plano de ação"
    : "Registrar plano de ação";

  return (
    <div className="a5s-confirm-overlay" role="presentation" onClick={onClose}>
      <div
        className="a5s-nc-board-treat-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="a5s-nc-board-treat-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="a5s-nc-board-treat-dialog__head">
          <div className="a5s-nc-board-treat-dialog__title-wrap">
            <ClipboardList size={20} aria-hidden />
            <div>
              <h2 id="a5s-nc-board-treat-title">{modalTitle}</h2>
              <p className="a5s-nc-board-treat-dialog__meta">
                {item.audit_code} · {item.area_name} · {shiftLabel(item.shift)} ·{" "}
                {formatDisplayDate(item.audit_date)}
              </p>
            </div>
          </div>
          <button
            type="button"
            className="a5s-nc-board-treat-dialog__close"
            aria-label="Fechar"
            onClick={onClose}
          >
            <X size={18} aria-hidden />
          </button>
        </header>

        <div className="a5s-nc-board-treat-dialog__body">
          <p className="a5s-nc-board-treat-dialog__criterion">{item.criterion_description}</p>

          {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}

          {loading ? (
            <p className="a5s-nc-board-treat-dialog__loading">Carregando plano de ação…</p>
          ) : treatmentItem && form ? (
            <AuditNcItemEditor
              auditId={item.audit_id}
              item={treatmentItem}
              form={form}
              attachmentsByNcId={attachmentsByNcId}
              disabled={readOnly}
              saving={saving}
              savedFlash={savedFlash}
              finalizing={finalizing}
              uploadingType={uploadingType}
              onChange={(patch) => setForm((prev) => (prev ? { ...prev, ...patch } : prev))}
              onBlurSave={(patch) => {
                void handleSave(patch);
              }}
              onUpload={handleUpload}
              onFinalize={() => {
                void handleFinalize();
              }}
            />
          ) : null}
        </div>

        <footer className="a5s-nc-board-treat-dialog__actions">
          <button type="button" className="a5s-btn a5s-btn--ghost" onClick={onClose}>
            Fechar
          </button>
        </footer>
      </div>
    </div>
  );
}
