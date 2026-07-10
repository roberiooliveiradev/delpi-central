import { createDashboardStatusBadge } from "@delpi/plugin-ui/index";

import "./StatusBadge.css";

/** Pill semântico de status (neutral/info/success/warning/danger). */
export const StatusBadge = createDashboardStatusBadge({ prefix: "si" });

export type { StatusBadgeVariant } from "@delpi/plugin-ui/index";
