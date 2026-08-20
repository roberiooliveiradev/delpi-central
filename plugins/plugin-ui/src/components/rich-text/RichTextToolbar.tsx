import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Bold,
  CodeXml,
  FileText,
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
  Table2,
  Type,
  Underline,
  Undo2,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";

import { TableInsertCatalogPanel } from "../charts/TableInsertCatalogPanel";
import { FormSelectControl } from "../forms/FormSelectControl";
import { NumberStepperControl } from "../forms/NumberStepperControl";
import { HintAction } from "../help/HintAction";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { RibbonColorPicker } from "../shape/RibbonColorPicker";
import {
  applyRichTextAlign,
  applyRichTextFontFamily,
  applyRichTextFontSize,
  getRichTextSelectionRange,
  queryRichTextAlign,
  queryRichTextCommandState,
  queryRichTextFontSize,
  restoreRichTextSelection,
  runRichTextCommand,
  type RichTextAlign,
} from "./richTextCommands";
import {
  clampRichTextFontSize,
  RICH_TEXT_FONT_FAMILIES,
  RICH_TEXT_FONT_SIZE_DEFAULT,
  RICH_TEXT_FONT_SIZE_MAX,
  RICH_TEXT_FONT_SIZE_MIN,
  RICH_TEXT_FONT_SIZE_PRESETS,
  RICH_TEXT_FONT_SIZE_STEP,
} from "./richTextConfig";
import { RICH_TEXT_LABELS } from "./richTextLabels";
import { insertRichTextTable } from "./richTextTable";

export type RichTextSourceKind = "visual" | "html" | "markdown";

