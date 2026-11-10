import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("PrcOfficialSupplierSearchField — REF-021-REF-01", () => {
  const src = read("PrcOfficialSupplierSearchField.tsx");
  const lookup = read("PrcSupplierLookup.tsx");
  const api = read("../api/productRegistrationApi.ts");

  it("reuses official SA2 search contract and cancels stale responses", () => {
    expect(lookup).toMatch(/export function useSupplierSearch/);
    expect(lookup).toMatch(/AbortController/);
    expect(lookup).toMatch(/seq\.current/);
    expect(api).toMatch(/reference-data\/suppliers\/search/);
    expect(src).toMatch(/useSupplierSearch/);
  });

  it("selects atomic supplierCode+store with leading zeros preserved as strings", () => {
    expect(src).toMatch(/supplierCode/);
    expect(src).toMatch(/store/);
    expect(src).toMatch(/String\(hit\.supplier_code/);
    expect(src).toMatch(/String\(hit\.supplier_store/);
    expect(src).not.toMatch(/Number\(/);
    expect(src).not.toMatch(/parseInt/);
  });

  it("fails closed without manual code/store inputs", () => {
    expect(src).toMatch(/supplierSearchUnavailable|Busca indisponível|indisponível/);
    expect(src).not.toMatch(/EngineeringTextField/);
    expect(src).not.toMatch(/onChange=\{\(value\) =>[\s\S]*supplierCode/);
  });
});
