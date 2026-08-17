import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  FALLBACK_NOTIFICATION_CATALOG,
  resolveNotificationPreferenceDisplay,
} from "./notificationCatalog";

describe("resolveNotificationPreferenceDisplay", () => {
  it("plataforma: notificação + Minha Delpi", () => {
    const display = resolveNotificationPreferenceDisplay("access", FALLBACK_NOTIFICATION_CATALOG, []);
    assert.equal(display.notificationName, "Acesso a aplicações");
    assert.equal(display.applicationName, "Minha Delpi");
    assert.equal(display.iconName, "key-round");
  });

  it("comercial: Faturar notas fiscais + Portal Comercial", () => {
    const display = resolveNotificationPreferenceDisplay(
      "commercial",
      FALLBACK_NOTIFICATION_CATALOG,
      [{ id: "commercial", name: "Portal Comercial", icon: "briefcase-business" }],
    );
    assert.equal(display.notificationName, "Faturar notas fiscais");
    assert.equal(display.applicationName, "Portal Comercial");
    assert.equal(display.iconName, "briefcase-business");
  });

  it("app: ícone do manifesto prevalece sobre hardcode do catálogo", () => {
    const withoutApp = resolveNotificationPreferenceDisplay(
      "commercial",
      FALLBACK_NOTIFICATION_CATALOG,
      [],
    );
    const withManifest = resolveNotificationPreferenceDisplay(
      "commercial",
      FALLBACK_NOTIFICATION_CATALOG,
      [{ id: "commercial", name: "Portal Comercial", icon: "briefcase-business" }],
    );
    assert.equal(withoutApp.iconName, "briefcase");
    assert.equal(withManifest.iconName, "briefcase-business");
  });

  it("emissão e lançamento: nomes distintos e apps distintos", () => {
    const emission = resolveNotificationPreferenceDisplay(
      "invoice_issuance",
      FALLBACK_NOTIFICATION_CATALOG,
      [{ id: "invoice-issuance", name: "Emissão de Notas Fiscais", icon: "file-output" }],
    );
    const posting = resolveNotificationPreferenceDisplay(
      "lancamento_notas_fiscais",
      FALLBACK_NOTIFICATION_CATALOG,
      [{ id: "lancamento-notas-fiscais", name: "Lançamento de Notas Fiscais", icon: "file-text" }],
    );
    assert.equal(emission.notificationName, "Solicitações de emissão de NF");
    assert.equal(emission.applicationName, "Emissão de Notas Fiscais");
    assert.equal(posting.notificationName, "Pendências e menções de lançamento");
    assert.equal(posting.applicationName, "Lançamento de Notas Fiscais");
  });
});
