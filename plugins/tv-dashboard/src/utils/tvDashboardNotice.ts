import { configureExportAlert, exportAlert } from "@delpi/plugin-ui/index";

/**
 * Aviso ao usuário no MFE.
 * Em runtime o `NoticeDialogProvider` registra `configureExportAlert` → Modal Delpi.
 * Fora do provider (testes), cai no fallback do plugin-ui.
 */
export function tvDashboardNotice(message: string): void {
  exportAlert(message);
}

/** @internal — testes podem reverter o handler. */
export { configureExportAlert };
