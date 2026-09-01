import type { ComponentProps } from "react";
import {
  ActionButton,
  createDashboardSegmentToggle,
  createSimpleKpiCard,
  createStateBoxPanel,
  PageHero,
  pageHeroBemClasses,
  type StateBoxVariant,
} from "@delpi/plugin-ui/index";
import { Activity, AlertTriangle, FileQuestion, Loader2 } from "lucide-react";

const PREFIX = "pp";

export function PpPageHero(props: ComponentProps<typeof PageHero>) {
  return <PageHero {...props} classNames={pageHeroBemClasses(PREFIX)} density="compact" />;
}

export const PpStateBox = createStateBoxPanel({
  prefix: PREFIX,
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} />;
    if (variant === "empty") return <FileQuestion size={22} />;
    return <Loader2 size={22} />;
  },
});

export const PpActionButton = ActionButton;
export const PpSimpleKpiCard = createSimpleKpiCard(PREFIX, { withBody: true, withSubtitle: true });
export const PpSegmentToggle = createDashboardSegmentToggle(PREFIX);

export const ppShellIcon = <Activity size={28} strokeWidth={1.75} />;
