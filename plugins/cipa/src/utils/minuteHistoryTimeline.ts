import type { TimelineItemModel, TimelineTone } from "@delpi/plugin-ui/index";

import { AUDIT_ACTION_LABELS } from "../constants/labels";
import { formatDateTimeBr } from "./htmlContent";

type RawRecord = Record<string, unknown>;

const AUDIT_ACTION_TONES: Record<string, TimelineTone> = {
  create: "info",
  send_for_signature: "info",
  sign: "success",
  finalize: "success",
  refuse_signature: "danger",
  cancel: "danger",
  soft_delete: "danger",
  create_version: "warning",
};

function str(record: RawRecord, key: string): string {
  const value = record[key];
  return value == null ? "" : String(value);
}

/**
 * Monta itens para o `Timeline` (layout `tree`) do plugin-ui:
 * tronco = versões da ata (mais recente primeiro); branches = eventos de
 * auditoria agrupados na janela temporal de cada versão.
 */
export function buildMinuteHistoryTimeline(
  versions: RawRecord[],
  audit: RawRecord[],
): TimelineItemModel[] {
  const orderedVersions = [...versions].sort((a, b) =>
    str(a, "created_at").localeCompare(str(b, "created_at")),
  );

  // Versão "dona" do evento = última versão criada até o instante do evento.
  function versionIdAt(occurredAt: string): string | null {
    let owner: RawRecord | null = null;
    for (const version of orderedVersions) {
      if (str(version, "created_at") <= occurredAt) owner = version;
    }
    if (!owner && orderedVersions.length > 0) owner = orderedVersions[0];
    return owner ? str(owner, "id") : null;
  }

  const items: TimelineItemModel[] = [];

  const newestFirst = [...orderedVersions].reverse();
  for (const version of newestFirst) {
    const createdAt = str(version, "created_at");
    items.push({
      id: `version-${str(version, "id")}`,
      title: `Versão ${str(version, "version_number")}`,
      occurredAt: createdAt,
      timeLabel: formatDateTimeBr(createdAt),
      detail: str(version, "change_reason") || undefined,
      branchKey: "main",
    });
  }

  const auditNewestFirst = [...audit].sort((a, b) =>
    str(b, "created_at").localeCompare(str(a, "created_at")),
  );
  for (const event of auditNewestFirst) {
    const action = str(event, "action");
    const createdAt = str(event, "created_at");
    const ownerVersionId = versionIdAt(createdAt);
    items.push({
      id: `audit-${str(event, "id")}`,
      title: AUDIT_ACTION_LABELS[action] || action,
      occurredAt: createdAt,
      timeLabel: formatDateTimeBr(createdAt),
      tone: AUDIT_ACTION_TONES[action] ?? "default",
      parentId: ownerVersionId ? `version-${ownerVersionId}` : null,
      branchKey: "audit",
    });
  }

  return items;
}
