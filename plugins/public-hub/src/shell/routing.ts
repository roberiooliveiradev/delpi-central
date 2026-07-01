export interface ResolvedRoute {
  appId: string;
  pageId: string;
  token: string;
}

function decode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/**
 * Resolve a rota pública a partir do pathname.
 *
 * Canônico: /p/{app}/{page}/{token}
 * Legado:   /welcome/{token} -> customer-experience / thanks
 */
export function resolveRoute(pathname: string): ResolvedRoute | null {
  const canonical = pathname.match(/^\/p\/([^/]+)\/([^/]+)\/([^/?#]+)/);
  if (canonical) {
    return {
      appId: decode(canonical[1]),
      pageId: decode(canonical[2]),
      token: decode(canonical[3]),
    };
  }

  const legacy = pathname.match(/^\/welcome\/([^/?#]+)/);
  if (legacy) {
    return { appId: "customer-experience", pageId: "thanks", token: decode(legacy[1]) };
  }

  return null;
}
