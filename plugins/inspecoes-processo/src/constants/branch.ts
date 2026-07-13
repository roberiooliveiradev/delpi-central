export type BranchCode = "01" | "02";

export const BRANCH_UNIT_LABELS: Record<BranchCode, string> = {
  "01": "Jaraguá do Sul/SC",
  "02": "Rio Bananal/ES",
};

export function branchFromPathname(pathname?: string): BranchCode | null {
  if (!pathname) return null;
  if (pathname.includes("filial-01")) return "01";
  if (pathname.includes("filial-02")) return "02";
  return null;
}

export function branchUnitLabel(branch: string): string {
  if (branch === "01" || branch === "02") {
    return BRANCH_UNIT_LABELS[branch];
  }
  return `Filial ${branch}`;
}

export function branchLabel(branch: string): string {
  if (branch === "01" || branch === "02") {
    return `Filial ${branch} · ${BRANCH_UNIT_LABELS[branch]}`;
  }
  return `Filial ${branch}`;
}
