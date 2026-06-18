import { describe, expect, it } from "vitest";

import { DEFAULT_PROJECT_ICON, normalizeProjectIcon } from "./chatProjectIcon";

describe("chatProjectIcon", () => {
  it("normaliza nomes Lucide conhecidos", () => {
    expect(normalizeProjectIcon("bar-chart-3")).toBe("bar-chart-3");
    expect(normalizeProjectIcon(" FOLDER ")).toBe("folder");
  });

  it("converte emojis legados para Lucide", () => {
    expect(normalizeProjectIcon("📊")).toBe("bar-chart-3");
    expect(normalizeProjectIcon("🛠️")).toBe("wrench");
  });

  it("usa pasta como fallback", () => {
    expect(normalizeProjectIcon(null)).toBe(DEFAULT_PROJECT_ICON);
    expect(normalizeProjectIcon("icone-desconhecido")).toBe(DEFAULT_PROJECT_ICON);
  });
});
