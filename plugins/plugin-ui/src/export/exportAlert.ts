export type ExportAlertFn = (message: string) => void;

let exportAlertImpl: ExportAlertFn = (message) => {
  if (typeof window !== "undefined" && typeof window.alert === "function") {
    window.alert(message);
  }
};

/** Substitui o alert padrão (ex.: toast do plugin). */
export function configureExportAlert(fn: ExportAlertFn): void {
  exportAlertImpl = fn;
}

export function exportAlert(message: string): void {
  exportAlertImpl(message);
}
