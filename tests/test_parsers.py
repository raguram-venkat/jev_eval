import json
from pathlib import Path

import pytest

from jev_eval.protocol.parsers import ParseError, parse_choice, parse_noul, parse_score

FIXTURES = Path("tests/fixtures")


def _fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    if not path.exists():
        pytest.fail(f"missing fixture {path} — run ./capture_fixtures.sh to capture it")
    return json.loads(path.read_text())


def test_parses_captured_choice_fixture():
    response = _fixture("choice_response")
    parsed = parse_choice(response, "intent", ["automatic top up", "request refund"])
    assert parsed.answer in ("automatic top up", "request refund")
    assert pytest.approx(sum(parsed.probabilities.values()), abs=1e-9) == 1.0
    assert parsed.is_argmax is (parsed.answer == max(parsed.probabilities, key=parsed.probabilities.get))


def test_parses_captured_noul_fixture():
    response = _fixture("noul_response")
    parsed = parse_noul(response, "answer")
    assert 0.0 <= parsed.p_yes <= 1.0
    assert parsed.p_no == pytest.approx(1.0 - parsed.p_yes)


def test_parses_captured_score_fixture():
    response = _fixture("score_response")
    parsed = parse_score(response, "stars", num_levels=5)
    assert parsed.stars in range(1, 6)
    assert set(parsed.probabilities) == {1, 2, 3, 4, 5}
    assert pytest.approx(sum(parsed.probabilities.values()), abs=1e-9) == 1.0


def test_choice_missing_answer_raises():
    with pytest.raises(ParseError, match="missing answers"):
        parse_choice({"answers": {}}, "intent", ["a", "b"])


def test_choice_wrong_type_raises():
    response = {"answers": {"intent": {"type": "noul", "choice": "a"}}}
    with pytest.raises(ParseError, match="type"):
        parse_choice(response, "intent", ["a", "b"])


def test_choice_missing_option_key_counts_as_zero():
    response = {"answers": {"intent": {"type": "choice", "choice": "a", "probabilities": {"a": 1.0}}}}
    parsed = parse_choice(response, "intent", ["a", "b"])
    assert parsed.probabilities == {"a": 1.0, "b": 0.0}


def test_choice_probabilities_clipped_and_renormalised():
    response = {
        "answers": {
            "intent": {"type": "choice", "choice": "a", "probabilities": {"a": 1.5, "b": 0.5}}
        }
    }
    parsed = parse_choice(response, "intent", ["a", "b"])
    assert parsed.probabilities["a"] == pytest.approx(2 / 3)
    assert parsed.probabilities["b"] == pytest.approx(1 / 3)


def test_choice_non_numeric_probability_raises():
    response = {"answers": {"intent": {"type": "choice", "probabilities": {"a": "high", "b": 0.5}}}}
    with pytest.raises(ParseError, match="not numeric"):
        parse_choice(response, "intent", ["a", "b"])


def test_noul_non_numeric_raises():
    with pytest.raises(ParseError, match="noul"):
        parse_noul({"answers": {"answer": {"type": "noul", "noul": "yes"}}}, "answer")


def test_score_missing_level_counts_as_zero_and_maps_to_stars():
    response = {
        "answers": {
            "stars": {
                "type": "score", "score": 0.0,
                "probabilities": {"0": 1.0},  # levels 1..4 missing -> 0
            }
        }
    }
    parsed = parse_score(response, "stars", num_levels=5)
    assert parsed.probabilities == {1: 1.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
    assert parsed.stars == 1
    assert parsed.score == 1.0  # level 0 + 1


def test_score_missing_score_field_raises():
    response = {"answers": {"stars": {"type": "score", "probabilities": {"0": 1.0}}}}
    with pytest.raises(ParseError, match="score"):
        parse_score(response, "stars", num_levels=5)
