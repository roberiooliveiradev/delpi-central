const assetModules = import.meta.glob("../assets/**/*.{png,jpg,jpeg,webp,svg}", {
  eager: true,
  import: "default",
}) as Record<string, string>;

const assetByName = new Map(
  Object.entries(assetModules).map(([path, url]) => [path.replace(/^\.\.\/assets\//, ""), url]),
);

function assetUrl(relativePath: string): string | null {
  return assetByName.get(relativePath) ?? null;
}

export function heroImageUrl(): string | null {
  return assetUrl("hero-factory.webp") ?? assetUrl("hero-factory.jpg") ?? assetUrl("hero-factory.png");
}

export function sidebarLogoUrl(): string | null {
  return assetUrl("logo-delpi-white.png") ?? assetUrl("logo-delpi-white.svg") ?? assetUrl("logo-delpi.png") ?? assetUrl("logo-delpi.webp");
}

export function sidebarArtUrl(): string | null {
  return assetUrl("sidebar-icon.webp") ?? assetUrl("sidebar-icon.png") ?? assetUrl("sidebar-icon.svg");
}

function normalizeWorkCenterAssetName(workCenter: string): string {
  return workCenter.trim().toUpperCase().replace(/[^A-Z0-9-]+/g, "-");
}

export function workCenterImageUrl(workCenter: string): string | null {
  const base = normalizeWorkCenterAssetName(workCenter);
  for (const ext of ["webp", "png", "jpg", "jpeg"]) {
    const url = assetUrl(`machines/${base}.${ext}`);
    if (url) return url;
  }
  return assetUrl("machines/machine-default.webp") ?? assetUrl("machines/machine-default.png");
}
