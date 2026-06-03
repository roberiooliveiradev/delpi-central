import { useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";

type CollapsiblePanelProps = {
  className?: string;
  triggerClassName?: string;
  bodyClassName?: string;
  defaultOpen?: boolean;
  header: ReactNode;
  children: ReactNode;
};

export function CollapsiblePanel({
  className,
  triggerClassName,
  bodyClassName,
  defaultOpen = true,
  header,
  children,
}: CollapsiblePanelProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className={className}>
      <button
        type="button"
        className={["ds-collapsible__trigger", triggerClassName].filter(Boolean).join(" ")}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {header}
        <ChevronDown
          size={20}
          className={["ds-collapsible__chevron", open ? "is-open" : ""].filter(Boolean).join(" ")}
          aria-hidden
        />
      </button>
      {open ? <div className={bodyClassName}>{children}</div> : null}
    </section>
  );
}
