import { getKaizenById } from "../api/qualityApi";
import { useQualityResource } from "./useQualityResource";

export function useKaizenDetail(kaizenId: string, enabled = true) {
  return useQualityResource(
    (signal) => getKaizenById(kaizenId, signal),
    [kaizenId],
    { enabled: enabled && Boolean(kaizenId.trim()) }
  );
}
