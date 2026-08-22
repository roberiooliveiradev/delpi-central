import { useMemo } from "react";

import { copy } from "../content/copy";
import {
  fetchAllDelinquencyCustomerOptions,
  type DelinquencyCustomerOption,
} from "../utils/delinquencyCustomers";
import { useAsyncResource } from "./useAsyncResource";

export function useDelinquencyCustomerOptions(params: {
  startDate: string | null;
  endDate: string | null;
}) {
  const key = useMemo(
    () => [params.startDate, params.endDate].join("|"),
    [params.endDate, params.startDate],
  );

  return useAsyncResource<DelinquencyCustomerOption[]>(
    (signal) =>
      fetchAllDelinquencyCustomerOptions({
        startDate: params.startDate,
        endDate: params.endDate,
        signal,
      }),
    [key],
    copy.delinquency.customerOptionsError,
  );
}
