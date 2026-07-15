import { useEffect, useState } from "react";

import {
  listAdminDepartments,
  type ApiAdminDepartment,
} from "../../api/guiasProcedimentosApi";
import { HttpRequestError } from "../../api/httpClient";
import { AdminShell } from "../../components/AdminShell";
import { DepartmentIcon } from "../../components/DepartmentIcon";
import { navigateGuiasProcedimentos } from "../../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../../utils/route";

type AdminDepartmentsPageProps = {
  standalone?: boolean;
};

export function AdminDepartmentsPage({
  standalone = false,
}: AdminDepartmentsPageProps) {
  const [items, setItems] = useState<ApiAdminDepartment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listAdminDepartments()
      .then((data) => {
        if (!cancelled) {
          setItems(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof HttpRequestError && err.status === 403) {
          setError("Acesso negado.");
        } else {
          setError("Não foi possível carregar os departamentos.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const message = sessionStorage.getItem("gp-admin-feedback");
    if (message) {
      setFeedback(message);
      sessionStorage.removeItem("gp-admin-feedback");
    }
  }, []);

  return (
    <AdminShell
      title="Departamentos"
      standalone={standalone}
      backTo={GUIAS_PROCEDIMENTOS_ROUTES.admin}
      backLabel="Voltar à administração"
      actions={
        <button
          type="button"
          className="gp-btn gp-btn--secondary gp-btn--compact"
          onClick={() =>
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminDepartmentNew)
          }
        >
          Novo departamento
        </button>
      }
    >
      {feedback ? (
        <p className="gp-feedback gp-feedback--ok">{feedback}</p>
      ) : null}
      {loading ? <p className="gp-intro">Carregando…</p> : null}
      {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}

      {!loading && !error && items.length === 0 ? (
        <p className="gp-intro">Nenhum departamento cadastrado.</p>
      ) : null}

      {!loading && items.length > 0 ? (
        <div className="gp-admin-table-wrap">
          <table className="gp-admin-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Slug</th>
                <th>Ícone</th>
                <th>Procedimentos</th>
                <th>Ordem</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.name}</td>
                  <td>
                    <code>{item.slug}</code>
                  </td>
                  <td>
                    <span className="gp-admin-icon-cell">
                      <DepartmentIcon
                        icon={item.icon || "book-open"}
                        size={18}
                      />
                      <code>{item.icon}</code>
                    </span>
                  </td>
                  <td>{item.procedure_count}</td>
                  <td>{item.order_index}</td>
                  <td>
                    <span
                      className={`gp-status-pill ${
                        item.active
                          ? "gp-status-pill--ok"
                          : "gp-status-pill--muted"
                      }`}
                    >
                      {item.active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="gp-btn gp-btn--ghost gp-btn--compact"
                      onClick={() =>
                        navigateGuiasProcedimentos(
                          GUIAS_PROCEDIMENTOS_ROUTES.adminDepartmentEdit(item.id),
                        )
                      }
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </AdminShell>
  );
}
