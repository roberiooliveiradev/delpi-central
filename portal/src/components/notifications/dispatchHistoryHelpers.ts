// src/components/notifications/dispatchHistoryHelpers.ts

import type { NotificationDispatchItem } from "../../data/coreApi";

export function canDeleteDispatch(item: NotificationDispatchItem) {
  if (item.revokedAt) return false;
  if (item.status === "pending") return true;
  if (item.status === "processing") return false;
  return item.createdCount > 0 || item.status === "completed";
}

export function bulkDeleteConfirmMessage(count: number) {
  return `Excluir ${count} envio(s) selecionado(s)? As notificações sumirão da caixa de entrada de quem recebeu (envios agendados serão cancelados).`;
}

export function singleDeleteConfirmMessage(item: NotificationDispatchItem) {
  if (item.status === "pending") {
    return "Cancelar este envio agendado? Ele será removido do histórico.";
  }
  const count = item.createdCount > 0 ? item.createdCount : "todos os";
  return `Excluir este envio para ${count} destinatário(s)? A notificação sumirá da caixa de entrada de quem recebeu.`;
}
