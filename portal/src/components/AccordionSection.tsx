// src/ui/admin/components/AccordionSection.tsx
import "./AccordionSection.css"
import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import * as LucideIcons from "lucide-react";

type Props = {
  title: string;
  icon?: keyof typeof LucideIcons;
  defaultOpen?: boolean;
  forceOpen?: boolean;
  hasError?: boolean;
  children: ReactNode;
};

export const AccordionSection = ({
  title,
  icon,
  defaultOpen = false,
  forceOpen,
  hasError = false,
  children,
}: Props) => {
  const [open, setOpen] = useState(defaultOpen);

  useEffect(() => {
    if (forceOpen) {
      setOpen(true);
    }
  }, [forceOpen]);

  const Icon = icon ? (LucideIcons as any)[icon] : null;

  return (
    <div className={`accordion-section ${hasError ? "has-error" : ""}`}>
      <button
        type="button"
        className="accordion-header"
        onClick={() => setOpen(!open)}
      >
        <div className="row">
          {Icon && <Icon size={18} />}
          <span>{title}</span>

          {hasError && (
            <span className="accordion-error-badge">
              !
            </span>
          )}
        </div>

        <LucideIcons.ChevronDown
          size={18}
          style={{
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "0.2s",
          }}
        />
      </button>

      {open && <div className="accordion-content">{children}</div>}
    </div>
  );
};