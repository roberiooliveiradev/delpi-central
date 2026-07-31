/**
 * @delpi/plugin-ui — componentes React reutilizáveis para plugins MFE.
 *
 * Catálogo: docs/component-catalog.md
 * Como contribuir: docs/contributing.md
 */
export * from "./components/actions";
export * from "./components/help";
export * from "./components/layout";
export * from "./components/feedback";
export * from "./components/data";
export * from "./components/forms";
export * from "./components/preview";
export * from "./components/charts";
export * from "./components/bpmn";

export * from "./components/shape";
/** Export nomeado — evita tree-shake do remote MF omitir a constante usada por hosts. */
export {
  SHAPE_CORNER_ADJUST_HANDLE,
  separateAdjustmentHandleFromChromeControls,
} from "./components/shape/selectionChromeAdjustSeparation";
export * from "./components/menu";
export * from "./components/signature";
export * from "./components/rich-text";
export * from "./components/ribbon";
export * from "./components/directory";
export * from "./components/document";
export * from "./components/deck";
export * from "./brand";
export * from "./theme";
export * from "./utils";
export * from "./hooks";
export * from "./types/chartGranularity";
export * from "./export";
export * from "./overlayLayers";
