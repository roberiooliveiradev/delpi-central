/**
 * Re-export do posicionamento canônico em `@delpi/plugin-ui`.
 * Preferir importar de `@delpi/plugin-ui/index` em código novo.
 */
export {
  resolveKeyTipPosition as resolveShortcutTipPosition,
  type KeyTipPlacement as ShortcutTipPlacement,
  type KeyTipPosition as ShortcutTipPosition,
  type KeyTipPositionInput as ShortcutTipPositionInput,
} from "@delpi/plugin-ui/index";
