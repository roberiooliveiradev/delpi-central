import type { ReactNode } from "react";
import {
  FilePenLine,
  FilePlus2,
  FileText,
  FileX2,
  GitBranch,
  PenLine,
  Send,
  ShieldCheck,
  Trash2,
  UserCheck,
  Users,
  XCircle,
} from "lucide-react";

import type { TimelineItemModel } from "@delpi/plugin-ui/index";

import { buildMinuteHistoryTimeline } from "./minuteHistoryTimeline";

const ACTION_ICONS: Record<string, ReactNode> = {
  create: <FilePlus2 size={12} />,
  edit: <FilePenLine size={12} />,
  edit_content: <FileText size={12} />,
  replace_participants: <Users size={12} />,
  replace_signers: <UserCheck size={12} />,
  send_for_signature: <Send size={12} />,
  sign: <PenLine size={12} />,
  signature_progress: <ShieldCheck size={12} />,
  refuse_signature: <XCircle size={12} />,
  create_version: <GitBranch size={12} />,
  finalize: <ShieldCheck size={12} />,
  cancel: <FileX2 size={12} />,
  soft_delete: <Trash2 size={12} />,
};

/**
 * Monta a timeline da ata com ícones Lucide no marker (kit Timeline).
 */
export function buildMinuteHistoryTimelineItems(
  versions: Record<string, unknown>[],
  audit: Record<string, unknown>[],
): TimelineItemModel[] {
  return buildMinuteHistoryTimeline(versions, audit).map((item) => ({
    ...item,
    marker: ACTION_ICONS[item.action || ""] ?? <GitBranch size={12} />,
  }));
}
