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

  return {
    markNotificationRead,
    markAllNotificationsRead,
    handleDelete,
    handleToggleImportant,
  };
}
