type DrillDownColumn = { key: string; label: string };

const CODE_KEY =
  /^(code|codigo|cod|id|numero|number|nropor|sku|produto|product|product_code|productcode)$/i;
const BRANCH_KEY = /^(branch|filial|loja|store)$/i;
const WAREHOUSE_KEY = /^(warehouse|armazem|deposito)$/i;
const DESC_KEY = /^(description|descricao|descri|nome|name|product_description)$/i;

function normalizeCode(value: string): string {
  return value.replace(/\./g, "").trim();
}

function normalizeBranchOrWarehouse(value: string): string {
  const digits = value.replace(/\D/g, "");

  if (!digits) {
    return value.trim();
  }

  if (digits.length <= 2) {
    return digits.padStart(2, "0");
  }

  return digits;
}

export function buildDrillDownQuery(
  row: Record<string, unknown>,
  columns: DrillDownColumn[],
): string | null {
  const codeCol = columns.find((column) => CODE_KEY.test(column.key));
  const descCol = columns.find((column) => DESC_KEY.test(column.key));
  const branchCol = columns.find((column) => BRANCH_KEY.test(column.key));
  const warehouseCol = columns.find((column) => WAREHOUSE_KEY.test(column.key));

  const code = codeCol
    ? normalizeCode(String(row[codeCol.key] ?? ""))
    : "";
  const desc = descCol ? String(row[descCol.key] ?? "").trim() : "";
  const branch = branchCol
    ? normalizeBranchOrWarehouse(String(row[branchCol.key] ?? ""))
    : "";
  const warehouse = warehouseCol
    ? normalizeBranchOrWarehouse(String(row[warehouseCol.key] ?? ""))
    : "";

  if (branch || warehouse) {
    const filters: string[] = [];

    if (branch) {
      filters.push(`filial ${branch}`);
    }

    if (warehouse) {
      filters.push(`armazém ${warehouse}`);
    }

    if (code) {
      filters.push(`do produto ${code}`);
    }

    return `filtre ${filters.join(" ")}`;
  }

  if (code) {
    return `Detalhe do item ${code}${desc ? ` (${desc})` : ""}`;
  }

  if (desc) {
    return `Mais informações sobre ${desc}`;
  }

  const firstVal = String(row[columns[0]?.key] ?? "").trim();

  return firstVal ? `Detalhe de ${firstVal}` : null;
}
