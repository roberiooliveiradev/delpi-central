from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_response import (
    InspecoesEntradaHistoricoItemResponse,
)


@dataclass
class InspecoesEntradaHistoricoDetalheSummaryResponse:
    result: str
    inspection_status: str
    report_code: str
    received_date: str | None
    received_time: str | None
    report_date: str | None
    report_time: str | None
    invoice_number: str
    invoice_series: str
    invoice_item: str
    supplier_code: str
    supplier_store: str
    supplier_name: str
    product_code: str
    product_description: str | None
    lot: str
    supplier_lot: str
    quantity: float
    unit: str
    approved_quantity: float | None
    rejected_quantity: float | None
    report_justification: str
    inspector_registration: str
    inspector_name: str
    inspector_login: str
    tests_count: int
    failed_tests_count: int
    is_approved: bool
    is_rejected: bool

    @classmethod
    def from_item(
        cls,
        item: InspecoesEntradaHistoricoItemResponse,
    ) -> InspecoesEntradaHistoricoDetalheSummaryResponse:
        return cls(
            result=item.result,
            inspection_status=item.inspection_status,
            report_code=item.report_code,
            received_date=item.received_date,
            received_time=item.received_time,
            report_date=item.report_date,
            report_time=item.report_time,
            invoice_number=item.invoice_number,
            invoice_series=item.invoice_series,
            invoice_item=item.invoice_item,
            supplier_code=item.supplier_code,
            supplier_store=item.supplier_store,
            supplier_name=item.supplier_name,
            product_code=item.product_code,
            product_description=item.product_description,
            lot=item.lot,
            supplier_lot=item.supplier_lot,
            quantity=item.quantity,
            unit=item.unit,
            approved_quantity=item.approved_quantity,
            rejected_quantity=item.rejected_quantity,
            report_justification=item.report_justification,
            inspector_registration=item.inspector_registration,
            inspector_name=item.inspector_name,
            inspector_login=item.inspector_login,
            tests_count=item.tests_count,
            failed_tests_count=item.failed_tests_count,
            is_approved=item.is_approved,
            is_rejected=item.is_rejected,
        )

    def to_dict(self) -> dict:
        return {
            "result": self.result,
            "inspection_status": self.inspection_status,
            "report_code": self.report_code,
            "received_date": self.received_date,
            "received_time": self.received_time,
            "report_date": self.report_date,
            "report_time": self.report_time,
            "invoice_number": self.invoice_number,
            "invoice_series": self.invoice_series,
            "invoice_item": self.invoice_item,
            "supplier_code": self.supplier_code,
            "supplier_store": self.supplier_store,
            "supplier_name": self.supplier_name,
            "product_code": self.product_code,
            "product_description": self.product_description,
            "lot": self.lot,
            "supplier_lot": self.supplier_lot,
            "quantity": self.quantity,
            "unit": self.unit,
            "approved_quantity": self.approved_quantity,
            "rejected_quantity": self.rejected_quantity,
            "report_justification": self.report_justification,
            "inspector_registration": self.inspector_registration,
            "inspector_name": self.inspector_name,
            "inspector_login": self.inspector_login,
            "tests_count": self.tests_count,
            "failed_tests_count": self.failed_tests_count,
            "is_approved": self.is_approved,
            "is_rejected": self.is_rejected,
        }


@dataclass
class InspecoesEntradaHistoricoDetalheTestResponse:
    test_code: str
    test_name: str | None
    expected_specification: str | None
    text_specification: str | None
    nominal_value: str | None
    lower_spec_limit: str | None
    upper_spec_limit: str | None
    lower_control_limit: str | None
    upper_control_limit: str | None
    min_max_rule: str | None
    specification_unit: str | None
    text_measured_value: str | None
    numeric_measured_value: str | None
    numeric_measurement_indicator: str | None
    measured_value: str | None
    measurement_source: str | None
    result_code: str
    result: str
    measurement_date: str | None
    measurement_time: str | None
    sample_number: int | None
    laboratory: str | None
    qer_key: str | None
    sequence_number: str | None
    inspector_registration: str
    inspector_name: str
    inspector_login: str

    def to_dict(self) -> dict:
        return {
            "test_code": self.test_code,
            "test_name": self.test_name,
            "expected_specification": self.expected_specification,
            "text_specification": self.text_specification,
            "nominal_value": self.nominal_value,
            "lower_spec_limit": self.lower_spec_limit,
            "upper_spec_limit": self.upper_spec_limit,
            "lower_control_limit": self.lower_control_limit,
            "upper_control_limit": self.upper_control_limit,
            "min_max_rule": self.min_max_rule,
            "specification_unit": self.specification_unit,
            "text_measured_value": self.text_measured_value,
            "numeric_measured_value": self.numeric_measured_value,
            "numeric_measurement_indicator": self.numeric_measurement_indicator,
            "measured_value": self.measured_value,
            "measurement_source": self.measurement_source,
            "result_code": self.result_code,
            "result": self.result,
            "measurement_date": self.measurement_date,
            "measurement_time": self.measurement_time,
            "sample_number": self.sample_number,
            "laboratory": self.laboratory,
            "qer_key": self.qer_key,
            "sequence_number": self.sequence_number,
            "inspector_registration": self.inspector_registration,
            "inspector_name": self.inspector_name,
            "inspector_login": self.inspector_login,
        }


@dataclass
class InspecoesEntradaHistoricoDetalheTotalsResponse:
    tests_count: int
    approved_tests_count: int
    failed_tests_count: int

    def to_dict(self) -> dict:
        return {
            "tests_count": self.tests_count,
            "approved_tests_count": self.approved_tests_count,
            "failed_tests_count": self.failed_tests_count,
        }


@dataclass
class InspecoesEntradaHistoricoDetalheResponse:
    branch: str
    inspection_id: str
    summary: InspecoesEntradaHistoricoDetalheSummaryResponse
    tests: list[InspecoesEntradaHistoricoDetalheTestResponse]
    totals: InspecoesEntradaHistoricoDetalheTotalsResponse

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "inspection_id": self.inspection_id,
            "summary": self.summary.to_dict(),
            "tests": [test.to_dict() for test in self.tests],
            "totals": self.totals.to_dict(),
        }
