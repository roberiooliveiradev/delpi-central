export type BranchCode = "01" | "02";

export function branchFromPathname(pathname?: string): BranchCode | null {
  if (!pathname) return null;
  if (pathname.includes("filial-01")) return "01";
  if (pathname.includes("filial-02")) return "02";
  return null;
}

export function branchLabel(branch: string): string {
  if (branch === "01") return "Filial 01";
  if (branch === "02") return "Filial 02";
  return `Filial ${branch}`;
}
