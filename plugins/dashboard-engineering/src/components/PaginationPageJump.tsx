import { useEffect, useId, useState } from "react";

import { ENGINEERING_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  parsePageJumpInput,
  type PageJumpValidationReason,
} from "../utils/paginationPages";
import { HelpTooltip } from "@delpi/plugin-ui";

type PaginationPageJumpProps = {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
};

function resolveJumpErrorMessage(
  reason: PageJumpValidationReason,
  totalPages: number,
): string {
  switch (reason) {
    case "empty":
      return ENGINEERING_HELP_TOOLTIPS.pagination.jumpEmpty;
    case "invalid":
      return ENGINEERING_HELP_TOOLTIPS.pagination.jumpInvalid;
    case "below_min":
      return ENGINEERING_HELP_TOOLTIPS.pagination.jumpBelowMin;
    case "above_max":
      return `A página máxima é ${totalPages}.`;
    default: {
      const _exhaustive: never = reason;
      return _exhaustive;
    }
  }
}

export function PaginationPageJump({
  page,
  totalPages,
  onPageChange,
}: PaginationPageJumpProps) {
  const inputId = useId();
  const errorId = `${inputId}-error`;
  const [draft, setDraft] = useState(String(page));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(String(page));
    setError(null);
  }, [page]);

  const commitJump = () => {
    const result = parsePageJumpInput(draft, totalPages);

    if (!result.ok) {
      setError(resolveJumpErrorMessage(result.reason, totalPages));
      return;
    }

    setError(null);
    setDraft(String(result.page));

    if (result.page !== page) {
      onPageChange(result.page);
    }
  };

  return (
    <div className="ds-pagination__jump">
      <label className="ds-pagination__jump-field" htmlFor={inputId}>
        <span className="ds-pagination__jump-label">Ir para</span>
        <input
          id={inputId}
          className={
            error
              ? "ds-pagination__jump-input ds-pagination__jump-input--invalid"
              : "ds-pagination__jump-input"
          }
          type="text"
          inputMode="numeric"
          autoComplete="off"
          value={draft}
          aria-label="Ir para página"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          onChange={(event) => {
            setDraft(event.target.value);
            if (error) {
              setError(null);
            }
          }}
          onBlur={commitJump}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commitJump();
            }
          }}
        />
      </label>
      <HelpTooltip
        content={ENGINEERING_HELP_TOOLTIPS.pagination.jump}
        ariaLabel="Ajuda: ir para página"
        className="ds-pagination__jump-help"
      />
      {error ? (
        <span id={errorId} className="ds-pagination__jump-error" role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
}
