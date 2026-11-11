/** PRC-REF-023-UI-FORM-UNIFICATION-05 — asserções de fonte: existe
 * UMA composição de formulário PRC no @delpi/plugin-ui e os dois MFEs
 * são wrappers finos (adapter + shell + navegação), sem wizard local. */

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const src = (rel: string) => readFileSync(resolve(__dirname, rel), "utf8");
const kitForm = () =>
  src("../../../../../plugin-ui/src/components/prc/PrcRequestForm.tsx");
const engPage = () => src("./PrcCreatePage.tsx");
const mrPage = () =>
  src("../../../../../my-requests/src/features/product-registration/PrcRequestPage.tsx");

describe("UNIFICATION-05 — formulário PRC único no kit", () => {
  it("o kit contém a composição completa do wizard", () => {
    const t = kitForm();
    expect(t).toContain("export function PrcRequestForm");
    expect(t).toContain("export type PrcFormDataProvider");
    // três etapas canônicas
    expect(t).toContain('"Identificação"');
    expect(t).toContain('"Ficha técnica"');
    expect(t).toContain('"Revisar e enviar"');
    // ficha técnica + grade + catálogos + fornecedores + anexos + revisão
    expect(t).toContain("delpi-prc__form-grid");
    expect(t).toContain("PrcCatalogStore");
    expect(t).toContain("PrcSupplierTable");
    expect(t).toContain("PrcReasonField");
    expect(t).toContain("PrcFileDropzone");
    expect(t).toContain("PrcAttachmentStrip");
    expect(t).toContain("PrcDetailFieldGrid");
    // payload e diff via helpers neutros — um único buildBody
    expect(t).toContain("buildCreateIntakeBody");
    expect(t).toContain("buildUpdateIntakeBody");
    expect(t).toContain("computeScalarDiff");
    expect(t).toContain("computeLinkDiff");
    // sem URLs/tokens/clients HTTP no kit
    expect(t).not.toMatch(/fetch\(|httpGet|httpPost|api-delpi/);
    expect(t).not.toContain("Authorization");
  });

  it("Portal Engenharia é wrapper fino do formulário compartilhado", () => {
    const t = engPage();
    expect(t).toContain("<PrcRequestForm");
    expect(t).toContain('source={PRC_PORTAL_SOURCE}');
    expect(t).toContain("dataProvider={dataProvider}");
    expect(t).toContain("portalScopeClassName={ENGINEERING_PORTAL_SCOPE}");
    expect(t).toContain("navigatePrc(PRC_PATHS.detail(requestId)");
    // sem composição de wizard local
    expect(t).not.toContain("renderSheetField");
    expect(t).not.toContain("delpi-prc__form-grid");
    expect(t).not.toContain("PrcSupplierTable");
    expect(t).not.toContain("FIELD_GROUPS");
    expect(t).not.toContain("buildCreateIntakeBody");
  });

  it("Minhas Solicitações consome o MESMO formulário", () => {
    const t = mrPage();
    expect(t).toContain("<PrcRequestForm");
    expect(t).toContain('source={PRC_SOURCE}');
    expect(t).toContain('"my-requests"');
    expect(t).toContain("dataProvider={dataProvider}");
    expect(t).toContain("onCompleted={onDone}");
    // sem segundo wizard
    expect(t).not.toContain("renderSheetField");
    expect(t).not.toContain("renderCatalogField");
    expect(t).not.toContain("delpi-prc__form-grid");
    expect(t).not.toContain("PrcSupplierTable");
    expect(t).not.toContain("FIELD_GROUPS");
    expect(t).not.toContain("new PrcCatalogStore");
  });
});
