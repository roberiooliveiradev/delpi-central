import { RotateCcw } from "lucide-react";

import { PP_HELP } from "../../content/helpTooltips";

type ReadingHardwareResetBadgeProps = {
  title?: string;
  compact?: boolean;
};

export function ReadingHardwareResetBadge({
  title = PP_HELP.detail.counterHardwareReset,
  compact = false,
}: ReadingHardwareResetBadgeProps) {
  return (
    <span
      className={`pp-reading-reset-badge${compact ? " pp-reading-reset-badge--compact" : ""}`}
      title={title}
    >
      <RotateCcw size={compact ? 12 : 14} aria-hidden="true" />
      <span>Reset HW</span>
    </span>
  );
}
