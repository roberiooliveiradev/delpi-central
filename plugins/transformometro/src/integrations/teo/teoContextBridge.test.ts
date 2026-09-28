import { describe, expect, it } from "vitest";

import {
  TEO_CONTEXT_SITE_TOOL_DESCRIPTION,
  TEO_CONTEXT_SITE_TOOL_NAME,
  buildTeoContextSiteTool,
  registerTeoContextSiteTool,
  resetTeoContextSiteToolRegistration,
  type TeoContextSiteTool,
} from "./teoContextBridge";

const BASE = "/apps/transformometro/processes";
const REVISION = `${BASE}/proc-1/instances/inst-1/revisions/rev-1`;

function fakeModelContext() {
  const calls: { tool: TeoContextSiteTool; signal?: AbortSignal }[] = [];
  return {
    calls,
    registerTool(tool: TeoContextSiteTool, options?: { signal?: AbortSignal }) {
      calls.push({ tool, signal: options?.signal });
    },
  };
}

describe("buildTeoContextSiteTool", () => {
  it("L: descritor segue o contrato WebMCP read-only sem input", () => {
    const tool = buildTeoContextSiteTool(() => ({ pathname: REVISION, hash: "#medicao" }));
    expect(tool.name).toBe(TEO_CONTEXT_SITE_TOOL_NAME);
    expect(tool.name).toBe("get_current_transformometro_context");
    expect(tool.inputSchema).toEqual({
      type: "object",
      properties: {},
      additionalProperties: false,
    });
    expect(tool.annotations).toEqual({ readOnlyHint: true });
    expect(tool.description).toBe(TEO_CONTEXT_SITE_TOOL_DESCRIPTION);
    expect(tool.description).toMatch(/not authorization/i);
    expect(tool.description).toMatch(/not domain state/i);
    expect(tool.description).toMatch(/get_process_context/);
  });

  it("execute resolve o contexto no momento da chamada", async () => {
    let current = { pathname: REVISION, hash: "" };
    const tool = buildTeoContextSiteTool(() => current);

    const first = await tool.execute();
    expect(first.process_id).toBe("proc-1");
    expect(first.revision_id).toBe("rev-1");

    current = { pathname: BASE, hash: "" };
    const second = await tool.execute();
    expect(second.process_id).toBeNull();
    expect(second.revision_id).toBeNull();
  });
});

describe("registerTeoContextSiteTool", () => {
  it("registra uma única vez e respeita abort", () => {
    resetTeoContextSiteToolRegistration();
    const mc = fakeModelContext();
    const controller = new AbortController();

    expect(registerTeoContextSiteTool({ signal: controller.signal, modelContext: mc })).toBe(true);
    expect(mc.calls).toHaveLength(1);
    expect(mc.calls[0].tool.name).toBe(TEO_CONTEXT_SITE_TOOL_NAME);

    expect(registerTeoContextSiteTool({ modelContext: mc })).toBe(true);
    expect(mc.calls).toHaveLength(1);

    controller.abort();
    expect(registerTeoContextSiteTool({ modelContext: mc })).toBe(true);
    expect(mc.calls).toHaveLength(2);
    resetTeoContextSiteToolRegistration();
  });

  it("sem modelContext é no-op", () => {
    resetTeoContextSiteToolRegistration();
    expect(registerTeoContextSiteTool({ modelContext: null })).toBe(false);
    expect(registerTeoContextSiteTool({ modelContext: {} })).toBe(false);
    resetTeoContextSiteToolRegistration();
  });
});
