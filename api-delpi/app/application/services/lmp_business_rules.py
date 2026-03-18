# app/application/services/lmp_business_rules.py
from datetime import date, timedelta
from typing import Optional


class LMPBusinessRules:
    SLA_BY_LEVEL = {
        "Nível 1": 4,
        "Nível 2": 8,
        "Nível 3": 20,
    }

    HOURS_PER_DAY = 24
    MINUTES_PER_DAY = HOURS_PER_DAY * 60
    SLA_TOLERANCE_DAYS = 1

    ENGINEERING_STATUS_FINISHED = "FINALIZADA"
    ENGINEERING_STATUS_IN_PROGRESS = "EM_ANDAMENTO"
    ENGINEERING_STATUS_PARTIAL = "PARCIAL"
    ENGINEERING_STATUS_RETURNED = "RETORNADA"

    DASHBOARD_STATUS_ON_TIME = "Pontual"
    DASHBOARD_STATUS_LATE = "Atrasado"
    DASHBOARD_STATUS_IN_PROGRESS = "Andamento"
    DASHBOARD_STATUS_RETURNED = "Retornada"

    @staticmethod
    def normalize_string(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        value = str(value).strip()
        return value if value else None

    @classmethod
    def parse_totvs_date(cls, value: Optional[str]) -> Optional[date]:
        value = cls.normalize_string(value)

        if not value or len(value) != 8:
            return None

        try:
            year = int(value[0:4])
            month = int(value[4:6])
            day = int(value[6:8])
            return date(year, month, day)
        except ValueError:
            return None

    @staticmethod
    def format_date_to_ymd(value: Optional[date]) -> Optional[str]:
        if not value:
            return None
        return value.strftime("%Y%m%d")

    @staticmethod
    def is_weekend(value: date) -> bool:
        return value.weekday() >= 5

    @classmethod
    def add_business_days(cls, start: date, business_days: int) -> date:
        result = start
        added = 0

        while added < business_days:
            result += timedelta(days=1)
            if not cls.is_weekend(result):
                added += 1

        return result

    @classmethod
    def business_days_between(cls, start: date, end: date) -> int:
        if end < start:
            return 0

        cursor = start
        count = 0

        while cursor <= end:
            if not cls.is_weekend(cursor):
                count += 1
            cursor += timedelta(days=1)

        return count

    @staticmethod
    def get_nivel(qtd_pi: Optional[int]) -> str:
        value = qtd_pi or 0

        if value <= 10:
            return "Nível 1"
        if value <= 20:
            return "Nível 2"
        return "Nível 3"

    @classmethod
    def get_sla_days(cls, nivel: str) -> int:
        return cls.SLA_BY_LEVEL[nivel]

    @classmethod
    def get_sla_minutes(cls, nivel: str) -> int:
        return cls.get_sla_days(nivel) * cls.MINUTES_PER_DAY

    @classmethod
    def get_sla_tolerance_minutes(cls) -> int:
        return cls.SLA_TOLERANCE_DAYS * cls.MINUTES_PER_DAY

    @classmethod
    def get_sla_limit_minutes(cls, nivel: str) -> int:
        return cls.get_sla_minutes(nivel) + cls.get_sla_tolerance_minutes()

    @classmethod
    def get_sla_limit_date(cls, start_date: Optional[date], nivel: str) -> Optional[date]:
        if not start_date:
            return None

        base_limit = cls.add_business_days(start_date, cls.get_sla_days(nivel))
        return cls.add_business_days(base_limit, cls.SLA_TOLERANCE_DAYS)

    @classmethod
    def is_engineering_finished(cls, engineering_status: Optional[str]) -> bool:
        normalized = cls.normalize_string(engineering_status)
        return normalized == cls.ENGINEERING_STATUS_FINISHED

    @classmethod
    def is_engineering_returned(cls, engineering_status: Optional[str]) -> bool:
        normalized = cls.normalize_string(engineering_status)
        return normalized == cls.ENGINEERING_STATUS_RETURNED

    @classmethod
    def is_engineering_in_progress(cls, engineering_status: Optional[str]) -> bool:
        normalized = cls.normalize_string(engineering_status)
        return normalized == cls.ENGINEERING_STATUS_IN_PROGRESS

    @classmethod
    def is_engineering_partial(cls, engineering_status: Optional[str]) -> bool:
        normalized = cls.normalize_string(engineering_status)
        return normalized == cls.ENGINEERING_STATUS_PARTIAL

    @classmethod
    def matches_engineering_status_filter(
        cls,
        engineering_status: Optional[str],
        filter_status: Optional[str],
    ) -> bool:
        normalized_status = cls.normalize_string(engineering_status)
        normalized_filter = cls.normalize_string(filter_status)

        if not normalized_filter:
            return True

        return normalized_status == normalized_filter

    @classmethod
    def get_dashboard_status(
        cls,
        start_date_str: Optional[str],
        end_date_str: Optional[str],
        qtd_pi: Optional[int],
        engineering_status: Optional[str] = None,
        engineering_total_minutes: Optional[int] = None,
        today: Optional[date] = None,
    ) -> tuple[str, int, int, Optional[str], Optional[int], str]:
        today = today or date.today()

        nivel = cls.get_nivel(qtd_pi)
        sla_days = cls.get_sla_days(nivel)
        sla_minutes = cls.get_sla_minutes(nivel)
        sla_limit_minutes = cls.get_sla_limit_minutes(nivel)

        start_date = cls.parse_totvs_date(start_date_str)
        end_date = cls.parse_totvs_date(end_date_str)

        data_limite = cls.add_business_days(start_date, sla_days) if start_date else None
        data_limite_com_tolerancia = cls.get_sla_limit_date(start_date, nivel)

        lead_time_util = (
            cls.business_days_between(start_date, end_date)
            if start_date and end_date
            else None
        )

        total_minutes = int(engineering_total_minutes or 0)
        finished = cls.is_engineering_finished(engineering_status)
        returned = cls.is_engineering_returned(engineering_status)

        if returned:
            status = cls.DASHBOARD_STATUS_RETURNED

        elif finished:
            within_date_limit = (
                end_date is not None
                and data_limite_com_tolerancia is not None
                and end_date <= data_limite_com_tolerancia
            )

            within_minutes_limit = total_minutes <= sla_limit_minutes

            status = (
                cls.DASHBOARD_STATUS_ON_TIME
                if (within_date_limit or within_minutes_limit)
                else cls.DASHBOARD_STATUS_LATE
            )
        else:
            over_date_limit = (
                data_limite_com_tolerancia is not None
                and today > data_limite_com_tolerancia
            )
            over_minutes_limit = total_minutes > sla_limit_minutes

            status = (
                cls.DASHBOARD_STATUS_LATE
                if (over_date_limit and over_minutes_limit)
                else cls.DASHBOARD_STATUS_IN_PROGRESS
            )

        return (
            nivel,
            sla_days,
            sla_minutes,
            cls.format_date_to_ymd(data_limite),
            lead_time_util,
            status,
        )