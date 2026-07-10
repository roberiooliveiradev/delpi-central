#!/usr/bin/env python3
"""Consolida imports duplicados de @delpi/plugin-ui/index (MF rollup)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASHBOARDS = [
    "dashboard-production",
    "dashboard-commercial",
    "dashboard-engineering",
    "dashboard-financial",
    "dashboard-hr",
    "dashboard-lmps",
    "dashboard-quality",
    "dashboard-supplies",
]

EXPORT_UTILS_BODY = '''/**
 * Reexporta o motor tabular canônico (`@delpi/plugin-ui`).
 */
import {{
  triggerFileDownload,
  triggerBlobDownload,
  csvCell,
  buildUtf8CsvBlob,
  sanitizeFilename,
  sanitizeSheetName,
  exportAlert,
  configureExportAlert,
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadsToCsv,
  exportPayloadsToXlsx,
  TABULAR_EXPORT_ACTIONS,
  exportPayloadToPdf as sharedExportPayloadToPdf,
  exportPayloadsToPdf as sharedExportPayloadsToPdf,
  exportTableFormat as sharedExportTableFormat,
  type TabularExportFormat,
  type ExportAction,
  type ExportColumn,
  type TableExportPayload,
  type ExportAlertFn,
  type ExportPdfOptions,
}} from "@delpi/plugin-ui/index";

export {{
  triggerFileDownload,
  triggerBlobDownload,
  csvCell,
  buildUtf8CsvBlob,
  sanitizeFilename,
  sanitizeSheetName,
  exportAlert,
  configureExportAlert,
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadsToCsv,
  exportPayloadsToXlsx,
  TABULAR_EXPORT_ACTIONS,
}};

export type {{
  TabularExportFormat,
  ExportAction,
  ExportColumn,
  TableExportPayload,
  ExportAlertFn,
  ExportPdfOptions,
}};

const {subtitle_var} = "{subtitle}";

export function exportPayloadToPdf(
  payload: TableExportPayload,
  options?: ExportPdfOptions,
): void {{
  sharedExportPayloadToPdf(payload, {{
    subtitle: options?.subtitle ?? {subtitle_var},
  }});
}}

export function exportPayloadsToPdf(
  title: string,
  payloads: TableExportPayload[],
  options?: ExportPdfOptions,
): void {{
  sharedExportPayloadsToPdf(title, payloads, {{
    subtitle: options?.subtitle ?? {subtitle_var},
  }});
}}

export function exportTableFormat(
  payload: TableExportPayload,
  format: TabularExportFormat,
  options?: ExportPdfOptions,
): void {{
  sharedExportTableFormat(payload, format, {{
    subtitle: options?.subtitle ?? {subtitle_var},
  }});
}}
'''

COMMERCIAL_EXPORT_UTILS_HEADER = '''/**
 * Reexporta o motor tabular canônico (`@delpi/plugin-ui`).
 * Mantém subtítulo do PDF Comercial e API estável para builders/dispatch locais.
 */
'''

PDF_INDEX_BODY = '''/** PDF DELPI — motor canônico em @delpi/plugin-ui. */
import {{
  exportChartPayloadToPdf as sharedExportChartPayloadToPdf,
  exportTablePayloadToPdf as sharedExportTablePayloadToPdf,
  exportTablePayloadsToPdf as sharedExportTablePayloadsToPdf,
  buildDelpiDocumentStyles,
  buildDelpiBrandBarHtml,
  buildDelpiDocumentHtml,
  buildDelpiDocumentTableSection,
  buildDefaultExportSummaryLines,
  escapeDelpiDocumentHtml,
  resolveDelpiLogoUrl,
  printDelpiDocumentHtml,
  printDelpiDocumentSpec,
  type TableExportPayload,
  type ExportPdfOptions,
  type DelpiDocumentBadgeTone,
  type DelpiDocumentColumn,
  type DelpiDocumentImageSection,
  type DelpiDocumentSpec,
  type DelpiDocumentSummaryLine,
  type DelpiDocumentTable,
}} from "@delpi/plugin-ui/index";

export {{
  buildDelpiDocumentStyles,
  buildDelpiBrandBarHtml,
  buildDelpiDocumentHtml,
  buildDelpiDocumentTableSection,
  buildDefaultExportSummaryLines,
  escapeDelpiDocumentHtml,
  resolveDelpiLogoUrl,
  printDelpiDocumentHtml,
  printDelpiDocumentSpec,
}};

export type {{
  DelpiDocumentBadgeTone,
  DelpiDocumentColumn,
  DelpiDocumentImageSection,
  DelpiDocumentSpec,
  DelpiDocumentSummaryLine,
  DelpiDocumentTable,
}};

const PDF_SUBTITLE = "{subtitle}";

export function exportTablePayloadToPdf(
  payload: TableExportPayload,
  options?: ExportPdfOptions,
): void {{
  sharedExportTablePayloadToPdf(payload, {{
    subtitle: options?.subtitle ?? PDF_SUBTITLE,
  }});
}}

export function exportTablePayloadsToPdf(
  title: string,
  payloads: TableExportPayload[],
  options?: ExportPdfOptions,
): void {{
  sharedExportTablePayloadsToPdf(title, payloads, {{
    subtitle: options?.subtitle ?? PDF_SUBTITLE,
  }});
}}

export function exportChartPayloadToPdf(
  title: string,
  payload: TableExportPayload,
  chartDataUrl: string | null,
  options?: ExportPdfOptions,
): void {{
  sharedExportChartPayloadToPdf(title, payload, chartDataUrl, {{
    subtitle: options?.subtitle ?? PDF_SUBTITLE,
  }});
}}
'''

SUBTITLES = {
    "dashboard-production": ("PDF_SUBTITLE", "Minha DELPI · Dashboard Produção"),
    "dashboard-commercial": ("COMMERCIAL_PDF_SUBTITLE", "Minha DELPI · Dashboard Comercial"),
    "dashboard-engineering": ("PDF_SUBTITLE", "Minha DELPI · Dashboard Engenharia"),
    "dashboard-financial": ("PDF_SUBTITLE", "Minha DELPI · Dashboard Financeiro"),
    "dashboard-hr": ("PDF_SUBTITLE", "Minha DELPI · Dashboard RH"),
    "dashboard-lmps": ("PDF_SUBTITLE", "Minha DELPI · Dashboard LMPs"),
    "dashboard-quality": ("PDF_SUBTITLE", "Minha DELPI · Dashboard Qualidade"),
    "dashboard-supplies": ("PDF_SUBTITLE", "Minha DELPI · Dashboard Suprimentos"),
}


def fix_export_utils(name: str) -> None:
    var, subtitle = SUBTITLES[name]
    body = EXPORT_UTILS_BODY.format(subtitle_var=var, subtitle=subtitle)
    if name == "dashboard-commercial":
        body = COMMERCIAL_EXPORT_UTILS_HEADER + body.split("*/", 1)[1]
    path = ROOT / "plugins" / name / "src/export/exportUtils.ts"
    path.write_text(body, encoding="utf-8")
    print(f"fixed exportUtils: {name}")


def fix_pdf_index(name: str) -> None:
    _, subtitle = SUBTITLES[name]
    path = ROOT / "plugins" / name / "src/export/pdf/index.ts"
    path.write_text(PDF_INDEX_BODY.format(subtitle=subtitle), encoding="utf-8")
    print(f"fixed pdf/index: {name}")


def main() -> None:
    for name in DASHBOARDS:
        fix_export_utils(name)
        fix_pdf_index(name)


if __name__ == "__main__":
    main()
