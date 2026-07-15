/**
 * Geração controlada de HTML de mídia/anexo (allowlist).
 * Não aceita HTML arbitrário do usuário.
 */

import {
  attachmentDownloadUrl,
  mediaContentUrl,
} from "./guideAssetUrls.ts";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function captionText(title: string, altText?: string): string {
  const primary = title.trim() || (altText || "").trim();
  return primary;
}

export function buildImageInsertHtml(input: {
  id: string;
  title: string;
  alt_text?: string;
}): string {
  const src = mediaContentUrl(input.id);
  const alt = escapeHtml(
    (input.alt_text || "").trim() || input.title.trim() || "Imagem",
  );
  const caption = escapeHtml(captionText(input.title, input.alt_text) || "Imagem");
  return [
    '<figure class="guide-media guide-media--image">',
    `  <img src="${src}" alt="${alt}" loading="lazy">`,
    `  <figcaption>${caption}</figcaption>`,
    "</figure>",
  ].join("\n");
}

export function buildVideoFileInsertHtml(input: {
  id: string;
  title: string;
}): string {
  const src = mediaContentUrl(input.id);
  const caption = escapeHtml(input.title.trim() || "Vídeo");
  return [
    '<figure class="guide-media guide-media--video">',
    `  <video src="${src}" controls preload="metadata" playsinline></video>`,
    `  <figcaption>${caption}</figcaption>`,
    "</figure>",
  ].join("\n");
}

export function buildExternalVideoInsertHtml(input: {
  title: string;
  external_url: string;
  external_provider?: string | null;
}): string {
  const href = escapeHtml(input.external_url.trim());
  const providerLabel =
    input.external_provider === "vimeo"
      ? "Vimeo"
      : input.external_provider === "google_drive"
        ? "Google Drive"
        : "YouTube";
  const label = escapeHtml(
    input.title.trim() || `Assistir no ${providerLabel}`,
  );
  const caption = escapeHtml(input.title.trim() || `Vídeo (${providerLabel})`);
  return [
    '<figure class="guide-media guide-media--video-external">',
    `  <a class="guide-media__link" href="${href}" target="_blank" rel="noopener noreferrer">${label}</a>`,
    `  <figcaption>${caption}</figcaption>`,
    "</figure>",
  ].join("\n");
}

export function buildAttachmentInsertHtml(input: {
  id: string;
  title: string;
  original_filename?: string | null;
}): string {
  const href = attachmentDownloadUrl(input.id);
  const label = escapeHtml(
    input.title.trim() ||
      (input.original_filename || "").trim() ||
      "Baixar anexo",
  );
  return [
    '<p class="guide-attachment">',
    `  <a class="guide-attachment__link" href="${href}">Baixar: ${label}</a>`,
    "</p>",
  ].join("\n");
}

export function appendHtmlBlock(current: string, block: string): string {
  const base = current.trimEnd();
  const chunk = block.trim();
  if (!chunk) return current;
  if (!base) return `${chunk}\n`;
  return `${base}\n\n${chunk}\n`;
}
