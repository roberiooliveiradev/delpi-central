import { useCallback, useEffect, useMemo, useState } from "react";
import type { StrategicIndicatorsSettingsResponse } from "../../data/types/settings";

type SettingsDraft = Pick<
  StrategicIndicatorsSettingsResponse,
  "parameters" | "governance"
>;

type SettingsDraftErrors = {
  root: string | null;
};

function cloneDraft(data: StrategicIndicatorsSettingsResponse): SettingsDraft {
  return {
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

  const isDirty = useMemo(() => {
    return !areDraftsEqual(draft, cloneDraft(data));
  }, [draft, data]);

  const validateAll = useCallback(() => {
    const hasInvalidParameter = draft.parameters.items.some(
      (item) => !item.key?.trim() || !item.label?.trim(),
    );
    if (hasInvalidParameter) {
      setErrors({
        root: "Todos os parâmetros devem possuir chave e rótulo válidos.",
      });
      return false;
    }

    const hasInvalidGovernance = draft.governance.items.some(
      (item) =>
        !item.key?.trim() ||
        !item.label?.trim() ||
        !item.value?.trim() ||
        !item.observation?.trim(),
    );
    if (hasInvalidGovernance) {
      setErrors({
        root: "Todos os itens de governança devem estar preenchidos corretamente.",
      });
      return false;
    }

    setErrors({ root: null });
    return true;
  }, [draft]);

  const isSaveDisabled = useMemo(() => {
    return !isDirty;
  }, [isDirty]);

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
    isDirty,
    isSaveDisabled,
    setParameterItems,
    setGovernanceItems,
    reset,
    validateAll,
  };
}