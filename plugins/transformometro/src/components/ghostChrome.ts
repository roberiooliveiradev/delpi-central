import { ghostBtnBemClasses, ghostBtnWithModifiers } from "@delpi/plugin-ui/index";

/** Ghost button dual-class canônico do Transformômetro. */
export const DS_GHOST_BTN = ghostBtnBemClasses("ds");

export function dsGhostBtn(...modifiers: Array<"icon" | "danger" | "active">): string {
  return modifiers.length > 0 ? ghostBtnWithModifiers("ds", ...modifiers) : DS_GHOST_BTN;
}
