import { useCallback, useEffect, useState } from "react";

import {
  fetchAuditNcAttachments,
  fetchNcActions,
  fetchNcCandidates,
  type NcAction,
  type NcAttachmentMap,
} from "../api/audit5sApi";
import type { NcBoardItem } from "../types/ncManagement";
import { buildBoardTreatmentItem } from "../utils/ncBoardTreat";
import type { NcTreatmentItem } from "../utils/auditNc";
import { groupAttachmentsByResponse } from "../utils/ncAttachments";

export function useNcBoardItemDetail(item: NcBoardItem | null, enabled: boolean) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [treatmentItem, setTreatmentItem] = useState<NcTreatmentItem | null>(null);
  const [attachmentsByNcId, setAttachmentsByNcId] = useState<NcAttachmentMap>({});
  const [actions, setActions] = useState<NcAction[]>([]);

  const load = useCallback(async (boardItem: NcBoardItem) => {
    setLoading(true);
    setError(null);
    try {
      const [candidates, attachmentItems, actionItems] = await Promise.all([
        fetchNcCandidates(boardItem.audit_id),
        boardItem.is_registered
          ? fetchAuditNcAttachments(boardItem.audit_id)
          : Promise.resolve([]),
        boardItem.is_registered
          ? fetchNcActions(boardItem.id)
          : Promise.resolve([]),
      ]);

      const candidate =
        candidates.find((entry) => entry.response.id === boardItem.response_id) ?? null;

      setTreatmentItem(buildBoardTreatmentItem(boardItem, candidate));
      setAttachmentsByNcId(groupAttachmentsByResponse(attachmentItems));
      setActions(actionItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar ficha da NC.");
      setTreatmentItem(null);
      setAttachmentsByNcId({});
      setActions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled || !item) {
      setTreatmentItem(null);
      setAttachmentsByNcId({});
      setActions([]);
      setError(null);
      return;
    }

    void load(item);
  }, [enabled, item, load]);

  const reload = useCallback(async () => {
    if (!item) return;
    await load(item);
  }, [item, load]);

  return {
    loading,
    error,
    treatmentItem,
    attachmentsByNcId,
    actions,
    reload,
  };
}
