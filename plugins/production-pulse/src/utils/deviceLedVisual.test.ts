import { describe, expect, it } from "vitest";

import { isDeviceLedState, preferLedVisualForConnectivity, resolveLedVisual } from "./deviceLedVisual";

const EXPECTED: Array<{
  ledState: string;
  colorClass: string;
  pattern: string;
  labelIncludes: RegExp;
}> = [
  { ledState: "offline", colorClass: "pp-led--red", pattern: "solid", labelIncludes: /Wi‑Fi|Wi-Fi/i },
  {
    ledState: "connecting",
    colorClass: "pp-led--red",
    pattern: "blink_slow",
    labelIncludes: /Conectando/i,
  },
  {
    ledState: "wifi_ok_never_contacted",
    colorClass: "pp-led--blue",
    pattern: "solid",
    labelIncludes: /sem Pulse/i,
  },
  {
    ledState: "backend_ok",
    colorClass: "pp-led--green",
    pattern: "solid",
    labelIncludes: /Pulse autenticado/i,
  },
  {
    ledState: "wifi_ok_stale",
    colorClass: "pp-led--blue",
    pattern: "blink_slow",
    labelIncludes: /stale/i,
  },
  {
    ledState: "ota_in_progress",
    colorClass: "pp-led--yellow",
    pattern: "blink_ota",
    labelIncludes: /OTA/i,
  },
  {
    ledState: "auth_error",
    colorClass: "pp-led--red",
    pattern: "blink_fast",
    labelIncludes: /autenticação/i,
  },
];

describe("resolveLedVisual", () => {
  it.each(EXPECTED)("maps $ledState to fixed color/pattern/label", (row) => {
    const visual = resolveLedVisual(row.ledState);
    expect(visual).not.toBeNull();
    expect(visual?.colorClass).toBe(row.colorClass);
    expect(visual?.pattern).toBe(row.pattern);
    expect(visual?.label).toMatch(row.labelIncludes);
  });

  it("never_contacted is blue solid, not green backend_ok", () => {
    const never = resolveLedVisual("wifi_ok_never_contacted");
    const ok = resolveLedVisual("backend_ok");
    expect(never?.colorClass).toBe("pp-led--blue");
    expect(ok?.colorClass).toBe("pp-led--green");
    expect(never?.pattern).toBe("solid");
  });

  it("returns null for missing or unknown ledState (Pulse badge fallback)", () => {
    expect(resolveLedVisual(undefined)).toBeNull();
    expect(resolveLedVisual(null)).toBeNull();
    expect(resolveLedVisual("online")).toBeNull();
    expect(resolveLedVisual("")).toBeNull();
    expect(isDeviceLedState("backend_ok")).toBe(true);
    expect(isDeviceLedState("online")).toBe(false);
  });
});

describe("preferLedVisualForConnectivity", () => {
  it("shows LED when online with backend_ok", () => {
    const visual = preferLedVisualForConnectivity("online", "backend_ok");
    expect(visual?.label).toMatch(/Pulse autenticado/);
    expect(visual?.colorClass).toBe("pp-led--green");
  });

  it("sibling: never-contacted is blue while online", () => {
    const visual = preferLedVisualForConnectivity("online", "wifi_ok_never_contacted");
    expect(visual?.colorClass).toBe("pp-led--blue");
  });

  it("negative: offline Pulse wins over stale ledState", () => {
    expect(preferLedVisualForConnectivity("offline", "backend_ok")).toBeNull();
  });

  it("negative: missing ledState yields null (Pulse badge)", () => {
    expect(preferLedVisualForConnectivity("online", undefined)).toBeNull();
  });
});
