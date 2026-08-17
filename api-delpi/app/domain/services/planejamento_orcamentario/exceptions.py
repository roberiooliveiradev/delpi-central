from __future__ import annotations


class BudgetPlanningError(Exception):
    code = "budget_user_not_authorized"
    status_code = 400

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        if code:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class BudgetExerciseNotFoundError(BudgetPlanningError):
    code = "budget_exercise_not_found"
    status_code = 404


class BudgetExerciseAlreadyActiveError(BudgetPlanningError):
    code = "budget_exercise_already_active"
    status_code = 409


class BudgetExerciseInvalidDatesError(BudgetPlanningError):
    code = "budget_exercise_invalid_dates"
    status_code = 422


class BudgetExerciseInvalidTransitionError(BudgetPlanningError):
    code = "budget_exercise_invalid_transition"
    status_code = 409


class BudgetGuidanceNotFoundError(BudgetPlanningError):
    code = "budget_guidance_not_found"
    status_code = 404


class BudgetGuidanceNotPublishedError(BudgetPlanningError):
    code = "budget_guidance_not_published"
    status_code = 409


class BudgetGuidanceAlreadyPublishedError(BudgetPlanningError):
    code = "budget_guidance_already_published"
    status_code = 409


class BudgetGuidanceVersionConflictError(BudgetPlanningError):
    code = "budget_guidance_version_conflict"
    status_code = 409


class BudgetGuidanceImmutableError(BudgetPlanningError):
    code = "budget_guidance_version_conflict"
    status_code = 409


class BudgetGuidanceAcknowledgementRequiredError(BudgetPlanningError):
    code = "budget_guidance_acknowledgement_required"
    status_code = 403


class BudgetDocumentNotFoundError(BudgetPlanningError):
    code = "budget_document_not_found"
    status_code = 404


class BudgetDocumentTypeNotAllowedError(BudgetPlanningError):
    code = "budget_document_type_not_allowed"
    status_code = 422


class BudgetDocumentTooLargeError(BudgetPlanningError):
    code = "budget_document_too_large"
    status_code = 422


class BudgetScopeNotFoundError(BudgetPlanningError):
    code = "budget_scope_not_found"
    status_code = 404


class BudgetScopeConflictError(BudgetPlanningError):
    code = "budget_scope_conflict"
    status_code = 409


class BudgetScopeForbiddenError(BudgetPlanningError):
    code = "budget_scope_forbidden"
    status_code = 403


class BudgetCostCenterInvalidError(BudgetPlanningError):
    code = "budget_cost_center_invalid"
    status_code = 422


class BudgetCostCenterNotFoundError(BudgetPlanningError):
    code = "budget_cost_center_not_found"
    status_code = 404


class BudgetCostCenterConflictError(BudgetPlanningError):
    code = "budget_cost_center_conflict"
    status_code = 409


class BudgetCostCenterAmbiguousError(BudgetPlanningError):
    code = "budget_cost_center_ambiguous"
    status_code = 422


class BudgetUserNotAuthorizedError(BudgetPlanningError):
    code = "budget_user_not_authorized"
    status_code = 403


class BudgetResponsibilityNotFoundError(BudgetPlanningError):
    code = "budget_responsibility_not_found"
    status_code = 404


class BudgetResponsibilityConflictError(BudgetPlanningError):
    code = "budget_responsibility_conflict"
    status_code = 409


class BudgetResponsibilityInvalidError(BudgetPlanningError):
    code = "budget_responsibility_invalid"
    status_code = 422


class BudgetResponsibilityForbiddenError(BudgetPlanningError):
    code = "budget_responsibility_forbidden"
    status_code = 403


class CapexCategoryNotFoundError(BudgetPlanningError):
    code = "capex_category_not_found"
    status_code = 404


class CapexCategoryConflictError(BudgetPlanningError):
    code = "capex_category_conflict"
    status_code = 409


