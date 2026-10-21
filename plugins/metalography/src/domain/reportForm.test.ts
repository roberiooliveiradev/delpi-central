import { describe, expect, it } from "vitest";

import { emptyReportForm, formFromReport, formsEqual, toWritePayload, type ReportSnapshot } from "./reportForm";

const report = {
  id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  report_number: "MET-2026-000001",
  report_date: "2026-10-21",
  revision: "01",
  sample: {
    terminal_code: "T1",
    terminal_part_number: null,
    product_harness: null,
    cable: null,
    conductor_section: null,
    applicator_tool: null,
    press_equipment: null,
    batch_production_order: null,
    sample_identification: "Amostra A",
  },
  measurements: {
    crimp_height_ch: { criterion: "1.0", measured: "1.1" },
    crimp_width_cb: { criterion: null, measured: null },
    void_area_av: { criterion: null, measured: null },
    left_burr_gh_e: { criterion: null, measured: null },
    right_burr_gh_d: { criterion: null, measured: null },
  },
  conclusion: { result: "conforming", notes: "ok" },
  analyst: { name: "Ana", user_id: null },
  images: {
    original: { present: false, content_type: null, sha256: null },
    measured: { present: false, content_type: null, sha256: null },
  },
  status: "draft",
  version: 2,
  created_at: null,
  updated_at: null,
} satisfies ReportSnapshot;

describe("report form", () => {
  it("maps the saved snapshot and omits server identity from the write", () => {
    const form = formFromReport(report);
    const payload = toWritePayload(form);
    expect(payload.revision).toBe("01");
    expect(payload.sample.terminal_code).toBe("T1");
    expect(payload.measurements.crimp_height_ch.measured).toBe("1.1");
    expect(payload.conclusion.result).toBe("conforming");
    expect(payload.status).toBe("draft");
    expect(payload).not.toHaveProperty("id");
    expect(payload).not.toHaveProperty("report_number");
    expect(payload.analyst).toEqual({ name: "Ana" });
  });

  it("treats an untouched empty form as clean and a typed value as dirty", () => {
    const empty = emptyReportForm();
    expect(formsEqual(empty, emptyReportForm())).toBe(true);
    const edited = { ...empty, analystName: "Ana" };
    expect(formsEqual(empty, edited)).toBe(false);
  });

  it("does not send a blank conclusion as conforming", () => {
    expect(toWritePayload(emptyReportForm()).conclusion.result).toBeNull();
  });
});
