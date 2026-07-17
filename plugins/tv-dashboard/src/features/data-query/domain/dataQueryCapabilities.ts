import type { DataQueryCapabilities } from "./dataQueryTypes";

export const LEGACY_SAFE_CAPABILITIES: DataQueryCapabilities = {
  enabled: false,
  writeV2Enabled: false,
  advancedEditorEnabled: false,
  profile: "m-delpi-v1",
};

export function canUseMWorkbench(capabilities: DataQueryCapabilities): boolean {
  return capabilities.enabled && capabilities.writeV2Enabled;
}

export function canUseAdvancedMEditor(capabilities: DataQueryCapabilities): boolean {
  return canUseMWorkbench(capabilities) && capabilities.advancedEditorEnabled;
}
