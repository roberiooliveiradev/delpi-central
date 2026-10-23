import {
  expect,
  request,
  type Browser,
  type Page,
  type Response,
} from "@playwright/test";

/**
 * Actor matrix (026): identidades provisionadas no Keycloak/RBAC local.
 * Login é o fluxo real: portal → Keycloak authorize → form → redirect.
 * Nenhum mock de boundary. Credenciais locais via env — nunca hardcoded
 * em arquivo versionado (local-only, não-produção).
 */

export type Actor = "editor" | "manager" | "viewer";

const USERNAMES: Record<Actor, string> = {
  editor: process.env.TV_E2E_USER_EDITOR ?? "e2e-editor",
  manager: process.env.TV_E2E_USER_MANAGER ?? "e2e-manager",
  viewer: process.env.TV_E2E_USER_VIEWER ?? "e2e-viewer",
};

function credentials(actor: Actor): { user: string; pass: string } {
  const pass = process.env[`TV_E2E_PASS_${actor.toUpperCase()}`];
  if (!pass) {
    throw new Error(
      `Missing TV_E2E_PASS_${actor.toUpperCase()} — provisione as credenciais locais.`,
    );
  }
  return { user: USERNAMES[actor], pass };
}

export const FIXTURE = {
  playlistId: process.env.TV_E2E_PLAYLIST ?? "",
  slideA: process.env.TV_E2E_SLIDE_A ?? "",
  slideB: process.env.TV_E2E_SLIDE_B ?? "",
};

export const PLAYLIST_URL = `/apps/tv-dashboard/playlists/${FIXTURE.playlistId}`;

/** Login real: portal /login → "Entrar com DELPI SSO" → form Keycloak. */
export async function loginAs(page: Page, actor: Actor): Promise<void> {
  const creds = credentials(actor);
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const ssoBtn = page.getByRole("button", {
    name: /Entrar com DELPI SSO/i,
  });
  // Pode redirecionar para /login assíncrono — espera o botão SSO aparecer.
  await ssoBtn.waitFor({ state: "visible", timeout: 45_000 });
  await ssoBtn.click();
  // Keycloak pode estar reiniciando (502 do gateway) — um retry de reload.
  await page.waitForTimeout(1500);
  if (await page.locator("text=502 Bad Gateway").isVisible().catch(() => false)) {
    await page.waitForTimeout(3000);
    await page.reload({ waitUntil: "domcontentloaded" });
  }
  const userField = page
    .getByRole("textbox", { name: /usuário|username|email/i })
    .first();
  const formShown = await userField
    .waitFor({ state: "visible", timeout: 10_000 })
    .then(() => true)
    .catch(() => false);
  if (formShown) {
    await userField.fill(creds.user);
    await page
      .getByRole("textbox", { name: /senha|password/i })
      .first()
      .fill(creds.pass);
    await page.getByRole("button", { name: /entrar|sign in|log in/i }).click();
  }
  await page.waitForURL(
    (url) => !url.pathname.startsWith("/auth/") && !url.pathname.endsWith("/login"),
    { timeout: 60_000 },
  );
  await page.waitForLoadState("domcontentloaded");
}

export async function newLoggedInPage(browser: Browser, actor: Actor): Promise<Page> {
  const ctx = await browser.newContext({ baseURL: process.env.TV_E2E_BASE_URL ?? "http://localhost" });
  const page = await ctx.newPage();
  await loginAs(page, actor);
  return page;
}

/** Token via password grant — somente para setup/read-back autoritativo. */
export async function apiToken(actor: Actor): Promise<string> {
  const creds = credentials(actor);
  const ctx = await request.newContext({
    baseURL: process.env.TV_E2E_BASE_URL ?? "http://localhost",
  });
  const res = await ctx.post(
    "/auth/realms/delpi/protocol/openid-connect/token",
    {
      form: {
        client_id: "delpi-central",
        grant_type: "password",
        username: creds.user,
        password: creds.pass,
      },
    },
  );
  if (!res.ok()) throw new Error(`token ${actor}: HTTP ${res.status()}`);
  const body = (await res.json()) as { access_token: string };
  await ctx.dispose();
  return body.access_token;
}

export type PlaylistReadBack = {
  revision: number;
  slides: Array<{
    id: string;
    title?: string;
    nativeConfig?: { blocks?: Array<Record<string, unknown>> };
  }>;
};

