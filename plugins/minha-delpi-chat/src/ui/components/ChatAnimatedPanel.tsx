import type { ReactNode } from "react";

type ChatAnimatedPanelProps = {
  panelKey: string;
  variant?: "page" | "tab";
  className?: string;
  children: ReactNode;
};

export function ChatAnimatedPanel({
  panelKey,
  variant = "page",
  className,
  children,
}: ChatAnimatedPanelProps) {
  return (
    <div
      key={panelKey}
      className={[
        variant === "tab" ? "mdc-chat-tab-panel" : "mdc-chat-page-panel",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
