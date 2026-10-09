/**
 * G4 — helpers de round-trip/interoperability E2E.
 *
 * Fluxo por caso (SPEC-FREEZE §18):
 *   import fixture via API real (POST /models/import)
 *   → GET working-copy (read-back opaco — TEXT_EQUAL do upload)
 *   → open no editor real (vendor parse + render check)
 *   → serialize via ação de produto "Validar" (POST body = exportXml())
 *   → compare semântico/DI/extensão (rt-compare)
 *   → reimport como NOVO model (importModelViaApi)
 *   → GET working-copy B (TEXT_EQUAL do serializado)
 *   → reabrir + re-serializar (idempotência) + revalidar
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, request, type Page } from "@playwright/test";
import {
  apiToken,
  importModelViaApi,
  type Actor,
} from "./helpers";
import { fetchWorkingCopyXml, openEditor } from "./ce-helpers";
import {
  checkIncomingOutgoingConsistency,
  compareBpmnXml,
  formatDiffs,
  type Diff,
} from "../../bpmn-editor/src/testing/rtCompare";

const BASE = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
const FIXTURE_DIR = join(
  dirname(fileURLToPath(import.meta.url)),
  "fixtures",
  "roundtrip",
);

export function readFixture(name: string): string {
  return readFileSync(join(FIXTURE_DIR, name), "utf-8");
}

export type ValidationReport = {
  evaluated_stages: string[];
  not_evaluated_stages: string[];
  issues: Array<{
    rule_id: string;
    stage: string;
    severity: string;
    element_id: string | null;
    path: string | null;
  }>;
};

/**
 * Serialização real do editor sem editar: o botão "Validar" do toolbar
 * chama `adapter.exportXml()` e POSTa o candidato — capturamos o body do
 * request (o artefato serializado pelo vendor) e o ValidationReport.
 */
export async function serializeViaValidate(
  page: Page,
  modelId: string,
): Promise<{ xml: string; report: ValidationReport }> {
  let posted: string | null = null;
  const onReq = (req: { url(): string; method(): string; postData(): string | null }) => {
    if (
      req.method() === "POST" &&
      req.url().includes(`/models/${modelId}/working-copy/validate`)
    ) {
      posted = req.postData();
    }
  };
  page.on("request", onReq);
  const respPromise = page.waitForResponse(
    (r) =>
      r.request().method() === "POST" &&
      r.url().includes(`/models/${modelId}/working-copy/validate`),
    { timeout: 30_000 },
  );
  await page.getByRole("button", { name: "Validar" }).click();
  const resp = await respPromise;
  page.off("request", onReq);
  if (posted == null) throw new Error("validate POST body não capturado");
  const body = (await resp.json()) as { data?: ValidationReport };
  if (!body.data) throw new Error("validate response sem envelope data");
  return { xml: posted, report: body.data };
}

