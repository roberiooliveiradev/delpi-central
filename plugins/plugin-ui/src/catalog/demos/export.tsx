import { DocumentExportActions, ExcelExportButton, TabularExportButtons } from "../../export";
import type { CatalogEntryDraft } from "../types";

function noopExport() {
  // Demo only — sem download real no catálogo.
}

export const exportCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "export.TabularExportButtons",
    family: "export",
    exportName: "TabularExportButtons",
    title: "TabularExportButtons",
    description: "Grupo CSV · Excel · PDF (handler no-op na demo).",
    docAnchor: "tabularexportbuttons",
    propsSummary: ["onExport", "actions", "exporting"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <TabularExportButtons onExport={noopExport} />,
      },
    ],
  },
  {
    id: "export.DocumentExportActions",
    family: "export",
    exportName: "DocumentExportActions",
    title: "DocumentExportActions",
    description: "Par Excel + PDF.",
    docAnchor: "documentexportactions",
    propsSummary: ["onExportExcel", "onExportPdf"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <DocumentExportActions onExportExcel={noopExport} onExportPdf={noopExport} />
        ),
      },
    ],
  },
  {
    id: "export.ExcelExportButton",
    family: "export",
    exportName: "ExcelExportButton",
    title: "ExcelExportButton",
    description: "Botão único de exportação Excel.",
    docAnchor: "excelexportbutton",
    propsSummary: ["onExport"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <ExcelExportButton onExport={noopExport} />,
      },
    ],
  },
];
