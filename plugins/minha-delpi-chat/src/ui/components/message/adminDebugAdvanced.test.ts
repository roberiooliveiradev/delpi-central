import { describe, expect, it } from "vitest";

import {
  extractAdminDebugTraceId,
  readAdminDebugAdvanced,
  shouldShowRawDebugJson,
  writeAdminDebugAdvanced,
} from "./adminDebugAdvanced";

describe("adminDebugAdvanced", () => {
  it("defaults advanced off and shows raw only when advanced", () => {
    const store = new Map<string, string>();
    const storage = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
    };

    expect(readAdminDebugAdvanced(storage)).toBe(false);
    expect(shouldShowRawDebugJson(false)).toBe(false);
    expect(shouldShowRawDebugJson(true)).toBe(true);

    writeAdminDebugAdvanced(true, storage);
    expect(readAdminDebugAdvanced(storage)).toBe(true);
  });

  it("extracts traceId when present and returns null otherwise", () => {
    expect(extractAdminDebugTraceId({ traceId: " abc-1 " })).toBe("abc-1");
    expect(extractAdminDebugTraceId({ requestId: "req-9" })).toBe("req-9");
    expect(extractAdminDebugTraceId({ intelligence: {} })).toBeNull();
    expect(extractAdminDebugTraceId(null)).toBeNull();
  });
});
