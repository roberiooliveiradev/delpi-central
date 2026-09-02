import type { PagePathItem } from "@delpi/plugin-ui/index";

import { PpPagePath } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type ProductionPulsePagePathProps = {
  panelHref: string;
  current: string;
  items?: PagePathItem[];
};

/** Breadcrumb das páginas profundas (detalhe / cadastro) — mesmo padrão do Portal Comercial. */
export function ProductionPulsePagePath({
  panelHref,
  current,
  items = [],
}: ProductionPulsePagePathProps) {
  return (
    <PpPagePath
      back={{
        label: PP_HELP.shell.breadcrumbRoot,
        href: panelHref,
        onNavigate: (event) => {
          event.preventDefault();
          navigateProductionPulse(panelHref);
        },
      }}
      items={items.map((item) => ({
        ...item,
        onNavigate:
          item.onNavigate ??
          ((event) => {
            event.preventDefault();
            navigateProductionPulse(item.href);
          }),
      }))}
      current={current}
    />
  );
}
