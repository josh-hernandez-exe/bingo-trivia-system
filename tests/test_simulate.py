import random

from bingo_trivia_system.cards import generate_cards
from bingo_trivia_system.simulate import simulate_card, simulate_event, winners_by_question


def test_zero_error_winner_is_deterministic(sample_event, sample_wordbank, sample_questions):
    cards = generate_cards(sample_event, sample_wordbank)
    a = simulate_event(cards, sample_questions.questions, win_rule=sample_event.win_rule, seed=1)
    b = simulate_event(cards, sample_questions.questions, win_rule=sample_event.win_rule, seed=1)
    assert [o.won_at_question for o in a.outcomes] == [o.won_at_question for o in b.outcomes]


def test_some_card_wins_in_zero_error_run(sample_event, sample_wordbank, sample_questions):
    cards = generate_cards(sample_event, sample_wordbank)
    result = simulate_event(
        cards, sample_questions.questions, win_rule="line", seed=0, error_rate=0.0
    )
    assert any(o.won_at_question is not None for o in result.outcomes)


def test_error_rate_delays_winners(sample_event, sample_wordbank, sample_questions):
    cards = generate_cards(sample_event, sample_wordbank)
    perfect = simulate_event(cards, sample_questions.questions, win_rule="line", seed=42)
    noisy = simulate_event(
        cards, sample_questions.questions, win_rule="line", seed=42, error_rate=0.4
    )
    # First-winner question with noise should be no earlier than perfect.
    perfect_steps = [o.won_at_question for o in perfect.outcomes if o.won_at_question]
    noisy_steps = [o.won_at_question for o in noisy.outcomes if o.won_at_question]
    if perfect_steps and noisy_steps:
        assert min(noisy_steps) >= min(perfect_steps)


def test_winners_by_question_is_subset_of_full_run(sample_event, sample_wordbank, sample_questions):
    cards = generate_cards(sample_event, sample_wordbank)
    qs = sample_questions.questions
    partial = winners_by_question(cards, qs, win_rule="line", upto_question=10)
    full = winners_by_question(cards, qs, win_rule="line", upto_question=len(qs))
    partial_ids = {cid for cid, _ in partial}
    full_ids = {cid for cid, _ in full}
    assert partial_ids.issubset(full_ids)


def test_simulate_card_records_stamps(sample_event, sample_wordbank, sample_questions):
    cards = generate_cards(sample_event, sample_wordbank)
    oc = simulate_card(
        cards[0],
        sample_questions.questions,
        win_rule="blackout",
        rng=random.Random(0),
        error_rate=0.0,
        max_questions=3,
    )
    assert oc.won_at_question is None  # 3 questions not enough for blackout
    assert isinstance(oc.stamps, list)
