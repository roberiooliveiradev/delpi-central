/** Base HTTP do backend SI (gateway → serviço strategic-indicators-api). */
const raw = import.meta.env.VITE_STRATEGIC_INDICATORS_API_BASE as string | undefined;

export const STRATEGIC_INDICATORS_API_BASE =
  typeof raw === "string" && raw.trim().length > 0
    ? raw.replace(/\/$/, "")
    : "/apps/strategic-indicators-api/strategic-indicators";
