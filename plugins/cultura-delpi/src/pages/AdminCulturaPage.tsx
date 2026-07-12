import { useEffect, useState, type FormEvent } from "react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { HttpRequestError } from "../api/httpClient";
import {
  getCulturaDelpiContent,
  updateCulturaDelpiContent,
} from "../api/culturaDelpiApi";
import {
  CULTURA_DELPI_ADMIN_SUBTITLE,
  CULTURA_DELPI_ADMIN_TITLE,
} from "../content/culturaDelpi";
import { CulturaNativeTextAreaControl } from "../components/culturaFormFields";
import type {
  CulturaDelpiContent,
  UpdateCulturaDelpiContentPayload,
} from "../types/culturaDelpi";

type FormState = UpdateCulturaDelpiContentPayload;

const EMPTY_FORM: FormState = {
  proposito: "",
  missao: "",
  visao: "",
  valores: [""],
};

function contentToForm(content: CulturaDelpiContent): FormState {
  const valores = content.valores.map((item) => item.trim()).filter(Boolean);
  return {
    proposito: content.proposito,
    missao: content.missao,
    visao: content.visao,
    valores: valores.length > 0 ? valores : [""],
  };
}

function formToPayload(form: FormState): UpdateCulturaDelpiContentPayload {
  return {
    proposito: form.proposito.trim(),
    missao: form.missao.trim(),
    visao: form.visao.trim(),
    valores: form.valores.map((item) => item.trim()).filter(Boolean),
  };
}

function formatUpdatedAt(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString("pt-BR");
}

