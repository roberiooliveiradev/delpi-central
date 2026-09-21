import { Search } from "lucide-react";
import { useId, type KeyboardEvent } from "react";

export type TaskSearchFieldProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  "aria-label"?: string;
  id?: string;
};

/** Campo de busca da fila. O portal filtra; o kit não consulta API. */
export function TaskSearchField({
  value,
  onChange,
  placeholder = "Buscar tarefas...",
  "aria-label": ariaLabel = "Buscar tarefas",
  id,
}: TaskSearchFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Escape" || !value) return;
    event.preventDefault();
    event.stopPropagation();
    onChange("");
  }

  return (
    <div className="delpi-ui-task-search">
      <label className="delpi-ui-task-search__label" htmlFor={fieldId}>
        {ariaLabel}
      </label>
      <span className="delpi-ui-task-search__control">
        <Search size={16} aria-hidden="true" />
        <input
          id={fieldId}
          type="search"
          value={value}
          placeholder={placeholder}
          aria-label={ariaLabel}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={onKeyDown}
        />
      </span>
    </div>
  );
}
