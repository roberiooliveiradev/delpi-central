// portal/src/ui/admin/manifest/ManifestAccessPanel.tsx

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, UsersRound } from "lucide-react";
import type {
  AdminApi,
  PluginAccessSnapshot,
  PluginAccessUser,
} from "../../../data/adminApi";
import {
  Alert,
  Badge,
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

type AccessLeaf = {
  key: string;
  roleId: string;
  roleName: string;
  codes: string[];
};

type AccessBranch =
  | { kind: "role"; key: string; leaf: AccessLeaf }
  | {
      kind: "group";
      key: string;
      groupId: string;
      groupName: string;
      roles: AccessLeaf[];
    };

/** Papéis herdados do mesmo grupo viram filhos dele, em vez de repetir o nome
 *  do grupo em cada linha do caminho. */
function buildAccessTree(user: PluginAccessUser): AccessBranch[] {
  const groups = new Map<string, Extract<AccessBranch, { kind: "group" }>>();
  const branches: AccessBranch[] = [];

  user.paths.forEach((path, index) => {
    const leaf: AccessLeaf = {
      key: `${path.roleId}-${index}`,
      roleId: path.roleId,
      roleName: path.roleName,
      codes: path.codes,
    };

    if (path.type === "role") {
      branches.push({ kind: "role", key: leaf.key, leaf });
      return;
    }

    const existing = groups.get(path.groupId);
    if (existing) {
      existing.roles.push(leaf);
      return;
    }

    const branch: Extract<AccessBranch, { kind: "group" }> = {
      kind: "group",
      key: `g-${path.groupId}`,
      groupId: path.groupId,
      groupName: path.groupName,
      roles: [leaf],
    };
    groups.set(path.groupId, branch);
    branches.push(branch);
  });

  return branches;
}

/** O prefixo do módulo se repete em todo code e só rouba espaço da coluna. */
function shortCode(code: string, appId: string) {
  const prefix = `${appId}.`;
  return code.startsWith(prefix) ? code.slice(prefix.length) : code;
}

function CodeBadges({
  codes,
  appId,
  highlight,
}: {
  codes: string[];
  appId: string;
  highlight: string;
}) {
  return (
    <div className="manifest-access-codes">
      {codes.map((code) => (
        <Badge
          key={code}
          tone={highlight === code ? "primary" : "default"}
          className="manifest-access-code"
          title={code}
        >
          {shortCode(code, appId)}
        </Badge>
      ))}
    </div>
  );
}

function RoleLeaf({
  leaf,
  appId,
  highlight,
  onOpen,
}: {
  leaf: AccessLeaf;
  appId: string;
  highlight: string;
  onOpen: () => void;
}) {
  return (
    <div className="manifest-access-node">
      <span className="manifest-access-node__label">
        <Shield size={13} aria-hidden="true" />
        <button
          type="button"
          className="manifest-access-node__link"
          onClick={onOpen}
          title="Abrir papel"
        >
          {leaf.roleName}
        </button>
      </span>
      <CodeBadges codes={leaf.codes} appId={appId} highlight={highlight} />
    </div>
  );
}

function AccessTree({
  user,
  appId,
  highlight,
  onOpenRole,
  onOpenGroup,
}: {
  user: PluginAccessUser;
  appId: string;
  highlight: string;
  onOpenRole: (roleId: string) => void;
  onOpenGroup: (groupId: string) => void;
}) {
  const branches = buildAccessTree(user);

  if (branches.length === 0) {
    return <span className="hint">Sem caminho de acesso.</span>;
  }

  return (
    <ul className="manifest-access-tree">
      {branches.map((branch) =>
        branch.kind === "role" ? (
          <li key={branch.key} className="manifest-access-tree__item">
            <RoleLeaf
              leaf={branch.leaf}
              appId={appId}
              highlight={highlight}
              onOpen={() => onOpenRole(branch.leaf.roleId)}
            />
          </li>
        ) : (
          <li key={branch.key} className="manifest-access-tree__item">
            <div className="manifest-access-node">
              <span className="manifest-access-node__label">
                <UsersRound size={13} aria-hidden="true" />
                <button
                  type="button"
                  className="manifest-access-node__link"
                  onClick={() => onOpenGroup(branch.groupId)}
                  title="Abrir grupo"
                >
                  {branch.groupName}
                </button>
              </span>
              <Badge tone="info">
                {branch.roles.length}{" "}
                {branch.roles.length === 1 ? "papel" : "papéis"}
              </Badge>
            </div>

            <ul className="manifest-access-tree manifest-access-tree--nested">
              {branch.roles.map((leaf) => (
                <li key={leaf.key} className="manifest-access-tree__item">
                  <RoleLeaf
                    leaf={leaf}
                    appId={appId}
                    highlight={highlight}
                    onOpen={() => onOpenRole(leaf.roleId)}
                  />
                </li>
              ))}
            </ul>
          </li>
        ),
      )}
    </ul>
  );
}

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
          {users.map((u) => {
            const total = data.permissions.length;
            const granted = u.permissionCodes.length;

            return (
              <tr key={u.id}>
                <td>
                  <div className="manifest-access-user">
                    <strong>{u.name}</strong>
                    <span className="hint">{u.email}</span>
                    {u.isSuperadmin && <Badge tone="warning">Superadmin</Badge>}
                  </div>
                </td>
                <td>
                  <AccessTree
                    user={u}
                    appId={appId}
                    highlight={codeFilter}
                    onOpenRole={(roleId) => navigate(`/admin/roles/${roleId}`)}
                    onOpenGroup={(groupId) =>
                      navigate(`/admin/groups/${groupId}`)
                    }
                  />
                </td>
                <td>
                  <Badge
                    tone={
                      granted === 0
                        ? "default"
                        : granted === total
                          ? "success"
                          : "warning"
                    }
                    title={u.permissionCodes.join(", ")}
                  >
                    {granted}/{total}
                  </Badge>
                </td>
                <td>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/admin/users/${u.id}`)}
                  >
                    Abrir usuário
                  </Button>
                </td>
              </tr>
            );
          })}
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
              <span className="manifest-access-summary">
                <code>{p.code}</code>
                <Badge tone={roles.length ? "primary" : "default"}>
                  {roles.length} {roles.length === 1 ? "papel" : "papéis"}
                </Badge>
                <Badge tone={userCount ? "success" : "warning"}>
                  {userCount} {userCount === 1 ? "usuário" : "usuários"}
                </Badge>
              </span>
            </summary>

            {roles.length > 0 ? (
              <ul className="manifest-access-tree manifest-access-tree--nested">
                {roles.map((r) => (
                  <li key={r.id} className="manifest-access-tree__item">
                    <div className="manifest-access-node">
                      <span className="manifest-access-node__label">
                        <Shield size={13} aria-hidden="true" />
                        <button
                          type="button"
                          className="manifest-access-node__link"
                          onClick={() => navigate(`/admin/roles/${r.id}`)}
                          title="Abrir papel"
                        >
                          {r.name}
                        </button>
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="hint">
                Nenhum papel concede este code — ninguém acessa a rota
                protegida por ele.
              </p>
            )}
          </details>
        );
      })}
    </div>
  );
}
