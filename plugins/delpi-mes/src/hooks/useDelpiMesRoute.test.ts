import { describe, expect, it } from "vitest";

import {
  buildDelpiMesHref,
  buildRegistrationHref,
  parseDelpiMesRoute,
} from "./useDelpiMesRoute";

describe("Delpi MES routing", () => {
  it("defaults the product root to monitoring and branch 01", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes", "")).toEqual({
      area: "monitoring",
      branch: "01",
      workCenter: null,
      registrationPage: null,
    });
  });

  it("preserves area and branch in a shareable URL", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/downtimes", "?branch=02")).toEqual({
      area: "downtimes",
      branch: "02",
      workCenter: null,
      registrationPage: null,
    });
    expect(buildDelpiMesHref("history", "02")).toBe("/apps/delpi-mes/history?branch=02");
  });

  it("parses the selected work center only on monitoring", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/monitoring", "?branch=01&workCenter=CT-35")).toEqual({
      area: "monitoring",
      branch: "01",
      workCenter: "CT-35",
      registrationPage: null,
    });
    expect(
      parseDelpiMesRoute("/apps/delpi-mes/downtimes", "?branch=01&workCenter=CT-35").workCenter,
    ).toBeNull();
    expect(buildDelpiMesHref("monitoring", "01", "CT 35")).toBe(
      "/apps/delpi-mes/monitoring?branch=01&workCenter=CT%2035",
    );
  });

  it("routes the registrations hub without branch", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/registrations", "")).toEqual({
      area: "registrations",
      branch: "01",
      workCenter: null,
      registrationPage: null,
    });
    expect(buildDelpiMesHref("registrations", "02")).toBe("/apps/delpi-mes/registrations");
  });

  it("routes the downtime-reasons catalog page", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/registrations/downtime-reasons", "")).toEqual({
      area: "registrations",
      branch: "01",
      workCenter: null,
      registrationPage: "downtime-reasons",
    });
    expect(buildRegistrationHref("downtime-reasons")).toBe(
      "/apps/delpi-mes/registrations/downtime-reasons",
    );
  });

  it("ignores branch and unknown segments on registrations routes", () => {
    expect(
      parseDelpiMesRoute("/apps/delpi-mes/registrations", "?branch=02").registrationPage,
    ).toBeNull();
    expect(
      parseDelpiMesRoute("/apps/delpi-mes/registrations/other", "").registrationPage,
    ).toBeNull();
    expect(parseDelpiMesRoute("/apps/delpi-mes/registrations", "").workCenter).toBeNull();
  });
});
