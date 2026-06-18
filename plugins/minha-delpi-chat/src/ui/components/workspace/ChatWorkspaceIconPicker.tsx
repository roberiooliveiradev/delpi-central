import type { ReactNode } from "react";

import "./ChatWorkspaceIconPicker.css";

type ChatWorkspaceIconPickerProps = {
  options: readonly string[];
  labels: Record<string, string>;
  value: string;
  onChange: (value: string) => void;
  renderIcon: (iconName: string, size: number) => ReactNode;
  ariaLabel?: string;
};

export function ChatWorkspaceIconPicker({
  options,
  labels,
  value,
  onChange,
  renderIcon,
  ariaLabel = "Ícone",
}: ChatWorkspaceIconPickerProps) {
  return (
    <div className="mdc-chat-workspace-icon-picker" role="listbox" aria-label={ariaLabel}>
      {options.map((option) => {
        const isSelected = value === option;

        return (
          <button
            key={option}
            type="button"
            role="option"
            aria-selected={isSelected}
            className={
              isSelected
                ? "mdc-chat-workspace-icon-picker__option mdc-chat-workspace-icon-picker__option--active"
                : "mdc-chat-workspace-icon-picker__option"
            }
            onClick={() => onChange(option)}
            title={labels[option] ?? option}
          >
            {renderIcon(option, 18)}
          </button>
        );
      })}
    </div>
  );
}
