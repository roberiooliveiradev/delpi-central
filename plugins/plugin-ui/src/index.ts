/**
 * @delpi/plugin-ui — componentes React reutilizáveis para plugins MFE.
 *
 * Catálogo: docs/component-catalog.md
 * Como contribuir: docs/contributing.md
 */
export * from "./components/actions";
export * from "./components/help";
export * from "./components/layout";
export * from "./components/navigation";
export * from "./components/feedback";
export * from "./components/data";
export * from "./components/forms";
export * from "./components/preview";
export * from "./components/charts";
export * from "./components/bpmn";
export * from "./components/org";
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
export * from "./components/collaboration";
export * from "./brand";
export * from "./theme";
/**
 * Export nomeado — Color Family Catalog é consumido por hosts (ex.: chat MFE)
 * sem uso interno no remote; `export *` sozinho pode sumir no tree-shake do MF
 * e o host recebe `resolveColorFamily` undefined → TypeError "X is not a function".
 */
export {
  getColorFamilyDefinition,
  listColorFamilies,
  resolveColorFamily,
} from "./theme/colorFamilyCatalog";
export * from "./utils";
export * from "./displayFormat";
export * from "./components/displayFormat";
export * from "./hooks";
export * from "./types/chartGranularity";
export * from "./export";
export * from "./overlayLayers";
