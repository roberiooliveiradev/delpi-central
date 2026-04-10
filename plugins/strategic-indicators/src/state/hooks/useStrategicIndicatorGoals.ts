import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  activateStrategicIndicatorGoal,
  createStrategicIndicatorGoal,
  deactivateStrategicIndicatorGoal,
  fetchStrategicIndicatorGoalHistory,
  fetchStrategicIndicatorGoals,
  updateStrategicIndicatorGoal,
} from "../../data/api/strategicIndicatorGoalsApi";
import type {
  CreateStrategicIndicatorGoalRequest,
  StrategicIndicatorGoalItem,
  UpdateStrategicIndicatorGoalRequest,
} from "../../data/types/indicatorGoals";

type UseStrategicIndicatorGoalsParams = {
  getAccessToken?: () => string | undefined;
  initialGoalYear?: number;
};

export function useStrategicIndicatorGoals({
  getAccessToken,
  initialGoalYear,
}: UseStrategicIndicatorGoalsParams) {
  const [items, setItems] = useState<StrategicIndicatorGoalItem[]>([]);
  const [selectedIndicatorId, setSelectedIndicatorId] = useState<string>("");
  const [selectedGoalYear, setSelectedGoalYear] = useState<number | "">(
    initialGoalYear ?? new Date().getFullYear(),
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyItems, setHistoryItems] = useState<StrategicIndicatorGoalItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const load = useCallback(async () => {
    const requestId = ++requestIdRef.current;

    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    if (hasLoadedOnceRef.current) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError(null);

    try {
      const response = await fetchStrategicIndicatorGoals(
        getAccessTokenRef.current,
        {
          indicatorId: selectedIndicatorId || undefined,
          goalYear:
            typeof selectedGoalYear === "number" ? selectedGoalYear : undefined,
        },
        controller.signal,
      );

      if (requestId !== requestIdRef.current || controller.signal.aborted) {
        return;
      }

      setItems(response.items);
      hasLoadedOnceRef.current = true;
    } catch (err) {
      if (requestId !== requestIdRef.current || controller.signal.aborted) {
        return;
      }

      setError(
        err instanceof Error ? err.message : "Unexpected error while loading goals.",
      );
    } finally {
      if (requestId === requestIdRef.current && !controller.signal.aborted) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [selectedIndicatorId, selectedGoalYear]);

  useEffect(() => {
    void load();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [load]);

  const loadHistory = useCallback(
    async (indicatorId: string, goalYear?: number) => {
      setHistoryLoading(true);
      setHistoryError(null);

      try {
        const response = await fetchStrategicIndicatorGoalHistory(
          indicatorId,
          getAccessTokenRef.current,
          goalYear,
        );
        setHistoryItems(response.items);
      } catch (err) {
        setHistoryError(
          err instanceof Error ? err.message : "Unexpected error while loading history.",
        );
      } finally {
        setHistoryLoading(false);
      }
    },
    [],
  );

  const createGoal = useCallback(
    async (payload: CreateStrategicIndicatorGoalRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await createStrategicIndicatorGoal(payload, getAccessTokenRef.current);
        setSuccessMessage("Goal created successfully.");
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unexpected error while creating goal.");
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const updateGoal = useCallback(
    async (goalId: string, payload: UpdateStrategicIndicatorGoalRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await updateStrategicIndicatorGoal(goalId, payload, getAccessTokenRef.current);
        setSuccessMessage("Goal updated successfully.");
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unexpected error while updating goal.");
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const activateGoal = useCallback(
    async (goalId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await activateStrategicIndicatorGoal(goalId, getAccessTokenRef.current);
        setSuccessMessage("Goal activated successfully.");
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unexpected error while activating goal.");
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const deactivateGoal = useCallback(
    async (goalId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deactivateStrategicIndicatorGoal(goalId, getAccessTokenRef.current);
        setSuccessMessage("Goal deactivated successfully.");
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unexpected error while deactivating goal.");
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const clearSuccessMessage = useCallback(() => {
    setSuccessMessage(null);
  }, []);

  return useMemo(
    () => ({
      items,
      historyItems,
      selectedIndicatorId,
      selectedGoalYear,
      setSelectedIndicatorId,
      setSelectedGoalYear,
      loading,
      refreshing,
      saving,
      historyLoading,
      error,
      historyError,
      successMessage,
      reload: load,
      loadHistory,
      createGoal,
      updateGoal,
      activateGoal,
      deactivateGoal,
      clearSuccessMessage,
    }),
    [
      items,
      historyItems,
      selectedIndicatorId,
      selectedGoalYear,
      loading,
      refreshing,
      saving,
      historyLoading,
      error,
      historyError,
      successMessage,
      load,
      loadHistory,
      createGoal,
      updateGoal,
      activateGoal,
      deactivateGoal,
      clearSuccessMessage,
    ],
  );
}