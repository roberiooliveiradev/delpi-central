export type BranchOption = {
  id: string;
  label: string;
};

export const PRODUCTION_PULSE_BRANCHES: BranchOption[] = [
  { id: "01", label: "SC" },
  { id: "02", label: "ES" },
];

export function branchLabel(branchId: string): string {
  return PRODUCTION_PULSE_BRANCHES.find((item) => item.id === branchId)?.label ?? branchId;
}

export function resolveBranchOptions(allowedBranches: string[]): BranchOption[] {
  if (allowedBranches.length === 0) {
    return PRODUCTION_PULSE_BRANCHES;
  }
  return PRODUCTION_PULSE_BRANCHES.filter((item) => allowedBranches.includes(item.id));
}
