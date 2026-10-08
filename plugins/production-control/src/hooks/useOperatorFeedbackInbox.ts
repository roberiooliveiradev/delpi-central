import { useCallback, useEffect, useRef, useState } from "react";

import {
  acknowledgeOperatorFeedback,
  fetchOperatorFeedbackInbox,
  resolveOperatorFeedback,
} from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { copy } from "../content/copy";
import type {
  OperatorFeedbackInboxSummary,
  PcpOperatorFeedback,
} from "../types";

const EMPTY_SUMMARY: OperatorFeedbackInboxSummary = {
  total: 0,
  open: 0,
  acknowledged: 0,
};

/** Polling leve da inbox — o Portal PCP nao tem websocket para esta feature. */
export const INBOX_POLL_MS = 20_000;

export type OperatorFeedbackInbox = {
  items: PcpOperatorFeedback[];
  summary: OperatorFeedbackInboxSummary;
  loading: boolean;
  error: string | null;
  notice: string | null;
  actingId: string | null;
  refresh: () => Promise<void>;
  acknowledge: (feedbackId: string) => Promise<boolean>;
  resolve: (feedbackId: string, resolutionNote: string | null) => Promise<boolean>;
};

export function useOperatorFeedbackInbox(branch: string): OperatorFeedbackInbox {
  const [items, setItems] = useState<PcpOperatorFeedback[]>([]);
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);
  const seqRef = useRef(0);

  const refresh = useCallback(async () => {
    const seq = ++seqRef.current;
    try {
      const data = await fetchOperatorFeedbackInbox({ branch });
      if (seq !== seqRef.current) return;
      setItems(data.items);
      setSummary(data.summary);
      setError(null);
    } catch (err) {
      if (seq !== seqRef.current) return;
      setError(
        err instanceof Error ? err.message : copy.machineLoad.feedback.loadError,
      );
    } finally {
      if (seq === seqRef.current) setLoading(false);
    }
  }, [branch]);

  // Carga inicial + troca de filial.
  useEffect(() => {
    queueMicrotask(() => {
      setItems([]);
      setSummary(EMPTY_SUMMARY);
      setError(null);
      setNotice(null);
      setLoading(true);
      void refresh();
    });
  }, [refresh]);

  // Polling leve: so enquanto a aba esta visivel; ao voltar, revalida na hora.
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    document.addEventListener("visibilitychange", onVisibility);
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      void refresh();
    }, INBOX_POLL_MS);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      window.clearInterval(timer);
    };
  }, [refresh]);

  const runAction = useCallback(
    async (feedbackId: string, action: () => Promise<PcpOperatorFeedback>) => {
      if (actingId) return false;
      setActingId(feedbackId);
      setNotice(null);
      try {
        await action();
        await refresh();
        return true;
      } catch (err) {
        if (httpErrorStatus(err) === 409) {
          // Outra pessoa do PCP mexeu primeiro: a lista sincroniza e avisa.
          await refresh();
          setNotice(copy.machineLoad.feedback.conflict);
          return true;
        }
        setNotice(
          err instanceof Error ? err.message : copy.machineLoad.feedback.error,
        );
        return false;
      } finally {
        setActingId(null);
      }
    },
    [actingId, refresh],
  );

  const acknowledge = useCallback(
    (feedbackId: string) =>
      runAction(feedbackId, () =>
        acknowledgeOperatorFeedback({ feedbackId }),
      ),
    [runAction],
  );

  const resolve = useCallback(
    (feedbackId: string, resolutionNote: string | null) =>
      runAction(feedbackId, () =>
        resolveOperatorFeedback({ feedbackId, resolutionNote }),
      ),
    [runAction],
  );

  return {
    items,
    summary,
    loading,
    error,
    notice,
    actingId,
    refresh,
    acknowledge,
    resolve,
  };
}
