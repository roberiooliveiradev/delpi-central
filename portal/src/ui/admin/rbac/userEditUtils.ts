// portal/src/ui/admin/rbac/userEditUtils.ts

export const normalizeIds = (items: unknown[]): string[] => {
  return items
    .map((item) => {
      if (typeof item === "string") return item;

      if (
        item &&
        typeof item === "object" &&
        "id" in item &&
        typeof (item as { id?: unknown }).id === "string"
      ) {
        return (item as { id: string }).id;
      }

      return null;
    })
    .filter((id): id is string => !!id);
};

export function userStatusLabel(active: boolean | undefined): string {
  return active === false ? "Inativo" : "Ativo";
}
