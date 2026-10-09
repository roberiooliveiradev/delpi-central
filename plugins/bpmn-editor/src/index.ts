/**
 * @delpi/bpmn-editor — shared BPMN editor surface (G7 / ADR-006).
 *
 * EDITOR É COMPARTILHADO. ARTEFATO NÃO. Este package contém APENAS a
 * superfície de edição + o port `BpmnDocumentHost`; cada bounded context
 * implementa o próprio host (Modeler ↔ bpmn_modeler.*, Transformômetro ↔
 * transformometro.*).
 */
export { BpmnDocumentEditorPage } from "./pages/BpmnDocumentEditorPage";
export { BpmnRevisionViewPage } from "./pages/BpmnRevisionViewPage";
export type { BpmnDocumentHost, RevisionMeta } from "./host/BpmnDocumentHost";
export * from "./host/types";

export { BpmnEditorAdapter } from "./editor/BpmnEditorAdapter";
export type { DiagramRef, ElementSummary } from "./editor/BpmnEditorAdapter";
export { ElementInspector } from "./editor/inspector/ElementInspector";
export { hasUnpreservableExtensionContent } from "./editor/extensionPreservation";
export { renderBpmnThumbnail, type BpmnThumbnailResult } from "./editor/modelThumbnail";
export {
  BpmnReadonlyViewer,
  type BpmnReadonlyViewerProps,
  type BpmnReadonlyViewerStatus,
} from "./editor/BpmnReadonlyViewer";

export { editableMode } from "./state/capabilities";
export type { Capabilities, ReadOnlyReason } from "./state/capabilities";
export { SaveMachine } from "./state/saveMachine";
export type { SaveState } from "./state/saveMachine";
export { AutosaveController } from "./state/autosave";

export { PaletteSearch } from "./components/PaletteSearch";
export { ValidationPanel } from "./components/ValidationPanel";
export { SaveStatus } from "./components/SaveStatus";
export { ReadOnlyBanner } from "./components/ReadOnlyBanner";
export { ConflictDialog } from "./components/ConflictDialog";
export { UnsavedChangesDialog } from "./components/UnsavedChangesDialog";
export { CreateRevisionDialog } from "./components/CreateRevisionDialog";
export { RevisionHistoryList } from "./components/RevisionHistoryList";
export { DiagramSelector } from "./components/DiagramSelector";
export { useExportActions } from "./components/ExportMenu";

export * from "./ui/kit";
export { HELP_TOOLTIPS } from "./content/helpTooltips";