class CapexCategoryInvalidError(BudgetPlanningError):
    code = "capex_category_invalid"
    status_code = 422


class CapexInvestmentNotFoundError(BudgetPlanningError):
    code = "budget_capex_investment_not_found"
    status_code = 404


class CapexInvestmentCategoryInvalidError(BudgetPlanningError):
    code = "budget_capex_category_invalid"
    status_code = 422


class CapexInvestmentCostCenterForbiddenError(BudgetPlanningError):
    code = "budget_capex_cost_center_forbidden"
    status_code = 403


class CapexInvestmentValueInvalidError(BudgetPlanningError):
    code = "budget_capex_value_invalid"
    status_code = 422


class CapexInvestmentDateInvalidError(BudgetPlanningError):
    code = "budget_capex_date_invalid"
    status_code = 422


class CapexInvestmentStatusInvalidError(BudgetPlanningError):
    code = "budget_capex_status_invalid"
    status_code = 422


class CapexInvestmentVersionConflictError(BudgetPlanningError):
    code = "budget_capex_version_conflict"
    status_code = 409


class CapexInvestmentArchivedError(BudgetPlanningError):
    code = "budget_capex_archived"
    status_code = 409


class CapexInvestmentInvalidError(BudgetPlanningError):
    code = "budget_capex_investment_invalid"
    status_code = 422


class CapexAttachmentNotFoundError(BudgetPlanningError):
    code = "budget_capex_attachment_not_found"
    status_code = 404


class CapexAttachmentForbiddenError(BudgetPlanningError):
    code = "budget_capex_attachment_forbidden"
    status_code = 403


class CapexAttachmentTypeInvalidError(BudgetPlanningError):
    code = "budget_capex_attachment_type_invalid"
    status_code = 422


class CapexAttachmentMimeInvalidError(BudgetPlanningError):
    code = "budget_capex_attachment_mime_invalid"
    status_code = 422


class CapexAttachmentExtensionInvalidError(BudgetPlanningError):
    code = "budget_capex_attachment_extension_invalid"
    status_code = 422


class CapexAttachmentTooLargeError(BudgetPlanningError):
    code = "budget_capex_attachment_too_large"
    status_code = 422


class CapexAttachmentArchivedError(BudgetPlanningError):
    code = "budget_capex_attachment_archived"
    status_code = 409


class CapexAttachmentInvestmentArchivedError(BudgetPlanningError):
    code = "budget_capex_investment_archived"
    status_code = 409


class CapexAttachmentInvalidError(BudgetPlanningError):
    code = "budget_capex_attachment_invalid"
    status_code = 422


class CapexPlanNotFoundError(BudgetPlanningError):
    code = "budget_capex_plan_not_found"
    status_code = 404


class CapexPlanInvalidStatusError(BudgetPlanningError):
    code = "budget_capex_plan_invalid_status"
    status_code = 422


class CapexPlanInvalidTransitionError(BudgetPlanningError):
    code = "budget_capex_plan_invalid_transition"
    status_code = 409


class CapexPlanIncompleteError(BudgetPlanningError):
    code = "budget_capex_plan_incomplete"
    status_code = 422

    def __init__(
        self,
        message: str,
        *,
        incomplete_investments: list[dict] | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message, code=code, status_code=status_code)
        self.incomplete_investments = incomplete_investments or []
        self.details = {"incomplete_investments": self.incomplete_investments}


class CapexPlanCommentRequiredError(BudgetPlanningError):
    code = "budget_capex_plan_comment_required"
    status_code = 422


class CapexPlanVersionConflictError(BudgetPlanningError):
    code = "budget_capex_plan_version_conflict"
    status_code = 409


class CapexPlanLockedError(BudgetPlanningError):
    code = "budget_capex_plan_locked"
    status_code = 409


class CapexPlanAlreadyApprovedError(BudgetPlanningError):
    code = "budget_capex_plan_already_approved"
    status_code = 409


