import { useEffect, useState } from "react";
import { Save } from "lucide-react";

import {
  createKaizenRecord,
  fetchKaizenRecord,
  updateKaizenRecord,
} from "../api/kaizenApi";
import { KaizenFormFields, KaizenFormProgress } from "../components/form";
import { KaizenPageHeader } from "../components/KaizenPageHeader";
import { FormActions, StateAlert } from "../components/ui";
import {
  emptyFormValues,
  formValuesToPayload,
  listPath,
  recordToFormValues,
} from "../constants/kaizen";
import type { KaizenFormValues } from "../types/kaizen";
import { validateKaizenFormStatusDates } from "../utils/validateKaizenStatusDates";
import { KZ_GHOST_BTN } from "../components/ui/ghostChrome";

type Props = {
  mode: "new" | "edit";
  recordId?: string;
  onNavigate: (path: string) => void;
  onCreated?: (id: string) => void;
};

export function KaizenFormPage({ mode, recordId, onNavigate, onCreated }: Props) {
  const [values, setValues] = useState<KaizenFormValues>(emptyFormValues);
  const [loading, setLoading] = useState(mode === "edit");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "edit" || !recordId) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchKaizenRecord(recordId)
      .then((record) => {
        if (!cancelled) setValues(recordToFormValues(record));
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Erro ao carregar kaizen.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [mode, recordId]);

  function updateField<K extends keyof KaizenFormValues>(key: K, value: KaizenFormValues[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = formValuesToPayload(values);
      if (!payload.title) {
        throw new Error("Informe o título do kaizen.");
      }
      const statusDateError = validateKaizenFormStatusDates(values);
      if (statusDateError) {
        throw new Error(statusDateError);
      }

      if (mode === "new") {
        const created = await createKaizenRecord(payload);
        if (onCreated && created?.id) {
          onCreated(created.id);
        } else {
          onNavigate(listPath());
        }
        return;
      }

      if (!recordId) {
        throw new Error("Identificador do kaizen não informado.");
      }

      await updateKaizenRecord(recordId, payload);
      setSuccess("Kaizen atualizado com sucesso.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar kaizen.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <StateAlert>Carregando formulário…</StateAlert>
    );
  }

  return (
    <>
      <KaizenPageHeader
        title={mode === "new" ? "Novo kaizen" : "Editar kaizen"}
        subtitle="Preencha os dados da melhoria contínua"
        showBack
        onBack={() => onNavigate(listPath())}
      />

      <form className="kz-form" onSubmit={(event) => void handleSubmit(event)}>
        {error ? <StateAlert variant="error">{error}</StateAlert> : null}
        {success ? <StateAlert variant="success">{success}</StateAlert> : null}

        <KaizenFormProgress values={values} />

        <KaizenFormFields values={values} onChange={updateField} />

        <FormActions>
          <button type="submit" className="kz-primary-btn" disabled={saving}>
            <Save size={16} aria-hidden="true" />
            {saving ? "Salvando…" : "Salvar"}
          </button>
          <button
            type="button"
            className={KZ_GHOST_BTN}
            onClick={() => onNavigate(listPath())}
          >
            Cancelar
          </button>
        </FormActions>
      </form>
    </>
  );
}
