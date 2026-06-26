#!/usr/bin/env python3
"""Replica o módulo de exportação tabular (CSV/Excel/PDF) do commercial para os demais dashboards."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMERCIAL_EXPORT = ROOT / "plugins/dashboard-commercial/src/export"
COMMERCIAL_PDF = COMMERCIAL_EXPORT / "pdf"

PLUGINS = [
    {
        "dir": "plugins/dashboard-production",
        "name": "Production",
        "slug": "production",
        "prefix": "dp",
        "subtitle": "Minha DELPI · Dashboard Produção",
    },
    {
        "dir": "plugins/dashboard-quality",
        "name": "Quality",
        "slug": "quality",
        "prefix": "dq",
        "subtitle": "Minha DELPI · Dashboard Qualidade",
    },
    {
        "dir": "plugins/dashboard-financial",
        "name": "Financial",
        "slug": "financial",
        "prefix": "ds",
        "subtitle": "Minha DELPI · Dashboard Financeiro",
    },
    {
        "dir": "plugins/dashboard-hr",
        "name": "Hr",
        "slug": "hr",
        "prefix": "dh",
        "subtitle": "Minha DELPI · Dashboard RH",
    },
    {
        "dir": "plugins/dashboard-supplies",
        "name": "Supplies",
        "slug": "supplies",
        "prefix": "ds",
        "subtitle": "Minha DELPI · Dashboard Suprimentos",
    },
    {
        "dir": "plugins/dashboard-engineering",
        "name": "Engineering",
        "slug": "engineering",
        "prefix": "ds",
        "subtitle": "Minha DELPI · Dashboard Engenharia",
    },
    {
        "dir": "plugins/dashboard-lmps",
        "name": "Lmps",
        "slug": "lmps",
        "prefix": "lmps",
        "subtitle": "Minha DELPI · Dashboard LMPs",
    },
]

EXPORT_CSS = """
/* export tabular — sincronizado com dashboard-commercial */
.{root} .{prefix}-export-actions {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}}

.{root} .{prefix}-export-actions--compact .{prefix}-export-actions__btn {{
  min-height: 34px;
  padding: 0 10px;
  font-size: 0.8125rem;
}}

.{root} .{prefix}-export-actions__btn {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
}}

