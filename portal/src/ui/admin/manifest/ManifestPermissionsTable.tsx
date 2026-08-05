// portal/src/ui/admin/manifest/ManifestPermissionsTable.tsx

import { Button, DenseTable, Input } from "../../../ui-kit";
import type { ManifestPermission } from "./manifestTypes";

type Props = {
  permissions: ManifestPermission[];
  moduleId: string;
  disabled?: boolean;
  onChange: (next: ManifestPermission[]) => void;
  onWhoUses?: (code: string) => void;
  onGrantToRole?: (code: string) => void;
};

export function ManifestPermissionsTable({
  permissions,
  moduleId,
  disabled,
  onChange,
  onWhoUses,
  onGrantToRole,
}: Props) {
  const prefix = moduleId ? `${moduleId}.` : "";

  const updateAt = (idx: number, patch: Partial<ManifestPermission>) => {
    const next = permissions.map((p, i) => (i === idx ? { ...p, ...patch } : p));
    onChange(next);
  };

  const removeAt = (idx: number) => {
    onChange(permissions.filter((_, i) => i !== idx));
  };

  const add = () => {
    onChange([
      ...permissions,
      {
        code: prefix ? `${prefix}access` : ".access",
        name: "Nova permissão",
        description: "",
        module: moduleId || "",
      },
    ]);
  };

  const duplicate = (idx: number) => {
    const src = permissions[idx];
    if (!src) return;
    const suffix = (src.code || "").split(".").slice(1).join(".") || "access";
    onChange([
      ...permissions,
      {
        ...src,
        code: `${prefix || ""}${suffix}-copy`,
        name: `${src.name || suffix} (cópia)`,
        module: moduleId || src.module,
      },
    ]);
  };

  return (
    <DenseTable
      toolbar={
        <>
          <span className="hint">
            Módulo fixo: <code>{moduleId || "(defina o ID)"}</code>
          </span>
          <Button variant="primary" size="sm" onClick={add} disabled={disabled}>
            Adicionar permissão
          </Button>
        </>
      }
      wrapTable
    >
      <thead>
        <tr>
          <th>Código</th>
          <th>Nome</th>
          <th>Descrição</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {permissions.map((p, idx) => {
          const suffix = p.code.includes(".")
            ? p.code.slice(p.code.indexOf(".") + 1)
            : p.code.replace(/^\./, "");
          return (
            <tr key={idx}>
              <td>
                <Input
                  size="sm"
                  mono
                  prefix={prefix || "."}
                  value={suffix}
                  disabled={disabled}
                  onChange={(e) =>
                    updateAt(idx, {
                      code: `${prefix}${e.target.value.replace(/^\./, "")}`,
                      module: moduleId || p.module,
                    })
                  }
                  placeholder="access"
                />
              </td>
              <td>
                <Input
                  size="sm"
                  value={p.name ?? ""}
                  disabled={disabled}
                  onChange={(e) => updateAt(idx, { name: e.target.value })}
                />
              </td>
              <td>
                <Input
                  size="sm"
                  value={p.description ?? ""}
                  disabled={disabled}
                  onChange={(e) => updateAt(idx, { description: e.target.value })}
                />
              </td>
              <td>
                <div className="portal-ui-dense__actions">
                  {onWhoUses && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onWhoUses(p.code)}
                    >
                      Quem usa
                    </Button>
                  )}
                  {onGrantToRole && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onGrantToRole(p.code)}
                    >
                      Conceder
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => duplicate(idx)}
                    disabled={disabled}
                  >
                    Duplicar
                  </Button>
                  <Button
                    variant="danger-soft"
                    size="sm"
                    onClick={() => removeAt(idx)}
                    disabled={disabled}
                  >
                    Remover
                  </Button>
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
      <tfoot>
        <tr>
          <td colSpan={4}>
            <span className="hint">{permissions.length} permissões</span>
          </td>
        </tr>
      </tfoot>
    </DenseTable>
  );
}
