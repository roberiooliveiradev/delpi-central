/** D16 — Bandeiras de acompanhamento do atendimento PRC.
 * Anotações operacionais; não alteram SB1/SA5/revisões. */

import { useCallback, useEffect, useId, useState } from "react";
import { Check, Flag, MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringFormActions,
  EngineeringStateBanner,
  EngineeringTextAreaField,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import { EngineeringConfirmDialog } from "../../../ui/EngineeringConfirmDialog";
import {
  createPrcFlag,
  deletePrcFlag,
  fetchPrcFlags,
  reopenPrcFlag,
  resolvePrcFlag,
  updatePrcFlag,
  type PrcAttendanceFlag,
} from "../api/productRegistrationApi";
import { PRC_FIELD_LABELS } from "../prcCopy";

function newIdempotencyKey(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function formatWhen(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

function actorLabel(actor?: {
  subject?: string | null;
  displayName?: string | null;
} | null): string {
  if (!actor) return "—";
  return actor.displayName || actor.subject || "—";
}

function contextLabel(flag: PrcAttendanceFlag): string | null {
  if (flag.subject === "FIELD" && flag.targetPath) {
    return PRC_FIELD_LABELS[flag.targetPath] || flag.targetPath;
  }
  if (flag.subject === "SUPPLIER_LINK" && flag.supplierKey) {
    return `Fornecedor ${flag.supplierKey.supplierCode} / ${flag.supplierKey.store}`;
  }
  return null;
}

type FormMode = "create" | "edit" | null;

export function PrcAttendanceFlags({ requestId }: { requestId: string }) {
  const formId = useId();
  const [items, setItems] = useState<PrcAttendanceFlag[]>([]);
  const [openCount, setOpenCount] = useState(0);
  const [resolvedCount, setResolvedCount] = useState(0);
  const [showResolved, setShowResolved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [formMode, setFormMode] = useState<FormMode>(null);
  const [editing, setEditing] = useState<PrcAttendanceFlag | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [formError, setFormError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<PrcAttendanceFlag | null>(
    null,
  );
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const status = showResolved ? "all" : "OPEN";
      const res = await fetchPrcFlags(requestId, {
        status,
        page: 1,
        pageSize: 50,
      });
      const data = res.data;
      setItems(data.items || []);
      setOpenCount(data.openCount ?? 0);
      setResolvedCount(data.resolvedCount ?? 0);
    } catch (err) {
      const msg =
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível carregar as bandeiras.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [requestId, showResolved]);

  useEffect(() => {
    void load();
  }, [load]);

  const openCreate = () => {
    setFormMode("create");
    setEditing(null);
    setTitle("");
    setDescription("");
    setFormError("");
  };

  const openEdit = (flag: PrcAttendanceFlag) => {
    setFormMode("edit");
    setEditing(flag);
    setTitle(flag.title);
    setDescription(flag.description);
    setFormError("");
    setMenuOpenId(null);
  };

  const closeForm = () => {
    setFormMode(null);
    setEditing(null);
    setTitle("");
    setDescription("");
    setFormError("");
  };

  const saveForm = async () => {
    const t = title.trim();
    const d = description.trim();
    if (!t) {
      setFormError("Informe o título.");
      return;
    }
    if (!d) {
      setFormError("Informe a descrição.");
      return;
    }
    if (t.length > 120) {
      setFormError("Título pode ter no máximo 120 caracteres.");
      return;
    }
    if (d.length > 1000) {
      setFormError("Descrição pode ter no máximo 1.000 caracteres.");
      return;
    }
    setBusy(true);
    setFormError("");
    try {
      if (formMode === "create") {
        await createPrcFlag(
          requestId,
          { title: t, description: d, subject: "GENERAL" },
          newIdempotencyKey("flag-create"),
        );
      } else if (formMode === "edit" && editing) {
        await updatePrcFlag(
          requestId,
          editing.id,
          {
            expectedVersion: editing.version,
            title: t,
            description: d,
          },
          newIdempotencyKey("flag-update"),
        );
      }
      closeForm();
      await load();
    } catch (err) {
      const msg =
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível salvar a bandeira.";
      setFormError(msg);
    } finally {
      setBusy(false);
    }
  };

  const runResolve = async (flag: PrcAttendanceFlag) => {
    setBusy(true);
    setError("");
    try {
      await resolvePrcFlag(
        requestId,
        flag.id,
        { expectedVersion: flag.version },
        newIdempotencyKey("flag-resolve"),
      );
      await load();
    } catch (err) {
      setError(
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível resolver a bandeira.",
      );
    } finally {
      setBusy(false);
      setMenuOpenId(null);
    }
  };

  const runReopen = async (flag: PrcAttendanceFlag) => {
    setBusy(true);
    setError("");
    try {
      await reopenPrcFlag(
        requestId,
        flag.id,
        { expectedVersion: flag.version },
        newIdempotencyKey("flag-reopen"),
      );
      await load();
    } catch (err) {
      setError(
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível reabrir a bandeira.",
      );
    } finally {
      setBusy(false);
      setMenuOpenId(null);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setBusy(true);
    try {
      await deletePrcFlag(
        requestId,
        deleteTarget.id,
        deleteTarget.version,
        newIdempotencyKey("flag-delete"),
      );
      setDeleteTarget(null);
      await load();
    } catch (err) {
      setError(
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível excluir a bandeira.",
      );
      setDeleteTarget(null);
    } finally {
      setBusy(false);
    }
  };

  const visible = showResolved
    ? items
    : items.filter((f) => f.status === "OPEN");

  return (
    <section
      className="engineering-prc__flags"
      aria-labelledby={`${formId}-flags-title`}
    >
      <header className="engineering-prc__flags-head">
        <div className="engineering-prc__flags-title-row">
          <Flag size={18} aria-hidden="true" />
          <h3 id={`${formId}-flags-title`}>Bandeiras de acompanhamento</h3>
          <span className="engineering-prc__flags-count" aria-live="polite">
            {openCount} aberta{openCount === 1 ? "" : "s"}
            {resolvedCount > 0 ? ` · ${resolvedCount} resolvida${resolvedCount === 1 ? "" : "s"}` : ""}
          </span>
        </div>
        <div className="engineering-prc__flags-actions">
          <EngineeringActionButton
            variant="ghost"
            onClick={openCreate}
            disabled={busy || formMode !== null}
          >
            + Nova bandeira
          </EngineeringActionButton>
        </div>
      </header>

      {error ? (
        <EngineeringStateBanner variant="error">
          {error}{" "}
          <EngineeringActionButton variant="ghost" onClick={() => void load()}>
            Tentar novamente
          </EngineeringActionButton>
        </EngineeringStateBanner>
      ) : null}

      {formMode ? (
        <div className="engineering-prc__flags-form" role="form">
          <EngineeringTextField
            id={`${formId}-title`}
            label="Título"
            value={title}
            onChange={setTitle}
            maxLength={120}
            required
            disabled={busy}
          />
          <EngineeringTextAreaField
            id={`${formId}-description`}
            label="Descrição"
            value={description}
            onChange={setDescription}
            maxLength={1000}
            required
            rows={3}
            disabled={busy}
          />
          {formError ? (
            <p className="engineering-prc__field-error" role="alert">
              {formError}
            </p>
          ) : null}
          <EngineeringFormActions>
            <EngineeringActionButton
              variant="primary"
              onClick={() => void saveForm()}
              disabled={busy}
            >
              Salvar
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="ghost"
              onClick={closeForm}
              disabled={busy}
            >
              Cancelar
            </EngineeringActionButton>
          </EngineeringFormActions>
        </div>
      ) : null}

      {loading ? (
        <p className="engineering-prc__muted">Carregando bandeiras…</p>
      ) : null}

      {!loading && !visible.length && !formMode ? (
        <EngineeringEmptyState
          title="Nenhuma bandeira aberta"
          message="Registre pendências operacionais do atendimento sem alterar a ficha técnica oficial."
        >
          <EngineeringActionButton variant="ghost" onClick={openCreate}>
            Nova bandeira
          </EngineeringActionButton>
        </EngineeringEmptyState>
      ) : null}

      {!loading && visible.length ? (
        <ul className="engineering-prc__flags-list">
          {visible.map((flag) => {
            const ctx = contextLabel(flag);
            const isOpen = flag.status === "OPEN";
            return (
              <li key={flag.id} className="engineering-prc__flag-card">
                <div className="engineering-prc__flag-main">
                  <div className="engineering-prc__flag-title-row">
                    <Flag size={16} aria-hidden="true" />
                    <strong>{flag.title}</strong>
                    <span
                      className={
                        isOpen
                          ? "engineering-prc__flag-badge engineering-prc__flag-badge--open"
                          : "engineering-prc__flag-badge engineering-prc__flag-badge--resolved"
                      }
                    >
                      {isOpen ? "Aberta" : "Resolvida"}
                    </span>
                  </div>
                  <p className="engineering-prc__flag-desc">{flag.description}</p>
                  {ctx ? (
                    <p className="engineering-prc__muted">Contexto: {ctx}</p>
                  ) : null}
                  <p className="engineering-prc__muted">
                    Criada por: {actorLabel(flag.createdBy)} ·{" "}
                    {formatWhen(flag.createdAt)}
                  </p>
                </div>
                <div className="engineering-prc__flag-ops">
                  {isOpen ? (
                    <>
                      <EngineeringActionButton
                        variant="ghost"
                        aria-label={`Editar bandeira ${flag.title}`}
                        onClick={() => openEdit(flag)}
                        disabled={busy}
                      >
                        <Pencil size={16} aria-hidden="true" />
                        Editar
                      </EngineeringActionButton>
                      <EngineeringActionButton
                        variant="ghost"
                        aria-label={`Resolver bandeira ${flag.title}`}
                        onClick={() => void runResolve(flag)}
                        disabled={busy}
                      >
                        <Check size={16} aria-hidden="true" />
                        Resolver
                      </EngineeringActionButton>
                    </>
                  ) : (
                    <EngineeringActionButton
                      variant="ghost"
                      aria-label={`Reabrir bandeira ${flag.title}`}
                      onClick={() => void runReopen(flag)}
                      disabled={busy}
                    >
                      <RotateCcw size={16} aria-hidden="true" />
                      Reabrir
                    </EngineeringActionButton>
                  )}
                  <div className="engineering-prc__flag-menu">
                    <EngineeringActionButton
                      variant="ghost"
                      aria-label={`Mais ações para ${flag.title}`}
                      aria-expanded={menuOpenId === flag.id}
                      onClick={() =>
                        setMenuOpenId((cur) =>
                          cur === flag.id ? null : flag.id,
                        )
                      }
                      disabled={busy}
                    >
                      <MoreHorizontal size={16} aria-hidden="true" />
                    </EngineeringActionButton>
                    {menuOpenId === flag.id ? (
                      <div className="engineering-prc__flag-menu-panel" role="menu">
                        <button
                          type="button"
                          role="menuitem"
                          className="engineering-prc__flag-menu-item"
                          onClick={() => {
                            setDeleteTarget(flag);
                            setMenuOpenId(null);
                          }}
                        >
                          <Trash2 size={14} aria-hidden="true" />
                          Remover
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}

      {resolvedCount > 0 ? (
        <div className="engineering-prc__flags-toggle">
          <EngineeringActionButton
            variant="ghost"
            onClick={() => setShowResolved((v) => !v)}
            disabled={busy}
          >
            {showResolved ? "Ocultar resolvidas" : "Mostrar resolvidas"}
          </EngineeringActionButton>
        </div>
      ) : null}

      <EngineeringConfirmDialog
        open={Boolean(deleteTarget)}
        title="Remover bandeira"
        message={
          deleteTarget
            ? `Remover a bandeira «${deleteTarget.title}»? A exclusão é lógica e o histórico permanece.`
            : ""
        }
        confirmLabel="Remover"
        variant="danger"
        confirmBusy={busy}
        onConfirm={() => void confirmDelete()}
        onCancel={() => setDeleteTarget(null)}
      />
    </section>
  );
}
