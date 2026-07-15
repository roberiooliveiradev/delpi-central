import { useEffect, useMemo, useState, type FormEvent } from "react";

import {
  createAdminDepartment,
  getAdminDepartment,
  updateAdminDepartment,
  type DepartmentPayload,
} from "../../api/guiasProcedimentosApi";
import { HttpRequestError } from "../../api/httpClient";
import { AdminShell } from "../../components/AdminShell";
import { DepartmentIconField } from "../../components/DepartmentIconField";
import { GuiasConfirmDialog } from "../../components/GuiasConfirmDialog";
import { slugify } from "../../utils/adminHelpers";
import { navigateGuiasProcedimentos } from "../../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../../utils/route";

type AdminDepartmentFormPageProps = {
  id?: string;
  standalone?: boolean;
};

const EMPTY: DepartmentPayload = {
  name: "",
  slug: "",
  description: "",
  icon: "book-open",
  active: true,
  order_index: 1,
};

export function AdminDepartmentFormPage({
  id,
  standalone = false,
}: AdminDepartmentFormPageProps) {
  const isEdit = Boolean(id);
  const [form, setForm] = useState<DepartmentPayload>(EMPTY);
  const [slugTouched, setSlugTouched] = useState(false);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    getAdminDepartment(id)
      .then((data) => {
        if (cancelled) return;
        setForm({
          name: data.name,
          slug: data.slug,
          description: data.description ?? "",
          icon: data.icon || "book-open",
          active: Boolean(data.active),
          order_index: data.order_index,
        });
        setSlugTouched(true);
        setDirty(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof HttpRequestError
            ? err.message
            : "Não foi possível carregar o departamento.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const canSubmit = useMemo(() => {
    return (
      form.name.trim().length >= 2 &&
      form.slug.trim().length >= 2 &&
      form.icon.trim().length > 0 &&
      !saving
    );
  }, [form, saving]);

  function patch(partial: Partial<DepartmentPayload>) {
    setForm((prev) => ({ ...prev, ...partial }));
    setDirty(true);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    setSaving(true);
    setError(null);
    const payload: DepartmentPayload = {
      ...form,
      name: form.name.trim(),
      slug: form.slug.trim(),
      description: form.description.trim(),
      icon: form.icon.trim(),
      order_index: Number(form.order_index) || 0,
    };
    try {
      if (isEdit && id) {
        await updateAdminDepartment(id, payload);
        sessionStorage.setItem("gp-admin-feedback", "Departamento atualizado.");
      } else {
        await createAdminDepartment(payload);
        sessionStorage.setItem("gp-admin-feedback", "Departamento criado.");
      }
      setDirty(false);
      navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminDepartments);
    } catch (err: unknown) {
      if (err instanceof HttpRequestError) {
        if (err.status === 409 || /slug/i.test(err.message)) {
          setError("Já existe um departamento com este slug.");
        } else if (err.status === 403) {
          setError("Acesso negado.");
        } else {
          setError(err.message || "Não foi possível salvar.");
        }
      } else {
        setError("Não foi possível salvar o departamento.");
      }
    } finally {
      setSaving(false);
    }
  }

  function onCancel() {
    if (dirty) {
      setLeaveOpen(true);
      return;
    }
    navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminDepartments);
  }

  return (
    <AdminShell
      title={isEdit ? "Editar departamento" : "Novo departamento"}
      standalone={standalone}
      backTo={GUIAS_PROCEDIMENTOS_ROUTES.adminDepartments}
      backLabel="Voltar à lista"
    >
      {loading ? <p className="gp-intro">Carregando…</p> : null}
      {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}

      {!loading ? (
        <form className="gp-form" onSubmit={onSubmit}>
          <label className="gp-field">
            <span>Nome</span>
            <input
              className="gp-input"
              value={form.name}
              required
              onChange={(event) => {
                const name = event.target.value;
                patch({
                  name,
                  ...(slugTouched ? {} : { slug: slugify(name) }),
                });
              }}
            />
          </label>

          <label className="gp-field">
            <span>Slug</span>
            <input
              className="gp-input"
              value={form.slug}
              required
              onChange={(event) => {
                setSlugTouched(true);
                patch({ slug: slugify(event.target.value) });
              }}
            />
          </label>

          <label className="gp-field">
            <span>Descrição</span>
            <textarea
              className="gp-textarea"
              rows={3}
              value={form.description}
              onChange={(event) => patch({ description: event.target.value })}
            />
          </label>

          <DepartmentIconField
            value={form.icon}
            disabled={saving}
            onChange={(icon) => patch({ icon })}
          />

          <label className="gp-field">
            <span>Ordem</span>
            <input
              className="gp-input"
              type="number"
              value={form.order_index}
              onChange={(event) =>
                patch({ order_index: Number(event.target.value) })
              }
            />
          </label>

          <label className="gp-field gp-field--checkbox">
            <input
              type="checkbox"
              checked={form.active}
              onChange={(event) => patch({ active: event.target.checked })}
            />
            <span>Departamento ativo</span>
          </label>

          <div className="gp-form-actions">
            <button
              type="button"
              className="gp-btn gp-btn--ghost"
              onClick={onCancel}
              disabled={saving}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="gp-btn gp-btn--secondary"
              disabled={!canSubmit}
            >
              {saving ? "Salvando…" : "Salvar"}
            </button>
          </div>
        </form>
      ) : null}

      <GuiasConfirmDialog
        open={leaveOpen}
        title="Sair sem salvar"
        message="Há alterações não salvas. Deseja sair?"
        confirmLabel="Sair"
        variant="danger"
        onCancel={() => setLeaveOpen(false)}
        onConfirm={() => {
          setLeaveOpen(false);
          navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminDepartments);
        }}
      />
    </AdminShell>
  );
}
