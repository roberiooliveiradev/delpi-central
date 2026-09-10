type DetailCommandChipsProps = {
  commands: string[];
  emptyLabel?: string;
};

export function DetailCommandChips({
  commands,
  emptyLabel = "Sem comandos.",
}: DetailCommandChipsProps) {
  if (commands.length === 0) {
    return <p className="pp-muted">{emptyLabel}</p>;
  }
  return (
    <ul className="pp-detail-chip-list" aria-label="Comandos do driver">
      {commands.map((command) => (
        <li key={command} className="pp-detail-chip">
          <code>{command}</code>
        </li>
      ))}
    </ul>
  );
}