type Props = {
  editorRef: RefObject<HTMLDivElement | null>;
  disabled?: boolean;
  /** Modo fonte (HTML/Markdown) — desabilita formatação WYSIWYG. */
  sourceKind?: RichTextSourceKind;
  onSourceKindChange?: (kind: RichTextSourceKind) => void;
  onFormatted: () => void;
  /** Abre o diálogo de link do editor (ModalShell) — sem prompt do navegador. */
  onRequestLink: () => void;
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

function RibbonSep() {
  return <span className="delpi-ui-rich-text-ribbon__sep" aria-hidden="true" />;
}

export function RichTextToolbar({
  editorRef,
  disabled = false,
  sourceKind = "visual",
  onSourceKindChange,
  onFormatted,
  onRequestLink,
  portalScopeClassName,
}: Props) {
  const [fontFamily, setFontFamily] = useState(RICH_TEXT_FONT_FAMILIES[0].value);
  const [fontSize, setFontSize] = useState(RICH_TEXT_FONT_SIZE_DEFAULT);
  const [textColor, setTextColor] = useState("#111111");
  const [highlightColor, setHighlightColor] = useState("#fef08a");
  const [formatTick, setFormatTick] = useState(0);
  const [tableMenuOpen, setTableMenuOpen] = useState(false);
  const savedRangeRef = useRef<Range | null>(null);
  const tableAnchorRef = useRef<HTMLDivElement>(null);
  const tablePanelRef = useRef<HTMLDivElement>(null);
  const sourceMode = sourceKind !== "visual";
  const formatDisabled = disabled || sourceMode;

  const refreshFormatState = useCallback(() => {
    setFormatTick((value) => value + 1);
    const editor = editorRef.current;
    const size = queryRichTextFontSize(editor);
    if (size != null) setFontSize(clampRichTextFontSize(size));
  }, [editorRef]);

  useEffect(() => {
    if (sourceMode) {
      savedRangeRef.current = null;
      return;
    }

    const editor = editorRef.current;
    if (!editor) return;

    const persistSelection = () => {
      const live = editorRef.current;
      if (!live) return;
      const range = getRichTextSelectionRange(live);
      if (range) savedRangeRef.current = range;
    };

    const handleSelection = () => {
      persistSelection();
      refreshFormatState();
    };

    document.addEventListener("selectionchange", persistSelection);
    editor.addEventListener("keyup", handleSelection);
    editor.addEventListener("mouseup", handleSelection);
    editor.addEventListener("focus", handleSelection);
    return () => {
      document.removeEventListener("selectionchange", persistSelection);
      editor.removeEventListener("keyup", handleSelection);
      editor.removeEventListener("mouseup", handleSelection);
      editor.removeEventListener("focus", handleSelection);
    };
  }, [editorRef, refreshFormatState, sourceMode]);

  void formatTick;

  const boldActive = queryRichTextCommandState("bold");
  const italicActive = queryRichTextCommandState("italic");
  const underlineActive = queryRichTextCommandState("underline");
  const strikeActive = queryRichTextCommandState("strikeThrough");
  const bulletActive = queryRichTextCommandState("insertUnorderedList");
  const orderedActive = queryRichTextCommandState("insertOrderedList");
  const alignActive = queryRichTextAlign(editorRef.current);

  function withEditor(action: (editor: HTMLElement) => void) {
    if (formatDisabled) return;
    const editor = editorRef.current;
    if (!editor) return;
    restoreRichTextSelection(editor, savedRangeRef.current);
    action(editor);
    const next = getRichTextSelectionRange(editor);
    if (next) savedRangeRef.current = next;
    onFormatted();
    refreshFormatState();
  }

  function applyFontSize(nextRaw: number) {
    const next = clampRichTextFontSize(nextRaw);
    setFontSize(next);
    withEditor((editor) => applyRichTextFontSize(editor, next));
    // Reafirma após refreshFormatState: HTML colado pode mentir no computed style.
    setFontSize(next);
  }

  return (
    <div className="delpi-ui-rich-text-ribbon" role="toolbar" aria-label={RICH_TEXT_LABELS.toolbar}>
      <section className="delpi-ui-rich-text-ribbon__cluster" aria-label={RICH_TEXT_LABELS.fontSection}>
        <FormSelectControl
          value={fontFamily}
          onChange={(value) => {
            setFontFamily(value);
            withEditor((editor) => applyRichTextFontFamily(editor, value));
          }}
          options={RICH_TEXT_FONT_FAMILIES.map((font) => ({
            value: font.value,
            label: font.label,
          }))}
          disabled={formatDisabled}
          className="delpi-ui-select--compact delpi-ui-rich-text-ribbon__font-select"
          ariaLabel={RICH_TEXT_LABELS.fontFamily}
          portalScopeClassName={portalScopeClassName}
        />
        <NumberStepperControl
          value={fontSize}
          onChange={applyFontSize}
          onStepDown={() => applyFontSize(fontSize - RICH_TEXT_FONT_SIZE_STEP)}
          onStepUp={() => applyFontSize(fontSize + RICH_TEXT_FONT_SIZE_STEP)}
          options={RICH_TEXT_FONT_SIZE_PRESETS}
          min={RICH_TEXT_FONT_SIZE_MIN}
          max={RICH_TEXT_FONT_SIZE_MAX}
          clamp={clampRichTextFontSize}
          disabled={formatDisabled}
          square={false}
          compact
          className="delpi-ui-rich-text-ribbon__size"
          aria-label={RICH_TEXT_LABELS.fontSize}
          groupAriaLabel={RICH_TEXT_LABELS.fontSize}
          stepDownAriaLabel={RICH_TEXT_LABELS.fontSizeDecrease}
          stepUpAriaLabel={RICH_TEXT_LABELS.fontSizeIncrease}
          portalScopeClassName={portalScopeClassName}
        />
      </section>

      <RibbonSep />

      <section className="delpi-ui-rich-text-ribbon__cluster" aria-label={RICH_TEXT_LABELS.fontSection}>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.bold}
          ariaLabel={RICH_TEXT_LABELS.bold}
          active={boldActive}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "bold"))}
        >
          <Bold size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.italic}
          ariaLabel={RICH_TEXT_LABELS.italic}
          active={italicActive}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "italic"))}
        >
          <Italic size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.underline}
          ariaLabel={RICH_TEXT_LABELS.underline}
          active={underlineActive}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "underline"))}
        >
          <Underline size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.strikethrough}
          ariaLabel={RICH_TEXT_LABELS.strikethrough}
          active={strikeActive}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "strikeThrough"))}
        >
          <Strikethrough size={15} aria-hidden="true" />
        </RichTextIconButton>
        <span
          className={
            formatDisabled ? "delpi-ui-rich-text-ribbon__color--disabled" : undefined
          }
          aria-disabled={formatDisabled || undefined}
        >
          <RibbonColorPicker
            label={RICH_TEXT_LABELS.textColor}
            ariaLabel={RICH_TEXT_LABELS.textColor}
            variant="text"
            value={textColor}
            className="delpi-ui-color-picker-trigger--inline"
            onChange={(color) => {
              if (formatDisabled) return;
              setTextColor(color);
              withEditor((editor) => runRichTextCommand(editor, "foreColor", color));
            }}
          />
        </span>
        <span
          className={
            formatDisabled ? "delpi-ui-rich-text-ribbon__color--disabled" : undefined
          }
          aria-disabled={formatDisabled || undefined}
        >
          <RibbonColorPicker
            label={RICH_TEXT_LABELS.highlightColor}
            ariaLabel={RICH_TEXT_LABELS.highlightColor}
            variant="fill"
            value={highlightColor}
            className="delpi-ui-color-picker-trigger--inline"
            onChange={(color) => {
              if (formatDisabled) return;
              setHighlightColor(color);
              withEditor((editor) => runRichTextCommand(editor, "hiliteColor", color));
            }}
          />
        </span>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.clearFormatting}
          ariaLabel={RICH_TEXT_LABELS.clearFormatting}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "removeFormat"))}
        >
          <RemoveFormatting size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.heading}
          ariaLabel={RICH_TEXT_LABELS.heading}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "formatBlock", "h2"))}
        >
          <Heading2 size={15} aria-hidden="true" />
        </RichTextIconButton>
      </section>

      <RibbonSep />

      <section
        className="delpi-ui-rich-text-ribbon__cluster"
        aria-label={RICH_TEXT_LABELS.paragraphSection}
      >
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
            disabled={formatDisabled}
            onClick={() =>
              withEditor((editor) => applyRichTextAlign(editor, align as RichTextAlign))
            }
          >
            <Icon size={15} aria-hidden="true" />
          </RichTextIconButton>
        ))}
        <RibbonSep />
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.bulletList}
          ariaLabel={RICH_TEXT_LABELS.bulletList}
          active={bulletActive}
          disabled={formatDisabled}
          onClick={() =>
            withEditor((editor) => runRichTextCommand(editor, "insertUnorderedList"))
          }
        >
          <List size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.orderedList}
          ariaLabel={RICH_TEXT_LABELS.orderedList}
          active={orderedActive}
          disabled={formatDisabled}
          onClick={() =>
            withEditor((editor) => runRichTextCommand(editor, "insertOrderedList"))
          }
        >
          <ListOrdered size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.outdent}
          ariaLabel={RICH_TEXT_LABELS.outdent}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "outdent"))}
        >
          <Outdent size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.indent}
          ariaLabel={RICH_TEXT_LABELS.indent}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "indent"))}
        >
          <Indent size={15} aria-hidden="true" />
        </RichTextIconButton>
      </section>

      <RibbonSep />

      <section
        className="delpi-ui-rich-text-ribbon__cluster"
        aria-label={RICH_TEXT_LABELS.insertSection}
      >
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.link}
          ariaLabel={RICH_TEXT_LABELS.link}
          disabled={formatDisabled}
          onClick={onRequestLink}
        >
          <Link size={15} aria-hidden="true" />
        </RichTextIconButton>
        <div ref={tableAnchorRef} className="delpi-ui-rich-text-ribbon__dropdown">
          <RichTextIconButton
            hint={RICH_TEXT_LABELS.table}
            ariaLabel={RICH_TEXT_LABELS.table}
            active={tableMenuOpen}
            disabled={formatDisabled}
            onClick={() => setTableMenuOpen((open) => !open)}
          >
            <Table2 size={15} aria-hidden="true" />
          </RichTextIconButton>
          <AnchoredPanelPortal
            open={tableMenuOpen && !sourceMode}
            anchorRef={tableAnchorRef}
            panelRef={tablePanelRef}
            variant="bare"
            preferredPlacement="bottom"
            density="compact"
            role="dialog"
            aria-label={RICH_TEXT_LABELS.tableCatalog}
            portalScopeClassName={portalScopeClassName}
            onDismiss={() => setTableMenuOpen(false)}
            className="delpi-ui-rich-text-ribbon__table-portal"
          >
            <TableInsertCatalogPanel
              title={RICH_TEXT_LABELS.table}
              onSelect={(selection) => {
                setTableMenuOpen(false);
                withEditor((editor) => insertRichTextTable(editor, selection));
              }}
            />
          </AnchoredPanelPortal>
        </div>
        <RibbonSep />
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.sourceVisual}
          ariaLabel={RICH_TEXT_LABELS.sourceVisual}
          active={sourceKind === "visual"}
          disabled={disabled || !onSourceKindChange}
          onClick={() => onSourceKindChange?.("visual")}
        >
          <Type size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.sourceHtml}
          ariaLabel={RICH_TEXT_LABELS.sourceHtml}
          active={sourceKind === "html"}
          disabled={disabled || !onSourceKindChange}
          onClick={() => onSourceKindChange?.("html")}
        >
          <CodeXml size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.sourceMarkdown}
          ariaLabel={RICH_TEXT_LABELS.sourceMarkdown}
          active={sourceKind === "markdown"}
          disabled={disabled || !onSourceKindChange}
          onClick={() => onSourceKindChange?.("markdown")}
        >
          <FileText size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.undo}
          ariaLabel={RICH_TEXT_LABELS.undo}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "undo"))}
        >
          <Undo2 size={15} aria-hidden="true" />
        </RichTextIconButton>
        <RichTextIconButton
          hint={RICH_TEXT_LABELS.redo}
          ariaLabel={RICH_TEXT_LABELS.redo}
          disabled={formatDisabled}
          onClick={() => withEditor((editor) => runRichTextCommand(editor, "redo"))}
        >
          <Redo2 size={15} aria-hidden="true" />
        </RichTextIconButton>
      </section>
    </div>
  );
}
