import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import {
  buildSupplierPerformanceQuery,
  type SupplierPerformance,
} from "../../api/supplierPerformance";
import {
  buildPluginPath,
  resolveActiveNavId,
  resolvePluginRoute,
} from "../../app/pluginRoutes";
import { canAccessView } from "../../app/routeAccess";
import { PerformanceComposition } from "./PerformanceComposition";
import {
  COVERAGE_LABELS,
  filterSuppliers,
  scoreLabel,
} from "./supplierPerformancePresentation";

const supplier = (
  name: string,
  code: string,
  status: SupplierPerformance["status"],
): SupplierPerformance => ({
  supplier_code: code,
  supplier_store: "01",
  supplier_name: name,
  status,
  branches: ["01"],
  idf: status === "complete" ? 0 : null,
  quality: {
    index: 0,
    assessed_count: 1,
    positive_count: 0,
    negative_count: 1,
    unknown_count: 0,
    conditional_count: 0,
    urgent_count: 0,
  },
  delivery: {
    index: null,
    assessed_count: 0,
    positive_count: 0,
    negative_count: 0,
    unknown_count: 0,
    conditional_count: 0,
    urgent_count: 0,
  },
  quality_contribution: 0,
  delivery_contribution: null,
});

describe("Supplier performance", () => {
  it("keeps branch collections and period in the BFF contract", () => {
    const params = new URLSearchParams(
      buildSupplierPerformanceQuery({
        branches: ["01", "02"],
        from: "2026-11-01",
        to: "2026-11-16",
      }),
    );
    expect(params.getAll("branch")).toEqual(["01", "02"]);
    expect(params.get("date_from")).toBe("2026-11-01");
    expect(params.get("date_to")).toBe("2026-11-16");
  });
  it("resolves deep links and uses normal portal access", () => {
    const path = buildPluginPath("supplier_performance");
    expect(resolvePluginRoute(path).view).toBe("supplier_performance");
    expect(resolveActiveNavId("supplier_performance")).toBe("overview");
    expect(
      canAccessView("supplier_performance", { access: true, manage: false }),
    ).toBe(true);
    expect(
      canAccessView("supplier_performance", { access: false, manage: true }),
    ).toBe(false);
  });
  it("searches accent-insensitively, matches codes and combines coverage", () => {
    const rows = [
      supplier("Conexões elétricas", "000001", "complete"),
      supplier("Conexões novas", "000002", "missing_quality"),
    ];
    expect(filterSuppliers(rows, "conexoes", "all")).toHaveLength(2);
    expect(filterSuppliers(rows, "conexoes", "incomplete")).toEqual([rows[1]]);
    expect(filterSuppliers(rows, "000001", "complete")).toEqual([rows[0]]);
    expect(filterSuppliers(rows, "outro", "all")).toEqual([]);
  });
  it("distinguishes missing data from a valid zero", () => {
    expect(scoreLabel(0)).toBe("0,00");
    expect(scoreLabel(null)).toBe("—");
    expect(COVERAGE_LABELS.missing_quality).toBe("Sem inspeções concluídas");
    const html = renderToStaticMarkup(
      <PerformanceComposition
        quality={0}
        delivery={null}
        score={null}
        qualityPoints={0}
        deliveryPoints={null}
        weights={{ quality_weight: 70, delivery_weight: 30 }}
      />,
    );
    expect(html).toContain("Aguardando base completa");
    expect(html).toContain("0,00 pontos na composição");
    expect(html).toContain("Sem contribuição calculável");
    expect(html).toContain("Sem base para cálculo");
  });
});