export function AdminCulturaPage() {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [meta, setMeta] = useState<Pick<
    CulturaDelpiContent,
    "updatedAt" | "updatedByName"
  > | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function loadContent() {
      setLoading(true);
      setError(null);
      setForbidden(false);
      setSuccess(null);

      try {
        const data = await getCulturaDelpiContent(controller.signal);
        setForm(contentToForm(data));
        setMeta({
          updatedAt: data.updatedAt,
          updatedByName: data.updatedByName,
        });
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err instanceof HttpRequestError && err.status === 403) {
          setForbidden(true);
          setError("Acesso negado. É necessária a permissão cultura-delpi.manage.");
          return;
        }
        const message =
          err instanceof Error
            ? err.message
            : "Não foi possível carregar o conteúdo para edição.";
        setError(message);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadContent();

    return () => controller.abort();
  }, []);

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    setSuccess(null);
  }

  function updateValor(index: number, value: string) {
    setForm((current) => {
      const valores = [...current.valores];
      valores[index] = value;
      return { ...current, valores };
    });
    setSuccess(null);
  }

  function addValor() {
    setForm((current) => ({ ...current, valores: [...current.valores, ""] }));
    setSuccess(null);
  }

  function removeValor(index: number) {
    setForm((current) => {
      const valores = current.valores.filter((_, itemIndex) => itemIndex !== index);
      return { ...current, valores: valores.length > 0 ? valores : [""] };
    });
    setSuccess(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setForbidden(false);
    setSuccess(null);

    try {
      const data = await updateCulturaDelpiContent(formToPayload(form));
      setForm(contentToForm(data));
      setMeta({
        updatedAt: data.updatedAt,
        updatedByName: data.updatedByName,
      });
      setSuccess("Conteúdo salvo com sucesso.");
    } catch (err) {
      if (err instanceof HttpRequestError && err.status === 403) {
        setForbidden(true);
        setError("Acesso negado. É necessária a permissão cultura-delpi.manage.");
        return;
      }
      const message =
        err instanceof Error ? err.message : "Não foi possível salvar o conteúdo.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  const updatedAtLabel = meta ? formatUpdatedAt(meta.updatedAt) : null;

  return (
    <div className="cultura-delpi cultura-delpi-page cultura-delpi-admin">
      <header className="cultura-delpi__hero">
        <p className="cultura-delpi__eyebrow">Administração</p>
        <h1 className="cultura-delpi__title">{CULTURA_DELPI_ADMIN_TITLE}</h1>
        <p className="cultura-delpi__subtitle">{CULTURA_DELPI_ADMIN_SUBTITLE}</p>
      </header>

      {loading ? (
        <div className="cultura-delpi__state" role="status" aria-live="polite">
          <p>Carregando conteúdo para edição…</p>
        </div>
      ) : null}

      {!loading && error ? (
        <div
          className={`cultura-delpi__state ${forbidden ? "cultura-delpi__state--forbidden" : "cultura-delpi__state--error"}`}
          role="alert"
        >
          <p>{error}</p>
        </div>
      ) : null}

      {!loading && success ? (
        <div className="cultura-delpi__state cultura-delpi__state--success" role="status">
          <p>{success}</p>
        </div>
      ) : null}

      {!loading && !forbidden ? (
        <form className="cultura-delpi-admin__form" onSubmit={handleSubmit}>
          <section className="cultura-delpi-admin__section">
            <label className="cultura-delpi-admin__label" htmlFor="cultura-proposito">
              Propósito
            </label>
            <CulturaNativeTextAreaControl
              id="cultura-proposito"
              className="cultura-delpi-admin__textarea"
              rows={5}
              value={form.proposito}
              onChange={(value) => updateField("proposito", value)}
              disabled={saving}
            />
          </section>

          <section className="cultura-delpi-admin__section">
            <label className="cultura-delpi-admin__label" htmlFor="cultura-missao">
              Missão
            </label>
            <CulturaNativeTextAreaControl
              id="cultura-missao"
              className="cultura-delpi-admin__textarea"
              rows={5}
              value={form.missao}
              onChange={(value) => updateField("missao", value)}
              disabled={saving}
            />
          </section>

          <section className="cultura-delpi-admin__section">
            <label className="cultura-delpi-admin__label" htmlFor="cultura-visao">
              Visão
            </label>
            <CulturaNativeTextAreaControl
              id="cultura-visao"
              className="cultura-delpi-admin__textarea"
              rows={5}
              value={form.visao}
              onChange={(value) => updateField("visao", value)}
              disabled={saving}
            />
          </section>

          <section className="cultura-delpi-admin__section">
            <div className="cultura-delpi-admin__section-header">
              <h2 className="cultura-delpi-admin__section-title">Valores</h2>
              <button
                type="button"
                className="cultura-delpi-admin__secondary-button"
                onClick={addValor}
                disabled={saving}
              >
                Adicionar valor
              </button>
            </div>

            <div className="cultura-delpi-admin__values">
              {form.valores.map((valor, index) => (
                <div key={`valor-${index}`} className="cultura-delpi-admin__value-row">
                  <NativeTextControl
                    type="text"
                    className="cultura-delpi-admin__input"
                    value={valor}
                    placeholder={`Valor ${index + 1}`}
                    onChange={(value) => updateValor(index, value)}
                    disabled={saving}
                    aria-label={`Valor ${index + 1}`}
                  />
                  <button
                    type="button"
                    className="cultura-delpi-admin__icon-button"
                    onClick={() => removeValor(index)}
                    disabled={saving || form.valores.length === 1}
                    aria-label={`Remover valor ${index + 1}`}
                  >
                    Remover
                  </button>
                </div>
              ))}
            </div>
          </section>

          {updatedAtLabel ? (
            <p className="cultura-delpi-admin__meta">
              Última atualização: {updatedAtLabel}
              {meta?.updatedByName ? ` — ${meta.updatedByName}` : ""}
            </p>
          ) : null}

          <div className="cultura-delpi-admin__actions">
            <button
              type="submit"
              className="cultura-delpi-admin__primary-button"
              disabled={saving}
            >
              {saving ? "Salvando…" : "Salvar conteúdo"}
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
