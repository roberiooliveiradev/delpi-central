import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("../data/api/invoicePostingApi", () => ({
  getLnfApiBase: vi.fn(),
}));

import { getLnfApiBase } from "../data/api/invoicePostingApi";
import {
  buildLnfRealtimeWsUrl,
  isLnfApiBaseOnBff,
  isLnfRealtimeFlagOn,
  shouldConnectLnfRealtime,
} from "./config";

describe("lnf realtime config", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.mocked(getLnfApiBase).mockReset();
  });

  it("flag off → shouldConnect false mesmo na BFF", () => {
    vi.stubEnv("VITE_LNF_REALTIME_ENABLED", "false");
    vi.mocked(getLnfApiBase).mockReturnValue(
      "/apps/controllership-finance-api/lancamento-notas-fiscais",
    );
    expect(isLnfRealtimeFlagOn()).toBe(false);
    expect(shouldConnectLnfRealtime()).toBe(false);
  });

  it("base api-delpi → shouldConnect false mesmo com flag on", () => {
    vi.stubEnv("VITE_LNF_REALTIME_ENABLED", "true");
    vi.mocked(getLnfApiBase).mockReturnValue(
      "/apps/api-delpi/lancamento-notas-fiscais",
    );
    expect(isLnfApiBaseOnBff()).toBe(false);
    expect(shouldConnectLnfRealtime()).toBe(false);
  });

  it("flag on + base BFF → shouldConnect true", () => {
    vi.stubEnv("VITE_LNF_REALTIME_ENABLED", "true");
    vi.mocked(getLnfApiBase).mockReturnValue(
      "/apps/controllership-finance-api/lancamento-notas-fiscais",
    );
    expect(shouldConnectLnfRealtime()).toBe(true);
  });

  it("buildLnfRealtimeWsUrl coloca o token na query", () => {
    const url = buildLnfRealtimeWsUrl("tok-abc");
    expect(url).toContain(
      "/apps/controllership-finance-api/lancamento-notas-fiscais/realtime",
    );
    expect(url).toContain("token=tok-abc");
  });
});
