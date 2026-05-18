export function beginStrategicIndicatorsLoad<T>(options: {
  cached: T | null;
  hasLoadedOnce: boolean;
  setValue: (value: T) => void;
  setLoading: (loading: boolean) => void;
  setRefreshing: (refreshing: boolean) => void;
}): void {
  if (options.cached) {
    options.setValue(options.cached);
    options.setRefreshing(true);
    options.setLoading(false);
    return;
  }

  if (options.hasLoadedOnce) {
    options.setRefreshing(true);
    return;
  }

  options.setLoading(true);
}
