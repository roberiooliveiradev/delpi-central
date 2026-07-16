export type RichTextAlign = "left" | "center" | "right" | "justify";

function focusEditor(editor: HTMLElement | null) {
  editor?.focus();
}

export function execRichTextCommand(command: string, value?: string) {
  try {
    document.execCommand(command, false, value);
  } catch {
    /* execCommand pode falhar em contextos sem seleção */
  }
}

export function runRichTextCommand(
  editor: HTMLElement | null,
  command: string,
  value?: string,
) {
  focusEditor(editor);
  execRichTextCommand(command, value);
}

export function applyRichTextFontFamily(editor: HTMLElement | null, fontFamily: string) {
  focusEditor(editor);
  execRichTextCommand("fontName", fontFamily);
}

export function applyRichTextFontSize(editor: HTMLElement | null, fontSizePx: number) {
  focusEditor(editor);
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    execRichTextCommand("fontSize", "3");
    return;
  }
  const range = selection.getRangeAt(0);
  if (range.collapsed) {
    execRichTextCommand("fontSize", "3");
    return;
  }
  const span = document.createElement("span");
  span.style.fontSize = `${fontSizePx}px`;
  try {
    range.surroundContents(span);
  } catch {
    span.appendChild(range.extractContents());
    range.insertNode(span);
  }
  selection.removeAllRanges();
  const next = document.createRange();
  next.selectNodeContents(span);
  next.collapse(false);
  selection.addRange(next);
}

export function applyRichTextAlign(editor: HTMLElement | null, align: RichTextAlign) {
  const map: Record<RichTextAlign, string> = {
    left: "justifyLeft",
    center: "justifyCenter",
    right: "justifyRight",
    justify: "justifyFull",
  };
  runRichTextCommand(editor, map[align]);
}

export function insertRichTextLink(editor: HTMLElement | null, url: string) {
  runRichTextCommand(editor, "createLink", url);
}

export function queryRichTextCommandState(command: string): boolean {
  try {
    return document.queryCommandState(command);
  } catch {
    return false;
  }
}

export function queryRichTextAlign(): RichTextAlign | null {
  if (queryRichTextCommandState("justifyCenter")) return "center";
  if (queryRichTextCommandState("justifyRight")) return "right";
  if (queryRichTextCommandState("justifyFull")) return "justify";
  if (queryRichTextCommandState("justifyLeft")) return "left";
  return null;
}
