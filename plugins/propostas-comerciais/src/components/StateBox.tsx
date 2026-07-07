import { AlertCircle, FileSearch, LoaderCircle } from "lucide-react";

import { createStateBoxPanel, type StateBoxVariant } from "@delpi/plugin-ui";

function renderStateIcon(variant: StateBoxVariant) {
  if (variant === "loading") {
    return <LoaderCircle size={28} strokeWidth={1.75} />;
  }
  if (variant === "error") {
    return <AlertCircle size={28} strokeWidth={1.75} />;
  }
  return <FileSearch size={28} strokeWidth={1.75} />;
}

export const StateBox = createStateBoxPanel({
  prefix: "pc",
  renderIcon: renderStateIcon,
  iconClassName: (variant) => (variant === "loading" ? "pc-spin" : undefined),
});

export type { DashboardStateBoxPanelProps as StateBoxProps } from "@delpi/plugin-ui";