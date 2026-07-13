export function CatalogStub({
  name,
  note,
}: {
  name: string;
  note?: string;
}) {
  return (
    <div className="puc-sandbox-notice" role="note">
      <strong>{name}</strong>
      <p>
        {note ??
          "Demo interativa ainda não montada com fixtures. O export existe no pacote — estenda src/catalog/demos/."}
      </p>
    </div>
  );
}