class CapexApprovalForbiddenError(BudgetPlanningError):
    code = "budget_capex_approval_forbidden"
    status_code = 403


class CapexInvestmentReviewInvalidError(BudgetPlanningError):
    code = "budget_capex_investment_review_invalid"
    status_code = 422


class CapexPlanInvalidError(BudgetPlanningError):
    code = "budget_capex_plan_invalid"
    status_code = 422


class CapexConsolidationForbiddenError(BudgetPlanningError):
    code = "budget_capex_consolidation_forbidden"
    status_code = 403


class CapexExportForbiddenError(BudgetPlanningError):
    code = "budget_capex_export_forbidden"
    status_code = 403


class CapexConsolidationInvalidError(BudgetPlanningError):
    code = "budget_capex_consolidation_invalid"
    status_code = 422


class CapexConsolidationCurrencyConflictError(BudgetPlanningError):
    code = "budget_capex_consolidation_currency_conflict"
    status_code = 422


# ---- Orçamento de Pessoal (Fase 3B.1 / 3B.1.1) ----


class PersonnelPositionNameRequiredError(BudgetPlanningError):
    code = "budget_personnel_position_name_required"
    status_code = 422


class PersonnelPositionNameTooLongError(BudgetPlanningError):
    code = "budget_personnel_position_name_too_long"
    status_code = 422


class PersonnelPlanNotFoundError(BudgetPlanningError):
    code = "budget_personnel_plan_not_found"
    status_code = 404


class PersonnelPlanInvalidError(BudgetPlanningError):
    code = "budget_personnel_plan_invalid"
    status_code = 422


class PersonnelLineNotFoundError(BudgetPlanningError):
    code = "budget_personnel_line_not_found"
    status_code = 404


class PersonnelLineDuplicatePositionError(BudgetPlanningError):
    code = "budget_personnel_line_duplicate_position"
    status_code = 409


class PersonnelInvalidHeadcountError(BudgetPlanningError):
    code = "budget_personnel_invalid_headcount"
    status_code = 422


class PersonnelLineVersionConflictError(BudgetPlanningError):
    code = "budget_personnel_line_version_conflict"
    status_code = 409


class PersonnelResponsibilityRequiredError(BudgetPlanningError):
    code = "budget_personnel_responsibility_required"
    status_code = 403


class PersonnelCostCenterBranchMismatchError(BudgetPlanningError):
    code = "budget_personnel_cost_center_branch_mismatch"
    status_code = 422


class PersonnelPlanInvalidStatusError(BudgetPlanningError):
    code = "budget_personnel_plan_invalid_status"
    status_code = 422


class PersonnelPlanInvalidTransitionError(BudgetPlanningError):
    code = "budget_personnel_plan_invalid_transition"
    status_code = 409


class PersonnelPlanIncompleteError(BudgetPlanningError):
    code = "budget_personnel_plan_incomplete"
    status_code = 422

    def __init__(
        self,
        message: str,
        *,
        incomplete_lines: list[dict] | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message, code=code, status_code=status_code)
        self.incomplete_lines = incomplete_lines or []
        self.details = {"incomplete_lines": self.incomplete_lines}


class PersonnelPlanCommentRequiredError(BudgetPlanningError):
    code = "budget_personnel_plan_comment_required"
    status_code = 422


class PersonnelPlanVersionConflictError(BudgetPlanningError):
    code = "budget_personnel_plan_version_conflict"
    status_code = 409


class PersonnelPlanLockedError(BudgetPlanningError):
    code = "budget_personnel_plan_locked"
    status_code = 409


class PersonnelPlanAlreadyApprovedError(BudgetPlanningError):
    code = "budget_personnel_plan_already_approved"
    status_code = 409


class PersonnelApprovalForbiddenError(BudgetPlanningError):
    code = "budget_personnel_approval_forbidden"
    status_code = 403
