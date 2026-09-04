import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import {
  MR_UI_PREFIX,
  MyRequestsCompactPagination,
  MyRequestsFilterSelectField,
  MyRequestsFiltersRow,
  MyRequestsModal,
  MyRequestsSectionCard,
  TextField,
} from "./mrUi";

const SRC_ROOT = join(__dirname, "..");

function collectTsx(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === "shims" || name.endsWith(".test.ts") || name.endsWith(".test.tsx")) continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) collectTsx(full, out);
    else if (name.endsWith(".tsx") || name.endsWith(".ts")) out.push(full);
  }
  return out;
}

describe("kit-first my-requests", () => {
  it("expõe factories do plugin-ui com prefixo my-requests", () => {
    expect(MR_UI_PREFIX).toBe("my-requests");
    expect(typeof MyRequestsSectionCard).toBe("function");
    expect(typeof TextField).toBe("function");
    expect(typeof MyRequestsFiltersRow).toBe("function");
    expect(typeof MyRequestsFilterSelectField).toBe("function");
    expect(typeof MyRequestsCompactPagination).toBe("function");
    expect(typeof MyRequestsModal).toBe("function");
  });

  it("não reintroduz chrome primitivo local (__btn / __panel / __table)", () => {
    const forbidden = [
      "dashboard-my-requests__btn",
      "dashboard-my-requests__panel",
      "dashboard-my-requests__table",
      "dashboard-my-requests__form",
    ];
    const files = collectTsx(SRC_ROOT);
    const offenders: string[] = [];
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      for (const token of forbidden) {
        if (text.includes(token)) offenders.push(`${file} → ${token}`);
      }
    }
    expect(offenders).toEqual([]);
  });
});