/** Read-back autoritativo da playlist inteira (rev + slides + blocks). */
export async function readBack(actor: Actor): Promise<PlaylistReadBack> {
  const tok = await apiToken(actor);
  const ctx = await request.newContext({
    baseURL: process.env.TV_E2E_BASE_URL ?? "http://localhost",
  });
  const res = await ctx.get(
    `/apps/tv-dashboard-api/playlists/${FIXTURE.playlistId}`,
    { headers: { Authorization: `Bearer ${tok}` } },
  );
  const body = (await res.json()) as { data: PlaylistReadBack };
  await ctx.dispose();
  return body.data;
}

export async function slideBlocks(actor: Actor, slideId: string) {
  const pl = await readBack(actor);
  const slide = pl.slides.find((s) => s.id === slideId);
  return slide?.nativeConfig?.blocks ?? [];
}

export async function blockFrameFromApi(
  actor: Actor,
  slideId: string,
  blockId: string,
): Promise<{ x: number; y: number; w: number; h: number } | null> {
  const blocks = await slideBlocks(actor, slideId);
  const b = blocks.find((item) => item.id === blockId) as
    | { frame?: { x: number; y: number; w: number; h: number } }
    | undefined;
  return b?.frame ?? null;
}


/** Reprojeção determinística da fixture — espalha os 3 textos para evitar overlap entre testes. */
export async function resetSlideA(actor: Actor = "editor"): Promise<void> {
  const tok = await apiToken(actor);
  const ctx = await request.newContext({
    baseURL: process.env.TV_E2E_BASE_URL ?? "http://localhost",
  });
  const frames: Record<string, { x: number; y: number }> = {
    e2e_txt1: { x: 8, y: 10 },
    e2e_txt2: { x: 40, y: 33 },
    e2e_txt3: { x: 70, y: 70 },
  };
  /* z-order hermético: comandos de camada (Trazer para a frente, Avançar…)
   * acumulam entre runs; sem baseline fixa, "bring-to-front" em e2e_txt3 vira
   * no-op quando a fixture já está no topo e o cenário perde a projeção. */
  const zIndexes: Record<string, number> = {
    e2e_shape: 1,
    e2e_txt1: 2,
    e2e_txt2: 3,
    e2e_txt3: 4,
    e2e_line: 5,
    e2e_icon: 6,
    e2e_group: 7,
  };
  const blocks = await slideBlocks(actor, FIXTURE.slideA);
  const ops = (blocks as Array<Record<string, unknown>>)
    .filter(
      (b) =>
        typeof b.id === "string" &&
        (frames[b.id as string] || zIndexes[b.id as string] != null),
    )
    .map((b) => {
      const id = b.id as string;
      const pos = frames[id];
      const z = zIndexes[id];
      const f = (b.frame ?? {}) as Record<string, number>;
      const style = (b.style ?? {}) as Record<string, unknown>;
      return {
        op: "upsert_block",
        block: {
          ...b,
          frame: pos ? { ...f, x: pos.x, y: pos.y } : f,
          style: z != null ? { ...style, zIndex: z } : style,
        },
      };
    });
  const res = await ctx.post(
    "/apps/tv-dashboard-api/playlists/" + FIXTURE.playlistId + "/slides/" + FIXTURE.slideA + "/presentation-mutations",
    { headers: { Authorization: "Bearer " + tok }, data: { ops } },
  );
  await ctx.dispose();
  if (!res.ok()) throw new Error("resetSlideA: HTTP " + res.status());
}

/** Abre o editor na playlist fixture e espera o palco montar. */
export async function openEditor(page: Page): Promise<void> {
  await page.goto(PLAYLIST_URL, { waitUntil: "domcontentloaded" });
  await page.locator("[data-block-id]").first().waitFor({ timeout: 30_000 });
}

/** Navega para um slide via filmstrip (`data-reorder-id`). */
export async function selectSlide(page: Page, slideId: string): Promise<void> {
  await page.locator(`[data-reorder-id="${slideId}"]`).first().click();
  await page.locator("[data-block-id]").first().waitFor({ timeout: 15_000 });
}

const blockSel = (id: string) => `.td-composer__block-wrap[data-block-id="${id}"]`;

export async function clickBlock(page: Page, blockId: string): Promise<void> {
  await page.locator(blockSel(blockId)).first().click();
}

