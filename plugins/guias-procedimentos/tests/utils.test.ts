/**
 * Testes de utilitários (sanitização, fallback, permissões, rotas).
 * Executar: npm test
 */
import assert from "node:assert/strict";
import test from "node:test";
import { JSDOM } from "jsdom";

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>");
Object.defineProperty(globalThis, "window", { value: dom.window, configurable: true });
Object.defineProperty(globalThis, "document", {
  value: dom.window.document,
  configurable: true,
});

class HttpRequestError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "HttpRequestError";
    this.status = status;
  }
}

/** Espelha src/data/catalogFallback.shouldUseCatalogFallback */
function shouldUseCatalogFallback(error: unknown): boolean {
  if (!(error instanceof HttpRequestError)) {
    return true;
  }
  if (error.status === 401 || error.status === 403 || error.status === 404) {
    return false;
  }
  return error.status >= 500;
}

const { hasManagePermission } = await import("../src/utils/permissions.ts");
const { parseGuiasProcedimentosPath, isAdminView } = await import(
  "../src/utils/route.ts"
);
const { sanitizeGuideHtml } = await import("../src/utils/sanitizeGuideHtml.ts");
const { slugify } = await import("../src/utils/adminHelpers.ts");
const {
  buildImageInsertHtml,
  buildVideoFileInsertHtml,
  buildExternalVideoInsertHtml,
  buildAttachmentInsertHtml,
} = await import("../src/utils/guideMediaInsert.ts");
const { parseExternalVideoUrl } = await import("../src/utils/externalVideo.ts");
const { resolveLucideIcon } = await import("../src/utils/lucideIcons.ts");

test("sanitize remove script", () => {
  const html = sanitizeGuideHtml("<p>ok</p><script>alert(1)</script>");
  assert.ok(html.includes("ok"));
  assert.ok(!html.toLowerCase().includes("script"));
});

test("sanitize remove onclick", () => {
  const html = sanitizeGuideHtml('<p onclick="evil()">texto</p>');
  assert.ok(html.includes("texto"));
  assert.ok(!html.toLowerCase().includes("onclick"));
});

test("sanitize bloqueia javascript:", () => {
  const html = sanitizeGuideHtml('<a href="javascript:alert(1)">x</a>');
  assert.ok(!html.toLowerCase().includes("javascript:"));
});

test("sanitize remove iframe/style/form", () => {
  const html = sanitizeGuideHtml(
    '<p>a</p><iframe src="x"></iframe><style>b{}</style><form></form>',
  );
  assert.ok(!html.toLowerCase().includes("iframe"));
  assert.ok(!html.toLowerCase().includes("<style"));
  assert.ok(!html.toLowerCase().includes("<form"));
});

test("fallback em 5xx e rede", () => {
  assert.equal(shouldUseCatalogFallback(new HttpRequestError("err", 500)), true);
  assert.equal(shouldUseCatalogFallback(new HttpRequestError("err", 503)), true);
  assert.equal(shouldUseCatalogFallback(new TypeError("Failed to fetch")), true);
});

test("fallback não ocorre em 401/403/404", () => {
  assert.equal(shouldUseCatalogFallback(new HttpRequestError("err", 401)), false);
  assert.equal(shouldUseCatalogFallback(new HttpRequestError("err", 403)), false);
  assert.equal(shouldUseCatalogFallback(new HttpRequestError("err", 404)), false);
});

test("manage permission não infere de access", () => {
  assert.equal(
    hasManagePermission({
      id: "1",
      name: "u",
      email: "u@x",
      permissions: ["guias-procedimentos.access"],
    }),
    false,
  );
  assert.equal(
    hasManagePermission({
      id: "1",
      name: "u",
      email: "u@x",
      permissions: ["guias-procedimentos.manage"],
    }),
    true,
  );
});

