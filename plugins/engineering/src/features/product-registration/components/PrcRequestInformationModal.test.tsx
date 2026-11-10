import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("PrcRequestInformationModal — PRC-REF-019 + REF-021-REF-01", () => {
  const src = read("PrcRequestInformationModal.tsx");
  const copy = read("../prcCopy.ts");
  const css = read("../prc.css");
  const search = read("PrcOfficialSupplierSearchField.tsx");
  const queue = read("../pages/PrcQueuePage.tsx");
  const flags = read("PrcFlagsOpsPanel.tsx");
  const verify = read("PrcVerificationPanel.tsx");

  it("permite adicionar/remover perguntas (labels em pt-BR no catálogo de copy)", () => {
    expect(copy).toMatch(/addQuestion: "Adicionar pergunta"/);
    expect(copy).toMatch(/removeQuestion: "Remover pergunta"/);
    expect(src).toMatch(/PRC_INFO_COPY\.addQuestion/);
    expect(src).toMatch(/PRC_INFO_COPY\.removeQuestion/);
  });

  it("exibe destinatário, tipos de alvo e mensagem complementar", () => {
    expect(copy).toMatch(/recipient: "Destinatário"/);
    expect(src).toMatch(/requesterLabel/);
    expect(src).toMatch(/INFO_TARGET_OPTIONS/);
    expect(src).toMatch(/targetType === "FIELD"/);
    expect(src).toMatch(/targetType === "SUPPLIER_LINK"/);
    expect(src).toMatch(/questionableFieldSpecs\(fieldSpecs\)/);
    expect(copy).toMatch(/message: "Mensagem complementar \(opcional\)"/);
  });

  it("valida ≥1 pergunta com texto antes de confirmar", () => {
    expect(src).toMatch(/validateInfoQuestions\(drafts\)/);
    expect(src).toMatch(/if \(!result\.valid\)/);
    expect(src).toMatch(/setRowErrors\(result\.rowErrors\)/);
    expect(src).toMatch(/pendingFieldsFromDrafts\(drafts\)/);
    expect(src).toMatch(/buildQuestionInputs\(drafts\)/);
  });

  it("usa HostDialog wide + SearchableSelect oficiais (sem HelpCircle)", () => {
    expect(src).toMatch(/EngineeringHostDialog/);
    expect(src).toMatch(/delpi-ui-modal--wide/);
    expect(src).toMatch(/EngineeringSearchableSelect/);
    expect(src).toMatch(/searchable/);
    expect(src).not.toMatch(/EngineeringSelectField/);
    expect(src).toMatch(/EngineeringTextAreaField/);
    expect(src).toMatch(/EngineeringFormActions/);
    expect(src).toMatch(/EngineeringActionButton/);
    expect(src).not.toMatch(/HelpCircle|HelpTooltip/);
    expect(src).not.toMatch(/my-requests|requests-api/);
    expect(css).toMatch(/engineering-prc-info-modal/);
  });

  it("SUPPLIER_LINK usa pesquisa oficial SA2 sem fallback manual código/loja", () => {
    expect(src).toMatch(/PrcOfficialSupplierSearchField/);
    expect(src).not.toMatch(/EngineeringTextField/);
    expect(src).not.toMatch(/supplierPickPlaceholder/);
    expect(search).toMatch(/searchPrcSuppliers|useSupplierSearch/);
    expect(search).toMatch(/supplier_code/);
    expect(search).toMatch(/supplier_store/);
    expect(copy).toMatch(/supplierSearch:/);
    expect(copy).toMatch(/supplierSearchUnavailable/);
  });

  it("bandeiras ficam compactas no hero da fila (sem faixa externa)", () => {
    expect(queue).toMatch(/<PrcFlagsOpsPanel basePath=\{basePath\} compact \/>/);
    expect(queue).toMatch(/EngineeringPageHero/);
    expect(queue).not.toMatch(
      /<\/EngineeringPageHero>\s*\n\s*\{!forbidden \? <PrcFlagsOpsPanel/,
    );
    expect(flags).toMatch(/compact/);
    expect(flags).toMatch(/engineering-prc__flags-ops--hero/);
    expect(flags).toMatch(/Campos sinalizados/);
    expect(flags).toMatch(/from "lucide-react"/);
  });

  it("remove Definir encaminhamento da verificação", () => {
    expect(verify).not.toMatch(/Definir encaminhamento|routeDivergence|Encaminhamento/);
    expect(verify).not.toMatch(/REQUESTER_CORRECTION|ERP_MANUAL_CORRECTION/);
    expect(verify).toMatch(/Revisar/);
    expect(verify).toMatch(/Problemas \(/);
    expect(verify).toMatch(/Comparação SB1 e SA5/);
  });

  it("ActionBar abre o modal para request_information e repassa questions", () => {
    const bar = read("PrcActionBar.tsx");
    const specs = read("prcActionSpecs.ts");
    expect(specs).toMatch(/needsQuestions: true/);
    expect(bar).toMatch(/spec\.needsQuestions/);
    expect(bar).toMatch(/PrcRequestInformationModal/);
    expect(bar).toMatch(/onRunAction\(infoSpec, \{ questions, message, pendingFields \}\)/);
    expect(bar).toMatch(/requesterLabel/);
    expect(bar).toMatch(/fieldSpecs/);
  });

  it("PrcDetailPage encaminha questions/message/pendingFields no corpo da ação", () => {
    const page = read("../pages/PrcDetailPage.tsx");
    expect(page).toMatch(/questions: extras\.questions/);
    expect(page).toMatch(/message: extras\.message/);
    expect(page).toMatch(/pendingFields: extras\.pendingFields/);
    expect(page).toMatch(/requesterLabel=\{prcRequesterLabel\(detail\.requester\)\}/);
    expect(page).toMatch(/fieldSpecs=\{fieldSpecs\}/);
    expect(page).toMatch(/<PrcInformationExchangePanel/);
    expect(page).not.toMatch(/onRouted|divergenceRoutings|routeDivergence/);
  });
});
