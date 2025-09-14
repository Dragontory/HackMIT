from processor.policy import pick_policy, estimate_duration_sec


def test_static_policy_uses_settings_defaults():
    pol = pick_policy("static", word_count=1000, clip_scores=[
                      0.2, 0.3], image_diversity=0.5)
    assert pol.mode == "static"
    assert 60 <= pol.wpm <= 200
    assert pol.max_images >= 1


def test_adaptive_policy_buckets_by_words():
    short = pick_policy("adaptive", word_count=300,
                        clip_scores=[], image_diversity=0.0)
    medium = pick_policy("adaptive", word_count=1000,
                         clip_scores=[], image_diversity=0.0)
    long = pick_policy("adaptive", word_count=3000,
                       clip_scores=[], image_diversity=0.0)
    assert short.wpm > medium.wpm > long.wpm
    assert short.max_images < medium.max_images < long.max_images


def test_learned_policy_reacts_to_confidence_and_diversity():
    low = pick_policy("learned", word_count=1200, clip_scores=[
                      0.05, 0.1], image_diversity=0.1)
    high = pick_policy("learned", word_count=1200, clip_scores=[
                       0.8, 0.9], image_diversity=0.8)
    assert high.max_images >= low.max_images
    assert 60 <= high.wpm <= 200


def test_duration_estimation_is_bounded_and_monotonic():
    pol = pick_policy("adaptive", word_count=1200,
                      clip_scores=[0.3], image_diversity=0.5)
    d1 = estimate_duration_sec(800, 3, pol)
    d2 = estimate_duration_sec(1600, 3, pol)
    d3 = estimate_duration_sec(1600, 30, pol)  # image bonus capped
    assert d2 > d1
    assert d3 >= d2  # but capped by pol.max_image_bonus
