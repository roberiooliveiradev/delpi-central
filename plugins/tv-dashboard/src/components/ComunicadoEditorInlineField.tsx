import { Link2, Type } from "lucide-react";
import { hasRichTextRuns, syncTextBlockFromRuns } from "@delpi/tv-dashboard-presentation";
import { useEffect, useState, type ClipboardEvent } from "react";

import {
  isLikelyExternalUrl,
  normalizeHrefInput,
  resolveDefaultTextLinkMode,
  textLinkFieldPlaceholder,
  type TextLinkFieldMode,
} from "../utils/comunicadoTextLinkField";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type TextBlockProps = {
  variant: "text";
  blockId: string;
  blockType: "heading" | "text";
  content: string;
  href?: string;
  contentRuns?: import("@delpi/tv-dashboard-presentation").ComunicadoTextBlock["contentRuns"];
};

type LinkOnlyProps = {
  variant: "link";
  blockId: string;
  href?: string;
};

type Props = TextBlockProps | LinkOnlyProps;

export function ComunicadoEditorInlineField(props: Props) {
  const { updateBlockLink, updateBlockTextFields } = useComunicadoEditor();

  const isTextVariant = props.variant === "text";
  const blockId = props.blockId;
  const href = props.href ?? "";
  const content = isTextVariant ? props.content : "";
  const richRuns = isTextVariant && hasRichTextRuns(props);

  const [mode, setMode] = useState<TextLinkFieldMode>(() =>
    isTextVariant
      ? resolveDefaultTextLinkMode(Boolean(props.href?.trim()), content)
      : "link",
  );

  useEffect(() => {
    if (!isTextVariant) return;
    setMode(resolveDefaultTextLinkMode(Boolean(props.href?.trim()), props.content));
  }, [blockId, isTextVariant, props.href]);

  const activeMode: TextLinkFieldMode = isTextVariant ? mode : "link";
  const fieldValue = activeMode === "link" ? href : content;
  const readOnly = isTextVariant && activeMode === "text" && richRuns;

  function commitHref(raw: string) {
    const next = normalizeHrefInput(raw);
    updateBlockLink(blockId, next || undefined);
    if (!next && isTextVariant) setMode("text");
  }

  function commitText(raw: string) {
    if (!isTextVariant) return;
    updateBlockTextFields(blockId, syncTextBlockFromRuns([{ text: raw }]));
  }

  function handleChange(value: string) {
    if (activeMode === "link") {
      commitHref(value);
      return;
    }
    if (isLikelyExternalUrl(value)) {
      commitHref(value);
      setMode("link");
      return;
    }
    commitText(value);
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    if (activeMode !== "text") return;
    const pasted = event.clipboardData.getData("text");
    if (!isLikelyExternalUrl(pasted)) return;
    event.preventDefault();
    commitHref(pasted);
    setMode("link");
  }

  const placeholder = isTextVariant
    ? textLinkFieldPlaceholder(activeMode, props.blockType, richRuns)
    : "https://…";

  return (
    <div
      className="td-composer__inline-field"
      onPointerDown={(event) => event.stopPropagation()}
    >
      {isTextVariant ? (
        <div className="td-composer__inline-field-modes" role="tablist" aria-label="Texto ou link">
          <button
            type="button"
            role="tab"
            aria-selected={activeMode === "text"}
            className={`td-composer__inline-field-mode${activeMode === "text" ? " td-composer__inline-field-mode--active" : ""}`}
            title="Texto exibido"
            onClick={() => setMode("text")}
          >
            <Type size={12} aria-hidden="true" />
            <span>Texto</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeMode === "link"}
            className={`td-composer__inline-field-mode${activeMode === "link" ? " td-composer__inline-field-mode--active" : ""}`}
            title="Endereço do link"
            onClick={() => setMode("link")}
          >
            <Link2 size={12} aria-hidden="true" />
            <span>Link</span>
          </button>
        </div>
      ) : (
        <span className="td-composer__inline-field-icon" aria-hidden="true">
          <Link2 size={12} />
        </span>
      )}
      <input
        type={activeMode === "link" ? "url" : "text"}
        className="td-composer__inline-field-input"
        aria-label={activeMode === "link" ? "Endereço do link" : "Texto exibido"}
        placeholder={placeholder}
        value={fieldValue}
        readOnly={readOnly}
        onChange={(event) => handleChange(event.target.value)}
        onPaste={handlePaste}
      />
    </div>
  );
}
