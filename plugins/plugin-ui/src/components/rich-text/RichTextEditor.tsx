import { useEffect, useMemo, useRef } from "react";

import { RichTextToolbar } from "./RichTextToolbar";

export type RichTextEditorMode = "edit" | "preview";

export type RichTextEditorProps = {
  value: string;
  onChange: (next: string) => void;
  mode?: RichTextEditorMode;
  disabled?: boolean;
  className?: string;
  ariaLabel?: string;
  /** Escopo CSS do host para portais (select/cor). Ex.: `dashboard-cipa`. */
  portalScopeClassName?: string;
  minHeight?: number;
};

export function RichTextEditor({
  value,
  onChange,
  mode = "edit",
  disabled = false,
  className,
  ariaLabel = "Editor de texto",
  portalScopeClassName,
  minHeight = 200,
}: RichTextEditorProps) {
  const ref = useRef<HTMLDivElement>(null);
  const focusedRef = useRef(false);
  const rootClass = useMemo(
    () => ["delpi-ui-rich-text", className].filter(Boolean).join(" "),
    [className],
  );

  useEffect(() => {
    if (mode !== "edit" || disabled || !ref.current || focusedRef.current) return;
    const next = value || "<p></p>";
    if (ref.current.innerHTML !== next) {
      ref.current.innerHTML = next;
    }
  }, [mode, disabled, value]);

  if (mode === "preview" || disabled) {
    return (
      <div
        className={`${rootClass} delpi-ui-rich-text--preview`}
        style={{ minHeight }}
        dangerouslySetInnerHTML={{ __html: value || "<p></p>" }}
      />
    );
  }

  return (
    <div className={rootClass}>
      <RichTextToolbar
        editorRef={ref}
        disabled={disabled}
        portalScopeClassName={portalScopeClassName}
        onFormatted={() => onChange(ref.current?.innerHTML || "")}
      />
      <div
        ref={ref}
        className="delpi-ui-rich-text__editor"
        style={{ minHeight }}
        contentEditable
        role="textbox"
        aria-multiline="true"
        aria-label={ariaLabel}
        suppressContentEditableWarning
        onFocus={() => {
          focusedRef.current = true;
        }}
        onBlur={() => {
          focusedRef.current = false;
          onChange(ref.current?.innerHTML || "");
        }}
        onInput={() => onChange(ref.current?.innerHTML || "")}
      />
    </div>
  );
}
