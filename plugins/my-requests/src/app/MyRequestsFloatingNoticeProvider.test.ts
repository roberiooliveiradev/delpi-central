import { describe, expect, it } from "vitest";

import { friendlyNoticeMessage } from "../app/MyRequestsFloatingNoticeProvider";

describe("friendlyNoticeMessage", () => {
  it("extrai message de envelope JSON cru", () => {
    const raw =
      '{"success":false,"message":"Transição não permitida para o status atual.","data":{"code":"invalid_transition"}}';
    expect(friendlyNoticeMessage(raw, "fallback")).toBe(
      "Transição não permitida para o status atual.",
    );
  });

  it("mantém texto amigável simples", () => {
    expect(friendlyNoticeMessage("Falha ao carregar", "fallback")).toBe("Falha ao carregar");
  });
});
