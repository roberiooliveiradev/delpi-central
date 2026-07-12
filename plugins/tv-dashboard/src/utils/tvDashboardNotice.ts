import { exportAlert } from "@delpi/plugin-ui/index";

/** Aviso ao usuário no MFE (toast/alert configurável via plugin-ui). */
export function tvDashboardNotice(message: string): void {
  exportAlert(message);
}
