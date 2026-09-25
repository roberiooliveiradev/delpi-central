from production_control_app.domain.services.production_run_counting import (
    pieces_from_anchor,
    sum_segment_pieces,
)


def test_pieces_from_anchor_positive():
    result = pieces_from_anchor(
        current_counter=150,
        current_epoch=1,
        anchor_counter=100,
        anchor_epoch=1,
    )
    assert result.pieces == 50
    assert result.epoch_changed is False


def test_pieces_from_anchor_never_negative():
    result = pieces_from_anchor(
        current_counter=90,
        current_epoch=1,
        anchor_counter=100,
        anchor_epoch=1,
    )
    assert result.pieces == 0


def test_pieces_from_anchor_epoch_change():
    result = pieces_from_anchor(
        current_counter=5,
        current_epoch=2,
        anchor_counter=100,
        anchor_epoch=1,
    )
    assert result.epoch_changed is True
    assert result.pieces == 0


def test_sum_segment_pieces():
    assert sum_segment_pieces([10, 20], 5) == 35
