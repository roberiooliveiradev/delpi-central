import type { LucideIcon } from "lucide-react";
import {
  Ban,
  CheckCircle2,
  CirclePlay,
  Eye,
  FileCheck2,
  Pencil,
  RotateCcw,
  Send,
  XCircle,
} from "lucide-react";

import { MY_REQUESTS_HELP_TOOLTIPS } from "./helpTooltips";
import { actionButtonVariant, actionLabel } from "./presentationLabels";

export type ActionPresentation = {
  label: string;
  variant: "primary" | "ghost" | "default";
  Icon: LucideIcon;
  help: string;
};

const ACTION_ICONS: Record<string, LucideIcon> = {
  view: Eye,
  edit: Pencil,
  start: CirclePlay,
  return: RotateCcw,
  resubmit: Send,
  complete: CheckCircle2,
  issue: FileCheck2,
  cancel: XCircle,
  reject: Ban,
};

const ACTION_HELPS = MY_REQUESTS_HELP_TOOLTIPS.actions;

/** Presentation-only mapping — codes remain API `allowed_actions`. */
export function resolveActionPresentation(action: string): ActionPresentation {
  const code = action.trim();
  const help =
    (ACTION_HELPS as Record<string, string>)[code] ||
    MY_REQUESTS_HELP_TOOLTIPS.detail.actions;
  return {
    label: code === "edit" ? "Corrigir dados" : actionLabel(code),
    variant: actionButtonVariant(code),
    Icon: ACTION_ICONS[code] || Send,
    help,
  };
}
