import { FolderTree, FileText } from "lucide-react";
import { useEffect, useState } from "react";

import {
  listAdminDepartments,
  listAdminProcedures,
} from "../../api/guiasProcedimentosApi";
import { HttpRequestError } from "../../api/httpClient";
import { AdminShell } from "../../components/AdminShell";
import { navigateGuiasProcedimentos } from "../../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../../utils/route";

type AdminHomePageProps = {
  standalone?: boolean;
};

export function AdminHomePage({ standalone = false }: AdminHomePageProps) {
  const [deptCount, setDeptCount] = useState<number | null>(null);
  const [procCount, setProcCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([listAdminDepartments(), listAdminProcedures()])
      .then(([departments, procedures]) => {
        if (cancelled) return;
        setDeptCount(departments.length);
        setProcCount(procedures.length);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof HttpRequestError && err.status === 403) {
          setError("Acesso negado pela API.");
        } else {
          setError("Não foi possível carregar o painel administrativo.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AdminShell title="Administração" standalone={standalone}>
      {loading ? <p className="gp-intro">Carregando…</p> : null}
      {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}

      <div className="gp-admin-nav">
        <button
          type="button"
          className="gp-admin-tile"
          onClick={() =>
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminDepartments)
          }
        >
          <FolderTree size={22} strokeWidth={2} aria-hidden="true" />
          <span className="gp-admin-tile__title">Departamentos</span>
          <span className="gp-admin-tile__meta">
            {deptCount == null ? "—" : `${deptCount} cadastrado(s)`}
          </span>
        </button>
        <button
          type="button"
          className="gp-admin-tile"
          onClick={() =>
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminProcedures)
          }
        >
          <FileText size={22} strokeWidth={2} aria-hidden="true" />
          <span className="gp-admin-tile__title">Procedimentos</span>
          <span className="gp-admin-tile__meta">
            {procCount == null ? "—" : `${procCount} cadastrado(s)`}
          </span>
        </button>
      </div>

      <div className="gp-admin-actions">
        <button
          type="button"
          className="gp-btn gp-btn--secondary"
          onClick={() =>
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminDepartmentNew)
          }
        >
          Novo departamento
        </button>
        <button
          type="button"
          className="gp-btn gp-btn--secondary"
          onClick={() =>
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.adminProcedureNew)
          }
        >
          Novo procedimento
        </button>
      </div>
    </AdminShell>
  );
}