.{root} .{prefix}-header-action {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}}
"""

CSS_MARKER = "/* export tabular — sincronizado com dashboard-commercial */"


def types_ts(name: str, slug: str) -> str:
    request = f"{name}ExportRequest"
    return f'''export type TabularExportFormat = "csv" | "xlsx" | "pdf";

export type ExportAction = {{
  format: TabularExportFormat;
  label: string;
  title: string;
}};

export const TABULAR_EXPORT_ACTIONS: ReadonlyArray<ExportAction> = [
  {{ format: "csv", label: "CSV", title: "Baixar CSV" }},
  {{ format: "xlsx", label: "Excel", title: "Baixar Excel" }},
  {{ format: "pdf", label: "PDF", title: "Baixar PDF" }},
];

export type ExportColumn = {{ key: string; label: string }};

export type TableExportPayload = {{
  title: string;
  columns: ExportColumn[];
  rows: Record<string, unknown>[];
}};

export type DashboardKpiExportRow = {{
  indicador: string;
  valor: string;
  contexto: string;
}};

export type DashboardExportContext = {{
  documentTitle: string;
  periodLabel: string;
  scopeLabel: string;
  sheets: TableExportPayload[];
}};

export type {request} =
  | {{
      kind: "table";
      payload: TableExportPayload;
      format: TabularExportFormat;
    }}
  | {{
      kind: "dashboard";
      context: DashboardExportContext;
      format: TabularExportFormat;
    }};
'''


def dispatch_ts(name: str, slug: str, subtitle: str) -> str:
    run_fn = f"run{name}Export"
    request = f"{name}ExportRequest"
    return f'''import {{
  exportPayloadsToCsv,
  exportPayloadsToPdf,
  exportPayloadsToXlsx,
  exportTableFormat,
}} from "./exportUtils";
import type {{{request}}} from "./types";

const DASHBOARD_SUBTITLE = "{subtitle}";

export function {run_fn}(request: {request}): void {{
  switch (request.kind) {{
    case "table":
      exportTableFormat(request.payload, request.format);
      return;
    case "dashboard": {{
      const sheets = request.context.sheets.filter(
        (sheet) => sheet.columns.length > 0,
      );
      if (request.format === "xlsx") {{
        exportPayloadsToXlsx(request.context.documentTitle, sheets);
        return;
      }}
      if (request.format === "pdf") {{
        exportPayloadsToPdf(request.context.documentTitle, sheets, {{
          subtitle: DASHBOARD_SUBTITLE,
        }});
        return;
      }}
      exportPayloadsToCsv(request.context.documentTitle, sheets);
      return;
    }}
    default: {{
      const _exhaustive: never = request;
      return _exhaustive;
    }}
  }}
}}
'''


def buttons_ts(name: str, prefix: str) -> str:
    run_fn = f"run{name}Export"
    component = f"{name}ExportButtons"
    props = f"{name}ExportButtonsProps"
    return f'''import {{ Download }} from "lucide-react";

import {{ {run_fn} }} from "./dispatch";
import {{ TABULAR_EXPORT_ACTIONS }} from "./types";
import type {{
  DashboardExportContext,
  TabularExportFormat,
  TableExportPayload,
}} from "./types";

type ExportButtonsBaseProps = {{
  disabled?: boolean;
  className?: string;
  buttonClassName?: string;
  showIcon?: boolean;
}};

type TableExportButtonsProps = ExportButtonsBaseProps & {{
  variant: "table";
  payload: TableExportPayload;
  resolvePayload?: () => Promise<TableExportPayload>;
}};

type DashboardExportButtonsProps = ExportButtonsBaseProps & {{
  variant: "dashboard";
  context: DashboardExportContext;
  resolveContext?: () => Promise<DashboardExportContext>;
}};

export type {props} = TableExportButtonsProps | DashboardExportButtonsProps;

function dispatchRequest(
  props: {props},
  format: TabularExportFormat,
): void {{
  if (props.variant === "table") {{
    void (async () => {{
      const payload = props.resolvePayload
        ? await props.resolvePayload()
        : props.payload;
      {run_fn}({{
        kind: "table",
        payload,
        format,
      }});
    }})();
    return;
  }}

  void (async () => {{
    const context = props.resolveContext
      ? await props.resolveContext()
      : props.context;
    {run_fn}({{ kind: "dashboard", context, format }});
  }})();
}}

export function {component}(props: {props}) {{
  const {{
    disabled = false,
    className = "{prefix}-export-actions",
    buttonClassName = "{prefix}-ghost-btn {prefix}-export-actions__btn",
    showIcon = true,
  }} = props;

  return (
    <div className={{className}} role="group" aria-label="Exportar dados">
      {{TABULAR_EXPORT_ACTIONS.map((action) => (
        <button
          key={{action.format}}
          type="button"
          className={{buttonClassName}}
          title={{action.title}}
          aria-label={{action.title}}
          disabled={{disabled}}
          onClick={{() => dispatchRequest(props, action.format)}}
        >
          {{showIcon ? <Download size={{15}} aria-hidden="true" /> : null}}
          <span>{{action.label}}</span>
        </button>
      ))}}
    </div>
  );
}}
'''


def builders_ts() -> str:
    return '''import type {
  DashboardExportContext,
  DashboardKpiExportRow,
  TableExportPayload,
} from "./types";

export function buildDashboardKpisPayload(
  rows: DashboardKpiExportRow[],
): TableExportPayload {
  return {
    title: "Indicadores",
    columns: [
      { key: "indicador", label: "Indicador" },
      { key: "valor", label: "Valor" },
      { key: "contexto", label: "Contexto" },
    ],
    rows,
  };
}

export function buildDashboardExportContext(
  base: Pick<DashboardExportContext, "documentTitle" | "periodLabel" | "scopeLabel">,
  kpiRows: DashboardKpiExportRow[],
  extraSheets: TableExportPayload[] = [],
): DashboardExportContext {
  const sheets = [buildDashboardKpisPayload(kpiRows), ...extraSheets].filter(
    (sheet) => sheet.columns.length > 0 && sheet.rows.length >= 0,
  );

  return {
    ...base,
    sheets,
  };
}
'''


def index_ts(name: str, slug: str) -> str:
    component = f"{name}ExportButtons"
    run_fn = f"run{name}Export"
    return f'''export {{ {run_fn} }} from "./dispatch";
export {{ {component} }} from "./{component}";
export type {{ {component}Props }} from "./{component}";
export {{
  buildDashboardExportContext,
  buildDashboardKpisPayload,
}} from "./dashboardExportBuilders";
export type {{
  DashboardExportContext,
  DashboardKpiExportRow,
  TabularExportFormat,
  TableExportPayload,
}} from "./types";
export {{ TABULAR_EXPORT_ACTIONS }} from "./types";
'''


def sync_plugin(plugin: dict[str, str]) -> None:
    name = plugin["name"]
    slug = plugin["slug"]
    prefix = plugin["prefix"]
    plugin_root = ROOT / plugin["dir"]
    export_dir = plugin_root / "src/export"
    export_dir.mkdir(parents=True, exist_ok=True)

    pdf_target = export_dir / "pdf"
    if pdf_target.exists():
        shutil.rmtree(pdf_target)
    shutil.copytree(COMMERCIAL_PDF, pdf_target)

    for src_name, content in [
        ("types.ts", types_ts(name, slug)),
        ("dispatch.ts", dispatch_ts(name, slug, plugin["subtitle"])),
        (f"{name}ExportButtons.tsx", buttons_ts(name, prefix)),
        ("dashboardExportBuilders.ts", builders_ts()),
        ("index.ts", index_ts(name, slug)),
    ]:
        (export_dir / src_name).write_text(content, encoding="utf-8")

    for copy_name in ("exportUtils.ts", "exportAlert.ts"):
        shutil.copy2(COMMERCIAL_EXPORT / copy_name, export_dir / copy_name)

    primitives_tail = (COMMERCIAL_EXPORT / "primitives.ts").read_text(encoding="utf-8")
    primitives_tail = primitives_tail.split("export function csvCell", 1)[1]
    primitives = (
        """export function triggerFileDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function csvCell"""
        + primitives_tail
    )
    (export_dir / "primitives.ts").write_text(primitives, encoding="utf-8")

    root_class = plugin_root.name

    css_path = plugin_root / "src/index.css"
    css_block = EXPORT_CSS.format(root=root_class, prefix=prefix)
    css_text = css_path.read_text(encoding="utf-8")
    if CSS_MARKER not in css_text:
        css_path.write_text(css_text.rstrip() + "\n" + css_block + "\n", encoding="utf-8")

    pkg_path = plugin_root / "package.json"
    pkg_text = pkg_path.read_text(encoding="utf-8")
    if '"xlsx"' not in pkg_text:
        pkg_text = pkg_text.replace(
            '"dependencies": {',
            '"dependencies": {\n    "xlsx": "^0.18.5",',
            1,
        )
        pkg_path.write_text(pkg_text, encoding="utf-8")

    print(f"OK {plugin['dir']}/src/export")


def main() -> None:
    for plugin in PLUGINS:
        sync_plugin(plugin)


if __name__ == "__main__":
    main()
