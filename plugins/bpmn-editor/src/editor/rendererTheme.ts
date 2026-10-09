/**
 * Theming canônico do renderer: CSS vars mapeadas no shell (light/dark via
 * `:root[data-theme]`). Fallbacks fixos rendem documento claro quando as vars
 * não existem (ex.: SVG exportado em `<img>` — contexto isolado sem vars).
 * DI colors do documento continuam vencendo (P5).
 *
 * Módulo próprio para que superfícies somente-leitura (NavigatedViewer)
 * não puxem o BpmnEditorAdapter (Modeler + properties panel) por um token.
 */
export const BPMN_RENDERER_THEME = {
  defaultFillColor: "var(--delpi-ui-bpmn-element-fill, #ffffff)",
  defaultStrokeColor: "var(--delpi-ui-bpmn-element-stroke, #22242a)",
  defaultLabelColor: "var(--delpi-ui-bpmn-label-color, #22242a)",
} as const;
