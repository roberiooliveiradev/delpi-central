/**
 * Catálogo canônico de atalhos do editor TV Dashboard.
 * Fonte única para modal, balões (Alt) e textos de ajuda.
 */

export type KeyboardShortcutGroupId =
  | "edicao"
  | "selecao"
  | "palco"
  | "apresentacao";

export type KeyboardShortcutEntry = {
  id: string;
  group: KeyboardShortcutGroupId;
  /** Rótulo curto da ação. */
  label: string;
  /** Combinação canônica (Windows/Linux): "Ctrl+Z", "Del", "Setas". */
  keys: string;
  /** Descrição opcional para o catálogo. */
  description?: string;
  /** Se true, aparece balão com Alt (toggle) na UI anotada. */
  showAltTip?: boolean;
};

export const KEYBOARD_SHORTCUT_GROUP_LABELS: Record<KeyboardShortcutGroupId, string> = {
  edicao: "Edição",
  selecao: "Seleção e elementos",
  palco: "Palco e visualização",
  apresentacao: "Apresentação",
};

export const TV_KEYBOARD_SHORTCUTS: readonly KeyboardShortcutEntry[] = [
  {
    id: "undo",
    group: "edicao",
    label: "Desfazer",
    keys: "Ctrl+Z",
    showAltTip: true,
  },
  {
    id: "redo",
    group: "edicao",
    label: "Refazer",
    keys: "Ctrl+Y",
    description: "Também Ctrl+Shift+Z",
    showAltTip: true,
  },
  {
    id: "cut",
    group: "edicao",
    label: "Recortar",
    keys: "Ctrl+X",
    showAltTip: true,
  },
  {
    id: "copy",
    group: "edicao",
    label: "Copiar",
    keys: "Ctrl+C",
    showAltTip: true,
  },
  {
    id: "paste",
    group: "edicao",
    label: "Colar",
    keys: "Ctrl+V",
    showAltTip: true,
  },
  {
    id: "duplicate",
    group: "edicao",
    label: "Duplicar elemento",
    keys: "Ctrl+D",
    showAltTip: true,
  },
  {
    id: "delete",
    group: "edicao",
    label: "Remover elemento",
    keys: "Del",
    description: "Também Backspace",
    showAltTip: true,
  },
  {
    id: "multi-select-click",
    group: "selecao",
    label: "Multi-seleção (clique)",
    keys: "Shift+Clique",
    description: "Alterna o bloco na seleção",
    showAltTip: false,
  },
  {
    id: "multi-select-marquee",
    group: "selecao",
    label: "Caixa de seleção",
    keys: "Arraste",
    description: "No fundo vazio; Shift+arraste une à seleção",
    showAltTip: false,
  },
  {
    id: "nudge",
    group: "selecao",
    label: "Mover 1%",
    keys: "Setas",
    description: "Shift+Setas move 10%",
    showAltTip: false,
  },
  {
    id: "escape-part",
    group: "selecao",
    label: "Sair da parte",
    keys: "Esc",
    description: "Limpa seleção de parte de KPI/gráfico/tabela",
    showAltTip: false,
  },
  {
    id: "zoom-wheel",
    group: "palco",
    label: "Zoom no palco",
    keys: "Ctrl+Scroll",
    showAltTip: true,
  },
  {
    id: "pan",
    group: "palco",
    label: "Pan (arrastar palco)",
    keys: "Ctrl",
    description: "Segure Ctrl e arraste; Esc cancela a ferramenta mão",
    showAltTip: true,
  },
  {
    id: "show-tips",
    group: "palco",
    label: "Mostrar atalhos na UI",
    keys: "Alt",
    description:
      "Toque Alt para ligar/desligar balões: F1–F8 nas abas e combinações Ctrl/Del nos controles",
    showAltTip: false,
  },
  {
    id: "keytips",
    group: "palco",
    label: "KeyTips das abas e ribbon",
    keys: "F1…F8",
    description:
      "Com Alt ativo, F1–F8 abrem a aba; em seguida uma letra dispara a ação da ribbon. Esc sai do nível de ação",
    showAltTip: false,
  },
  {
    id: "preview-nav",
    group: "apresentacao",
    label: "Trocar slide (pré-visualização)",
    keys: "← →",
    showAltTip: false,
  },
  {
    id: "preview-pause",
    group: "apresentacao",
    label: "Pausar (pré-visualização)",
    keys: "Espaço",
    showAltTip: false,
  },
] as const;

const BY_ID = new Map(TV_KEYBOARD_SHORTCUTS.map((entry) => [entry.id, entry]));

export function getKeyboardShortcut(id: string): KeyboardShortcutEntry | undefined {
  return BY_ID.get(id);
}

/** Rótulo de teclas adaptado a Mac quando possível. */
export function formatShortcutKeys(keys: string): string {
  if (typeof navigator === "undefined") return keys;
  const isMac = /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent);
  if (!isMac) return keys;
  return keys
    .replace(/Ctrl\+/g, "⌘")
    .replace(/\bCtrl\b/g, "⌘")
    .replace(/Alt\+/g, "⌥")
    .replace(/\bAlt\b/g, "⌥")
    .replace(/Shift\+/g, "⇧")
    .replace(/\bShift\b/g, "⇧");
}

/** Texto de ajuda: descrição + atalho entre parênteses. */
export function shortcutHelpSuffix(id: string): string {
  const entry = getKeyboardShortcut(id);
  if (!entry) return "";
  return ` (${formatShortcutKeys(entry.keys)})`;
}

export function listKeyboardShortcutsByGroup(): Array<{
  group: KeyboardShortcutGroupId;
  label: string;
  entries: KeyboardShortcutEntry[];
}> {
  const order: KeyboardShortcutGroupId[] = ["edicao", "selecao", "palco", "apresentacao"];
  return order.map((group) => ({
    group,
    label: KEYBOARD_SHORTCUT_GROUP_LABELS[group],
    entries: TV_KEYBOARD_SHORTCUTS.filter((entry) => entry.group === group),
  }));
}
