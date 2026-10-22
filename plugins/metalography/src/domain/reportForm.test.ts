import { describe, expect, it } from "vitest";

import {
  copyReportForm,
  displayDateToIso,
  emptyReportForm,
  formatBusinessDate,
  formFromReport,
  formsEqual,
  isoToDisplayDate,
  newReportForm,
  toWritePayload,
  type ReportSnapshot,
} from "./reportForm";

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
    expect(form.reportDate).toBe("21/10/2026");
    expect(payload.report_date).toBe("2026-10-21");
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

  it("copies the html field policy instead of cloning the whole report", () => {
    const source = formFromReport(report);
    source.sample.batch_production_order = "OP-1";
    source.measurements.crimp_width_cb = { criterion: "2.0", measured: "2.1" };
    const copy = copyReportForm(source, new Date("2026-10-22T15:00:00.000Z"));
    const payload = toWritePayload(copy);
    expect(payload.revision).toBe("01");
    expect(payload.sample.terminal_code).toBe("T1");
    expect(payload.sample.batch_production_order).toBeNull();
    expect(payload.sample.sample_identification).toBeNull();
    expect(payload.measurements.crimp_height_ch).toEqual({ criterion: "1.0", measured: null });
    expect(payload.measurements.crimp_width_cb).toEqual({ criterion: "2.0", measured: null });
    expect(copy.reportDate).toBe("22/10/2026");
    expect(payload.report_date).toBe("2026-10-22");
    expect(payload.report_date).not.toBe(report.report_date);
    expect(payload.conclusion).toEqual({ result: null, notes: null });
    expect(payload.analyst).toEqual({ name: null });
    expect(payload).not.toHaveProperty("images");
  });

  it("stamps the São Paulo calendar date on a new report and keeps it on later writes", () => {
    const beforeMidnight = new Date("2026-10-22T02:30:00.000Z");
    const afterMidnight = new Date("2026-10-22T03:30:00.000Z");
    const created = newReportForm(beforeMidnight);
    const payload = toWritePayload(created);
    expect(created.reportDate).toBe("21/10/2026");
    expect(payload.report_date).toBe("2026-10-21");
    expect(formatBusinessDate(beforeMidnight)).not.toBe(beforeMidnight.toISOString().slice(0, 10).split("-").reverse().join("/"));
    expect(toWritePayload(newReportForm(afterMidnight)).report_date).toBe("2026-10-22");

    const reopened = formFromReport({ ...report, report_date: payload.report_date });
    expect(reopened.reportDate).toBe("21/10/2026");
    expect(toWritePayload(reopened).report_date).toBe("2026-10-21");
    const manual = { ...reopened, reportDate: "01/11/2026" };
    expect(toWritePayload(manual).report_date).toBe("2026-11-01");
    expect(toWritePayload(reopened).report_date).toBe("2026-10-21");
  });

  it("keeps a legacy report without a date empty until the field is edited", () => {
    const legacy = formFromReport({ ...report, report_date: null });
    expect(legacy.reportDate).toBe("");
    expect(toWritePayload(legacy).report_date).toBeNull();
    expect(emptyReportForm().reportDate).toBe("");
    const edited = { ...legacy, reportDate: "15/01/2020" };
    expect(toWritePayload(edited).report_date).toBe("2020-01-15");
  });

  it("converts display and ISO dates without shifting the calendar day", () => {
    expect(isoToDisplayDate("2026-10-21")).toBe("21/10/2026");
    expect(displayDateToIso("21/10/2026")).toBe("2026-10-21");
    expect(displayDateToIso("")).toBeNull();
    expect(isoToDisplayDate(null)).toBe("");
    expect(isoToDisplayDate("não é data")).toBe("não é data");
  });
});
