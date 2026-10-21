import { describe, expect, it } from "vitest";

import { EMPTY_REPORT_FILTERS, reportMatches } from "./reportListFilter";
import type { ReportSnapshot } from "./reportForm";

const report = {
  id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  report_number: "MET-2026-000001",
  report_date: "2026-10-21",
  revision: "00",
  sample: {
    terminal_code: "Terminal Ácido",
    terminal_part_number: "PN-1",
    product_harness: null,
    cable: null,
    conductor_section: null,
    applicator_tool: null,
    press_equipment: null,
    batch_production_order: null,
    sample_identification: null,
  },
  measurements: {
    crimp_height_ch: { criterion: null, measured: null },
    crimp_width_cb: { criterion: null, measured: null },
    void_area_av: { criterion: null, measured: null },
    left_burr_gh_e: { criterion: null, measured: null },
    right_burr_gh_d: { criterion: null, measured: null },
  },
  conclusion: { result: null, notes: null },
  analyst: { name: null, user_id: null },
  images: {
    original: { present: false, content_type: null, sha256: null },
    measured: { present: false, content_type: null, sha256: null },
  },
  status: "draft",
  version: 1,
  created_at: "2026-10-01T00:00:00Z",
  updated_at: null,
} satisfies ReportSnapshot;

describe("report list filter", () => {
  it("matches an accent-insensitive terminal and rejects a sibling that does not contain it", () => {
    expect(reportMatches(report, { ...EMPTY_REPORT_FILTERS, terminal: "acido" })).toBe(true);
    expect(reportMatches(report, { ...EMPTY_REPORT_FILTERS, terminal: "outro" })).toBe(false);
  });

  it("uses the report date and ignores a created-at date outside the range", () => {
    expect(reportMatches(report, { ...EMPTY_REPORT_FILTERS, from: "2026-10-20", to: "2026-10-22" })).toBe(true);
    expect(reportMatches(report, { ...EMPTY_REPORT_FILTERS, from: "2026-10-01", to: "2026-10-02" })).toBe(false);
  });

  it("falls back to the creation date when the report date is empty", () => {
    const undated = { ...report, report_date: null };
    expect(reportMatches(undated, { ...EMPTY_REPORT_FILTERS, from: "2026-10-01", to: "2026-10-01" })).toBe(true);
  });
});
