export type DepartmentIddFilterInput = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
};

export function resolveSiBranchFilter(branches: string[]): string | undefined {
  if (branches.length === 1) {
    return branches[0];
  }
  return undefined;
}
