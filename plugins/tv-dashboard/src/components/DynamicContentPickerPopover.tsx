import {
  AnchoredPanelPortal,
  type AnchoredPanelPlacement,
} from "@delpi/plugin-ui/index";
import {
  DYNAMIC_CONTENT_KIND_CATALOG,
  dataRefToDynamicContent,
  type DynamicContentKind,
  type DynamicContentSpec,
} from "@delpi/tv-dashboard-presentation";
import { useRef, type RefObject } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { PRESERVE_TEXT_EDIT_FOCUS_ATTR } from "../utils/preserveTextEditFocus";

const H = TV_DASHBOARD_HELP_TOOLTIPS.data;
const C = TV_DASHBOARD_HELP_TOOLTIPS.dynamicContent;

export type DynamicContentFieldOption = {
  field: string;
  label: string;
};

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  anchorRef: RefObject<HTMLElement | null>;
  kind: DynamicContentKind;
  onKindChange: (kind: DynamicContentKind) => void;
  fieldOptions: DynamicContentFieldOption[];
  hasDataSource: boolean;
  onPick: (spec: DynamicContentSpec) => void;
  onLinkOrOpenCatalog: () => void;
  preferredPlacement?: AnchoredPanelPlacement;
};

/**
 * Picker canônico do atalho `{ }` — kinds de conteúdo dinâmico;
 * `data_field` lista campos do modelo de dados ligado.
 */
export function DynamicContentPickerPopover({
  open,
  onOpenChange,
  anchorRef,
  kind,
  onKindChange,
  fieldOptions,
  hasDataSource,
  onPick,
  onLinkOrOpenCatalog,
  preferredPlacement = "bottom",
}: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  if (!open) return null;

  const dismiss = () => onOpenChange(false);
  const activeKind = DYNAMIC_CONTENT_KIND_CATALOG.find((item) => item.kind === kind);

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      density="compact"
      preferredPlacement={preferredPlacement}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      className="td-dynamic-content-picker"
      role="dialog"
      aria-label={C.pickerTitle}
      onDismiss={dismiss}
    >
      <div
        className="td-dynamic-content-picker__panel"
        {...{ [PRESERVE_TEXT_EDIT_FOCUS_ATTR]: "" }}
        onMouseDown={(event) => event.preventDefault()}
      >
        <p className="td-dynamic-content-picker__title">{C.pickerTitle}</p>
        <p className="td-dynamic-content-picker__hint">{H.insertFieldAtCursor}</p>
        <div className="td-dynamic-content-picker__kinds" role="tablist" aria-label={C.kindsLabel}>
          {DYNAMIC_CONTENT_KIND_CATALOG.map((item) => (
            <button
              key={item.kind}
              type="button"
              role="tab"
              aria-selected={kind === item.kind}
              className={[
                "td-dynamic-content-picker__kind",
                kind === item.kind ? "td-dynamic-content-picker__kind--active" : "",
                !item.implemented ? "td-dynamic-content-picker__kind--soon" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onKindChange(item.kind)}
            >
              <span className="td-dynamic-content-picker__kind-label">{item.label}</span>
              {!item.implemented ? (
                <span className="td-dynamic-content-picker__badge">{C.comingSoon}</span>
              ) : null}
            </button>
          ))}
        </div>
        <p className="td-dynamic-content-picker__kind-desc">{activeKind?.description}</p>

        {kind === "data_field" ? (
          <div className="td-dynamic-content-picker__fields">
            {!hasDataSource ? (
              <div className="td-dynamic-content-picker__empty">
                <p className="td-subtitle">{C.needSource}</p>
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--primary"
                  onClick={() => {
                    onLinkOrOpenCatalog();
                    dismiss();
                  }}
                >
                  {C.linkSource}
                </button>
              </div>
            ) : fieldOptions.length === 0 ? (
              <p className="td-subtitle">{C.noFields}</p>
            ) : (
              <ul className="td-dynamic-content-picker__list">
                {fieldOptions.map((option) => (
                  <li key={option.field}>
                    <button
                      type="button"
                      className="td-dynamic-content-picker__field"
                      onClick={() => {
                        onPick(
                          dataRefToDynamicContent({
                            field: option.field,
                            format: "number",
                            label: option.label,
                          }),
                        );
                        dismiss();
                      }}
                    >
                      <span className="td-dynamic-content-picker__field-label">{option.label}</span>
                      <span className="td-dynamic-content-picker__field-key">{option.field}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : (
          <p className="td-subtitle td-dynamic-content-picker__scaffold">{C.scaffoldBody}</p>
        )}
      </div>
    </AnchoredPanelPortal>
  );
}
