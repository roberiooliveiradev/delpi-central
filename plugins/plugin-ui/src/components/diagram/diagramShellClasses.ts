/** Root shell + alias opcional do consumidor (ex.: `dashboard-transformometro`). */
export function flowchartEditorShellClassName(consumerRootClass?: string): string {
  return ["delpi-ui-flowchart-shell", consumerRootClass].filter(Boolean).join(" ");
}

export const FLOWCHART_EDITOR_ROOT_CLASS = "tm-diagram-editor";
