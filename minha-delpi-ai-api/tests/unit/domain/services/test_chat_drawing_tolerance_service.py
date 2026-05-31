from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService


def test_lengths_within_tolerance_ok():
    assert ChatDrawingToleranceService.lengths_within_tolerance(105, 100) is True


def test_lengths_within_tolerance_fail():
    assert ChatDrawingToleranceService.lengths_within_tolerance(120, 100) is False


def test_decape_within_tolerance():
    assert ChatDrawingToleranceService.decape_within_tolerance(10.5, 10.0) is True
    assert ChatDrawingToleranceService.decape_within_tolerance(12, 10.0) is False
