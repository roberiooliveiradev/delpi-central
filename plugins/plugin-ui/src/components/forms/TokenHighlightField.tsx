import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  type FocusEvent,
  type InputHTMLAttributes,
  type KeyboardEvent,
  type ReactNode,
  type Ref,
} from "react";

import {
  formFieldShellBemClasses,
  FormFieldShell,
  type FormFieldShellClassNames,
} from "./FormFieldShell";
import {
  mergeClassNames,
  NATIVE_CONTROL_CLASS,
  NATIVE_CONTROL_TEXTAREA_CLASS,
} from "./nativeControlClasses";
import { delpiUiClass } from "../../utils/delpiUiClass";

/** Segmento do espelho de destaque: `token` = ocorrência exata de `tokens`. */
export type TokenHighlightSegment = {
  text: string;
  token: boolean;
};

/**
 * Divide `value` em segmentos texto/etiqueta. Casa só ocorrências exatas de
 * `tokens` (varredura esquerda→direita; empates resolvidos pelo token mais
 * longo e depois pela ordem da lista). Função pura — testável sem DOM.
 */
export function splitTokenHighlightSegments(
  value: string,
  tokens: readonly string[],
): TokenHighlightSegment[] {
  const validTokens = tokens.filter((token) => token.length > 0);
  if (value.length === 0 || validTokens.length === 0) {
    return value.length === 0 ? [] : [{ text: value, token: false }];
  }

  const segments: TokenHighlightSegment[] = [];
  let cursor = 0;
  let plain = "";

  while (cursor < value.length) {
    let matched = "";
    for (const token of validTokens) {
      if (token.length > matched.length && value.startsWith(token, cursor)) {
        matched = token;
      }
    }
    if (matched.length === 0) {
      plain += value[cursor];
      cursor += 1;
      continue;
    }
    if (plain.length > 0) {
      segments.push({ text: plain, token: false });
      plain = "";
    }
    segments.push({ text: matched, token: true });
    cursor += matched.length;
  }

  if (plain.length > 0) segments.push({ text: plain, token: false });
  return segments;
}

export type TokenHighlightFieldClassNames = {
  shell: FormFieldShellClassNames;
  root: string;
  stack: string;
  backdrop: string;
  mirror: string;
  mark: string;
  control: string;
  error: string;
};

/** Classes BEM `{prefix}-token-highlight-field*` + canônicas `delpi-ui-token-highlight-field*`. */
export function tokenHighlightFieldBemClasses(prefix: string): TokenHighlightFieldClassNames {
  const dual = (suffix: string) =>
    delpiUiClass(
      `${prefix}-token-highlight-field${suffix}`,
      `delpi-ui-token-highlight-field${suffix}`,
    );
  return {
    shell: formFieldShellBemClasses(prefix),
    root: dual(""),
    stack: dual("__stack"),
    backdrop: dual("__backdrop"),
    mirror: dual("__mirror"),
    mark: dual("__mark"),
    control: dual("__control"),
    error: dual("__error"),
  };
}

type NativeControlElement = HTMLInputElement | HTMLTextAreaElement;

export type TokenHighlightFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  /** Marcadores destacados (ocorrência exata, ex.: `["{cliente}", "{data}"]`). */
  tokens: readonly string[];
  classNames: TokenHighlightFieldClassNames;
  hint?: string;
  error?: string;
  multiline?: boolean;
  rows?: number;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  /** Ocupa a linha inteira do grid do FormFieldShell (`span-2`). */
  fullWidth?: boolean;
  placeholder?: string;
  maxLength?: number;
  name?: string;
  autoComplete?: InputHTMLAttributes<HTMLInputElement>["autoComplete"];
  spellCheck?: boolean;
  inputMode?: InputHTMLAttributes<HTMLInputElement>["inputMode"];
  /** Ref do controle nativo — o host pode ler/mover `selectionStart` para
   * inserir um marcador na posição do cursor. */
  inputRef?: Ref<NativeControlElement>;
  className?: string;
  onFocus?: (event: FocusEvent<NativeControlElement>) => void;
  onBlur?: (event: FocusEvent<NativeControlElement>) => void;
  onKeyDown?: (event: KeyboardEvent<NativeControlElement>) => void;
  "aria-label"?: string;
  "aria-labelledby"?: string;
  "aria-describedby"?: string;
  "aria-details"?: string;
  "aria-invalid"?: boolean;
};

/**
 * `<input>`/`<textarea>` nativo com camada `aria-hidden` atrás do texto que
 * desenha o fundo do campo e destaca ocorrências exatas de `tokens`
 * (`<mark>` sem largura extra). O espelho copia as métricas computadas do
 * controle (fonte, padding, borda, quebra) e segue a rolagem — alinhamento
 * caractere a caractere, inclusive com scrollbar e redimensionamento.
 */
