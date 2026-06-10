export const DELPI_PORTAL_TOUR_SYNC_STATUS_EVENT = "DELPI_PORTAL_TOUR_SYNC_STATUS";

export type PortalTourSyncStatus = {
  failed: boolean;
};

export function publishPortalTourSyncStatus(failed: boolean) {
  window.dispatchEvent(
    new CustomEvent<PortalTourSyncStatus>(DELPI_PORTAL_TOUR_SYNC_STATUS_EVENT, {
      detail: { failed },
    }),
  );
}

export function subscribePortalTourSyncStatus(
  listener: (status: PortalTourSyncStatus) => void,
): () => void {
  const handler = (event: Event) => {
    const detail = (event as CustomEvent<PortalTourSyncStatus>).detail;
    if (!detail) return;
    listener(detail);
  };
  window.addEventListener(DELPI_PORTAL_TOUR_SYNC_STATUS_EVENT, handler);
  return () => window.removeEventListener(DELPI_PORTAL_TOUR_SYNC_STATUS_EVENT, handler);
}
