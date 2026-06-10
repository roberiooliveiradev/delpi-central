import { useCallback, useContext } from "react";

import { useConfirmDialog } from "../ConfirmDialogProvider";
import { AuthContext } from "../../state/AuthContext";

const DELETE_CONFIRM =
  "Excluir esta notificação? Ela não aparecerá mais no seu histórico.";

export function useNotificationActions() {
  const confirm = useConfirmDialog();
  const {
    markNotificationRead,
    markAllNotificationsRead,
    deleteNotification,
    setNotificationImportant,
  } = useContext(AuthContext);

  const handleDelete = useCallback(
    async (id: string) => {
      const confirmed = await confirm({
        title: "Excluir notificação",
        message: DELETE_CONFIRM,
        confirmText: "Excluir",
        danger: true,
      });
      if (!confirmed) return;
      await deleteNotification(id);
    },
    [confirm, deleteNotification],
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

      const confirmed = await confirm({
        title:
          unique.length === 1
            ? "Excluir notificação"
            : "Excluir notificações",
        message,
        confirmText: "Excluir",
        danger: true,
      });
      if (!confirmed) return;

      await Promise.all(unique.map((id) => deleteNotification(id)));
    },
    [confirm, deleteNotification],
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
