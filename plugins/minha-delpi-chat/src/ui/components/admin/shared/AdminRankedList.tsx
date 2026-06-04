type AdminRankedListItem = {
  label: string;
  value: string | number;
  key?: string;
};

type AdminRankedListProps = {
  title: string;
  items: AdminRankedListItem[];
  emptyMessage?: string;
};

export function AdminRankedList({
  title,
  items,
  emptyMessage = "Sem dados na janela.",
}: AdminRankedListProps) {
  return (
    <div className="mdc-admin-ranked-list">
      <h4>{title}</h4>
      {!items.length ? (
        <p className="mdc-chat-muted">{emptyMessage}</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.key ?? item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
