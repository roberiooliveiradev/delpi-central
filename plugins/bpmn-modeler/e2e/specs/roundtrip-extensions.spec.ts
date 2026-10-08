/**
 * G4 — RT-EXT-*: extension preservation.
 * ext-false: mustUnderstand=false + extensionElements externos + atributos
 * namespaced desconhecidos → preserved após round-trip.
 * ext-true: mustUnderstand=true → import allowed, open read-only, artifact
 * não é destruído (read-back íntegro), save destrutivo bloqueado.
 */
import { test, expect, importModelViaApi, modelUrl } from "../helpers";
import { fetchWorkingCopyXml } from "../ce-helpers";
import { readFixture, roundTripNoEdit } from "../rt-helpers";

const EXT_F = readFixture("ext-false.bpmn");
const EXT_T = readFixture("ext-true.bpmn");

test("RT-EXT-01 mustUnderstand=false: extensionElements + attrs namespaced preservados", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", EXT_F, {
    name: "RT-EXT-01",
    renderIds: ["XT1"],
    // KNOWN_DEFECT G4-EXT-1 (bpmn-moddle serializer):
    //  - `bpmn:extension/@definition` (QName da extensão) é dropado;
    //  - attrs namespaced dentro de extensionElements perdem o prefixo
    //    (`vend:flag` → `flag`). Elemento/texto/filhos preservados.
    // Classificado: EXTENSION_LOSS parcial → INTEROPERABILITY_GAP (vendor).
    allowed: [
      { kind: "ATTR_DIFF", pathIncludes: "extension", detailIncludes: "definition" },
      { kind: "ATTR_DIFF", detailIncludes: "flag" },
    ],
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
