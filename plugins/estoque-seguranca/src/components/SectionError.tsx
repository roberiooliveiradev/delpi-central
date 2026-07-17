import type { ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

import { createStateBoxPanel } from "@delpi/plugin-ui/index";

const StateBoxPanel = createStateBoxPanel({
  prefix: "ess",
  renderIcon: () => <AlertTriangle size={22} />,
});

type SectionErrorProps = {
  title: string;
  message: string;
  onRetry?: () => void;
};

export function SectionError({ title, message, onRetry }: SectionErrorProps) {
  let action: ReactNode;
  if (onRetry) {
    action = (
      <button type="button" className="ess-btn ess-btn--primary" onClick={onRetry}>
        Tentar novamente
      </button>
    );
  }

  return (
    <StateBoxPanel variant="error" title={title} message={message} action={action} />
  );
}