export async function selectBlocks(page: Page, ids: string[]): Promise<void> {
  await page.locator(blockSel(ids[0]!)).first().click();
  for (const id of ids.slice(1)) {
    await page
      .locator(blockSel(id))
      .first()
      .click({ modifiers: ["Control"] });
  }
}

/**
 * Menu de contexto do palco: botão direito no bloco → itens por label.
 * `path` = rótulos em sequência (ex.: ["Alinhar", "Alinhar à esquerda"]).
 */
export async function runContextCommand(
  page: Page,
  path: string[],
): Promise<void> {
  for (const label of path) {
    await page
      .getByRole("menuitem", { name: new RegExp(`^${label}$`, "i") })
      .first()
      .click();
  }
}

export async function openBlockMenuAndRun(
  page: Page,
  blockId: string,
  path: string[],
): Promise<void> {
  await page.locator(blockSel(blockId)).first().click({ button: "right" });
  await runContextCommand(page, path);
}

export type FrameSnapshot = { x: number; y: number; w: number; h: number };

/** Estilo inline do wrap do bloco — projeção altera o atributo em frame. */
export async function blockStyle(page: Page, blockId: string): Promise<string> {
  const el = page.locator(blockSel(blockId)).first();
  return (await el.getAttribute("style")) ?? "";
}

export type CommandTiming = {
  clickToFirstVisualMs: number | null;
  clickToAckMs: number | null;
  clickToConfirmedVisualMs: number | null;
  visualCorrections: number;
  mutationRequests: number;
};

/**
 * Mede: clique → 1ª mutação visual do atributo style do bloco (raf-polling),
 * clique → resposta HTTP da mutation, clique → style estabilizado pós-ACK.
 * `visualCorrections` conta mudanças de style APÓS a primeira (saltos).
 */
export async function measureCommand(
  page: Page,
  watchBlockIds: string[],
  run: () => Promise<void>,
): Promise<CommandTiming> {
  const before = await Promise.all(watchBlockIds.map((id) => blockStyle(page, id)));

  const ackPromise = page
    .waitForResponse(
      (r: Response) =>
        r.url().includes("presentation-mutations") && r.request().method() === "POST",
      { timeout: 15_000 },
    )
    .catch(() => null);
  const mutationRequestPromise = page
    .waitForRequest(
      (r) => r.url().includes("presentation-mutations") && r.method() === "POST",
      { timeout: 15_000 },
    )
    .catch(() => null);

  const t0 = Date.now();
  await run();

  // 1º frame visual: qualquer wrap mudou de style (polling em raf).
  const firstVisualMs = await page
    .waitForFunction(
      ([ids, prevStyles]) => {
        for (let i = 0; i < ids.length; i += 1) {
          const el = document.querySelector(`[data-block-id="${ids[i]}"]`);
          if (!el) continue;
          const now = el.getAttribute("style") ?? "";
          if (now !== prevStyles[i]) return true;
        }
        return false;
      },
      [watchBlockIds, before] as const,
      { polling: "raf", timeout: 5_000 },
    )
    .then(() => Date.now() - t0)
    .catch(() => null);

  const styleAfterProjection = await Promise.all(
    watchBlockIds.map((id) => blockStyle(page, id)),
  );

  const ackResp = await ackPromise;
  const mutationReq = await mutationRequestPromise;
  const clickToAckMs = ackResp ? Date.now() - t0 : null;

  // Confirmed: style estável após ACK — espera mais uma mutação ou timeout curto.
  let visualCorrections = 0;
  const tAck = Date.now();
  const corrected = await page
    .waitForFunction(
      ([ids, projStyles]) => {
        for (let i = 0; i < ids.length; i += 1) {
          const el = document.querySelector(`[data-block-id="${ids[i]}"]`);
          if (!el) continue;
          if ((el.getAttribute("style") ?? "") !== projStyles[i]) return true;
        }
        return false;
      },
      [watchBlockIds, styleAfterProjection] as const,
      { polling: "raf", timeout: 2_500 },
    )
    .then(() => true)
    .catch(() => false);
  if (corrected) visualCorrections = 1;

  return {
    clickToFirstVisualMs: firstVisualMs,
    clickToAckMs,
    clickToConfirmedVisualMs: ackResp
      ? corrected
        ? Date.now() - t0
        : tAck - t0
      : null,
    visualCorrections,
    mutationRequests: mutationReq ? 1 : 0,
  };
}
