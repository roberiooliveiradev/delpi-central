import { expect, test, type Page } from "@playwright/test";
import {
  FIXTURE,
  loginAs,
  openEditor,
  readBack,
  resetSlideA,
  selectSlide,
} from "../helpers";

type Frame = { x: number; y: number; w: number; h: number };

/** Extrai frame percentual de um style inline (`left: 40%; top: 33%; ...`). */
function parseFrame(style: string): Frame | null {
  const num = (k: string) => {
    const m = new RegExp(k + ":\\s*([\\d.]+)%").exec(style);
    return m ? Number(m[1]) : NaN;
  };
  const f = { x: num("left"), y: num("top"), w: num("width"), h: num("height") };
  return Object.values(f).every((v) => Number.isFinite(v)) ? f : null;
}

async function stageFrames(page: Page, selector: string): Promise<Frame[]> {
  const styles = await page.locator(selector).evaluateAll((els) =>
    els.map((el) => (el as HTMLElement).getAttribute("style") ?? ""),
  );
  return styles.map(parseFrame).filter((f): f is Frame => f !== null);
}

function assertFramesCover(expected: Frame[], actual: Frame[], label: string) {
  for (const e of expected) {
    const hit = actual.some(
      (a) =>
        Math.abs(a.x - e.x) < 0.6 &&
        Math.abs(a.y - e.y) < 0.6 &&
        Math.abs(a.w - e.w) < 0.6 &&
        Math.abs(a.h - e.h) < 0.6,
    );
    expect(
      hit,
      `${label}: frame ${JSON.stringify(e)} não encontrado`,
    ).toBe(true);
  }
}

test.describe("Scenario 8 — paridade editor / preview / TV", () => {
  test("geometria confirmada é idêntica nas três superfícies", async ({
    page,
    context,
  }) => {
    test.setTimeout(120_000);
    await resetSlideA("editor");
    await loginAs(page, "editor");

    // Read-back autoritativo → frames esperados do slide A.
    const back = await readBack("editor");
    const slide = back.slides.find((s) => s.id === FIXTURE.slideA);
    const blocks = (slide?.nativeConfig?.blocks ?? []) as Array<{
      id: string;
      frame?: Frame;
      style?: { zIndex?: number };
    }>;
    // Linhas/conectores renderizam via endpoints SVG, não wrap percentual —
    // excluir frames finos (<1%) da comparação de wraps.
    const expected = blocks
      .filter((b) => b.frame && b.frame.w > 0 && b.frame.h >= 1)
      .map((b) => b.frame!);
    expect(expected.length).toBeGreaterThanOrEqual(3);

    // 1) Editor: wraps com data-block-id carregam frame percentual inline.
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);
    const editorFrames = await stageFrames(
      page,
      '.td-composer__block-wrap[data-block-id]',
    );
    assertFramesCover(expected, editorFrames, "editor");

    // 2) Preview administrativo (mesma playlist, renderização presentation).
    await page.goto(
      `/apps/tv-dashboard/playlists/${FIXTURE.playlistId}/preview`,
      { waitUntil: "domcontentloaded" },
    );
    await page.locator(".tdp-comunicado__block").first().waitFor({ timeout: 30_000 });
    const previewFrames = await stageFrames(page, ".tdp-comunicado__block");
    assertFramesCover(expected, previewFrames, "preview");

    // 3) TV pública (public-hub kiosk, sem autenticação).
    const publicToken = (back as { publicToken?: string }).publicToken;
    expect(publicToken, "playlist precisa de publicToken").toBeTruthy();
    const tvPage = await context.newPage();
    await tvPage.goto(`/p/tv-dashboard/present/${publicToken}`, {
      waitUntil: "domcontentloaded",
    });
    await tvPage
      .locator(".tdp-comunicado__block")
      .first()
      .waitFor({ timeout: 30_000 });
    const tvFrames = await stageFrames(tvPage, ".tdp-comunicado__block");
    assertFramesCover(expected, tvFrames, "tv");

    // eslint-disable-next-line no-console
    console.log(
      JSON.stringify({
        expectedCount: expected.length,
        editorCount: editorFrames.length,
        previewCount: previewFrames.length,
        tvCount: tvFrames.length,
      }),
    );
  });
});
