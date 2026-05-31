type DrillDownColumn = { key: string; label: string };

export type TableRowMenuAction = {
  id: string;
  label: string;
  query: string;
};

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

export function extractRowContext(
  row: Record<string, unknown>,
  columns: DrillDownColumn[],
): {
  code: string;
  desc: string;
  branch: string;
  warehouse: string;
} {
  const codeCol = columns.find((column) => CODE_KEY.test(column.key));
  const descCol = columns.find((column) => DESC_KEY.test(column.key));
  const branchCol = columns.find((column) => BRANCH_KEY.test(column.key));
  const warehouseCol = columns.find((column) => WAREHOUSE_KEY.test(column.key));

  return {
    code: codeCol ? normalizeCode(String(row[codeCol.key] ?? "")) : "",
    desc: descCol ? String(row[descCol.key] ?? "").trim() : "",
    branch: branchCol
      ? normalizeBranchOrWarehouse(String(row[branchCol.key] ?? ""))
      : "",
    warehouse: warehouseCol
      ? normalizeBranchOrWarehouse(String(row[warehouseCol.key] ?? ""))
      : "",
  };
}

export function buildDrillDownQuery(
  row: Record<string, unknown>,
  columns: DrillDownColumn[],
): string | null {
  const { code, desc, branch, warehouse } = extractRowContext(row, columns);

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

export function buildTableRowMenuActions(
  row: Record<string, unknown>,
  columns: DrillDownColumn[],
): TableRowMenuAction[] {
  const detailQuery = buildDrillDownQuery(row, columns);
  const { code, desc } = extractRowContext(row, columns);
  const actions: TableRowMenuAction[] = [];

  if (detailQuery) {
    actions.push({
      id: "detail",
      label: "Detalhar item",
      query: detailQuery,
    });
  }

  if (code) {
    const suffix = desc ? ` (${desc})` : "";
    actions.push(
      {
        id: "stock",
        label: "Ver estoque",
        query: `qual o estoque do produto ${code}?`,
      },
      {
        id: "suppliers",
        label: "Ver fornecedores",
        query: `liste os fornecedores do produto ${code}`,
      },
      {
        id: "structure",
        label: "Ver estrutura",
        query: `mostre a estrutura do produto ${code}`,
      },
      {
        id: "parents",
        label: "Onde é usado?",
        query: `onde o produto ${code} é usado?`,
      },
      {
        id: "product",
        label: "Consultar produto",
        query: `me fale do produto ${code}${suffix}`,
      },
    );
  }

  const seen = new Set<string>();

  return actions.filter((action) => {
    if (seen.has(action.query)) {
      return false;
    }

    seen.add(action.query);
    return true;
  });
}

export function buildTreeDrillDownQuery(node: {
  id?: string;
  label?: string;
  subtitle?: string;
}): string | null {
  return buildDrillDownQuery(
    {
      code: node.label || node.id || "",
      description: node.subtitle || "",
    },
    [
      { key: "code", label: "Código" },
      { key: "description", label: "Descrição" },
    ],
  );
}
