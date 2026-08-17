// portal/src/ui-kit/form/SearchInput.tsx

import { forwardRef, type InputHTMLAttributes } from "react";
import { Search, X } from "lucide-react";
import { Input, type ControlSize } from "./Input";
import { Button } from "../button/Button";
import "./controls.css";
import "./SearchInput.css";

export type SearchInputProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "size" | "type"
> & {
  size?: ControlSize;
  onClear?: () => void;
};

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  function SearchInput(
    { size = "md", onClear, value, className, ...rest },
    ref,
  ) {
    const hasValue = value != null && String(value).length > 0;

    return (
      <div className={["portal-ui-search", className ?? ""].filter(Boolean).join(" ")}>
        <span className="portal-ui-search__icon" aria-hidden="true">
          <Search size={14} />
        </span>
        <Input
          ref={ref}
          type="search"
          size={size}
          value={value}
          className="portal-ui-search__input"
          {...rest}
        />
        {hasValue && onClear ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="portal-ui-search__clear"
            aria-label="Limpar busca"
            onClick={onClear}
            icon={<X size={14} />}
          />
        ) : null}
      </div>
    );
  },
);
