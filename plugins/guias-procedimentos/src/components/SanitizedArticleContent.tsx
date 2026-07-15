import { useEffect, useRef } from "react";

import { downloadProtectedBlob } from "../api/guiasProcedimentosApi";
import { isProtectedGuideMediaSrc } from "../utils/guideAssetUrls";
import { externalVideoEmbedUrl } from "../utils/externalVideo";
import { sanitizeGuideHtml } from "../utils/sanitizeGuideHtml";

type SanitizedArticleContentProps = {
  html: string;
  className?: string;
};

/**
 * Renderiza HTML sanitizado e hidrata mídias JWT-protegidas com blob URLs.
 * Vídeos externos viram embed controlado a partir da URL HTTPS já validada.
 */
export function SanitizedArticleContent({
  html,
  className = "gp-article__html",
}: SanitizedArticleContentProps) {
  const ref = useRef<HTMLDivElement>(null);
  const safe = sanitizeGuideHtml(html);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;

    const objectUrls: string[] = [];
    let cancelled = false;

    const hydrateProtected = async (
      el: HTMLImageElement | HTMLVideoElement,
    ) => {
      const src = (el.getAttribute("src") || "").trim();
      if (!isProtectedGuideMediaSrc(src)) return;
      try {
        const blob = await downloadProtectedBlob(src);
        if (cancelled) return;
        const objectUrl = URL.createObjectURL(blob);
        objectUrls.push(objectUrl);
        el.src = objectUrl;
      } catch {
        el.removeAttribute("src");
        el.setAttribute("data-load-error", "1");
      }
    };

    root.querySelectorAll("img, video").forEach((node) => {
      void hydrateProtected(node as HTMLImageElement | HTMLVideoElement);
    });

    root
      .querySelectorAll("figure.guide-media--video-external")
      .forEach((figure) => {
        if (figure.querySelector("iframe.guide-media__embed")) return;
        const link = figure.querySelector("a.guide-media__link");
        const href = link?.getAttribute("href") || "";
        const embed = href ? externalVideoEmbedUrl(href, null) : null;
        if (!embed) return;
        const iframe = document.createElement("iframe");
        iframe.className = "guide-media__embed";
        iframe.src = embed;
        iframe.title = link?.textContent?.trim() || "Vídeo externo";
        iframe.setAttribute(
          "allow",
          "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
        );
        iframe.allowFullscreen = true;
        link?.replaceWith(iframe);
      });

    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      const anchor = target?.closest?.(
        "a.guide-attachment__link",
      ) as HTMLAnchorElement | null;
      if (!anchor) return;
      const href = anchor.getAttribute("href") || "";
      if (!href.includes("/guias-procedimentos/attachments/")) return;
      event.preventDefault();
      const filename =
        anchor.textContent?.replace(/^Baixar:\s*/i, "").trim() || "anexo";
      void downloadProtectedBlob(href)
        .then((blob) => {
          const objectUrl = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = objectUrl;
          a.download = filename;
          a.rel = "noopener";
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(objectUrl);
        })
        .catch(() => {
          window.open(href, "_blank", "noopener,noreferrer");
        });
    };

    root.addEventListener("click", onClick);

    return () => {
      cancelled = true;
      root.removeEventListener("click", onClick);
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [safe]);

  return (
    <div
      ref={ref}
      className={className}
      // Conteúdo já sanitizado (DOMPurify + allowlist alinhada à API).
      dangerouslySetInnerHTML={{ __html: safe }}
    />
  );
}