/** Validação on-demand via API real (mesmo endpoint do editor). */
export async function validateXmlApi(
  actor: Actor,
  modelId: string,
  xml: string,
): Promise<ValidationReport> {
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: BASE });
  const resp = await ctx.post(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy/validate`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/xml; charset=utf-8",
      },
      data: xml,
    },
  );
  if (!resp.ok())
    throw new Error(`validate failed: ${resp.status()} ${await resp.text()}`);
  const body = (await resp.json()) as { data?: ValidationReport };
  if (!body.data) throw new Error("validate response sem envelope data");
  return body.data;
}

/** Assinatura comparável de um report (ids de issue são runtime-generated). */
function reportSignature(rep: ValidationReport): string[] {
  return rep.issues
    .map((i) => `${i.rule_id}|${i.severity}|${i.element_id ?? ""}`)
    .sort();
}

export function expectReportsEquivalent(
  a: ValidationReport,
  b: ValidationReport,
  label: string,
): void {
  expect(
    reportSignature(b),
    `issues divergem após reimport (${label})`,
  ).toEqual(reportSignature(a));
  expect(
    [...b.evaluated_stages].sort(),
    `stages avaliados divergem (${label})`,
  ).toEqual([...a.evaluated_stages].sort());
}

/** Diffs que o teste declara esperar (ex.: attr editado no safe-edit). */
export type AllowedDiff = {
  kind?: Diff["kind"];
  pathIncludes?: string;
  detailIncludes?: string;
};

/**
 * Safe-edit determinístico: dblclick no elemento abre o directEditing do
 * vendor (sem depender de hit-test de seleção/context pad — frágil em
 * diagramas largos com zoom-out). Edita o texto e confirma com Enter.
 */
export async function renameViaDirectEdit(
  page: Page,
  elementId: string,
  text: string,
): Promise<void> {
  // dblclick real no centro do elemento — directEditing do vendor.
  // ATENÇÃO: escolher elemento fora da zona da palette/panel (esquerda/
  // direita do canvas) — em diagramas largos após fitViewport, elementos
  // extremos podem ficar sob overlays que interceptam pointer events.
  const el = page.locator(`.djs-element[data-element-id="${elementId}"]`);
  await expect(el).toBeAttached({ timeout: 15_000 });
  await el.scrollIntoViewIfNeeded();
  const box = await el.boundingBox();
  if (!box) throw new Error(`element ${elementId} sem boundingBox`);
  await page.mouse.dblclick(box.x + box.width / 2, box.y + box.height / 2);
  const editor = page.locator(
    ".djs-direct-editing-parent textarea, .djs-direct-editing-parent [contenteditable]",
  );
  await expect(editor.first()).toBeVisible({ timeout: 5_000 });
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.type(text);
  await page.keyboard.press("Enter");
}

export function expectEquivalent(
  expectedXml: string,
  actualXml: string,
  label: string,
  allowed: AllowedDiff[] = [],
): void {
  const diffs = [
    ...compareBpmnXml(expectedXml, actualXml),
    ...checkIncomingOutgoingConsistency(actualXml),
  ];
  const unexpected = diffs.filter(
    (d) =>
      !allowed.some(
        (a) =>
          (!a.kind || a.kind === d.kind) &&
          (!a.pathIncludes || d.path.includes(a.pathIncludes)) &&
          (!a.detailIncludes || d.detail.includes(a.detailIncludes)),
      ),
  );
  expect(
    unexpected,
    `round-trip divergiu (${label}):\n${formatDiffs(unexpected)}\n--- esperados permitidos: ${JSON.stringify(allowed)}`,
  ).toEqual([]);
}

export type RoundTripOptions = {
  /** ids de shapes que devem estar renderizados no editor (`.djs-element`). */
  renderIds?: string[];
  /** nome base do model. */
  name: string;
  /** severidades de issue proibidas nos reports (default: ["ERROR"]). */
  forbidSeverities?: string[];
  /**
   * Diffs declarados esperados no fixture→serialize (EXPECTED_*_DIFF ou
   * defeito conhecido registrado — cada item exige comentário no spec).
   */
  allowed?: AllowedDiff[];
};

/**
 * No-op round-trip completo via produto real.
 * Retorna ids dos dois models para asserts adicionais.
 */
export async function roundTripNoEdit(
  page: Page,
  actor: Actor,
  fixtureXml: string,
  opts: RoundTripOptions,
): Promise<{ modelA: string; modelB: string; serializedA: string }> {
  const forbid = opts.forbidSeverities ?? ["ERROR"];

  // 1. import → store (persistência opaca)
  const modelA = await importModelViaApi(actor, opts.name, fixtureXml);
  const storedA = await fetchWorkingCopyXml(actor, modelA);
  expect(
    storedA,
    "working-copy importado deve ser TEXT_EQUAL ao upload (opaque persistence)",
  ).toBe(fixtureXml);

  // 2. validação do fixture (baseline antes de export)
  const reportBase = await validateXmlApi(actor, modelA, fixtureXml);
  const baseErrors = reportBase.issues.filter((i) =>
    forbid.includes(i.severity),
  );
  expect(
    baseErrors,
    `fixture com issues ${forbid.join("/")}: ${JSON.stringify(baseErrors)}`,
  ).toEqual([]);

  // 3. open editor (vendor parse) + render check
  await openEditor(page, modelA);
  for (const id of opts.renderIds ?? []) {
    await expect(
      page.locator(`.djs-element[data-element-id="${id}"]`),
      `fixture ${id} não renderizou no editor`,
    ).toBeAttached({ timeout: 15_000 });
  }

  // 4. serialize via produto ("Validar" = exportXml) — NO-OP edit
  const { xml: serializedA, report: reportA } = await serializeViaValidate(
    page,
    modelA,
  );
  expectEquivalent(
    fixtureXml,
    serializedA,
    `${opts.name}: fixture→serialize`,
    opts.allowed,
  );

  // 5. reimport como NOVO model
  const modelB = await importModelViaApi(
    actor,
    `${opts.name}-rt`,
    serializedA,
  );
  const storedB = await fetchWorkingCopyXml(actor, modelB);
  expect(storedB, "reimport deve persistir bytes do serializado").toBe(
    serializedA,
  );

  // 6. reabrir + re-serializar (idempotência) + revalidar
  await openEditor(page, modelB);
  for (const id of opts.renderIds ?? []) {
    await expect(
      page.locator(`.djs-element[data-element-id="${id}"]`),
      `reimported ${id} não renderizou`,
    ).toBeAttached({ timeout: 15_000 });
  }
  const { xml: serializedB, report: reportB } = await serializeViaValidate(
    page,
    modelB,
  );
  expectEquivalent(serializedA, serializedB, `${opts.name}: serialize→reimport→serialize`);
  expectReportsEquivalent(reportA, reportB, opts.name);
  const errsB = reportB.issues.filter((i) => forbid.includes(i.severity));
  expect(
    errsB,
    `reimported com issues ${forbid.join("/")}: ${JSON.stringify(errsB)}`,
  ).toEqual([]);

  return { modelA, modelB, serializedA };
}
