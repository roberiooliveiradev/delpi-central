import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { getRunTimeline } from "../api/mesApi";
import { useRunTimeline } from "./useRunTimeline";

vi.mock("../api/mesApi", () => ({ getRunTimeline: vi.fn() }));

describe("useRunTimeline", () => {
  it("does not request history without permission or selected run", () => { renderHook(() => useRunTimeline("run", "sig", false)); expect(getRunTimeline).not.toHaveBeenCalled(); });
  it("requests exactly the selected run and isolates errors", async () => { vi.mocked(getRunTimeline).mockRejectedValue(new Error("timeline indisponível")); const hook = renderHook(() => useRunTimeline("run-1", "sig", true)); await waitFor(() => expect(hook.result.current.error).toBe("timeline indisponível")); expect(getRunTimeline).toHaveBeenCalledTimes(1); expect(getRunTimeline).toHaveBeenCalledWith("run-1", expect.any(AbortSignal)); });
});
