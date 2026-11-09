import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("PrcRequestInformationModal — PRC-REF-019", () => {
  const src = read("PrcRequestInformationModal.tsx");
  const copy = read("../prcCopy.ts");

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

  it("usa o kit Engineering host-contained e não cria ícone de ajuda", () => {
    expect(src).toMatch(/EngineeringHostDialog/);
    expect(src).not.toMatch(/HelpCircle|HelpTooltip/);
    expect(src).not.toMatch(/my-requests|requests-api/);
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
  });
});
