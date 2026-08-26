export function resolveInboxLoadingState(input: {
  loading: boolean;
  itemCount: number;
  hasError: boolean;
}): { initialLoading: boolean; refreshing: boolean } {
  const { loading, itemCount, hasError } = input;
  return {
    initialLoading: loading && itemCount === 0 && !hasError,
    refreshing: loading && itemCount > 0,
  };
}

export function resolveThreadLoadingState(input: {
  loading: boolean;
  hasRoomSnapshot: boolean;
}): { initialLoading: boolean; refreshing: boolean } {
  const { loading, hasRoomSnapshot } = input;
  return {
    initialLoading: loading && !hasRoomSnapshot,
    refreshing: loading && hasRoomSnapshot,
  };
}
