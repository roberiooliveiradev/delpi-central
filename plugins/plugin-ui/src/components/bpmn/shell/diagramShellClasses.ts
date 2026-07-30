/** Root shell + alias opcional do consumidor (ex.: `dashboard-transformometro`). */
export function flowchartEditorShellClassName(consumerRootClass?: string): string {
  return ["delpi-ui-flowchart-shell", consumerRootClass].filter(Boolean).join(" ");
}

/** Classe canônica do root do editor. */
export const FLOWCHART_EDITOR_ROOT_CLASS = "delpi-ui-bpmn-editor";

/** Legado — mantido em dual-class para CSS remoto/cache durante a migração. */
export const FLOWCHART_EDITOR_ROOT_CLASS_LEGACY = "tm-diagram-editor";

/**
 * Dual BEM do editor: `delpi-ui-bpmn-editor{suffix}` + `tm-diagram-editor{suffix}`.
 * Sufixos: `""`, `"--fill"`, `"--overlay-tools"`, `"__canvas"`, `"__stage"`, etc.
 */
export function bpmnEditorBem(...suffixes: string[]): string {
  const classes: string[] = [];
  for (const suffix of suffixes) {
    classes.push(`${FLOWCHART_EDITOR_ROOT_CLASS}${suffix}`, `${FLOWCHART_EDITOR_ROOT_CLASS_LEGACY}${suffix}`);
  }
  return classes.join(" ");
}
