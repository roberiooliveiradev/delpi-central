import type { ActionResponsible, PlanAction } from "../types/actionPlan";

export function splitLegacyResponsibleNames(name?: string | null): string[] {
  const raw = name?.trim() ?? "";
  if (!raw) return [];
  if (raw.includes("/")) {
    return raw
      .split(/\s*\/\s*/)
      .map((part) => part.trim())
      .filter(Boolean);
  }
  return [raw];
}

export function responsiblesFromAction(action: PlanAction): ActionResponsible[] {
  if (action.responsibles?.length) {
    return action.responsibles.map((item) => ({
      id: item.id,
      user_id: item.user_id ?? null,
      display_name: item.display_name.trim(),
      sort_order: item.sort_order,
    }));
  }
  const names = splitLegacyResponsibleNames(action.responsible_name);
  if (!names.length) return [];
  return names.map((display_name, index) => ({
    display_name,
    user_id: index === 0 ? action.responsible_user_id ?? null : null,
  }));
}

export function formatActionResponsiblesDisplay(action: PlanAction): string {
  const names = responsiblesFromAction(action).map((item) => item.display_name);
  return names.length ? names.join(" / ") : "—";
}

export function hasLinkedQueueResponsibles(action: PlanAction): boolean {
  return responsiblesFromAction(action).some((item) => Boolean(item.user_id?.trim()));
}

export function responsiblesToPayload(responsibles: ActionResponsible[]): Array<{
  user_id?: string | null;
  display_name: string;
}> {
  const seenUsers = new Set<string>();
  const seenNames = new Set<string>();
  const payload: Array<{ user_id?: string | null; display_name: string }> = [];
  for (const item of responsibles) {
    const display_name = item.display_name.trim();
    if (!display_name) continue;
    const userId = item.user_id?.trim() || null;
    if (userId) {
      if (seenUsers.has(userId)) continue;
      seenUsers.add(userId);
    } else {
      const key = display_name.toLocaleLowerCase("pt-BR");
      if (seenNames.has(key)) continue;
      seenNames.add(key);
    }
    payload.push({ user_id: userId, display_name });
  }
  return payload;
}

export function legacyResponsibleFromResponsibles(responsibles: ActionResponsible[]): {
  responsible_name?: string;
  responsible_user_id?: string | null;
} {
  const payload = responsiblesToPayload(responsibles);
  if (!payload.length) {
    return { responsible_name: undefined, responsible_user_id: null };
  }
  return {
    responsible_name: payload.map((item) => item.display_name).join(" / "),
    responsible_user_id: payload.find((item) => item.user_id)?.user_id ?? null,
  };
}
