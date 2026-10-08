/**
 * G4 — RT-EXT-*: extension preservation.
 * ext-false: mustUnderstand=false + extensionElements externos + atributos
 * namespaced desconhecidos preserváveis → round-trip completo sem perda
 * (G4-EXT-1 correction: `bpmn:extension/@definition` reparado via $attrs).
 * ext-true: mustUnderstand=true → import allowed, open read-only, artifact
 * não é destruído (read-back íntegro), save destrutivo bloqueado.
 * ext-risky: attr namespaced com URI == ns do elemento (não reemissível
 * pelo serializer vendor) → fail-closed: read-only + artefato byte-exact.
 */
import { test, expect, importModelViaApi, modelUrl, waitSaved } from "../helpers";
import { fetchWorkingCopyXml, openEditor } from "../ce-helpers";
import {
  expectEquivalent,
  readFixture,
  renameViaDirectEdit,
  roundTripNoEdit,
  serializeViaValidate,
} from "../rt-helpers";

const EXT_F = readFixture("ext-false.bpmn");
const EXT_T = readFixture("ext-true.bpmn");
const EXT_R = readFixture("ext-risky.bpmn");

test("RT-EXT-01 mustUnderstand=false: extensionElements + attrs namespaced preservados", async ({
  page,
}) => {
  // EXTENSION_LOSS ALLOWLIST: 0 — definition QName, extensionElements,
  // nested, texto e attrs namespaced preserváveis (ns != ns do elemento)
  // sobrevivem ao round-trip completo via produto.
  await roundTripNoEdit(page, "editor", EXT_F, {
    name: "RT-EXT-01",
    renderIds: ["XT1"],
    allowed: [],
  });
});

test("RT-EXT-02 mustUnderstand=true: read-only + artifact não destruído", async ({
  page,
}) => {
  const modelId = await importModelViaApi("editor", "RT-EXT-02", EXT_T);

  // bytes persistidos intactos (backend opaco)
  const stored = await fetchWorkingCopyXml("editor", modelId);
  expect(stored).toContain('mustUnderstand="true"');
  expect(stored).toContain("vend:prop");

  await page.goto(modelUrl(modelId));
  await expect(page.locator(".djs-container")).toBeVisible({ timeout: 20_000 });

  // banner read-only do contrato §10/§16
  await expect(page.locator(".bpmnm-banner--readonly")).toContainText(
    "somente leitura",
    { timeout: 10_000 },
  );

  // read-back autoritativo após open: conteúdo não foi silenciado
  const afterOpen = await fetchWorkingCopyXml("editor", modelId);
  expect(afterOpen).toBe(stored);
});

test("RT-EXT-03 extensão não reemissível: fail-closed read-only + artifact byte-exact", async ({
  page,
}) => {
  const modelId = await importModelViaApi("editor", "RT-EXT-03", EXT_R);

  // persistência opaca intacta — vend:flag (same-ns attr) está nos bytes
  const stored = await fetchWorkingCopyXml("editor", modelId);
  expect(stored).toContain('vend:flag="1"');

  await page.goto(modelUrl(modelId));
  await expect(page.locator(".djs-container")).toBeVisible({ timeout: 20_000 });

  // G4-EXT-1 gate: UNSUPPORTED_EXTENSION_SERIALIZATION → read-only
  await expect(page.locator(".bpmnm-banner--readonly")).toContainText(
    "somente leitura",
    { timeout: 10_000 },
  );
  // "Salvar" não existe para o usuário nesse estado — write destrutivo impossível
  await expect(
    page.getByRole("button", { name: "Salvar", exact: true }),
  ).toHaveCount(0);

  // open não mutou o canônico
  const afterOpen = await fetchWorkingCopyXml("editor", modelId);
  expect(afterOpen).toBe(stored);
});

test("RT-EXT-04 safe-edit com extensões: rename não destrói extensionElements", async ({
  page,
}) => {
  const modelId = await importModelViaApi("editor", "RT-EXT-04", EXT_F);
  await openEditor(page, modelId);
  await expect(
    page.locator('.djs-element[data-element-id="XT1"]'),
  ).toBeAttached({ timeout: 15_000 });

  // rename do próprio elemento que carrega extensionElements — prova que
  // safe-edit no path mais agressivo não toca o conteúdo de extensão
  await renameViaDirectEdit(page, "XT1", "Task Renomeada");
  await waitSaved(page);

  const saved = await fetchWorkingCopyXml("editor", modelId);
  expect(saved).toContain("Task Renomeada");
  expect(saved).toContain("vend:prop");
  expect(saved).toContain('acme:flag="1"');
  expect(saved).toContain("vend:nested");
  expect(saved).toContain('definition="vend:suite"');

  // compare estrutural: único delta = name editado (+ BPMNLabel de DI)
  expectEquivalent(EXT_F, saved, "RT-EXT-04 fixture→saved", [
    { kind: "ATTR_DIFF", pathIncludes: "XT1", detailIncludes: "name" },
    { kind: "EXTRA_ELEMENT", pathIncludes: "SH_XT1" },
  ]);

  // re-serialize via produto e reimport — extensões continuam íntegras
  const { xml: serializedB } = await serializeViaValidate(page, modelId);
  expect(serializedB).toContain("vend:prop");
  expect(serializedB).toContain('definition="vend:suite"');
});
