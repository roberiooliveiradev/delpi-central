import { afterEach, describe, expect, it, vi } from "vitest";

import type { TeoPortalContext } from "./teoPortalContext";
import {
  buildWorkspaceContextPayload,
  publishWorkspaceContext,
  resetWorkspaceClientInstanceId,
  unpublishWorkspaceContext,
  workspaceClientInstanceId,
  workspaceContextSignature,
} from "./workspaceContextPublisher";

const baseContext: TeoPortalContext = {
  version: "1",
  product: "transformometro",
  process_id: "P1",
  instance_id: "I1",
  revision_id: "R1",
  area: "resultados",
  canonical_path: "/apps/transformometro/processes/P1/instances/I1/revisions/R1#resultados",
};

describe("workspaceContextPublisher", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    resetWorkspaceClientInstanceId();
  });

  it("projeta refs bounded no contrato workspace_context_v1", () => {
    const payload = buildWorkspaceContextPayload(baseContext, "revisao", true);
    expect(payload.version).toBe(1);
    expect(payload.app_id).toBe("transformometro");
    expect(payload.route_id).toBe("revisao");
    expect(payload.entity_refs).toEqual([
      { entity_type: "process", entity_id: "P1" },
      { entity_type: "instance", entity_id: "I1" },
      { entity_type: "revision", entity_id: "R1" },
    ]);
    expect(payload.presentation_state).toEqual({ area: "resultados" });
    expect(payload.active).toBe(true);
    expect(payload.focused).toBe(true);
    expect(payload.source).toBe("mfe");
    expect(payload.client_instance_id).toBe(workspaceClientInstanceId());
  });

  it("omite refs e presentation_state vazios", () => {
    const empty: TeoPortalContext = {
      ...baseContext,
      process_id: null,
      instance_id: null,
      revision_id: null,
      area: null,
    };
    const payload = buildWorkspaceContextPayload(empty, "home", false);
    expect(payload.entity_refs).toEqual([]);
    expect(payload.presentation_state).toEqual({});
    expect(payload.focused).toBe(false);
  });

  it("client_instance_id é estável por aba e único após reset", () => {
    const first = workspaceClientInstanceId();
    expect(workspaceClientInstanceId()).toBe(first);
    resetWorkspaceClientInstanceId();
    expect(workspaceClientInstanceId()).not.toBe(first);
  });

  it("assinatura muda só em mudança material (inclui focused)", () => {
    const a = buildWorkspaceContextPayload(baseContext, "revisao", true);
    const b = buildWorkspaceContextPayload(baseContext, "revisao", true);
    expect(workspaceContextSignature(a)).toBe(workspaceContextSignature(b));
    const c = buildWorkspaceContextPayload(baseContext, "revisao", false);
    expect(workspaceContextSignature(c)).not.toBe(workspaceContextSignature(a));
    const d = buildWorkspaceContextPayload(
      { ...baseContext, area: "mapeamento" },
      "revisao",
      true,
    );
    expect(workspaceContextSignature(d)).not.toBe(workspaceContextSignature(a));
  });

  it("PUT /core-api/me/workspace-context com bearer do usuário e sem user_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);
    const payload = buildWorkspaceContextPayload(baseContext, "revisao", true);
    await publishWorkspaceContext(payload, () => "token-1");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/core-api/me/workspace-context");
    expect(init.method).toBe("PUT");
    expect(init.headers.Authorization).toBe("Bearer token-1");
    const body = JSON.parse(String(init.body));
    expect(body).not.toHaveProperty("user_id");
    expect(JSON.stringify(body)).not.toMatch(/token-1|Bearer/);
  });

  it("lança erro em publish não-ok (caller decide engolir)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    await expect(
      publishWorkspaceContext(
        buildWorkspaceContextPayload(baseContext, "revisao", true),
        () => "t",
      ),
    ).rejects.toThrow("503");
  });

  it("unpublish usa DELETE keepalive com client_instance_id", () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);
    unpublishWorkspaceContext(() => "token-9");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/core-api/me/workspace-context?client_instance_id=");
    expect(url).toContain(encodeURIComponent(workspaceClientInstanceId()));
    expect(init.method).toBe("DELETE");
    expect(init.keepalive).toBe(true);
    expect(init.headers.Authorization).toBe("Bearer token-9");
  });
});
