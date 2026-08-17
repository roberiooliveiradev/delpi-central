import type { Plugin } from "vite";

/**
 * Substitui o <script type="module" src="/assets/…"> por import() com recuperação.
 * Evita cache Cloudflare envenenado (HTML servido no lugar do chunk JS após deploy).
 *
 * A URL importada aqui precisa ser exatamente a mesma que os chunks lazy usam nos
 * imports estáticos: qualquer query string cria um segundo módulo para o browser e
 * duplica todo o grafo do entry (React contexts, Keycloak, providers) — o que quebra
 * qualquer rota com code-split.
 */
export function portalCacheBustEntryPlugin(): Plugin {
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
const __key="delpi-portal-asset-recover";
const __url=new URL(location.href);
const __recovering=__url.searchParams.has("_recover");
// Na recuperação, revalida no CDN sem trocar a URL do módulo.
const __load=__recovering
  ?fetch(__entry,{cache:"reload"}).then(function(){return import(/* @vite-ignore */__entry)})
  :import(/* @vite-ignore */__entry);
__load.then(function(){
  try{sessionStorage.removeItem(__key)}catch(e){}
  if(__recovering){
    __url.searchParams.delete("_recover");
    history.replaceState(history.state,"",__url.pathname+__url.search+__url.hash);
  }
}).catch(function(){
  try{
    if(sessionStorage.getItem(__key))return;
    sessionStorage.setItem(__key,"1");
  }catch(e){}
  __url.searchParams.set("_recover",String(Date.now()));
  location.replace(__url.toString());
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
