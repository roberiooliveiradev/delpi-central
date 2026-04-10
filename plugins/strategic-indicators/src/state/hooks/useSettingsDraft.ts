import { useCallback, useEffect, useMemo, useState } from "react";
import type { StrategicIndicatorsSettingsResponse } from "../../data/types/settings";

type SettingsDraft = Pick<
  StrategicIndicatorsSettingsResponse,
  "weights" | "goals" | "parameters" | "governance"
>;

type SettingsDraftErrors = {
  root: string | null;
};

function cloneDraft(data: StrategicIndicatorsSettingsResponse): SettingsDraft {
  return {
    weights: {
      items: data.weights.items.map((item) => ({ ...item })),
    },
    goals: {
      items: data.goals.items.map((item) => ({ ...item })),
    },
    parameters: {
      items: data.parameters.items.map((item) => ({ ...item })),
    },
    governance: {
      items: data.governance.items.map((item) => ({ ...item })),
    },
  };
}

function areDraftsEqual(a: SettingsDraft, b: SettingsDraft) {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function useSettingsDraft(data: StrategicIndicatorsSettingsResponse) {
  const [draft, setDraft] = useState<SettingsDraft>(() => cloneDraft(data));
  const [errors, setErrors] = useState<SettingsDraftErrors>({
    root: null,
  });

  useEffect(() => {
    setDraft(cloneDraft(data));
    setErrors({ root: null });
  }, [data]);

  const totalWeight = useMemo(() => {
    return draft.weights.items.reduce(
      (sum, item) => sum + Number(item.weight_pct || 0),
      0,
    );
  }, [draft.weights.items]);

  const isDirty = useMemo(() => {
    return !areDraftsEqual(draft, cloneDraft(data));
  }, [draft, data]);

  const validateAll = useCallback(() => {
    if (totalWeight !== 100) {
      setErrors({
        root: "A soma dos pesos deve ser exatamente 100%.",
      });
      return false;
    }

    setErrors({ root: null });
    return true;
  }, [totalWeight]);

  const isSaveDisabled = useMemo(() => {
    return !isDirty || totalWeight !== 100;
  }, [isDirty, totalWeight]);

  const setWeightItems = useCallback(
    (items: SettingsDraft["weights"]["items"]) => {
      setDraft((current) => ({
        ...current,
        weights: {
          items: items.map((item) => ({
            ...item,
            weight_pct: Number(item.weight_pct || 0),
          })),
        },
      }));
    },
    [],
  );

  const setGoalItems = useCallback(
    (items: SettingsDraft["goals"]["items"]) => {
      setDraft((current) => ({
        ...current,
        goals: {
          items: items.map((item) => ({ ...item })),
        },
      }));
    },
    [],
  );

  const setParameterItems = useCallback(
    (items: SettingsDraft["parameters"]["items"]) => {
      setDraft((current) => ({
        ...current,
        parameters: {
          items: items.map((item) => ({ ...item })),
        },
      }));
    },
    [],
  );

  const setGovernanceItems = useCallback(
    (items: SettingsDraft["governance"]["items"]) => {
      setDraft((current) => ({
        ...current,
        governance: {
          items: items.map((item) => ({ ...item })),
        },
      }));
    },
    [],
  );

  const reset = useCallback(() => {
    setDraft(cloneDraft(data));
    setErrors({ root: null });
  }, [data]);

  return {
    draft,
    errors,
    totalWeight,
    isDirty,
    isSaveDisabled,
    setWeightItems,
    setGoalItems,
    setParameterItems,
    setGovernanceItems,
    reset,
    validateAll,
  };
}