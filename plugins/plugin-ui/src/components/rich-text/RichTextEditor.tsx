import { useEffect, useMemo, useRef } from "react";

export type RichTextEditorMode = "edit" | "preview";

export type RichTextEditorProps = {
  value: string;
  onChange: (next: string) => void;
  mode?: RichTextEditorMode;
  disabled?: boolean;
  className?: string;
  ariaLabel?: string;
};

function exec(command: string, value?: string) {
  document.execCommand(command, false, value);
}

export function RichTextEditor({
  value,
  onChange,
  mode = "edit",
  disabled = false,
  className,
  ariaLabel = "Editor de texto",
}: RichTextEditorProps) {
  const ref = useRef<HTMLDivElement>(null);
  const seeded = useRef(false);
  const rootClass = useMemo(
    () => ["delpi-ui-rich-text", className].filter(Boolean).join(" "),
    [className],
  );

  useEffect(() => {
    if (mode !== "edit" || disabled) return;
    if (!ref.current || seeded.current) return;
    ref.current.innerHTML = value || "<p></p>";
    seeded.current = true;
  }, [mode, disabled, value]);

  if (mode === "preview" || disabled) {
    return (
      <div
        className={`${rootClass} delpi-ui-rich-text--preview`}
        dangerouslySetInnerHTML={{ __html: value || "<p></p>" }}
      />
    );
  }

  return (
    <div className={rootClass}>
      <div className="delpi-ui-rich-text__toolbar" role="toolbar" aria-label="Formatação">
        <button type="button" onClick={() => exec("bold")}>N</button>
        <button type="button" onClick={() => exec("italic")}>I</button>
        <button type="button" onClick={() => exec("underline")}>S</button>
        <button type="button" onClick={() => exec("formatBlock", "h2")}>H2</button>
        <button type="button" onClick={() => exec("insertUnorderedList")}>•</button>
        <button type="button" onClick={() => exec("insertOrderedList")}>1.</button>
        <button type="button" onClick={() => exec("justifyLeft")}>⟸</button>
        <button type="button" onClick={() => exec("justifyCenter")}>≡</button>
        <button type="button" onClick={() => exec("justifyRight")}>⟹</button>
        <button
          type="button"
          onClick={() => {
            const url = window.prompt("URL do link");
            if (url) exec("createLink", url);
          }}
        >
          Link
        </button>
        <button type="button" onClick={() => exec("removeFormat")}>Limpar</button>
        <button type="button" onClick={() => exec("undo")}>Desfazer</button>
        <button type="button" onClick={() => exec("redo")}>Refazer</button>
      </div>
      <div
        ref={ref}
        className="delpi-ui-rich-text__editor"
        contentEditable
        role="textbox"
        aria-multiline="true"
        aria-label={ariaLabel}
        suppressContentEditableWarning
        onInput={() => onChange(ref.current?.innerHTML || "")}
      />
    </div>
  );
}
