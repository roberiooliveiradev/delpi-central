import { CommercialUnderlineNav } from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";
import type { PluginView } from "../../../app/pluginRoutes";
import { GESTAO_CONTENT } from "../../../content/gestaoContent";

type GestaoSubNavProps = {
  view: PluginView;
  basePath: string;
};

const ITEMS = [
  { id: "gestao" as const, label: GESTAO_CONTENT.nav.overview },
  { id: "gestao_otd" as const, label: GESTAO_CONTENT.nav.otd },
  { id: "gestao_equipe" as const, label: GESTAO_CONTENT.nav.equipe },
  { id: "gestao_oportunidades" as const, label: GESTAO_CONTENT.nav.oportunidades },
];

function resolveActiveId(view: PluginView): (typeof ITEMS)[number]["id"] {
  if (view === "gestao_otd" || view === "gestao_otd_line") return "gestao_otd";
  if (view === "gestao_equipe") return "gestao_equipe";
  if (view === "gestao_oportunidades" || view === "gestao_oportunidade_detail") {
    return "gestao_oportunidades";
  }
  return "gestao";
}

export function GestaoSubNav({ view, basePath }: GestaoSubNavProps) {
  const activeId = resolveActiveId(view);
  const search =
    typeof window !== "undefined" ? window.location.search || undefined : undefined;

  return (
    <CommercialUnderlineNav
      aria-label="Áreas de gestão"
      activeId={activeId}
      items={ITEMS.map((item) => ({
        id: item.id,
        label: item.label,
        onSelect: () =>
          navigatePluginView(item.id, {
            basePath,
            search,
          }),
      }))}
    />
  );
}
