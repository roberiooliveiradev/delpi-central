import type { ReactNode } from "react";
import type {
  CanvasTableOptions,
  CanvasTableStylePresetId,
} from "@delpi/tv-dashboard-presentation";
import { canvasTablePresetOptions, mergeCanvasTableOptions } from "@delpi/tv-dashboard-presentation";

export type CanvasTableBlockStyleActionId =
  | "preset-grid"
  | "preset-minimal"
  | "preset-banded"
  | "toggle-banded-rows"
  | "toggle-banded-cols"
  | "header-subtle"
  | "header-accent"
  | "header-none"
  | "borders-all"
  | "borders-horizontal"
  | "borders-none";

type Props = {
  options?: CanvasTableOptions | null;
  headerRow?: boolean;
  onSelect: (actionId: CanvasTableBlockStyleActionId) => void;
  onToggleHeaderRow?: () => void;
  footer?: ReactNode;
  className?: string;
};

function resolveActivePreset(
  opts: ReturnType<typeof mergeCanvasTableOptions>,
): CanvasTableStylePresetId | null {
  for (const id of ["grid", "minimal", "banded"] as const) {
    const preset = canvasTablePresetOptions(id);
    if (
      opts.bandedRows === Boolean(preset.bandedRows) &&
      opts.bandedColumns === Boolean(preset.bandedColumns) &&
      opts.headerStyle === (preset.headerStyle ?? "subtle") &&
      opts.borderStyle === (preset.borderStyle ?? "all")
    ) {
      return id;
    }
  }
  return null;
}

type Choice = {
  id: CanvasTableBlockStyleActionId;
  label: string;
  active?: boolean;
};

/**
 * Menu pincel do **bloco** Grade — presets/faixas/cabeçalho/bordas.
 * Chrome `td-chart-style-menu`; sem `td-deck-ribbon__float-panel`.
 */
export function CanvasTableBlockStylesMenu({
  options,
  headerRow,
  onSelect,
  onToggleHeaderRow,
  footer,
  className,
}: Props) {
  const opts = mergeCanvasTableOptions(options);
  const activePreset = resolveActivePreset(opts);

  const presets: Choice[] = [
    { id: "preset-grid", label: "Grade", active: activePreset === "grid" },
    { id: "preset-minimal", label: "Minimalista", active: activePreset === "minimal" },
    { id: "preset-banded", label: "Faixas", active: activePreset === "banded" },
  ];
  const bands: Choice[] = [
    { id: "toggle-banded-rows", label: "Linhas alternadas", active: opts.bandedRows },
    { id: "toggle-banded-cols", label: "Colunas alternadas", active: opts.bandedColumns },
  ];
  const headers: Choice[] = [
    { id: "header-subtle", label: "Cabeçalho sutil", active: opts.headerStyle === "subtle" },
    { id: "header-accent", label: "Cabeçalho destaque", active: opts.headerStyle === "accent" },
    { id: "header-none", label: "Sem estilo de cabeçalho", active: opts.headerStyle === "none" },
  ];
  const borders: Choice[] = [
    { id: "borders-all", label: "Todas as bordas", active: opts.borderStyle === "all" },
    {
      id: "borders-horizontal",
      label: "Bordas horizontais",
      active: opts.borderStyle === "horizontal",
    },
    { id: "borders-none", label: "Sem bordas", active: opts.borderStyle === "none" },
  ];

  function renderSection(title: string, choices: Choice[]) {
    return (
      <section className="td-chart-style-menu__section">
        <h4>{title}</h4>
        <div className="td-chart-style-menu__styles">
          {choices.map((choice) => (
            <button
              key={choice.id}
              type="button"
              role="menuitemradio"
              aria-checked={Boolean(choice.active)}
              className={[
                "td-chart-style-menu__style",
                choice.active ? "td-chart-style-menu__style--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onSelect(choice.id)}
            >
              <span>{choice.label}</span>
            </button>
          ))}
        </div>
      </section>
    );
  }

  return (
    <div
      className={["td-chart-style-menu", className].filter(Boolean).join(" ")}
      role="menu"
      aria-label="Estilo do bloco Grade"
    >
      {renderSection("Presets", presets)}
      {renderSection("Faixas", bands)}
      {onToggleHeaderRow ? (
        <section className="td-chart-style-menu__section">
          <h4>Linha de cabeçalho</h4>
          <div className="td-chart-style-menu__styles">
            <button
              type="button"
              role="menuitemcheckbox"
              aria-checked={Boolean(headerRow)}
              className={[
                "td-chart-style-menu__style",
                headerRow ? "td-chart-style-menu__style--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={onToggleHeaderRow}
            >
              <span>Usar 1ª linha como cabeçalho</span>
            </button>
          </div>
        </section>
      ) : null}
      {renderSection("Cabeçalho", headers)}
      {renderSection("Bordas", borders)}
      {footer ? <div className="td-chart-style-menu__footer">{footer}</div> : null}
    </div>
  );
}
