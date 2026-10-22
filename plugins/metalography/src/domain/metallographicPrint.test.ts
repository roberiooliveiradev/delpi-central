/** @vitest-environment jsdom */
import { describe, expect, it } from "vitest";

import {
  buildMetallographicPrintHtml,
  metallographicPrintStylesheet,
  printIsolatedMetallographicSheet,
  readMetallographicStylesheet,
  serializeMetallographicSheet,
} from "./metallographicPrint";

const FONT_400 = "/apps/metalography/assets/delpi-sans-400.otf";
const FONT_700 = "/apps/metalography/assets/delpi-sans-700.otf";
const SHEET_CSS = `.dashboard-metalography{--navy:#0b3a5d}
@font-face{font-family:DelpiSans;src:url("../assets/delpi-sans-400.otf")}
@font-face{font-family:DelpiSans;src:url("../assets/delpi-sans-700.otf")}
@media print{.dashboard-metalography,.dashboard-metalography *{print-color-adjust:exact!important}}`;

function hostWithSheet(): { host: HTMLElement; sheet: HTMLElement } {
  const host = document.createElement("div");
  host.innerHTML = `
    <aside id="portal-sidebar">PORTAL-SIDEBAR Minha DELPI</aside>
    <div class="toolbar"><button type="button">Exportar PDF</button><button type="button">Imprimir</button></div>
    <main class="sheet">
      <input id="lot" class="entry" type="text" value="" />
      <textarea id="observations"></textarea>
      <label class="choice"><input type="radio" name="result" value="conforme" /><span>Conforme</span></label>
      <img class="preview" alt="Micrografia original" />
      <div class="upload-row"><button type="button">Selecionar imagem</button></div>
      <img alt="Esquema" src="/apps/metalography/assets/measurement-scheme.png" />
      <img data-brand-logo="delpi" data-print-src="/apps/metalography/assets/delpi-logo.png" src="/apps/metalography/assets/delpi-logo-on-dark.png" alt="Delpi — conexões elétricas" />
    </main>
  `;
  document.body.appendChild(host);
  const sheet = host.querySelector("main.sheet");
  if (!(sheet instanceof HTMLElement)) throw new Error("sheet missing");
  return { host, sheet };
}

describe("metallographic print isolation", () => {
  it("serializa a folha atual, inclusive valor ainda não gravado no atributo", () => {
    const { sheet } = hostWithSheet();
    const lot = sheet.querySelector("#lot");
    const notes = sheet.querySelector("#observations");
    const result = sheet.querySelector('input[value="conforme"]');
    const photo = sheet.querySelector("img.preview");
    if (!(lot instanceof HTMLInputElement) || !(notes instanceof HTMLTextAreaElement)) {
      throw new Error("fields missing");
    }
    if (!(result instanceof HTMLInputElement) || !(photo instanceof HTMLImageElement)) {
      throw new Error("controls missing");
    }
    lot.value = "LOTE-NAO-SALVO-77";
    notes.value = "observação ainda não salva";
    result.checked = true;
    photo.src = "blob:https://minhadelpi.com.br/micrografia";
    photo.setAttribute("style", "display:block");

    const html = serializeMetallographicSheet(sheet);

    expect(html).toContain("LOTE-NAO-SALVO-77");
    expect(html).toContain("observação ainda não salva");
    expect(html).toContain("checked");
    expect(html).toContain("blob:https://minhadelpi.com.br/micrografia");
    expect(html).toContain("measurement-scheme.png");
    expect(html).toContain('src="/apps/metalography/assets/delpi-logo.png"');
    expect(html).not.toContain("delpi-logo-on-dark.png");
    expect(html).not.toContain("PORTAL-SIDEBAR");
    expect(html).not.toContain("Exportar PDF");
    expect(html).not.toContain("Selecionar imagem");
    expect(html).not.toContain("upload-row");
  });

  it("mantém as orientações no HTML da folha e a impressão as oculta por CSS", () => {
    const { sheet } = hostWithSheet();
    sheet.insertAdjacentHTML(
      "beforeend",
      `<div class="sec-heading"><span class="sec-number">01</span><h2>Identificação da amostra</h2><p class="sub">Preencha os dados do terminal, cabo e processo avaliados.</p></div>`,
    );
    const html = buildMetallographicPrintHtml(
      serializeMetallographicSheet(sheet),
      `.dashboard-metalography .sec-heading .sub{font-size:7.2pt}@media print{.dashboard-metalography .sec-heading .sub{display:none!important}}`,
    );
    expect(html).toContain("Preencha os dados do terminal, cabo e processo avaliados.");
    expect(html).toContain("Identificação da amostra");
    expect(html).toContain(".sec-heading .sub{display:none!important}");
  });

  it("não copia um controle que está fora da folha", () => {
    const { host, sheet } = hostWithSheet();
    const outside = document.createElement("input");
    outside.value = "FILTRO-DA-LISTA";
    host.appendChild(outside);

    expect(serializeMetallographicSheet(sheet)).not.toContain("FILTRO-DA-LISTA");
  });

  it("lê o CSS aplicado da folha e ignora o estilo do host", () => {
    const hostStyle = document.createElement("style");
    hostStyle.textContent = "#portal-sidebar{background:#0b1f33}";
    const sheetStyle = document.createElement("style");
    sheetStyle.textContent = SHEET_CSS;
    document.head.append(hostStyle, sheetStyle);

    const css = readMetallographicStylesheet();
    expect(css).toContain(".dashboard-metalography");
    expect(css).toContain("DelpiSans");
    expect(css).not.toContain("portal-sidebar");
  });

  it("monta um documento A4 sem chrome do host e com a fonte resolvida", () => {
    const stylesheet = metallographicPrintStylesheet(SHEET_CSS, FONT_400, FONT_700);
    const html = buildMetallographicPrintHtml("<main class=\"sheet\">FOLHA-A4</main>", stylesheet);

    expect(html).toContain("@page{size:A4 portrait;margin:0}");
    expect(html).toContain("print-color-adjust:exact");
    expect(html).toContain("--navy:#0b3a5d");
    expect(html).toContain("FOLHA-A4");
    expect(html).toContain(FONT_400);
    expect(html).toContain(FONT_700);
    expect(html).not.toContain("../assets/delpi-sans-400.otf");
    expect(html).not.toContain("portal-sidebar");
    expect(stylesheet).not.toContain('url("../assets/delpi-sans-700.otf")');
  });

  it("entrega ao impressor só o documento isolado", () => {
    const { sheet } = hostWithSheet();
    const calls: string[] = [];
    const printed = printIsolatedMetallographicSheet(sheet, "/*sheet*/", (html, title) => {
      calls.push(`${title}:${html}`);
      return true;
    });

    expect(printed).toBe(true);
    expect(calls).toHaveLength(1);
    expect(calls[0]).toContain("Análise metalográfica");
    expect(calls[0]).toContain("@page{size:A4 portrait;margin:0}");
    expect(calls[0]).not.toContain("PORTAL-SIDEBAR");
    expect(calls[0]).not.toContain("Exportar PDF");
  });
});