export function TokenHighlightField({
  id,
  label,
  value,
  onChange,
  tokens,
  classNames,
  hint,
  error,
  multiline = false,
  rows,
  disabled = false,
  readOnly = false,
  required = false,
  fullWidth = false,
  placeholder,
  maxLength,
  name,
  autoComplete,
  spellCheck,
  inputMode,
  inputRef,
  className,
  onFocus,
  onBlur,
  onKeyDown,
  "aria-label": ariaLabel,
  "aria-labelledby": ariaLabelledBy,
  "aria-describedby": ariaDescribedBy,
  "aria-details": ariaDetails,
  "aria-invalid": ariaInvalid,
}: TokenHighlightFieldProps) {
  const controlRef = useRef<NativeControlElement | null>(null);
  const backdropRef = useRef<HTMLDivElement | null>(null);
  const mirrorRef = useRef<HTMLDivElement | null>(null);

  const setControlRef = useCallback(
    (element: NativeControlElement | null) => {
      controlRef.current = element;
      if (typeof inputRef === "function") inputRef(element);
      else if (inputRef) inputRef.current = element;
    },
    [inputRef],
  );

  /** Copia métricas computadas do controle para o espelho/backdrop e
   * sincroniza a rolagem. Tolerante a ambiente sem layout (jsdom). */
  const syncMirror = useCallback(() => {
    const control = controlRef.current;
    const mirror = mirrorRef.current;
    const backdrop = backdropRef.current;
    if (!control || !mirror || !backdrop) return;
    const cs = getComputedStyle(control);

    mirror.style.fontFamily = cs.fontFamily;
    mirror.style.fontSize = cs.fontSize;
    mirror.style.fontWeight = cs.fontWeight;
    mirror.style.fontStyle = cs.fontStyle;
    mirror.style.lineHeight = cs.lineHeight;
    mirror.style.letterSpacing = cs.letterSpacing;
    mirror.style.wordSpacing = cs.wordSpacing;
    mirror.style.textTransform = cs.textTransform;
    mirror.style.tabSize = cs.tabSize;
    mirror.style.overflowWrap = cs.overflowWrap;
    mirror.style.wordBreak = cs.wordBreak;
    mirror.style.textAlign = cs.textAlign;
    mirror.style.boxSizing = cs.boxSizing;
    mirror.style.paddingTop = cs.paddingTop;
    mirror.style.paddingRight = cs.paddingRight;
    mirror.style.paddingBottom = cs.paddingBottom;
    mirror.style.paddingLeft = cs.paddingLeft;
    mirror.style.top = cs.borderTopWidth;
    mirror.style.left = cs.borderLeftWidth;

    backdrop.style.borderRadius = cs.borderRadius;

    if (multiline && control.clientWidth > 0) {
      mirror.style.width = `${control.clientWidth}px`;
    }

    mirror.style.transform = `translate(${-control.scrollLeft}px, ${-control.scrollTop}px)`;
  }, [multiline]);

  useLayoutEffect(() => {
    syncMirror();
  });

  useEffect(() => {
    window.addEventListener("resize", syncMirror);
    return () => window.removeEventListener("resize", syncMirror);
  }, [syncMirror]);

  const errorId = `${id}-error`;
  const describedBy =
    [error ? errorId : null, ariaDescribedBy].filter(Boolean).join(" ") || undefined;
  const invalid = ariaInvalid ?? (error ? true : undefined);

  const segments = splitTokenHighlightSegments(value, tokens);
  const trailingSpace = value.endsWith("\n") || value.endsWith("\r") ? " " : "";

  const sharedControlProps = {
    id,
    className: mergeClassNames(
      NATIVE_CONTROL_CLASS,
      multiline ? NATIVE_CONTROL_TEXTAREA_CLASS : undefined,
      classNames.control,
    ),
    value,
    disabled,
    required: required || undefined,
    "aria-required": required || undefined,
    "aria-invalid": invalid,
    "aria-label": ariaLabel,
    "aria-labelledby": ariaLabelledBy,
    "aria-describedby": describedBy,
    "aria-details": ariaDetails,
    placeholder,
    maxLength,
    name,
    autoComplete,
    spellCheck,
    inputMode,
    onFocus,
    onBlur,
    onKeyDown,
    onScroll: syncMirror,
    onPointerUp: syncMirror,
    onChange: (event: { target: { value: string } }) => onChange(event.target.value),
  };

  const control = multiline ? (
    <textarea
      {...sharedControlProps}
      ref={setControlRef}
      rows={rows}
      readOnly={readOnly}
    />
  ) : (
    <input
      {...sharedControlProps}
      ref={setControlRef}
      type="text"
      readOnly={readOnly}
    />
  );

  const afterControl: ReactNode = error ? (
    <span id={errorId} className={classNames.error} role="alert">
      {error}
    </span>
  ) : null;

  return (
    <FormFieldShell
      id={id}
      label={label}
      hint={hint}
      span={fullWidth}
      className={mergeClassNames(classNames.root, className)}
      required={required}
      afterControl={afterControl}
      classNames={classNames.shell}
    >
      <div
        className={classNames.stack}
        data-disabled={disabled || undefined}
        data-readonly={readOnly || undefined}
        data-multiline={multiline || undefined}
      >
        <div ref={backdropRef} className={classNames.backdrop} aria-hidden="true">
          <div ref={mirrorRef} className={classNames.mirror}>
            {segments.map((segment, index) =>
              segment.token ? (
                <mark key={index} className={classNames.mark}>
                  {segment.text}
                </mark>
              ) : (
                segment.text
              ),
            )}
            {trailingSpace}
          </div>
        </div>
        {control}
      </div>
    </FormFieldShell>
  );
}

export type DashboardTokenHighlightFieldProps = Omit<TokenHighlightFieldProps, "classNames">;

export function createDashboardTokenHighlightField(config: { prefix: string }) {
  const classNames = tokenHighlightFieldBemClasses(config.prefix);
  return function DashboardTokenHighlightField(props: DashboardTokenHighlightFieldProps) {
    return <TokenHighlightField classNames={classNames} {...props} />;
  };
}
