import { useEffect, useMemo, useState, type FormEvent } from "react";

import {
  archiveAdminProcedure,
  createAdminProcedure,
  getAdminProcedure,
  listAdminDepartments,
  publishAdminProcedure,
  restoreAdminProcedure,
  unpublishAdminProcedure,
  updateAdminProcedure,
  type ApiAdminDepartment,
  type ApiAdminProcedureDetail,
  type ProcedurePayload,
  type ProcedureStatus,
} from "../../api/guiasProcedimentosApi";
import { HttpRequestError } from "../../api/httpClient";
import { AdminShell } from "../../components/AdminShell";
import { GuiasConfirmDialog } from "../../components/GuiasConfirmDialog";
import { HtmlEditorWithPreview } from "../../components/HtmlEditorWithPreview";
import { ProcedureAttachmentsManager } from "../../components/ProcedureAttachmentsManager";
import { ProcedureMediaManager } from "../../components/ProcedureMediaManager";
import { SanitizedArticleContent } from "../../components/SanitizedArticleContent";
import { slugify, statusLabel } from "../../utils/adminHelpers";
import { navigateGuiasProcedimentos } from "../../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../../utils/route";

type AdminProcedureFormPageProps = {
  id?: string;
  standalone?: boolean;
};

type ConfirmKind = "publish" | "unpublish" | "archive" | "restore" | "leave";
type FormTab = "content" | "media" | "attachments" | "preview";

const EMPTY: ProcedurePayload = {
  department_id: "",
  title: "",
  slug: "",
  summary: "",
  content_html: "",
  reading_time_minutes: 5,
  order_index: 1,
};

const TABS: { id: FormTab; label: string }[] = [
  { id: "content", label: "Conteúdo" },
  { id: "media", label: "Mídias" },
  { id: "attachments", label: "Anexos" },
  { id: "preview", label: "Prévia" },
];

