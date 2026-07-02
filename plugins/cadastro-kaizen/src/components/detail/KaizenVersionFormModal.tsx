import { useState } from "react";
import { Save, X } from "lucide-react";

import { KaizenFormFields } from "../form/KaizenFormFields";
import { StateAlert } from "../StateAlert";
import { formValuesToPayload } from "../../constants/kaizen";
import type { KaizenFormValues } from "../../types/kaizen";

type Props = {
  title: string;
  subtitle?: string;
  initialValues: KaizenFormValues;
  submitLabel: string;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
  onClose: () => void;
};

export function KaizenVersionFormModal({
  title,
  subtitle,
  initialValues,
  submitLabel,
  onSubmit,
  onClose,
}: Props) {
  const [values, setValues] = useState<KaizenFormValues>(initialValues);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof KaizenFormValues>(key: K, value: KaizenFormValues[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = formValuesToPayload(values);
      if (!payload.title) {
        throw new Error("Informe o título do kaizen.");
      }
      await onSubmit(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar versão.");
      setSaving(false);
    }
  }

  return (
    <div className="kz-modal-overlay" role="dialog" aria-modal="true" aria-label={title}>
      <div className="kz-modal">
        <div className="kz-modal__header">
          <div>
            <h3 className="kz-modal__title">{title}</h3>
            {subtitle ? <p className="kz-modal__subtitle">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            className="kz-icon-btn"
            onClick={onClose}
            aria-label="Fechar"
            disabled={saving}
          >
            <X size={18} />
          </button>
        </div>

        <form className="kz-modal__body kz-form" onSubmit={(event) => void handleSubmit(event)}>
          {error ? <StateAlert variant="error">{error}</StateAlert> : null}
          <KaizenFormFields values={values} onChange={updateField} />
          <div className="kz-form-actions kz-modal__actions">
            <button type="submit" className="kz-primary-btn" disabled={saving}>
              <Save size={16} aria-hidden="true" />
              {saving ? "Salvando…" : submitLabel}
            </button>
            <button type="button" className="kz-ghost-btn" onClick={onClose} disabled={saving}>
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
