// portal/src/ui/admin/manifest/ManifestAccessPanel.tsx

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { AdminApi, PluginAccessSnapshot } from "../../../data/adminApi";
import {
  Alert,
  Button,
  DenseTable,
  SearchInput,
  Select,
  Spinner,
} from "../../../ui-kit";

type Props = {
  appId: string | undefined;
  api: AdminApi;
  filterCode?: string | null;
  permissionCodes: string[];
};

export function ManifestAccessPanel({
  appId,
  api,
  filterCode,
  permissionCodes,
}: Props) {
  const navigate = useNavigate();
  const [data, setData] = useState<PluginAccessSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState("");
  const [codeFilter, setCodeFilter] = useState(filterCode || "");

  useEffect(() => {
    if (filterCode) setCodeFilter(filterCode);
  }, [filterCode]);

  useEffect(() => {
    if (!appId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .getPluginAccess(appId)
      .then((snap) => {
        if (!cancelled) setData(snap);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(
            e instanceof Error
              ? e.message
              : "Não foi possível carregar o acesso RBAC.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api, appId]);

  const users = useMemo(() => {
    if (!data) return [];
    return data.users.filter((u) => {
      const matchQ =
        !q ||
        u.name.toLowerCase().includes(q.toLowerCase()) ||
        u.email.toLowerCase().includes(q.toLowerCase());
      const matchCode =
        !codeFilter ||
        u.permissionCodes.includes(codeFilter) ||
        u.paths.some((p) => p.codes.includes(codeFilter));
      return matchQ && matchCode;
    });
  }, [data, q, codeFilter]);

  if (!appId) {
    return (
      <Alert tone="info">
        Publique o plugin para ver quem tem acesso às permissões deste manifesto.
      </Alert>
    );
  }

  if (loading) return <Spinner label="Carregando acesso…" />;
  if (error) return <Alert tone="danger">{error}</Alert>;
  if (!data) return null;

  const codesParam = permissionCodes.filter(Boolean).join(",");

  return (
    <div className="manifest-access">
      <div className="manifest-access-header">
        <div>
          <h3>Quem tem acesso a este app</h3>
          <p className="hint">
            {data.summary.userCount} usuários · {data.summary.roleCount} papéis ·{" "}
            {data.summary.groupCount} grupos
          </p>
        </div>
        <div className="portal-ui-dense__actions">
          <Button
            variant="primary"
            size="sm"
            onClick={() =>
              navigate(
                `/admin/roles/new?module=${encodeURIComponent(appId)}&permissionCodes=${encodeURIComponent(codesParam)}`,
              )
            }
          >
            Criar papel com codes deste app
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate("/admin?tab=roles")}
          >
            Abrir Papéis
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate("/admin?tab=groups")}
          >
            Grupos
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate("/admin?tab=users")}
          >
            Usuários
          </Button>
        </div>
      </div>

      <div className="portal-ui-dense__toolbar">
        <SearchInput
          placeholder="Filtrar usuário…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onClear={() => setQ("")}
        />
        <Select
          size="sm"
          value={codeFilter}
          aria-label="Filtrar por code"
          onChange={setCodeFilter}
          options={[
            { value: "", label: "Todos os codes" },
            ...data.permissions.map((p) => ({ value: p.code, label: p.code })),
          ]}
        />
      </div>

      <DenseTable wrapTable>
        <thead>
          <tr>
            <th>Usuário</th>
            <th>Caminho de acesso</th>
            <th>Codes</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>
                <strong>{u.name}</strong>
                <div className="hint">{u.email}</div>
                {u.isSuperadmin && <span className="hint">superadmin</span>}
              </td>
              <td>
                <ul className="manifest-path-list">
                  {u.paths.map((p, i) => (
                    <li key={i}>
                      {p.type === "role" ? (
                        <>
                          Papel «{p.roleName}» → {p.codes.join(", ")}
                        </>
                      ) : (
                        <>
                          Grupo «{p.groupName}» → Papel «{p.roleName}» →{" "}
                          {p.codes.join(", ")}
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </td>
              <td>
                {u.permissionCodes.length}/{data.permissions.length}
              </td>
              <td>
                <div className="portal-ui-dense__actions">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/admin/users/${u.id}`)}
                  >
                    Abrir usuário
                  </Button>
                  {u.paths[0]?.type === "role" && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() =>
                        navigate(`/admin/roles/${u.paths[0].roleId}`)
                      }
                    >
                      Abrir papel
                    </Button>
                  )}
                  {u.paths.some((p) => p.type === "group_role") && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        const g = u.paths.find((p) => p.type === "group_role");
                        if (g && g.type === "group_role") {
                          navigate(`/admin/groups/${g.groupId}`);
                        }
                      }}
                    >
                      Abrir grupo
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </DenseTable>

      <h4>Por permissão</h4>
      {data.permissions.map((p) => {
        const roles = data.roles.filter((r) =>
          r.permissionCodes.includes(p.code),
        );
        const userCount = data.users.filter((u) =>
          u.permissionCodes.includes(p.code),
        ).length;
        return (
          <details key={p.code} className="manifest-perm-accordion">
            <summary>
              {p.code} — {roles.length} papéis · {userCount} users
            </summary>
            <ul>
              {roles.map((r) => (
                <li key={r.id}>
                  <Button
                    variant="link"
                    onClick={() => navigate(`/admin/roles/${r.id}`)}
                  >
                    {r.name}
                  </Button>
                </li>
              ))}
            </ul>
          </details>
        );
      })}
    </div>
  );
}
