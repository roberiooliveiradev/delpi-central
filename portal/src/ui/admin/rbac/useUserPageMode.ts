// portal/src/ui/admin/rbac/useUserPageMode.ts

import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export type UserPageTab = "summary" | "roles" | "groups" | "usage" | "totvs";

export type UserPageMode = "view" | "edit";

const MODE_PARAM = "mode";
const TAB_PARAM = "tab";

const TAB_VALUES: UserPageTab[] = ["summary", "roles", "groups", "usage", "totvs"];

function parseTab(value: string | null): UserPageTab {
  if (value && TAB_VALUES.includes(value as UserPageTab)) {
    return value as UserPageTab;
  }
  return "summary";
}

export function useUserPageMode() {
  const [searchParams, setSearchParams] = useSearchParams();

  const mode: UserPageMode =
    searchParams.get(MODE_PARAM) === "edit" ? "edit" : "view";
  const activeTab = parseTab(searchParams.get(TAB_PARAM));
  const isEditing = mode === "edit";

  const setActiveTab = useCallback(
    (tab: UserPageTab) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current);
          if (tab === "summary") {
            next.delete(TAB_PARAM);
          } else {
            next.set(TAB_PARAM, tab);
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const enterEdit = useCallback(
    (tab?: UserPageTab) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current);
          next.set(MODE_PARAM, "edit");
          if (tab && tab !== "summary") {
            next.set(TAB_PARAM, tab);
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const exitEdit = useCallback(() => {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        next.delete(MODE_PARAM);
        return next;
      },
      { replace: true },
    );
  }, [setSearchParams]);

  const pageTitleSuffix = useMemo(
    () => (isEditing ? "Editar usuário" : "Usuário"),
    [isEditing],
  );

  return {
    mode,
    isEditing,
    activeTab,
    setActiveTab,
    enterEdit,
    exitEdit,
    pageTitleSuffix,
  };
}
