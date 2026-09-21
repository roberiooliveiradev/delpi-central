import { buildMeetingMinutePath } from "../../constants/routes";
import type { AtaListItem } from "../../data/api/transformometroMeetingMinutesApi";

/** Projeção de leitura. O status verdadeiro continua no signatário da ata. */
export type MyTaskProjection = {
  id: string;
  type: "meeting_minute_signature";
  title: string;
  description: string | null;
  status: string;
  sourceType: "meeting_minute";
  sourceId: string;
  route: string;
  contextLabel: string | null;
  updatedAt: string | null;
};

export function projectPendingSignatureTasks(items: readonly AtaListItem[]): MyTaskProjection[] {
  return items.map((item) => ({
    id: `meeting_minute_signature:${item.id}`,
    type: "meeting_minute_signature",
    title: item.title,
    description: item.minute_number?.trim() || null,
    status: item.status,
    sourceType: "meeting_minute",
    sourceId: item.id,
    route: buildMeetingMinutePath(item.id),
    contextLabel: item.unit_code ? `Unidade ${item.unit_code}` : null,
    updatedAt: item.updated_at ?? null,
  }));
}
