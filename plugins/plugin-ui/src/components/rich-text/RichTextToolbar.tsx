import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Bold,
  Heading2,
  Indent,
  Italic,
  Link,
  List,
  ListOrdered,
  Outdent,
  Redo2,
  RemoveFormatting,
  Strikethrough,
  Underline,
  Undo2,
} from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode, type RefObject } from "react";

import { ComboboxNumberControl } from "../forms/ComboboxNumberControl";
import { FormSelectControl } from "../forms/FormSelectControl";
import { HintAction } from "../help/HintAction";
import { RibbonColorPicker } from "../shape/RibbonColorPicker";
import {
  applyRichTextAlign,
  applyRichTextFontFamily,
  applyRichTextFontSize,
  insertRichTextLink,
  queryRichTextAlign,
  queryRichTextCommandState,
  runRichTextCommand,
  type RichTextAlign,
} from "./richTextCommands";
import {
  clampRichTextFontSize,
  RICH_TEXT_FONT_FAMILIES,
  RICH_TEXT_FONT_SIZE_DEFAULT,
  RICH_TEXT_FONT_SIZE_PRESETS,
} from "./richTextConfig";
import { RICH_TEXT_LABELS } from "./richTextLabels";

type Props = {
  editorRef: RefObject<HTMLDivElement | null>;
  disabled?: boolean;
  onFormatted: () => void;
  portalScopeClassName?: string;
};

