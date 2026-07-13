import { CenteredScaledPreview } from "../../components/preview/CenteredScaledPreview";
import { CatalogStub } from "../CatalogStub";
import type { CatalogEntryDraft } from "../types";

export const previewCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "preview.FilePreviewModal",
    family: "preview",
    exportName: "FilePreviewModal",
    title: "FilePreviewModal",
    description: "Modal de prévia de arquivo (PDF/imagem/planilha).",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => (
          <CatalogStub
            name="FilePreviewModal"
            note="Requer File/blob ou previewState. Use no consumidor com anexo real."
          />
        ),
      },
    ],
  },
  {
    id: "preview.FilePreviewView",
    family: "preview",
    exportName: "FilePreviewView",
    title: "FilePreviewView",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => (
          <CatalogStub name="FilePreviewView" note="Renderiza conteúdo já resolvido pelo loader." />
        ),
      },
    ],
  },
  {
    id: "preview.FilePreviewMetaFooter",
    family: "preview",
    exportName: "FilePreviewMetaFooter",
    title: "FilePreviewMetaFooter",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => <CatalogStub name="FilePreviewMetaFooter" />,
      },
    ],
  },
  {
    id: "preview.CenteredScaledPreview",
    family: "preview",
    exportName: "CenteredScaledPreview",
    title: "CenteredScaledPreview",
    demos: [
      {
        id: "default",
        label: "Escalado",
        render: () => (
          <div className="puc-sandbox-chart" style={{ height: 160 }}>
            <CenteredScaledPreview referenceWidth={320} referenceHeight={120}>
              <div className="puc-card" style={{ width: 320, height: 120, padding: 24 }}>
                Conteúdo escalado ao centro
              </div>
            </CenteredScaledPreview>
          </div>
        ),
      },
    ],
  },
  {
    id: "preview.SpreadsheetPreview",
    family: "preview",
    exportName: "SpreadsheetPreview",
    title: "SpreadsheetPreview",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => (
          <CatalogStub name="SpreadsheetPreview" note="Requer parseSpreadsheetPreview + dados." />
        ),
      },
    ],
  },
  {
    id: "preview.DocxPreview",
    family: "preview",
    exportName: "DocxPreview",
    title: "DocxPreview",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => <CatalogStub name="DocxPreview" note="Requer parseDocxPreview + HTML." />,
      },
    ],
  },
];
