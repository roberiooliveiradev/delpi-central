import { describe, expect, it } from "vitest";

import {
  canDeleteMeetingMinute,
  meetingMinuteDeleteConfirmCopy,
} from "./meetingMinuteDeletePolicy";

describe("canDeleteMeetingMinute", () => {
  it("allows clean draft", () => {
    expect(
      canDeleteMeetingMinute({ status: "draft", submitted_for_signature_at: null }, []),
    ).toBe(true);
  });

  it("blocks non-draft statuses", () => {
    for (const status of [
      "in_review",
      "awaiting_signatures",
      "partially_signed",
      "signed",
      "finalized",
      "cancelled",
    ]) {
      expect(canDeleteMeetingMinute({ status }, [])).toBe(false);
    }
  });

  it("blocks when submitted_for_signature_at is set", () => {
    expect(
      canDeleteMeetingMinute(
        { status: "draft", submitted_for_signature_at: "2026-11-09T00:00:00Z" },
        [],
      ),
    ).toBe(false);
  });

  it("blocks when signatures exist", () => {
    expect(
      canDeleteMeetingMinute({ status: "draft" }, [{ id: "sig1" }]),
    ).toBe(false);
  });

  it("blocks list items with signatures_done > 0", () => {
    expect(
      canDeleteMeetingMinute({ status: "draft", signatures_done: 1 }, []),
    ).toBe(false);
  });
});

describe("meetingMinuteDeleteConfirmCopy", () => {
  it("includes number and title", () => {
    const copy = meetingMinuteDeleteConfirmCopy({
      minute_number: "2026/017",
      title: "QA VALIDATION",
    });
    expect(copy.title).toBe("Excluir ata?");
    expect(copy.message).toContain("2026/017");
    expect(copy.message).toContain("QA VALIDATION");
    expect(copy.confirmLabel).toBe("Excluir ata");
  });

  it("mentions unsaved discard when requested", () => {
    const copy = meetingMinuteDeleteConfirmCopy(
      { minute_number: "2026/001", title: "X" },
      { discardUnsaved: true },
    );
    expect(copy.message).toContain("não salvas");
  });
});
