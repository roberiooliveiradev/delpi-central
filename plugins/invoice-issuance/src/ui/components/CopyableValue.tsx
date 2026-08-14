import { useState, type ReactNode } from "react";
import { Check, Copy } from "lucide-react";

type Props = {
  value: string;
  label: string;
  children?: ReactNode;
};

export function CopyableValue({ value, label, children }: Props) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  }

  return (
    <span className="ii-copy">
      <span className="ii-code">{children ?? value}</span>
      <button
        type="button"
        className="ii-copy__btn"
        aria-label={copied ? `Copiado: ${label}` : `Copiar ${label}`}
        onClick={() => void copy()}
      >
        {copied ? (
          <Check size={12} strokeWidth={2.25} aria-hidden="true" />
        ) : (
          <Copy size={12} strokeWidth={2.25} aria-hidden="true" />
        )}
      </button>
    </span>
  );
}
