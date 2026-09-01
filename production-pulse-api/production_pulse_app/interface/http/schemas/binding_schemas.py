from pydantic import BaseModel, ConfigDict, Field


class DeviceBindingBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    anchor_type: str = Field(alias="anchorType")
    work_center_code: str | None = Field(default=None, alias="workCenterCode")
    work_center_name: str | None = Field(default=None, alias="workCenterName")
    machine_code: str | None = Field(default=None, alias="machineCode")
    machine_label: str | None = Field(default=None, alias="machineLabel")
    equipment_label: str | None = Field(default=None, alias="equipmentLabel")
    area_label: str | None = Field(default=None, alias="areaLabel")
    resource_code: str | None = Field(default=None, alias="resourceCode")
    tool_code: str | None = Field(default=None, alias="toolCode")
    notes: str | None = None
