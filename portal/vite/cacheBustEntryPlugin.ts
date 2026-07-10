import type { Plugin } from "vite";

/**
 * Substitui o <script type="module" src="/assets/…"> por import() com query string.
 * Evita cache Cloudflare envenenado (HTML servido no lugar do chunk JS após deploy).
 */
export function portalCacheBustEntryPlugin(): Plugin {
  const buildStamp = String(Date.now());

  return {
    name: "portal-cache-bust-entry",
    apply: "build",
    transformIndexHtml: {
      order: "post",
      handler(html) {
        const match = html.match(
          /<script type="module" crossorigin src="(\/assets\/[^"]+\.js)"><\/script>/,
        );
        if (!match) {
          return html;
        }

        const entryPath = match[1];
        const loader = `<script type="module">
const __entry=${JSON.stringify(entryPath)};
const __recover=new URLSearchParams(location.search).get("_recover");
const __suffix=__recover?"?cb="+encodeURIComponent(__recover):"?v=${buildStamp}";
import(/* @vite-ignore */__entry+__suffix).catch(function(){
  if(sessionStorage.getItem("delpi-portal-asset-recover"))return;
  sessionStorage.setItem("delpi-portal-asset-recover","1");
  var u=new URL(location.href);
  u.searchParams.set("_recover",String(Date.now()));
  location.replace(u.toString());
});
</script>`;

        return html
          .replace(
            /<script>\s*\(function\s*\(\)\s*\{[\s\S]*?<\/script>\s*/m,
            "",
          )
          .replace(match[0], loader);
      },
    },
  };
}
