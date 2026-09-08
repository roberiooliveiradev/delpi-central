import type { LucideIcon } from "lucide-react";
import { ClipboardList, FileText, PackagePlus } from "lucide-react";

/** Mapa MFE code → ícone (sem metadado no banco neste entregável). */
const REQUEST_TYPE_ICONS: Record<string, LucideIcon> = {
  "invoice-issuance": FileText,
  "raw-material-creation": PackagePlus,
};

export function iconForRequestType(code: string): LucideIcon {
  return REQUEST_TYPE_ICONS[code] || ClipboardList;
}
