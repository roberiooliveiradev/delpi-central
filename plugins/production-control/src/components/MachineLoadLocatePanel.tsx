import { useId } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { Search, X } from "lucide-react";

import { MachineLoadLocateResults } from "./MachineLoadLocateResults";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { MachineLoadLocatePayload, MachineLoadLocateStop } from "../types";

type Props = {
  draftQuery: string;
  onDraftQueryChange: (value: string) => void;
  onSearch: (query: string) => void;
  onClear: () => void;
  loading: boolean;
  error: string | null;
  result: MachineLoadLocatePayload | null;
  onGoToStop: (stop: MachineLoadLocateStop) => void;
};

export function MachineLoadLocatePanel({
  draftQuery,
  onDraftQueryChange,
  onSearch,
  onClear,
  loading,
  error,
  result,
  onGoToStop,
}: Props) {
  const fieldId = useId();
  const open = Boolean(result) || Boolean(error) || loading;

  return (
    <div className="ppc-locate">
      <form
        className="ppc-locate__form"
        onSubmit={(event) => {
          event.preventDefault();
          onSearch(draftQuery);
        }}
      >
        <label className="ppc-locate__label" htmlFor={fieldId}>
          {copy.machineLoad.locate.label}
          <HelpTooltip content={helpTooltips.machineLoadLocate} />
        </label>
        <div className="ppc-locate__field">
          <Search size={16} strokeWidth={1.75} aria-hidden className="ppc-locate__icon" />
          <input
            id={fieldId}
            type="search"
            value={draftQuery}
            onChange={(event) => onDraftQueryChange(event.target.value)}
            placeholder={copy.machineLoad.locate.placeholder}
            autoComplete="off"
            spellCheck={false}
          />
          <button type="submit" className="ppc-locate__submit" disabled={loading}>
            {loading ? copy.machineLoad.locate.searching : copy.machineLoad.locate.search}
          </button>
        </div>
      </form>

      {open ? (
        <section className="ppc-locate__panel">
          <header className="ppc-locate__panel-head">
            <div>
              <p className="ppc-locate__eyebrow">{copy.machineLoad.locate.panelTitle}</p>
              {result?.query ? <h2 className="ppc-locate__heading">{result.query}</h2> : null}
            </div>
            <button type="button" className="ppc-locate__close" onClick={onClear} title={copy.machineLoad.locate.close}>
              <X size={16} strokeWidth={1.75} aria-hidden />
              <span>{copy.machineLoad.locate.close}</span>
            </button>
          </header>
          <MachineLoadLocateResults
            loading={loading}
            error={error}
            result={result}
            onGoToStop={onGoToStop}
          />
        </section>
      ) : null}
    </div>
  );
}
