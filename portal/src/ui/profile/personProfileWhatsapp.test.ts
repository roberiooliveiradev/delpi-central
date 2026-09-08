import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  resolveWhatsappE164,
  resolveWhatsappSource,
} from "./personProfileWhatsapp.ts";

describe("personProfileWhatsapp", () => {
  it("resolves whatsapp source from matching phone", () => {
    assert.equal(
      resolveWhatsappSource({
        phone_e164: "+5511999",
        mobile_e164: "+5511888",
        whatsapp_e164: "+5511999",
      }),
      "phone",
    );
  });

  it("resolves whatsapp source from matching mobile", () => {
    assert.equal(
      resolveWhatsappSource({
        phone_e164: "+5511999",
        mobile_e164: "+5511888",
        whatsapp_e164: "+5511888",
      }),
      "mobile",
    );
  });

  it("builds whatsapp e164 from selected source", () => {
    assert.equal(resolveWhatsappE164("phone", "+5511", "+5522"), "+5511");
    assert.equal(resolveWhatsappE164("mobile", "+5511", "+5522"), "+5522");
    assert.equal(resolveWhatsappE164(null, "+5511", "+5522"), null);
  });

  it("returns null when whatsapp absent", () => {
    assert.equal(
      resolveWhatsappSource({
        phone_e164: "+5511999",
        mobile_e164: null,
        whatsapp_e164: null,
      }),
      null,
    );
  });
});
