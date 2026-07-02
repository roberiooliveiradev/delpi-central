import { useCallback, useState } from "react";

export function useKaizenSectionEdit() {
  const [editingKeys, setEditingKeys] = useState<Set<string>>(() => new Set());

  const isEditing = useCallback((key: string) => editingKeys.has(key), [editingKeys]);

  const startEdit = useCallback((key: string) => {
    setEditingKeys((current) => {
      const next = new Set(current);
      next.add(key);
      return next;
    });
  }, []);

  const stopEdit = useCallback((key: string) => {
    setEditingKeys((current) => {
      if (!current.has(key)) return current;
      const next = new Set(current);
      next.delete(key);
      return next;
    });
  }, []);

  const stopAll = useCallback(() => setEditingKeys(new Set()), []);

  return { isEditing, startEdit, stopEdit, stopAll };
}
