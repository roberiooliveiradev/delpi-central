import { ghostBtnBemClasses, ghostBtnWithModifiers } from "@delpi/plugin-ui/index";

/** Ghost button dual-class canônico do Kaizen. */
export const KZ_GHOST_BTN = ghostBtnBemClasses("kz");

export function kzGhostBtn(...modifiers: Array<"icon" | "danger" | "active">): string {
  return modifiers.length > 0 ? ghostBtnWithModifiers("kz", ...modifiers) : KZ_GHOST_BTN;
}