export function AdminProcedureFormPage({
  id,
  standalone = false,
}: AdminProcedureFormPageProps) {
  const isEdit = Boolean(id);
  const [departments, setDepartments] = useState<ApiAdminDepartment[]>([]);
  const [form, setForm] = useState<ProcedurePayload>(EMPTY);
  const [status, setStatus] = useState<ProcedureStatus>("draft");
  const [slugTouched, setSlugTouched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [confirm, setConfirm] = useState<ConfirmKind | null>(null);
  const [actionBusy, setActionBusy] = useState(false);
  const [tab, setTab] = useState<FormTab>("content");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const load = async () => {
      try {
        const deps = await listAdminDepartments();
        if (cancelled) return;
        setDepartments(deps);
        if (id) {
          const procedure = await getAdminProcedure(id);
          if (cancelled) return;
          applyProcedure(procedure);
        } else if (deps[0]) {
          setForm((prev) => ({ ...prev, department_id: deps[0].id }));
        }
        setError(null);
      } catch (err: unknown) {
        if (cancelled) return;
        setError(
          err instanceof HttpRequestError
            ? err.message
            : "Não foi possível carregar o formulário.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  function applyProcedure(procedure: ApiAdminProcedureDetail) {
    setForm({
      department_id: procedure.department.id,
      title: procedure.title,
      slug: procedure.slug,
      summary: procedure.summary,
      content_html: procedure.content_html,
      reading_time_minutes: procedure.reading_time_minutes,
      order_index: procedure.order_index,
    });
    setStatus(procedure.status);
    setSlugTouched(true);
    setDirty(false);
  }

  function patch(partial: Partial<ProcedurePayload>) {
    setForm((prev) => ({ ...prev, ...partial }));
    setDirty(true);
  }

  const canSubmit = useMemo(() => {
    return (
      form.title.trim().length >= 2 &&
      form.slug.trim().length >= 2 &&
      form.summary.trim().length >= 2 &&
      form.department_id.trim().length > 0 &&
      form.content_html.trim().length > 0 &&
      !saving
    );
  }, [form, saving]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    setSaving(true);
    setError(null);
    const payload: ProcedurePayload = {
      ...form,
      title: form.title.trim(),
      slug: form.slug.trim(),
      summary: form.summary.trim(),
      content_html: form.content_html,
      reading_time_minutes:
        form.reading_time_minutes == null
          ? null
          : Number(form.reading_time_minutes) || null,
      order_index: Number(form.order_index) || 0,
    };
    try {
      if (isEdit && id) {
        const updated = await updateAdminProcedure(id, payload);
        applyProcedure(updated);
        setFeedback("Procedimento salvo.");
      } else {
        const created = await createAdminProcedure(payload);
        sessionStorage.setItem(
          "gp-admin-feedback",
          "Procedimento criado como rascunho. Agora você pode enviar mídias e anexos.",
        );
        navigateGuiasProcedimentos(
          GUIAS_PROCEDIMENTOS_ROUTES.adminProcedureEdit(created.id),
        );
      }
    } catch (err: unknown) {
      if (err instanceof HttpRequestError) {
        if (err.status === 409 || /slug/i.test(err.message)) {
          setError("Já existe um procedimento com este slug.");
        } else if (err.status === 403) {
          setError("Acesso negado.");
        } else {
          setError(err.message || "Não foi possível salvar.");
        }
      } else {
        setError("Não foi possível salvar o procedimento.");
      }
    } finally {
      setSaving(false);
    }
  }

  function requestLeave() {
    if (dirty) {
      setConfirm("leave");
      return;
    }
    navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminProcedures);
  }

  async function runStatusAction() {
    if (!id || !confirm || confirm === "leave") return;
    setActionBusy(true);
    setError(null);
    try {
      let updated: ApiAdminProcedureDetail;
      switch (confirm) {
        case "publish":
          updated = await publishAdminProcedure(id);
          setFeedback("Procedimento publicado.");
          break;
        case "unpublish":
          updated = await unpublishAdminProcedure(id);
          setFeedback("Procedimento despublicado.");
          break;
        case "archive":
          updated = await archiveAdminProcedure(id);
          setFeedback("Procedimento arquivado.");
          break;
        case "restore":
          updated = await restoreAdminProcedure(id);
          setFeedback("Procedimento restaurado.");
          break;
        default:
          return;
      }
      applyProcedure(updated);
      setConfirm(null);
    } catch (err: unknown) {
      if (err instanceof HttpRequestError && err.status === 403) {
        setError("Acesso negado.");
      } else if (err instanceof HttpRequestError) {
        setError(err.message || "Não foi possível concluir a ação.");
      } else {
        setError("Não foi possível concluir a ação.");
      }
      setConfirm(null);
    } finally {
      setActionBusy(false);
    }
  }

  const confirmCopy = (() => {
    switch (confirm) {
      case "publish":
        return {
          title: "Publicar",
          message: "Publicar este procedimento na área pública?",
          label: "Publicar",
        };
      case "unpublish":
        return {
          title: "Despublicar",
          message: "Despublicar e voltar a rascunho?",
          label: "Despublicar",
        };
      case "archive":
        return {
          title: "Arquivar",
          message: "Arquivar este procedimento?",
          label: "Arquivar",
        };
      case "restore":
        return {
          title: "Restaurar",
          message: "Restaurar para rascunho?",
          label: "Restaurar",
        };
      case "leave":
        return {
          title: "Sair sem salvar",
          message: "Há alterações não salvas. Deseja sair?",
          label: "Sair",
        };
      default:
        return { title: "", message: "", label: "Confirmar" };
    }
  })();

  useEffect(() => {
    const message = sessionStorage.getItem("gp-admin-feedback");
    if (message) {
      sessionStorage.removeItem("gp-admin-feedback");
      setFeedback(message);
    }
  }, []);

  return (
    <AdminShell
      title={isEdit ? "Editar procedimento" : "Novo procedimento"}
      standalone={standalone}
      backTo={GUIAS_PROCEDIMENTOS_ROUTES.adminProcedures}
      backLabel="Voltar à lista"
    >
      {loading ? <p className="gp-intro">Carregando…</p> : null}
      {feedback ? (
        <p className="gp-feedback gp-feedback--ok">{feedback}</p>
      ) : null}
      {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}

      {!loading ? (
        <form className="gp-form gp-form--wide" onSubmit={onSubmit}>
          {isEdit ? (
            <p className="gp-intro">
              Status atual:{" "}
              <strong className={`gp-status-pill gp-status-pill--${status}`}>
                {statusLabel(status)}
              </strong>
              . O status só muda pelos botões de fluxo (publicar, despublicar,
              arquivar, restaurar).
            </p>
          ) : (
            <p className="gp-intro">
              Novos procedimentos são salvos sempre como <strong>rascunho</strong>.
              Após criar, você poderá enviar mídias e anexos nesta mesma edição.
            </p>
          )}

          <label className="gp-field">
            <span>Título</span>
            <input
              className="gp-input"
              value={form.title}
              required
              onChange={(event) => {
                const title = event.target.value;
                patch({
                  title,
                  ...(slugTouched ? {} : { slug: slugify(title) }),
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
            <span>Resumo</span>
            <textarea
              className="gp-textarea"
              rows={3}
              value={form.summary}
              required
              onChange={(event) => patch({ summary: event.target.value })}
            />
          </label>

          <label className="gp-field">
            <span>Departamento</span>
            <select
              className="gp-input"
              value={form.department_id}
              required
              onChange={(event) => patch({ department_id: event.target.value })}
            >
              <option value="" disabled>
                Selecione…
              </option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                  {!dept.active ? " (inativo)" : ""}
                </option>
              ))}
            </select>
          </label>

          <div className="gp-form-row">
            <label className="gp-field">
              <span>Tempo de leitura (min)</span>
              <input
                className="gp-input"
                type="number"
                min={1}
                value={form.reading_time_minutes ?? ""}
                onChange={(event) =>
                  patch({
                    reading_time_minutes: event.target.value
                      ? Number(event.target.value)
                      : null,
                  })
                }
              />
            </label>
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
          </div>

          <div className="gp-form-tabs" role="tablist" aria-label="Seções do artigo">
            {TABS.map((entry) => (
              <button
                key={entry.id}
                type="button"
                role="tab"
                aria-selected={tab === entry.id}
                className={`gp-form-tabs__tab${tab === entry.id ? " is-active" : ""}`}
                onClick={() => setTab(entry.id)}
              >
                {entry.label}
              </button>
            ))}
          </div>

          {tab === "content" ? (
            <fieldset className="gp-field">
              <legend>HTML do artigo</legend>
              <HtmlEditorWithPreview
                value={form.content_html}
                onChange={(content_html) => patch({ content_html })}
                disabled={saving}
              />
            </fieldset>
          ) : null}

          {tab === "media" ? (
            <ProcedureMediaManager
              procedureId={id ?? null}
              contentHtml={form.content_html}
              onContentHtmlChange={(content_html) => patch({ content_html })}
              disabled={saving}
            />
          ) : null}

          {tab === "attachments" ? (
            <ProcedureAttachmentsManager
              procedureId={id ?? null}
              contentHtml={form.content_html}
              onContentHtmlChange={(content_html) => patch({ content_html })}
              disabled={saving}
            />
          ) : null}

          {tab === "preview" ? (
            <div className="gp-article-preview-panel">
              <p className="gp-field__hint">
                Prévia sanitizada do artigo (mídias protegidas exigem autenticação).
              </p>
              <h1 className="gp-article__title">{form.title || "Sem título"}</h1>
              <p className="gp-article__intro">{form.summary}</p>
              <SanitizedArticleContent html={form.content_html} />
            </div>
          ) : null}

          <div className="gp-form-actions">
            <button
              type="button"
              className="gp-btn gp-btn--ghost"
              onClick={requestLeave}
              disabled={saving || actionBusy}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="gp-btn gp-btn--secondary"
              disabled={!canSubmit}
            >
              {saving ? "Salvando…" : isEdit ? "Salvar" : "Criar rascunho"}
            </button>
          </div>

          {isEdit && id ? (
            <div className="gp-admin-actions">
              {status === "draft" ? (
                <button
                  type="button"
                  className="gp-btn gp-btn--secondary"
                  disabled={actionBusy || dirty}
                  title={dirty ? "Salve antes de publicar" : undefined}
                  onClick={() => setConfirm("publish")}
                >
                  Publicar
                </button>
              ) : null}
              {status === "published" ? (
                <button
                  type="button"
                  className="gp-btn gp-btn--ghost"
                  disabled={actionBusy}
                  onClick={() => setConfirm("unpublish")}
                >
                  Despublicar
                </button>
              ) : null}
              {status !== "archived" ? (
                <button
                  type="button"
                  className="gp-btn gp-btn--ghost"
                  disabled={actionBusy}
                  onClick={() => setConfirm("archive")}
                >
                  Arquivar
                </button>
              ) : (
                <button
                  type="button"
                  className="gp-btn gp-btn--secondary"
                  disabled={actionBusy}
                  onClick={() => setConfirm("restore")}
                >
                  Restaurar
                </button>
              )}
            </div>
          ) : null}
        </form>
      ) : null}

      <GuiasConfirmDialog
        open={confirm != null}
        title={confirmCopy.title}
        message={confirmCopy.message}
        confirmLabel={confirmCopy.label}
        busy={actionBusy}
        variant={confirm === "archive" || confirm === "leave" ? "danger" : "default"}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          if (confirm === "leave") {
            setConfirm(null);
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminProcedures);
            return;
          }
          void runStatusAction();
        }}
      />
    </AdminShell>
  );
}
