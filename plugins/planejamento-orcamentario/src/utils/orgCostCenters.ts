/** Identidade visual e chaves de centro de custo cientes de filial. */

export const BUDGET_BRANCHES = [
  { code: "01", label: "Jaraguá do Sul/SC" },
  { code: "02", label: "Rio Bananal/ES" },
] as const;

export type BudgetBranchCode = (typeof BUDGET_BRANCHES)[number]["code"];

export type CostCenterIdentity = {
  branch?: string | null;
  unit_id?: string | null;
  unit_code?: string | null;
  code?: string | null;
  cost_center_id?: string | null;
  name?: string | null;
  description?: string | null;
  id?: string | null;
};

export function normalizeBranchCode(raw?: string | null): BudgetBranchCode | "" {
  const value = String(raw ?? "").trim();
  if (value === "01" || value === "02") return value;
  return "";
}

export function branchLabel(branch?: string | null): string {
  const code = normalizeBranchCode(branch);
  if (!code) return String(branch ?? "").trim() || "—";
  const found = BUDGET_BRANCHES.find((b) => b.code === code);
  return found ? `Filial ${code} (${found.label})` : `Filial ${code}`;
}

/** Chave estável para React keys / selects: prioriza UUID interno, senão branch+code. */
export function costCenterKey(cc: CostCenterIdentity): string {
  const id = String(cc.id ?? "").trim();
  if (id) return `id:${id}`;
  const branch =
    normalizeBranchCode(cc.branch) ||
    normalizeBranchCode(cc.unit_id) ||
    normalizeBranchCode(cc.unit_code);
  const code = String(cc.code ?? cc.cost_center_id ?? "").trim();
  if (branch && code) return `${branch}:${code}`;
  return code || "unknown";
}

export function costCenterBranch(cc: CostCenterIdentity): string {
  return (
    normalizeBranchCode(cc.branch) ||
    normalizeBranchCode(cc.unit_id) ||
    normalizeBranchCode(cc.unit_code) ||
    ""
  );
}

export function costCenterCode(cc: CostCenterIdentity): string {
  return String(cc.code ?? cc.cost_center_id ?? "").trim();
}

export function costCenterDescription(cc: CostCenterIdentity): string {
  return String(cc.description ?? cc.name ?? "").trim();
}

/** Ex.: "Filial 01 · 1234 — Produção" */
export function formatCostCenterLabel(cc: CostCenterIdentity): string {
  const branch = costCenterBranch(cc);
  const code = costCenterCode(cc);
  const desc = costCenterDescription(cc);
  const head = branch ? `Filial ${branch}` : "Filial —";
  if (!code && !desc) return head;
  if (!desc) return `${head} · ${code}`;
  if (!code) return `${head} · ${desc}`;
  return `${head} · ${code} — ${desc}`;
}

export function matchesCostCenterSearch(
  cc: CostCenterIdentity,
  query: string,
): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const hay = [
    costCenterCode(cc),
    costCenterDescription(cc),
    costCenterBranch(cc),
  ]
    .join(" ")
    .toLowerCase();
  return hay.includes(q);
}

export function isSameCostCenter(
  a: CostCenterIdentity,
  b: CostCenterIdentity,
): boolean {
  const aId = String(a.id ?? "").trim();
  const bId = String(b.id ?? "").trim();
  if (aId && bId) return aId === bId;
  const aBranch = costCenterBranch(a);
  const bBranch = costCenterBranch(b);
  const aCode = costCenterCode(a);
  const bCode = costCenterCode(b);
  return Boolean(aBranch && bBranch && aCode && bCode && aBranch === bBranch && aCode === bCode);
}
