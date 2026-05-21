import {
  appendStrategicIndicatorsFiltersToPath,
  type StrategicIndicatorsFilterState,
} from "./strategicIndicatorsFilterUrl";

export function navigateStrategicIndicators(
  path: string,
  filterState?: StrategicIndicatorsFilterState,
): void {
  if (typeof window === "undefined") {
    return;
  }

  const target = appendStrategicIndicatorsFiltersToPath(path, filterState);
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;

  if (current === target) {
    return;
  }

  window.history.pushState(window.history.state, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
