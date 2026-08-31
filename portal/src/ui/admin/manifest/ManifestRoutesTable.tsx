// portal/src/ui/admin/manifest/ManifestRoutesTable.tsx

import { type ReactNode } from "react";
import { GripVertical, Image as ImageIcon } from "lucide-react";
import {
  Button,
  FormField,
  Input,
  Select,
  Switch,
} from "../../../ui-kit";
import type { ManifestPermission, ManifestRoute } from "./manifestTypes";
import { moveRoute, normalizeRouteOrders } from "./manifestUtils";
import { useCardReorder } from "./useCardReorder";

type Props = {
  routes: ManifestRoute[];
  permissions: ManifestPermission[];
  basePath: string;
  disabled?: boolean;
  onChange: (next: ManifestRoute[]) => void;
  onPickIcon: (routeIndex: number) => void;
  onCreatePermFromRoute?: (route: ManifestRoute) => void;
  renderIcon?: (kebab: string | null | undefined) => ReactNode;
};

export function ManifestRoutesTable({
  routes,
  permissions,
  basePath,
  disabled,
  onChange,
  onPickIcon,
  onCreatePermFromRoute,
  renderIcon,
}: Props) {
  const { getCardProps, getHandleProps } = useCardReorder({
    count: routes.length,
    disabled,
    itemLabel: "rota",
    onMove: (from, to) => onChange(moveRoute(routes, from, to)),
  });

  const updateAt = (idx: number, patch: Partial<ManifestRoute>) => {
    onChange(routes.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  };

  const removeAt = (idx: number) => {
    onChange(normalizeRouteOrders(routes.filter((_, i) => i !== idx)));
  };

  const add = () => {
    onChange(
      normalizeRouteOrders([
        ...routes,
        {
          path: basePath || "",
          label: "Nova rota",
          permission: permissions[0]?.code || null,
          icon: "layout-dashboard",
          showInMenu: true,
          openInNewTab: false,
          order: routes.length + 1,
        },
      ])
    );
  };

  const duplicate = (idx: number) => {
    const src = routes[idx];
    if (!src) return;

    const copy = {
      ...src,
      path: `${src.path || basePath}-copy`,
      label: `${src.label || "Rota"} (cópia)`,
    };

    const next = [...routes];
    next.splice(idx + 1, 0, copy);
    onChange(normalizeRouteOrders(next));
  };

  /** A ordem digitada só reposiciona a rota ao sair do campo, senão o card
   *  saltaria de lugar a cada tecla. */
  const commitOrder = () => onChange(normalizeRouteOrders(routes));

  const permOptions = [
    { value: "", label: "(Pública)" },
    ...permissions.map((p) => ({ value: p.code, label: p.code })),
  ];

  return (
    <div className="manifest-cards">
      <div className="manifest-cards__toolbar">
        <span className="hint">
          <code>permission</code> referencia <code>permissions[].code</code> ·
          arraste pela alça para reordenar
        </span>
        <Button variant="primary" size="sm" onClick={add} disabled={disabled}>
          Adicionar rota
        </Button>
      </div>

      <ul className="manifest-cards__list">
        {routes.map((r, idx) => (
          <li key={`r-${idx}`} {...getCardProps(idx, "manifest-card")}>
            <div className="manifest-card__head">
              <button className="manifest-card__handle" {...getHandleProps(idx)}>
                <GripVertical size={16} aria-hidden />
              </button>

              <FormField
                label="Ord"
                htmlFor={`route-order-${idx}`}
                className="manifest-card__order"
              >
                <Input
                  id={`route-order-${idx}`}
                  type="number"
                  min={1}
                  size="sm"
                  value={r.order ?? ""}
                  disabled={disabled}
                  onChange={(e) =>
                    updateAt(idx, {
                      order:
                        e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                  onBlur={commitOrder}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      e.currentTarget.blur();
                    }
                  }}
                />
              </FormField>

              <FormField
                label="Path"
                htmlFor={`route-path-${idx}`}
                className="manifest-card__path"
              >
                <Input
                  id={`route-path-${idx}`}
                  size="sm"
                  mono
                  value={r.path}
                  disabled={disabled}
                  onChange={(e) => updateAt(idx, { path: e.target.value })}
                  placeholder="ex: /apps/crm"
                />
              </FormField>

              <div className="manifest-card__head-controls">
                <FormField label="Ícone">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={disabled}
                    onClick={() => onPickIcon(idx)}
                    title={r.icon ? `Ícone: ${r.icon}` : "Selecionar ícone"}
                    aria-label={
                      r.icon ? `Ícone ${r.icon}` : "Selecionar ícone da rota"
                    }
                    icon={renderIcon?.(r.icon) || <ImageIcon size={16} />}
                  />
                </FormField>

                <FormField label="Menu" htmlFor={`route-menu-${idx}`}>
                  <Switch
                    id={`route-menu-${idx}`}
                    checked={r.showInMenu !== false}
                    disabled={disabled}
                    onChange={(e) =>
                      updateAt(idx, { showInMenu: e.target.checked })
                    }
                    aria-label="Exibir no menu"
                  />
                </FormField>

                <FormField label="Nova aba" htmlFor={`route-new-tab-${idx}`}>
                  <Switch
                    id={`route-new-tab-${idx}`}
                    checked={Boolean(r.openInNewTab)}
                    disabled={disabled}
                    onChange={(e) =>
                      updateAt(idx, { openInNewTab: e.target.checked })
                    }
                    aria-label="Abrir em nova aba"
                  />
                </FormField>
              </div>

              <div className="manifest-card__actions">
                {onCreatePermFromRoute && (
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={disabled}
                    onClick={() => onCreatePermFromRoute(r)}
                  >
                    Criar perm.
                  </Button>
                )}
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={disabled}
                  onClick={() => duplicate(idx)}
                >
                  Duplicar
                </Button>
                <Button
                  variant="danger-soft"
                  size="sm"
                  disabled={disabled}
                  onClick={() => removeAt(idx)}
                >
                  Remover
                </Button>
              </div>
            </div>

            <div className="manifest-card__grid">
              <FormField
                label="Label"
                htmlFor={`route-label-${idx}`}
                className="manifest-card__field--wide"
              >
                <Input
                  id={`route-label-${idx}`}
                  value={r.label ?? ""}
                  disabled={disabled}
                  onChange={(e) => updateAt(idx, { label: e.target.value })}
                  placeholder="Nome exibido no menu"
                />
              </FormField>

              <FormField label="Permissão" htmlFor={`route-perm-${idx}`}>
                <Select
                  value={r.permission ?? ""}
                  disabled={disabled}
                  options={permOptions}
                  aria-label="Permissão da rota"
                  onChange={(next) => updateAt(idx, { permission: next || null })}
                />
              </FormField>

              <FormField
                label="Entry (opcional)"
                htmlFor={`route-entry-${idx}`}
                hint="Com «Nova aba», Entry http(s) abre o link; sem Entry abre o path."
              >
                <Input
                  id={`route-entry-${idx}`}
                  mono
                  value={r.entry ?? ""}
                  disabled={disabled}
                  onChange={(e) =>
                    updateAt(idx, { entry: e.target.value || null })
                  }
                  placeholder="ex: ./RemoteApp"
                />
              </FormField>
            </div>
          </li>
        ))}
      </ul>

      <span className="hint">{routes.length} rotas</span>
    </div>
  );
}