function RichTextIconButton({
  hint,
  ariaLabel,
  active,
  disabled,
  onClick,
  children,
}: {
  hint: string;
  ariaLabel: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <HintAction hint={hint} ariaLabel={ariaLabel} placement="bottom">
      <button
        type="button"
        className={[
          "delpi-ui-rich-text-ribbon__icon-btn",
          active ? "is-active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label={ariaLabel}
        aria-pressed={active}
        disabled={disabled}
        onMouseDown={(event) => event.preventDefault()}
        onClick={onClick}
      >
        {children}
      </button>
    </HintAction>
  );
}

export function RichTextToolbar({
  editorRef,
  disabled = false,
  onFormatted,
  portalScopeClassName,
}: Props) {
  const [fontFamily, setFontFamily] = useState(RICH_TEXT_FONT_FAMILIES[0].value);
  const [fontSize, setFontSize] = useState(RICH_TEXT_FONT_SIZE_DEFAULT);
  const [textColor, setTextColor] = useState("#111111");
  const [highlightColor, setHighlightColor] = useState("#fef08a");
  const [formatTick, setFormatTick] = useState(0);

  const refreshFormatState = useCallback(() => {
    setFormatTick((value) => value + 1);
  }, []);

  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const handleSelection = () => refreshFormatState();
    editor.addEventListener("keyup", handleSelection);
    editor.addEventListener("mouseup", handleSelection);
    editor.addEventListener("focus", handleSelection);
    return () => {
      editor.removeEventListener("keyup", handleSelection);
      editor.removeEventListener("mouseup", handleSelection);
      editor.removeEventListener("focus", handleSelection);
    };
  }, [editorRef, refreshFormatState]);

  const editor = editorRef.current;
  void formatTick;

  const boldActive = queryRichTextCommandState("bold");
  const italicActive = queryRichTextCommandState("italic");
  const underlineActive = queryRichTextCommandState("underline");
  const strikeActive = queryRichTextCommandState("strikeThrough");
  const bulletActive = queryRichTextCommandState("insertUnorderedList");
  const orderedActive = queryRichTextCommandState("insertOrderedList");
  const alignActive = queryRichTextAlign();

  function run(action: () => void) {
    if (disabled) return;
    action();
    onFormatted();
    refreshFormatState();
  }

  return (
    <div className="delpi-ui-rich-text-ribbon" role="toolbar" aria-label={RICH_TEXT_LABELS.toolbar}>
      <section className="delpi-ui-rich-text-ribbon__group" aria-label={RICH_TEXT_LABELS.fontSection}>
        <span className="delpi-ui-rich-text-ribbon__legend">{RICH_TEXT_LABELS.fontSection}</span>
        <div className="delpi-ui-rich-text-ribbon__rows">
          <div className="delpi-ui-rich-text-ribbon__row">
            <FormSelectControl
              value={fontFamily}
              onChange={(value) => {
                setFontFamily(value);
                run(() => applyRichTextFontFamily(editor, value));
              }}
              options={RICH_TEXT_FONT_FAMILIES.map((font) => ({
                value: font.value,
                label: font.label,
              }))}
              disabled={disabled}
              className="delpi-ui-select--compact delpi-ui-rich-text-ribbon__font-select"
              ariaLabel={RICH_TEXT_LABELS.fontFamily}
              portalScopeClassName={portalScopeClassName}
            />
            <ComboboxNumberControl
              value={fontSize}
              onChange={(value) => {
                const next = clampRichTextFontSize(value);
                setFontSize(next);
                run(() => applyRichTextFontSize(editor, next));
              }}
              options={RICH_TEXT_FONT_SIZE_PRESETS}
              min={10}
              max={72}
              clamp={clampRichTextFontSize}
              disabled={disabled}
              square
              compact
              className="delpi-ui-rich-text-ribbon__size"
              aria-label={RICH_TEXT_LABELS.fontSize}
              portalScopeClassName={portalScopeClassName}
            />
          </div>
          <div className="delpi-ui-rich-text-ribbon__row delpi-ui-rich-text-ribbon__row--icons">
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.bold}
              ariaLabel={RICH_TEXT_LABELS.bold}
              active={boldActive}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "bold"))}
            >
              <Bold size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.italic}
              ariaLabel={RICH_TEXT_LABELS.italic}
              active={italicActive}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "italic"))}
            >
              <Italic size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.underline}
              ariaLabel={RICH_TEXT_LABELS.underline}
              active={underlineActive}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "underline"))}
            >
              <Underline size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.strikethrough}
              ariaLabel={RICH_TEXT_LABELS.strikethrough}
              active={strikeActive}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "strikeThrough"))}
            >
              <Strikethrough size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RibbonColorPicker
              label={RICH_TEXT_LABELS.textColor}
              ariaLabel={RICH_TEXT_LABELS.textColor}
              variant="text"
              value={textColor}
              disabled={disabled}
              onChange={(color) => {
                setTextColor(color);
                run(() => runRichTextCommand(editor, "foreColor", color));
              }}
              portalScopeClassName={portalScopeClassName}
            />
            <RibbonColorPicker
              label={RICH_TEXT_LABELS.highlightColor}
              ariaLabel={RICH_TEXT_LABELS.highlightColor}
              variant="fill"
              value={highlightColor}
              disabled={disabled}
              onChange={(color) => {
                setHighlightColor(color);
                run(() => runRichTextCommand(editor, "hiliteColor", color));
              }}
              portalScopeClassName={portalScopeClassName}
            />
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.clearFormatting}
              ariaLabel={RICH_TEXT_LABELS.clearFormatting}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "removeFormat"))}
            >
              <RemoveFormatting size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.heading}
              ariaLabel={RICH_TEXT_LABELS.heading}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "formatBlock", "h2"))}
            >
              <Heading2 size={15} aria-hidden="true" />
            </RichTextIconButton>
          </div>
        </div>
      </section>

      <section
        className="delpi-ui-rich-text-ribbon__group"
        aria-label={RICH_TEXT_LABELS.paragraphSection}
      >
        <span className="delpi-ui-rich-text-ribbon__legend">{RICH_TEXT_LABELS.paragraphSection}</span>
        <div className="delpi-ui-rich-text-ribbon__rows">
          <div className="delpi-ui-rich-text-ribbon__row delpi-ui-rich-text-ribbon__row--icons">
            {(
              [
                { align: "left" as const, icon: AlignLeft, label: RICH_TEXT_LABELS.alignLeft },
                { align: "center" as const, icon: AlignCenter, label: RICH_TEXT_LABELS.alignCenter },
                { align: "right" as const, icon: AlignRight, label: RICH_TEXT_LABELS.alignRight },
                { align: "justify" as const, icon: AlignJustify, label: RICH_TEXT_LABELS.alignJustify },
              ] as const
            ).map(({ align, icon: Icon, label }) => (
              <RichTextIconButton
                key={align}
                hint={label}
                ariaLabel={label}
                active={alignActive === align}
                disabled={disabled}
                onClick={() => run(() => applyRichTextAlign(editor, align as RichTextAlign))}
              >
                <Icon size={15} aria-hidden="true" />
              </RichTextIconButton>
            ))}
            <span className="delpi-ui-rich-text-ribbon__sep" aria-hidden="true" />
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.bulletList}
              ariaLabel={RICH_TEXT_LABELS.bulletList}
              active={bulletActive}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "insertUnorderedList"))}
            >
              <List size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.orderedList}
              ariaLabel={RICH_TEXT_LABELS.orderedList}
              active={orderedActive}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "insertOrderedList"))}
            >
              <ListOrdered size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.outdent}
              ariaLabel={RICH_TEXT_LABELS.outdent}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "outdent"))}
            >
              <Outdent size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.indent}
              ariaLabel={RICH_TEXT_LABELS.indent}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "indent"))}
            >
              <Indent size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.link}
              ariaLabel={RICH_TEXT_LABELS.link}
              disabled={disabled}
              onClick={() => {
                const url = window.prompt(RICH_TEXT_LABELS.linkPrompt);
                if (!url?.trim()) return;
                run(() => insertRichTextLink(editor, url.trim()));
              }}
            >
              <Link size={15} aria-hidden="true" />
            </RichTextIconButton>
            <span className="delpi-ui-rich-text-ribbon__sep" aria-hidden="true" />
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.undo}
              ariaLabel={RICH_TEXT_LABELS.undo}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "undo"))}
            >
              <Undo2 size={15} aria-hidden="true" />
            </RichTextIconButton>
            <RichTextIconButton
              hint={RICH_TEXT_LABELS.redo}
              ariaLabel={RICH_TEXT_LABELS.redo}
              disabled={disabled}
              onClick={() => run(() => runRichTextCommand(editor, "redo"))}
            >
              <Redo2 size={15} aria-hidden="true" />
            </RichTextIconButton>
          </div>
        </div>
      </section>
    </div>
  );
}
