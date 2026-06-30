import { useCallback, useState } from "react";

export function usePlanSectionEdit() {
  const [editingKeys, setEditingKeys] = useState<Set<string>>(() => new Set());

  const isEditing = useCallback((key: string) => editingKeys.has(key), [editingKeys]);

  const startEdit = useCallback((key: string) => {
    setEditingKeys((prev) => new Set(prev).add(key));
  }, []);

  const stopEdit = useCallback((key: string) => {
    setEditingKeys((prev) => {
      const next = new Set(prev);
      next.delete(key);
      return next;
    });
  }, []);

  const stopAll = useCallback(() => {
    setEditingKeys(new Set());
  }, []);

  return { isEditing, startEdit, stopEdit, stopAll };
}

export type PlanSectionEditBindings = {
  isEditing: boolean;
  onEdit: () => void;
  onCancelEdit: () => void;
};
