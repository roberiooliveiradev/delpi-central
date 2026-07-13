type EmptyStateProps = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="ip-empty-state" role="status">
      <h3 className="ip-empty-state__title">{title}</h3>
      <p className="ip-empty-state__description">{description}</p>
    </div>
  );
}
