/**
 * Impressão isolada da folha A4.
 * O documento resultante entra no iframe canônico de `printDelpiDocumentHtml`.
 * Não inclui o host do Portal nem a toolbar do editor.
 */

const PRINT_PAGE_RESET = `
html,body{margin:0;padding:0;background:#fff;color:#25465f}
@media print{
 @page{size:A4 portrait;margin:0}
 html,body{width:210mm;height:297mm;margin:0;padding:0;background:#fff}
}`;

export function readMetallographicStylesheet(): string {
  const parts: string[] = [];
  for (const sheet of Array.from(document.styleSheets)) {
    let rules: CSSRuleList;
    try {
      rules = sheet.cssRules;
    } catch {
      continue;
    }
    const css = Array.from(rules)
      .map((rule) => rule.cssText)
      .join("\n");
    if (css.includes(".dashboard-metalography") || css.includes("DelpiSans")) parts.push(css);
  }
  return parts.join("\n");
}

export function metallographicPrintStylesheet(
  cssText: string,
  font400Url: string,
  font700Url: string,
): string {
  return cssText
    .replaceAll('url("../assets/delpi-sans-400.otf")', `url("${font400Url}")`)
    .replaceAll('url("../assets/delpi-sans-700.otf")', `url("${font700Url}")`);
}

export function serializeMetallographicSheet(sheet: HTMLElement): string {
  const clone = sheet.cloneNode(true) as HTMLElement;
  copyControlState(sheet, clone);
  copyImageState(sheet, clone);
  clone.querySelectorAll(".upload-row, .screen-only, .crop-modal, .app-toast").forEach((node) => {
    node.remove();
  });
  return clone.outerHTML;
}

export function buildMetallographicPrintHtml(sheetHtml: string, stylesheet: string): string {
  return `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8" /><title>Análise metalográfica</title><style>${stylesheet}</style><style>${PRINT_PAGE_RESET}</style></head><body class="dashboard-metalography editor-active">${sheetHtml}</body></html>`;
}

export function printIsolatedMetallographicSheet(
  sheet: HTMLElement,
  stylesheet: string,
  printHtml: (html: string, title: string) => boolean,
): boolean {
  return printHtml(
    buildMetallographicPrintHtml(serializeMetallographicSheet(sheet), stylesheet),
    "Análise metalográfica",
  );
}

function copyControlState(source: ParentNode, clone: ParentNode): void {
  const sources = source.querySelectorAll("input, textarea");
  const targets = clone.querySelectorAll("input, textarea");
  sources.forEach((node, index) => {
    const target = targets[index];
    if (!isField(node) || !isField(target)) return;
    if (node instanceof HTMLInputElement && target instanceof HTMLInputElement && isCheckable(node)) {
      target.checked = node.checked;
      if (node.checked) target.setAttribute("checked", "");
      else target.removeAttribute("checked");
      return;
    }
    target.value = node.value;
    if (target instanceof HTMLTextAreaElement) target.textContent = node.value;
    else target.setAttribute("value", node.value);
  });
}

function copyImageState(source: ParentNode, clone: ParentNode): void {
  const sources = source.querySelectorAll("img");
  const targets = clone.querySelectorAll("img");
  sources.forEach((image, index) => {
    const target = targets[index];
    if (!(target instanceof HTMLImageElement)) return;
    const printSrc = image.dataset.printSrc;
    const src = image.dataset.brandLogo === "delpi" && printSrc
      ? printSrc
      : image.getAttribute("src") || image.currentSrc;
    if (src) target.setAttribute("src", src);
    const style = image.getAttribute("style");
    if (style) target.setAttribute("style", style);
  });
}

function isField(node: Element | undefined): node is HTMLInputElement | HTMLTextAreaElement {
  return node instanceof HTMLInputElement || node instanceof HTMLTextAreaElement;
}

function isCheckable(input: HTMLInputElement): boolean {
  return input.type === "checkbox" || input.type === "radio";
}