test("rotas admin", () => {
  assert.equal(
    parseGuiasProcedimentosPath("/apps/guias-procedimentos/admin").view,
    "admin-home",
  );
  assert.equal(
    parseGuiasProcedimentosPath("/apps/guias-procedimentos/admin/departamentos")
      .view,
    "admin-departments",
  );
  assert.equal(
    parseGuiasProcedimentosPath(
      "/apps/guias-procedimentos/admin/procedimentos/novo",
    ).view,
    "admin-procedure-new",
  );
  assert.equal(isAdminView("admin-home"), true);
  assert.equal(isAdminView("home"), false);
});

test("slugify", () => {
  assert.equal(slugify("Emissão de Nota Fiscal"), "emissao-de-nota-fiscal");
});

test("sanitize mantém figure guide-media com src protegido", () => {
  const id = "11111111-1111-4111-8111-111111111111";
  const html = buildImageInsertHtml({
    id,
    title: "Diagrama",
    alt_text: "Fluxo",
  });
  const cleaned = sanitizeGuideHtml(html);
  assert.ok(cleaned.includes("guide-media--image"));
  assert.ok(cleaned.includes(`/media/${id}/file`));
  assert.ok(cleaned.includes("Fluxo") || cleaned.includes("Diagrama"));
});

test("sanitize remove img com src arbitrário", () => {
  const cleaned = sanitizeGuideHtml(
    '<img src="https://evil.example/x.png" alt="x"><p>ok</p>',
  );
  assert.ok(!cleaned.toLowerCase().includes("<img"));
  assert.ok(cleaned.includes("ok"));
});

test("insert html de vídeo e anexo é controlado", () => {
  const id = "22222222-2222-4222-8222-222222222222";
  const video = buildVideoFileInsertHtml({ id, title: "Demo" });
  const attachment = buildAttachmentInsertHtml({
    id,
    title: "Manual",
    original_filename: "manual.pdf",
  });
  assert.ok(video.includes("guide-media--video"));
  assert.ok(video.includes("preload=\"metadata\""));
  assert.ok(!video.includes("autoplay"));
  assert.ok(attachment.includes("guide-attachment"));
  assert.ok(attachment.includes(`/attachments/${id}/file`));
});

test("vídeo externo rejeita iframe e http", () => {
  assert.equal(parseExternalVideoUrl('<iframe src="x"></iframe>').ok, false);
  assert.equal(parseExternalVideoUrl("http://youtube.com/watch?v=1").ok, false);
  assert.equal(
    parseExternalVideoUrl("https://www.youtube.com/watch?v=abc123").ok,
    true,
  );
  const block = buildExternalVideoInsertHtml({
    title: "Demo",
    external_url: "https://www.youtube.com/watch?v=abc123",
    external_provider: "youtube",
  });
  assert.ok(block.includes("guide-media--video-external"));
  assert.ok(!block.toLowerCase().includes("<iframe"));
});

test("resolveLucideIcon aceita kebab e componente forwardRef", () => {
  assert.ok(resolveLucideIcon("book-open"));
  assert.ok(resolveLucideIcon("building-2"));
  assert.ok(resolveLucideIcon("factory"));
  assert.equal(resolveLucideIcon("nao-existe-xyz"), null);
});

test("vídeo externo aceita Google Drive público e normaliza", async () => {
  const { externalVideoEmbedUrl } = await import("../src/utils/externalVideo.ts");
  const fileId = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms";
  const parsed = parseExternalVideoUrl(
    `https://drive.google.com/file/d/${fileId}/view?usp=sharing`,
  );
  assert.equal(parsed.ok, true);
  if (!parsed.ok) return;
  assert.equal(parsed.provider, "google_drive");
  assert.equal(parsed.url, `https://drive.google.com/file/d/${fileId}/view`);
  assert.equal(
    externalVideoEmbedUrl(parsed.url, "google_drive"),
    `https://drive.google.com/file/d/${fileId}/preview`,
  );
  assert.equal(
    parseExternalVideoUrl("https://drive.google.com/drive/folders/abc").ok,
    false,
  );
});
