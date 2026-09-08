import { describe, expect, it } from "vitest";
import { ClipboardList, FileText, PackagePlus } from "lucide-react";

import { iconForRequestType } from "./requestTypeIcons";

describe("iconForRequestType", () => {
  it("mapeia NF e MP", () => {
    expect(iconForRequestType("invoice-issuance")).toBe(FileText);
    expect(iconForRequestType("raw-material-creation")).toBe(PackagePlus);
  });

  it("usa fallback para código desconhecido", () => {
    expect(iconForRequestType("future-type")).toBe(ClipboardList);
  });
});
