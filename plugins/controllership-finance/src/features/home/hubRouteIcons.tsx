import type { ReactNode } from "react";
import {
  CalendarCheck2,
  ClipboardList,
  ExternalLink,
  FileText,
  FolderOpen,
  Settings,
  ShieldCheck,
} from "lucide-react";

import type { PluginNavigationTarget } from "../../app/pluginRoutes";

const props = { size: 16, strokeWidth: 1.75, "aria-hidden": true as const };

/** Ícone por rota do hub (H2) — evita calendário genérico em tudo. */
export function hubRouteIcon(
  viewId: PluginNavigationTarget | string | undefined,
  opts?: { external?: boolean },
): ReactNode {
  if (opts?.external) {
    return <ExternalLink {...props} />;
  }
  switch (viewId) {
    case "entry_audit":
      return <ShieldCheck {...props} />;
    case "monthly_closing":
      return <CalendarCheck2 {...props} />;
    case "checklist_admin":
      return <ClipboardList {...props} />;
    case "documents_admin":
      return <FolderOpen {...props} />;
    case "catalogs_admin":
      return <Settings {...props} />;
    case "received_documents":
      return <FileText {...props} />;
    case "profile":
      return <Settings {...props} />;
    default:
      return <FileText {...props} />;
  }
}

export const LNF_EXTERNAL_TOOLTIP =
  "Abre o app Lançamento de Notas Fiscais";
