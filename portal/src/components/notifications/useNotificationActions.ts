import { useCallback, useContext } from "react";

import { AuthContext } from "../../state/AuthContext";

const DELETE_CONFIRM =
  "Excluir esta notificação? Ela não aparecerá mais no seu histórico.";

export function useNotificationActions() {
  const {
    markNotificationRead,
    markAllNotificationsRead,
    deleteNotification,
    setNotificationImportant,
  } = useContext(AuthContext);

  const handleDelete = useCallback(
    async (id: string) => {
      if (!window.confirm(DELETE_CONFIRM)) {
        return;
      }
      await deleteNotification(id);
    },
    [deleteNotification],
  );

  const handleToggleImportant = useCallback(
    async (id: string, isImportant: boolean) => {
      await setNotificationImportant(id, isImportant);
    },
    [setNotificationImportant],
  );

  const bulkMarkRead = useCallback(
    async (ids: string[]) => {
      const unique = [...new Set(ids)].filter(Boolean);
      if (!unique.length) return;

      await Promise.all(unique.map((id) => markNotificationRead(id)));
    },
    [markNotificationRead],
  );

  const bulkDelete = useCallback(
    async (ids: string[]) => {
      const unique = [...new Set(ids)].filter(Boolean);
      if (!unique.length) return;

      const message =
        unique.length === 1
          ? DELETE_CONFIRM
          : `Excluir ${unique.length} notificações? Elas não aparecerão mais no seu histórico.`;

      if (!window.confirm(message)) {
        return;
      }

      await Promise.all(unique.map((id) => deleteNotification(id)));
    },
    [deleteNotification],
  );

  return {
    markNotificationRead,
    markAllNotificationsRead,
    handleDelete,
    handleToggleImportant,
    bulkMarkRead,
    bulkDelete,
  };
}
