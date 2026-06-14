import type { ReactNode } from "react";
import { AlertCircle, FileSearch, LoaderCircle } from "lucide-react";

type StateBoxProps = {
  variant: "loading" | "error" | "empty";
  title: string;
  message?: string;
  action?: ReactNode;
};

export function StateBox({ variant, title, message, action }: StateBoxProps) {
  const Icon = variant === "loading" ? LoaderCircle : variant === "error" ? AlertCircle : FileSearch;

  return (
    <div className={`pc-state-box pc-state-box--${variant}`} role="status">
      <span className="pc-state-box__icon" aria-hidden="true">
        <Icon size={28} strokeWidth={1.75} className={variant === "loading" ? "pc-spin" : undefined} />
      </span>
      <div>
        <h2>{title}</h2>
        {message ? <p>{message}</p> : null}
      </div>
      {action}
    </div>
  );
}
