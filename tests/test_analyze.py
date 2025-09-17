from nlp.analyze import analyze_text


def test_stress_score_increases_with_negative_words():
	low = analyze_text("I feel okay and calm today")
	high = analyze_text("I am stressed, anxious and overwhelmed with pressure")
	assert high["stress_score"] >= low["stress_score"]
	assert 0.0 <= low["stress_score"] <= 1.0
	assert 0.0 <= high["stress_score"] <= 1.0


