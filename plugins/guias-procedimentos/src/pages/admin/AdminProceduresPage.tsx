import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveAdminProcedure,
  listAdminDepartments,
  listAdminProcedures,
  publishAdminProcedure,
  restoreAdminProcedure,
  unpublishAdminProcedure,
  type ApiAdminDepartment,
  type ApiAdminProcedureListItem,
  type ProcedureStatus,
} from "../../api/guiasProcedimentosApi";
import { HttpRequestError } from "../../api/httpClient";
import { AdminShell } from "../../components/AdminShell";
import { GuiasConfirmDialog } from "../../components/GuiasConfirmDialog";
import {
  formatDateTime,
  statusLabel,
} from "../../utils/adminHelpers";
import { navigateGuiasProcedimentos } from "../../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../../utils/route";

type AdminProceduresPageProps = {
  standalone?: boolean;
};

type ConfirmAction = {
  id: string;
  kind: "publish" | "unpublish" | "archive" | "restore";
  title: string;
};

export function AdminProceduresPage({
  standalone = false,
}: AdminProceduresPageProps) {
  const [items, setItems] = useState<ApiAdminProcedureListItem[]>([]);
  const [departments, setDepartments] = useState<ApiAdminDepartment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [qDebounced, setQDebounced] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [status, setStatus] = useState<"" | ProcedureStatus>("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<ConfirmAction | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setQDebounced(q.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [q]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [procedures, deps] = await Promise.all([
        listAdminProcedures({
          q: qDebounced || undefined,
          department_id: departmentId || undefined,
          status: status || undefined,
        }),
        listAdminDepartments(),
      ]);
      setItems(procedures);
      setDepartments(deps);
      setError(null);
    } catch (err: unknown) {
      if (err instanceof HttpRequestError && err.status === 403) {
        setError("Acesso negado.");
      } else {
        setError("Não foi possível carregar os procedimentos.");
      }
    } finally {
      setLoading(false);
    }
  }, [qDebounced, departmentId, status]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const message = sessionStorage.getItem("gp-admin-feedback");
    if (message) {
      setFeedback(message);
      sessionStorage.removeItem("gp-admin-feedback");
    }
  }, []);

  const confirmCopy = useMemo(() => {
    if (!confirm) return { title: "", message: "", label: "Confirmar" };
    switch (confirm.kind) {
      case "publish":
        return {
          title: "Publicar procedimento",
          message: `Publicar «${confirm.title}»? Ele ficará visível na área pública.`,
          label: "Publicar",
        };
      case "unpublish":
        return {
          title: "Despublicar procedimento",
          message: `Despublicar «${confirm.title}»? Ele voltará a rascunho.`,
          label: "Despublicar",
        };
      case "archive":
        return {
          title: "Arquivar procedimento",
          message: `Arquivar «${confirm.title}»?`,
          label: "Arquivar",
        };
      case "restore":
        return {
          title: "Restaurar procedimento",
          message: `Restaurar «${confirm.title}» para rascunho?`,
          label: "Restaurar",
        };
      default:
        return { title: "", message: "", label: "Confirmar" };
    }
  }, [confirm]);

  async function runConfirm() {
    if (!confirm) return;
    setBusyId(confirm.id);
    try {
      let updated: ApiAdminProcedureListItem;
      switch (confirm.kind) {
        case "publish":
          updated = await publishAdminProcedure(confirm.id);
          setFeedback("Procedimento publicado.");
          break;
        case "unpublish":
          updated = await unpublishAdminProcedure(confirm.id);
          setFeedback("Procedimento despublicado.");
          break;
        case "archive":
          updated = await archiveAdminProcedure(confirm.id);
          setFeedback("Procedimento arquivado.");
          break;
        case "restore":
          updated = await restoreAdminProcedure(confirm.id);
          setFeedback("Procedimento restaurado.");
          break;
      }
      setItems((prev) =>
        prev.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)),
      );
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
      setBusyId(null);
    }
  }

  return (
    <AdminShell
      title="Procedimentos"
      standalone={standalone}
      backTo={GUIAS_PROCEDIMENTOS_ROUTES.admin}
      backLabel="Voltar à administração"
      actions={
        <button
          type="button"
          className="gp-btn gp-btn--secondary gp-btn--compact"
          onClick={() =>
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminProcedureNew)
          }
        >
          Novo procedimento
        </button>
      }
    >
      {feedback ? (
        <p className="gp-feedback gp-feedback--ok">{feedback}</p>
      ) : null}
      {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}

      <div className="gp-admin-filters">
        <label className="gp-field">
          <span>Busca</span>
          <input
            className="gp-input"
            value={q}
            placeholder="Título ou slug"
            onChange={(event) => setQ(event.target.value)}
          />
        </label>
        <label className="gp-field">
          <span>Departamento</span>
          <select
            className="gp-input"
            value={departmentId}
            onChange={(event) => setDepartmentId(event.target.value)}
          >
            <option value="">Todos</option>
            {departments.map((dept) => (
              <option key={dept.id} value={dept.id}>
                {dept.name}
              </option>
            ))}
          </select>
        </label>
        <label className="gp-field">
          <span>Status</span>
          <select
            className="gp-input"
            value={status}
            onChange={(event) =>
              setStatus(event.target.value as "" | ProcedureStatus)
            }
          >
            <option value="">Todos</option>
            <option value="draft">Rascunho</option>
            <option value="published">Publicado</option>
            <option value="archived">Arquivado</option>
          </select>
        </label>
      </div>

      {loading ? <p className="gp-intro">Carregando…</p> : null}

      {!loading && items.length === 0 ? (
        <p className="gp-intro">Nenhum procedimento encontrado.</p>
      ) : null}

      {!loading && items.length > 0 ? (
        <div className="gp-admin-table-wrap">
          <table className="gp-admin-table">
            <thead>
              <tr>
                <th>Título</th>
                <th>Slug</th>
                <th>Departamento</th>
                <th>Status</th>
                <th>Leitura</th>
                <th>Atualização</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const busy = busyId === item.id;
                return (
                  <tr key={item.id}>
                    <td>{item.title}</td>
                    <td>
                      <code>{item.slug}</code>
                    </td>
                    <td>{item.department.name}</td>
                    <td>
                      <span
                        className={`gp-status-pill gp-status-pill--${item.status}`}
                      >
                        {statusLabel(item.status)}
                      </span>
                    </td>
                    <td>
                      {item.reading_time_minutes != null
                        ? `${item.reading_time_minutes} min`
                        : "—"}
                    </td>
                    <td>{formatDateTime(item.updated_at)}</td>
                    <td>
                      <div className="gp-admin-row-actions">
                        <button
                          type="button"
                          className="gp-btn gp-btn--ghost gp-btn--compact"
                          disabled={busy}
                          onClick={() =>
                            navigateGuiasProcedimentos(
                              GUIAS_PROCEDIMENTOS_ROUTES.adminProcedureEdit(
                                item.id,
                              ),
                            )
                          }
                        >
                          Editar
                        </button>
                        {item.status === "draft" || item.status === "archived" ? (
                          <button
                            type="button"
                            className="gp-btn gp-btn--ghost gp-btn--compact"
                            disabled={busy || item.status === "archived"}
                            onClick={() =>
                              item.status === "draft"
                                ? setConfirm({
                                    id: item.id,
                                    kind: "publish",
                                    title: item.title,
                                  })
                                : undefined
                            }
                          >
                            Publicar
                          </button>
                        ) : null}
                        {item.status === "published" ? (
                          <button
                            type="button"
                            className="gp-btn gp-btn--ghost gp-btn--compact"
                            disabled={busy}
                            onClick={() =>
                              setConfirm({
                                id: item.id,
                                kind: "unpublish",
                                title: item.title,
                              })
                            }
                          >
                            Despublicar
                          </button>
                        ) : null}
                        {item.status !== "archived" ? (
                          <button
                            type="button"
                            className="gp-btn gp-btn--ghost gp-btn--compact"
                            disabled={busy}
                            onClick={() =>
                              setConfirm({
                                id: item.id,
                                kind: "archive",
                                title: item.title,
                              })
                            }
                          >
                            Arquivar
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="gp-btn gp-btn--ghost gp-btn--compact"
                            disabled={busy}
                            onClick={() =>
                              setConfirm({
                                id: item.id,
                                kind: "restore",
                                title: item.title,
                              })
                            }
                          >
                            Restaurar
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}

      <GuiasConfirmDialog
        open={confirm != null}
        title={confirmCopy.title}
        message={confirmCopy.message}
        confirmLabel={confirmCopy.label}
        busy={busyId != null}
        variant={confirm?.kind === "archive" ? "danger" : "default"}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          void runConfirm();
        }}
      />
    </AdminShell>
  );
}
