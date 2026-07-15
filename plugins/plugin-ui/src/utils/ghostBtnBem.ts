import { delpiUiClass, withBemModifier } from "./delpiUiClass";

/** Classes dual `{prefix}-ghost-btn` + `.delpi-ui-ghost-btn` (base). */
export function ghostBtnBemClasses(prefix: string): string {
  return delpiUiClass(`${prefix}-ghost-btn`, "delpi-ui-ghost-btn");
}

/** Aplica modificadores (`icon`, `danger`, …) em ambos os tokens BEM. */
export function ghostBtnWithModifiers(
  prefix: string,
  ...modifiers: string[]
): string {
  return modifiers.reduce(
    (classNames, modifier) => withBemModifier(classNames, modifier),
    ghostBtnBemClasses(prefix),
  );
}
