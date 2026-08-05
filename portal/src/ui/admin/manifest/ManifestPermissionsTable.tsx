// portal/src/ui/admin/manifest/ManifestPermissionsTable.tsx

import { Button, FormField, Input, Textarea } from "../../../ui-kit";
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
    <div className="manifest-cards">
      <div className="manifest-cards__toolbar">
        <span className="hint">
          Módulo fixo: <code>{moduleId || "(defina o ID)"}</code>
        </span>
        <Button variant="primary" size="sm" onClick={add} disabled={disabled}>
          Adicionar permissão
        </Button>
      </div>

      <ul className="manifest-cards__list">
        {permissions.map((p, idx) => {
          const suffix = p.code.includes(".")
            ? p.code.slice(p.code.indexOf(".") + 1)
            : p.code.replace(/^\./, "");
          return (
            <li key={idx} className="manifest-card">
              <div className="manifest-card__head">
                <FormField
                  label="Código"
                  htmlFor={`perm-code-${idx}`}
                  className="manifest-card__code"
                >
                  <Input
                    id={`perm-code-${idx}`}
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
                </FormField>

                <div className="manifest-card__actions">
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
              </div>

              <div className="manifest-card__grid manifest-card__grid--full">
                <FormField label="Nome" htmlFor={`perm-name-${idx}`}>
                  <Input
                    id={`perm-name-${idx}`}
                    value={p.name ?? ""}
                    disabled={disabled}
                    onChange={(e) => updateAt(idx, { name: e.target.value })}
                    placeholder="Ex.: Acessar módulo"
                  />
                </FormField>

                <FormField label="Descrição" htmlFor={`perm-desc-${idx}`}>
                  <Textarea
                    id={`perm-desc-${idx}`}
                    rows={2}
                    autoGrow
                    value={p.description ?? ""}
                    disabled={disabled}
                    onChange={(e) =>
                      updateAt(idx, { description: e.target.value })
                    }
                    placeholder="O que esta permissão libera para o usuário"
                  />
                </FormField>
              </div>
            </li>
          );
        })}
      </ul>

      <span className="hint">{permissions.length} permissões</span>
    </div>
  );
}
