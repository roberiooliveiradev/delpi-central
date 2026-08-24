/** Tipagem mínima do plugin Vite — evita depender de `vite` no typecheck dos MFEs. */
type VitePlugin = {
  name: string;
  apply?: "build" | "serve";
  transformIndexHtml?: {
    order?: "pre" | "post";
    handler: (html: string) => string;
  };
};

export type CacheBustEntryPluginOptions = {
  /** Prefixo dos chunks Vite no HTML (ex.: `/assets/` portal, `/p/assets/` public-hub). */
  assetPathPrefix: string;
  /** Chave em `sessionStorage` — uma recuperação automática por sessão. */
  sessionKey: string;
  /** Remove script inline de boot legado do portal (não usar no public-hub). */
  stripInlineBootScript?: boolean;
};

/**
 * Substitui o `<script type="module" src="…">` do entry por import() com recuperação.
 * Evita cache Cloudflare envenenado (HTML servido no lugar do chunk JS após deploy).
 *
 * A URL importada precisa ser exatamente a mesma que os chunks lazy usam nos imports
 * estáticos — sem query string no módulo.
 */
export function cacheBustEntryPlugin(options: CacheBustEntryPluginOptions): VitePlugin {
  const escapedPrefix = options.assetPathPrefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const entryPattern = new RegExp(
    `<script type="module" crossorigin src="(${escapedPrefix}[^"]+\\.js)"></script>`,
  );

  return {
    name: "delpi-cache-bust-entry",
    apply: "build",
    transformIndexHtml: {
      order: "post",
      handler(html) {
        const match = html.match(entryPattern);
        if (!match) {
          return html;
        }

        const entryPath = match[1];
        const sessionKey = JSON.stringify(options.sessionKey);
        const loader = `<script type="module">
const __entry=${JSON.stringify(entryPath)};
const __key=${sessionKey};
const __url=new URL(location.href);
const __recovering=__url.searchParams.has("_recover");
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

        let next = html.replace(match[0], loader);
        if (options.stripInlineBootScript) {
          next = next.replace(/<script>\s*\(function\s*\(\)\s*\{[\s\S]*?<\/script>\s*/m, "");
        }
        return next;
      },
    },
  };
}

/** Defaults do portal shell (`/assets/*`). */
export function portalCacheBustEntryPlugin(): VitePlugin {
  return cacheBustEntryPlugin({
    assetPathPrefix: "/assets/",
    sessionKey: "delpi-portal-asset-recover",
    stripInlineBootScript: true,
  });
}

/** Defaults do public-hub (`/p/assets/*`). */
export function publicHubCacheBustEntryPlugin(): VitePlugin {
  return cacheBustEntryPlugin({
    assetPathPrefix: "/p/assets/",
    sessionKey: "delpi-public-hub-asset-recover",
  });
}
