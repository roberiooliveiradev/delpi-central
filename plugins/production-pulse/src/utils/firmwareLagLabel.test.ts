import { describe, expect, it } from "vitest";

import {
  formatFamilyOutdatedSummary,
  isFirmwareBehind,
  resolveFirmwareLagInfo,
} from "./firmwareLagLabel";

describe("firmwareLagLabel", () => {
  it("detecta atraso com prefixo de família vs versão do catálogo", () => {
    expect(isFirmwareBehind("esp8266_counter_v1.3.2", "2.0.0")).toBe(true);
    expect(isFirmwareBehind("1.0.0", "2.0.0")).toBe(true);
  });

  it("considera atual quando SemVer normalizado coincide (positive)", () => {
    expect(isFirmwareBehind("esp8266_counter_v1.2.0.0", "2.0.0")).toBe(false);
    expect(isFirmwareBehind("2.0.0", "2.0.0")).toBe(false);
  });

  it("sem instalação reportada conta como atrás quando há catálogo", () => {
    expect(isFirmwareBehind(null, "2.0.0")).toBe(true);
  });

  it("negativo: sem versão no catálogo não é atrás", () => {
    expect(isFirmwareBehind("1.0.0", null)).toBe(false);
  });

  it("rótulo curto mostra instalada → disponível quando atrás", () => {
    const lag = resolveFirmwareLagInfo("esp8266_counter_v1.3.2", "2.0.0");
    expect(lag.kind).toBe("behind");
    expect(lag.shortLabel).toBe("FW 1.3.2 → 2.0.0");
    expect(lag.detailLabel).toBe("Em execução 1.3.2 · catálogo 2.0.0");
  });

  it("irmão: sem report do chip mostra seta para o catálogo", () => {
    const lag = resolveFirmwareLagInfo(null, "2.0.0");
    expect(lag.kind).toBe("no-install");
    expect(lag.shortLabel).toBe("FW — → 2.0.0");
  });

  it("negativo: atual omite seta", () => {
    const lag = resolveFirmwareLagInfo("esp8266_counter_v1.2.0.0", "2.0.0");
    expect(lag.kind).toBe("current");
    expect(lag.shortLabel).toBe("FW 2.0.0");
  });

  it("resumo da família usa atrás com alvo", () => {
    expect(formatFamilyOutdatedSummary(1, "2.0.0")).toBe(" · 1 atrás (→2.0.0)");
    expect(formatFamilyOutdatedSummary(0, "2.0.0")).toBe("");
  });
});
