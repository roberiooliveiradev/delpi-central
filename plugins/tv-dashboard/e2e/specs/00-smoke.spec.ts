import { expect, test } from "@playwright/test";
import { loginAs, openEditor, readBack, FIXTURE } from "../helpers";

test("smoke: login real + editor carrega palco com blocos da fixture", async ({
  page,
}) => {
  await loginAs(page, "editor");
  await openEditor(page);

  await expect(page.locator('[data-block-id="e2e_txt1"]')).toBeVisible();
  await expect(page.locator('[data-block-id="e2e_txt3"]')).toBeVisible();

  const pl = await readBack("editor");
  const slide = pl.slides.find((s) => s.id === FIXTURE.slideA);
  expect(slide?.nativeConfig?.blocks?.length).toBeGreaterThanOrEqual(6);
});
