import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import presentationVocabulary from "../../content/presentation_vocabulary.json";

const componentsDir = dirname(fileURLToPath(import.meta.url));

const PRESENTATION_SCAN_MODULES = [
  "message/assistantProseRendering.ts",
  "chatPresentation.ts",
  "presentationCategoryFilter.ts",
  "presentationFieldLabels.ts",
  "presentationInteractivityPolicy.ts",
  "presentationMetadataPolicy.ts",
  "presentationMultiRoute.ts",
  "presentationStackBlueprint.ts",
  "presentationStackPlan.ts",
  "presentationStackSections.ts",
  "presentationStructureDedup.ts",
  "presentationTableDedup.ts",
  "visualSegmentCollector.ts",
];

function countPathIncludes(relativePath: string): number {
  const source = readFileSync(join(componentsDir, relativePath), "utf8");

  return (source.match(/path\.includes\(/g) ?? []).length;
}

function countInferTableRoleConditionalReturns(): number {
  const source = readFileSync(join(componentsDir, "presentationStackPlan.ts"), "utf8");
  const fnMatch = source.match(/export function inferTableRoleFromTitle[\s\S]*?\n\}/);

  if (!fnMatch) {
    return 0;
  }

  return (fnMatch[0].match(/^\s+if \(/gm) ?? []).length;
}

describe("presentationLegacyFallbackGate (Playbook 12 R20)", () => {
  const legacyFallbacks = presentationVocabulary.legacyFallbacks;
  const baseline = legacyFallbacks.inventoryBaseline;
  const allowedModules = new Set(legacyFallbacks.allowedPathIncludesModules);

  it("documenta fallbacks legacy no vocabulário", () => {
    expect(legacyFallbacks.tableRoleFromTitle.preferMetadataField).toBe("presentation.role");
    expect(legacyFallbacks.humanizeFieldKey.preferMetadataField).toBe("columns[].label");
  });

  it("não adiciona path.includes fora dos módulos permitidos", () => {
    for (const moduleName of PRESENTATION_SCAN_MODULES) {
      const count = countPathIncludes(moduleName);

      if (allowedModules.has(moduleName)) {
        const maxCount =
          baseline.pathIncludesByModule[
            moduleName as keyof typeof baseline.pathIncludesByModule
          ] ?? 0;

        expect(count).toBeLessThanOrEqual(maxCount);
        continue;
      }

      expect(count).toBe(0);
    }
  });

  it("mantém baseline de inferTableRoleFromTitle (fallback legacy por título)", () => {
    expect(countInferTableRoleConditionalReturns()).toBeLessThanOrEqual(
      baseline.inferTableRoleFromTitleConditionalReturns,
    );
  });

  it("não reintroduz ROUTE_VISUAL_ORDER no multi-rota", () => {
    const source = readFileSync(join(componentsDir, "presentationMultiRoute.ts"), "utf8");

    expect(source.includes("ROUTE_VISUAL_ORDER")).toBe(false);
  });
});
