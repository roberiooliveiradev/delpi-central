// src/ui/admin/modals/base/BackendOnlyBaseFields.tsx

export const BackendOnlyBaseFields = () => {
  return (
    <div className="hint">
      <strong>backend-only:</strong> Este plugin não possui interface visual.
      Não é necessário configurar <code>entry</code>.
    </div>
  );
};