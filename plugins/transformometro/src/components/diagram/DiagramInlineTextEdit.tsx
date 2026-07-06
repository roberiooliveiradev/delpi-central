import { useEffect, useRef, useState } from "react";

type Props = {
  value: string;
  readOnly?: boolean;
  onCommit: (next: string) => void;
  className?: string;
  inputClassName?: string;
  ariaLabel?: string;
  emptyFallback?: string;
  placeholder?: string;
};

export function DiagramInlineTextEdit({
  value,
  readOnly = false,
  onCommit,
  className,
  inputClassName,
  ariaLabel = "Editar texto",
  emptyFallback = "Texto",
  placeholder,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!editing) {
      setDraft(value);
    }
  }, [editing, value]);

  useEffect(() => {
    if (!editing) return;
    inputRef.current?.focus();
    inputRef.current?.select();
  }, [editing]);

  const commit = () => {
    const trimmed = draft.trim();
    onCommit(trimmed || value || emptyFallback);
    setEditing(false);
  };

  const cancel = () => {
    setDraft(value);
    setEditing(false);
  };

  if (readOnly) {
    return <span className={className}>{value}</span>;
  }

  if (editing) {
    return (
      <input
        ref={inputRef}
        type="text"
        className={["tm-diagram-inline-edit", inputClassName].filter(Boolean).join(" ")}
        value={draft}
        placeholder={placeholder ?? emptyFallback}
        aria-label={ariaLabel}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={commit}
        onKeyDown={(event) => {
          event.stopPropagation();
          if (event.key === "Enter") {
            event.preventDefault();
            commit();
          }
          if (event.key === "Escape") {
            event.preventDefault();
            cancel();
          }
        }}
        onMouseDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
        onDoubleClick={(event) => event.stopPropagation()}
      />
    );
  }

  return (
    <span
      className={[
        "tm-diagram-inline-edit__display",
        "tm-diagram-inline-edit__display--editable",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      onDoubleClick={(event) => {
        event.stopPropagation();
        setEditing(true);
      }}
      title="Duplo clique para editar"
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          setEditing(true);
        }
      }}
    >
      {value || emptyFallback}
    </span>
  );
}
