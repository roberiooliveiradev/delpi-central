import type { ReactNode } from "react";
import { AlertTriangle, Inbox, LoaderCircle } from "lucide-react";

import { createStateBoxPanel, type StateBoxVariant } from "@delpi/plugin-ui/index";

const StateBoxPanel = createStateBoxPanel({
  prefix: "sm",
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} />;
    if (variant === "empty") return <Inbox size={22} />;
    return <LoaderCircle size={22} />;
  },
});

type ErrorStateProps = {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function ErrorState({ title, message, actionLabel, onAction }: ErrorStateProps) {
  let action: ReactNode;
  if (actionLabel && onAction) {
    action = (
      <button type="button" className="sm-btn sm-btn--primary" onClick={onAction}>
        {actionLabel}
      </button>
    );
  }

  return (
    <StateBoxPanel variant="error" title={title} message={message} action={action} />
  );
}
