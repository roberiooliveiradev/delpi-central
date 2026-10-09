import { MessageComposer } from "@delpi/plugin-ui/index";

import { INTERACTION_INPUT_CHAR_LIMIT } from "../api/interactionClient";

export type DeliaComposerProps = {
  inputId: string;
  value: string;
  onChange: (value: string) => void;
  /** Explicit user intent only — never invoked programmatically. */
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
};

/**
 * DÉLIA composer — thin product wrapper over the plugin-ui
 * `MessageComposer` (single surface, write band + toolbar).
 *
 * DÉLIA owns the draft, submission, loading and error handling; the
 * shared component owns only presentation and deterministic input
 * behavior (Enter/Shift+Enter/IME, auto-grow, empty-submit guard).
 */
export function DeliaComposer({
  inputId,
  value,
  onChange,
  onSubmit,
  loading = false,
  placeholder = "Pergunte à DÉLIA…",
}: DeliaComposerProps) {
  return (
    <MessageComposer
      className="delia-composer"
      inputId={inputId}
      inputLabel="Pergunte à DÉLIA"
      value={value}
      onChange={onChange}
      onSubmit={onSubmit}
      loading={loading}
      placeholder={placeholder}
      characterLimit={INTERACTION_INPUT_CHAR_LIMIT}
      helperText="A DÉLIA pode cometer erros. Confirme informações importantes."
    />
  );
}
