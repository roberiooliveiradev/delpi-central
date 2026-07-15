import { ghostBtnBemClasses, ghostBtnWithModifiers } from "@delpi/plugin-ui/index";

/** Ghost button dual-class canônico do PAC. */
export const PAC_GHOST_BTN = ghostBtnBemClasses("pac");

export function pacGhostBtn(...modifiers: Array<"icon" | "danger">): string {
  return modifiers.length > 0 ? ghostBtnWithModifiers("pac", ...modifiers) : PAC_GHOST_BTN;
}
