type Props = {
  displayNames: string[];
};

export function RemoteSelectionFrame({ displayNames }: Props) {
  const names = [...new Set(displayNames.map((name) => name.trim()).filter(Boolean))];
  if (names.length === 0) return null;
  return (
    <div className="td-composer__remote-selection" aria-hidden="true">
      <span className="td-composer__remote-selection-label">{names.join(", ")}</span>
    </div>
  );
}

