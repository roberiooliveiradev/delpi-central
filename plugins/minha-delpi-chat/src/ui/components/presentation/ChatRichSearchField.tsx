import {
  TextField,
  textFieldBemClasses,
  type TextFieldClassNames,
} from "@delpi/plugin-ui/index";

const searchFieldClasses: TextFieldClassNames = {
  ...textFieldBemClasses("mdc-rich-search"),
  root: "mdc-rich-search",
  control: "mdc-rich-search__control",
  labelWrapper: "mdc-rich-search__label",
};

type ChatRichSearchFieldProps = {
  value: string;
  onChange: (value: string) => void;
  label: string;
  placeholder?: string;
  className?: string;
  /** Quando true, o label fica só para a11y (placeholder na UI). */
  hideLabel?: boolean;
};

export function ChatRichSearchField({
  value,
  onChange,
  label,
  placeholder,
  className,
  hideLabel = true,
}: ChatRichSearchFieldProps) {
  return (
    <TextField
      className={["mdc-rich-search-field", className].filter(Boolean).join(" ")}
      classNames={searchFieldClasses}
      hideLabel={hideLabel}
      label={label}
      onChange={onChange}
      placeholder={placeholder}
      type="search"
      value={value}
    />
  );
}
