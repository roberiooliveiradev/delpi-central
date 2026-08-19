import type { InteractionRoomInboxItemDto } from "../../api/interactionRoomsApi";

/** Iniciais da lista = nome do cliente, nunca o título da sala (ex.: Pedido 002573). */
export function inboxCustomerAvatarName(
  item: Pick<InteractionRoomInboxItemDto, "customer_name">,
): string {
  return (item.customer_name ?? "").trim();
}
