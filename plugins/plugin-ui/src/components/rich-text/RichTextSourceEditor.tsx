import { RICH_TEXT_LABELS } from "./richTextLabels";

export type RichTextSourceEditorProps = {
  value: string;
  onChange: (next: string) => void;
  minHeight?: number;
  disabled?: boolean;
};

/** Textarea monoespaçado para edição da fonte HTML do rich text. */
export function RichTextSourceEditor({
  value,
  onChange,
  minHeight = 200,
  disabled = false,
}: RichTextSourceEditorProps) {
  return (
    <div className="delpi-ui-rich-text__source-wrap">
      <p className="delpi-ui-rich-text__source-hint" role="note">
        {RICH_TEXT_LABELS.sourceHint}
      </p>
      <textarea
        className="delpi-ui-rich-text__source"
        style={{ minHeight }}
        value={value}
        disabled={disabled}
        spellCheck={false}
        aria-label={RICH_TEXT_LABELS.sourceEditor}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
