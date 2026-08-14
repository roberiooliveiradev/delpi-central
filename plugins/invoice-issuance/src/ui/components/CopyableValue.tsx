import { useState, type ReactNode } from "react";

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
        className="ii-btn ii-btn--ghost ii-btn--sm"
        onClick={() => void copy()}
        aria-label={`Copiar ${label}`}
      >
        {copied ? "Copiado" : "Copiar"}
      </button>
    </span>
  );
}
