import { useCallback, useMemo, useState } from "react";

export function useSectionEdit() {
  const [editingKeys, setEditingKeys] = useState<Set<string>>(() => new Set());

  const isEditing = useCallback((key: string) => editingKeys.has(key), [editingKeys]);

  const startEdit = useCallback((key: string) => {
    setEditingKeys((current) => new Set(current).add(key));
  }, []);

  const cancelEdit = useCallback((key: string) => {
    setEditingKeys((current) => {
      const next = new Set(current);
      next.delete(key);
      return next;
    });
  }, []);

  const stopEdit = useCallback((key: string) => {
    cancelEdit(key);
  }, [cancelEdit]);

  return useMemo(
    () => ({ isEditing, startEdit, cancelEdit, stopEdit }),
    [cancelEdit, isEditing, startEdit, stopEdit]
  );
}
