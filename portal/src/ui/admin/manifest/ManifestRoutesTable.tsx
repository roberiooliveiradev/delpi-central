// portal/src/ui/admin/manifest/ManifestRoutesTable.tsx

import { Fragment, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp, Image as ImageIcon } from "lucide-react";
import {
  Button,
  DenseTable,
  FormField,
  Input,
  Select,
  Switch,
} from "../../../ui-kit";
import type { ManifestPermission, ManifestRoute } from "./manifestTypes";
import { normalizeRouteOrders } from "./manifestUtils";

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
  const [expanded, setExpanded] = useState<number | null>(null);

  const updateAt = (idx: number, patch: Partial<ManifestRoute>) => {
    onChange(routes.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  };

  const removeAt = (idx: number) => {
    setExpanded(null);
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

  /** A ordem digitada só reposiciona a rota ao sair do campo, senão a linha
   *  saltaria de lugar a cada tecla. */
  const commitOrder = () => onChange(normalizeRouteOrders(routes));

  const permOptions = [
    { value: "", label: "(Pública)" },
    ...permissions.map((p) => ({ value: p.code, label: p.code })),
  ];

  return (
    <DenseTable
      toolbar={
        <>
          <span className="hint">
            <code>permission</code> referencia <code>permissions[].code</code>
          </span>
          <Button variant="primary" size="sm" onClick={add} disabled={disabled}>
            Adicionar rota
          </Button>
        </>
      }
      wrapTable
    >
      <thead>
        <tr>
          <th>Ord</th>
          <th>Path</th>
          <th>Label</th>
          <th>Permissão</th>
          <th>Ícone</th>
          <th>Menu</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {routes.map((r, idx) => (
          <Fragment key={`r-${idx}`}>
            <tr
              className={
                expanded === idx ? "portal-ui-dense__row--expanded" : undefined
              }
            >
              <td style={{ width: 72 }}>
                <Input
                  type="number"
                  min={1}
                  size="sm"
                  value={r.order ?? ""}
                  disabled={disabled}
                  aria-label="Ordem da rota"
                  onChange={(e) =>
                    updateAt(idx, {
                      order: e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                  onBlur={commitOrder}
                />
              </td>
              <td>
                <Input
                  size="sm"
                  mono
                  value={r.path}
                  disabled={disabled}
                  onChange={(e) => updateAt(idx, { path: e.target.value })}
                  placeholder="ex: /apps/crm"
                />
              </td>
              <td>
                <Input
                  size="sm"
                  value={r.label ?? ""}
                  disabled={disabled}
                  onChange={(e) => updateAt(idx, { label: e.target.value })}
                />
              </td>
              <td>
                <Select
                  size="sm"
                  value={r.permission ?? ""}
                  disabled={disabled}
                  options={permOptions}
                  aria-label="Permissão da rota"
                  onChange={(next) =>
                    updateAt(idx, { permission: next || null })
                  }
                />
              </td>
              <td>
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
              </td>
              <td>
                <Switch
                  checked={r.showInMenu !== false}
                  disabled={disabled}
                  onChange={(e) =>
                    updateAt(idx, { showInMenu: e.target.checked })
                  }
                  aria-label="Exibir no menu"
                />
              </td>
              <td>
                <div className="portal-ui-dense__actions">
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-expanded={expanded === idx}
                    aria-label={
                      expanded === idx ? "Ocultar detalhes" : "Mais detalhes"
                    }
                    title={expanded === idx ? "Ocultar detalhes" : "Mais detalhes"}
                    onClick={() => setExpanded(expanded === idx ? null : idx)}
                    icon={
                      expanded === idx ? (
                        <ChevronUp size={14} />
                      ) : (
                        <ChevronDown size={14} />
                      )
                    }
                  />
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
              </td>
            </tr>
            {expanded === idx && (
              <tr className="portal-ui-dense__detail">
                <td colSpan={7}>
                  <div className="portal-ui-dense__detail-inner">
                    <FormField
                      label="Entry da rota (opcional)"
                      htmlFor={`route-entry-${idx}`}
                    >
                      <Input
                        id={`route-entry-${idx}`}
                        size="sm"
                        mono
                        value={r.entry ?? ""}
                        disabled={disabled}
                        onChange={(e) =>
                          updateAt(idx, { entry: e.target.value || null })
                        }
                      />
                    </FormField>
                  </div>
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <td colSpan={7}>
            <span className="hint">{routes.length} rotas</span>
          </td>
        </tr>
      </tfoot>
    </DenseTable>
  );
}
