import { useCallback, useEffect, useState } from "react";
import { addMonths, endOfMonth, startOfMonth, subMonths } from "date-fns";

import {
  fetchBookings,
  fetchResources,
  type SchedulingBooking,
  type SchedulingResource,
} from "../api/schedulingApi";
import type { BranchCode, ResourceType } from "../constants/scheduling";

export function useSchedulingData(branch: BranchCode | null, currentDate: Date) {
  const [resources, setResources] = useState<SchedulingResource[]>([]);
  const [bookings, setBookings] = useState<SchedulingBooking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<ResourceType[]>([]);
  const [selectedResourceIds, setSelectedResourceIds] = useState<string[]>([]);

  const loadData = useCallback(async () => {
    if (!branch) return;

    setLoading(true);
    setError(null);

    try {
      const rangeStart = startOfMonth(subMonths(currentDate, 1));
      const rangeEnd = endOfMonth(addMonths(currentDate, 1));

      const [resourceData, bookingData] = await Promise.all([
        fetchResources(branch, true),
        fetchBookings(branch, rangeStart, rangeEnd),
      ]);

      setResources(resourceData);
      setBookings(bookingData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados.");
    } finally {
      setLoading(false);
    }
  }, [branch, currentDate]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const filteredResources = resources.filter((resource) => {
    if (selectedTypes.length > 0 && !selectedTypes.includes(resource.resource_type)) {
      return false;
    }
    if (selectedResourceIds.length > 0 && !selectedResourceIds.includes(resource.id)) {
      return false;
    }
    return true;
  });

  const filteredResourceIds = new Set(filteredResources.map((item) => item.id));

  const filteredBookings = bookings.filter((booking) =>
    filteredResourceIds.has(booking.resource_id),
  );

  function toggleType(type: ResourceType) {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((item) => item !== type) : [...prev, type],
    );
  }

  function toggleResource(resourceId: string) {
    setSelectedResourceIds((prev) =>
      prev.includes(resourceId)
        ? prev.filter((item) => item !== resourceId)
        : [...prev, resourceId],
    );
  }

  function clearFilters() {
    setSelectedTypes([]);
    setSelectedResourceIds([]);
  }

  return {
    resources,
    bookings: filteredBookings,
    allBookings: bookings,
    filteredResources,
    loading,
    error,
    selectedTypes,
    selectedResourceIds,
    toggleType,
    toggleResource,
    clearFilters,
    reload: loadData,
  };
}
