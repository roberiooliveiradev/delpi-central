import { afterEach, describe, expect, it, vi } from "vitest";

import { getEngineeringHome } from "./engineeringHomeApi";
import {
  configureHttpClient,
  DELPI_CALLER_APP,
} from "./httpClient";
import type { HomeSection } from "../types/home";

const SECTION: HomeSection = { status: "empty", items: [] };

function homePayload(overrides: Record<string, unknown> = {}) {
  return {
    success: true,
    message: null,
    data: {
      schema_version: "1.0",
      generated_at: "2026-10-27T12:00:00Z",
      status: "available",
      sections: {
        attention: SECTION,
        tasks: SECTION,
        lmps: SECTION,
        requests: SECTION,
        activity: SECTION,
        collaboration: SECTION,
      },
      ...overrides,
    },
    meta: { operationId: "get_engineering_home" },
  };
}

function stubFetch(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(body), { status })),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getEngineeringHome", () => {
  it("consome o envelope canônico e devolve data", async () => {
    stubFetch(homePayload());
    const home = await getEngineeringHome();
    expect(home.schema_version).toBe("1.0");
    expect(home.sections.tasks.status).toBe("empty");
  });

  it("rejeita envelope sem success", async () => {
    stubFetch({ success: false, message: "erro", data: null });
    await expect(getEngineeringHome()).rejects.toMatchObject({
      kind: "contract_error",
    });
  });

  it("rejeita data sem seção obrigatória", async () => {
    const payload = homePayload();
    delete (payload.data.sections as Record<string, unknown>).collaboration;
    stubFetch(payload);
    await expect(getEngineeringHome()).rejects.toMatchObject({
      kind: "contract_error",
    });
  });

  it("rejeita seção sem status", async () => {
    const payload = homePayload();
    payload.data.sections.tasks = { items: [] } as unknown as HomeSection;
    stubFetch(payload);
    await expect(getEngineeringHome()).rejects.toMatchObject({
      kind: "contract_error",
    });
  });

  it("mapeia 401/403/429/503 para os tipos honestos", async () => {
    const cases: Array<[number, string]> = [
      [401, "unauthorized"],
      [403, "forbidden"],
      [429, "rate_limited"],
      [503, "unavailable"],
    ];
    for (const [status, kind] of cases) {
      stubFetch({ message: "x" }, status);
      await expect(getEngineeringHome()).rejects.toMatchObject({
        kind,
        status,
      });
    }
  });

  it("envia Bearer do host + caller-app engineering, nunca na URL", async () => {
    configureHttpClient(() => "jwt-user-1");
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify(homePayload()), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await getEngineeringHome();
    const [url, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(url).toBe("/apps/engineering-api/v1/home");
    expect(url).not.toContain("jwt-user-1");
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer jwt-user-1");
    expect(headers["X-Delpi-Caller-App"]).toBe(DELPI_CALLER_APP);
    expect(DELPI_CALLER_APP).toBe("engineering");
    expect(url).not.toContain("service");
  });
});
