import type { ProductionPulseRoute } from "../../constants/routes";
import type { ProductionPulsePermissionFlags } from "../../constants/permissions";
import { OperatorDevicePicker } from "./OperatorDevicePicker";
import { OperatorDeviceSurfacePage } from "./OperatorDeviceSurfacePage";
import { OperatorPlacementHub } from "./OperatorPlacementHub";

type OperatorPageProps = {
  route: Extract<
    ProductionPulseRoute,
    { kind: "operatorHub" | "operatorPicker" | "operatorDevice" }
  >;
  permissions: ProductionPulsePermissionFlags;
};

export function OperatorPage({ route, permissions }: OperatorPageProps) {
  if (route.kind === "operatorHub") {
    return (
      <OperatorPlacementHub
        branch={route.branch}
        anchorType={route.anchorType}
        search={route.search}
        permissions={permissions}
      />
    );
  }

  if (route.kind === "operatorPicker") {
    return (
      <OperatorDevicePicker
        placementKey={route.placementKey}
        branch={route.branch}
        permissions={permissions}
      />
    );
  }

  return (
    <OperatorDeviceSurfacePage
      deviceId={route.deviceId}
      branch={route.branch}
      placementKey={route.placementKey}
      permissions={permissions}
    />
  );
}
