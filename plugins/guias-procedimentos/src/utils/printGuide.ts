import { printScopedWindow } from "@delpi/plugin-ui/index";

export function printGuide(): boolean {
  if (typeof window === "undefined") return false;
  return printScopedWindow({ deferFrames: true });
}
