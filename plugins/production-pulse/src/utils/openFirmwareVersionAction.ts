/** Action payload for opening a specific firmware version from map menu/popover. */

export function openFirmwareVersionAction(firmwareId: string): string {
  return `open-version:${firmwareId}`;
}

export function parseOpenFirmwareVersionAction(action: string): string | null {
  if (!action.startsWith("open-version:")) return null;
  const id = action.slice("open-version:".length).trim();
  return id || null;
}
