from typing import Dict, List


def _breathing_exercises() -> List[str]:
	return [
		"Box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s × 4",
		"4-7-8 breathing for sleep: inhale 4s, hold 7s, exhale 8s × 4",
		"Diaphragmatic breathing: hand on belly, slow breaths for 2 minutes",
	]


def _micro_breaks() -> List[str]:
	return [
		"Stand up and stretch neck/shoulders for 60 seconds",
		"Drink a glass of water and look away from screens for 2 minutes",
		"Walk for 5 minutes to reset your focus",
	]


def _mindfulness_exercises() -> List[str]:
	return [
		"Body scan meditation (5 min): notice sensations from head to toe",
		"5-4-3-2-1 grounding: name things you can see, feel, hear, smell, taste",
		"Gratitude note: write 3 small positives from today",
	]


def generate_recommendations(analysis: Dict) -> Dict:
	stress = analysis.get("stress_score", 0)
	sentiment = analysis.get("sentiment", "neutral")
	keywords = analysis.get("top_keywords", [])

	recs: Dict[str, List[str]] = {}

	if stress >= 0.5 or sentiment == "negative":
		recs["Immediate Calm"] = _breathing_exercises()
		recs["Mindfulness Reset"] = _mindfulness_exercises()
		recs["Short Breaks"] = _micro_breaks()
	elif stress >= 0.2:
		recs["Focus Reset"] = _micro_breaks()
		recs["Light Mindfulness"] = [
			"2-minute breathing: inhale through nose, exhale longer through mouth",
			"Write one sentence about what's in your control right now",
		]
	else:
		recs["Keep the Momentum"] = [
			"Celebrate a small win from today",
			"Plan a 25-minute focused session with a 5-minute break",
		]

	if any(k in {"sleep", "tired", "exhausted"} for k in keywords):
		recs["Sleep Hygiene"] = [
			"Avoid screens 30 minutes before bed",
			"Keep a consistent sleep-wake schedule",
		]

	if any(k in {"exam", "deadline", "assignment"} for k in keywords):
		recs["Study Strategy"] = [
			"Pomodoro: 25m study + 5m break × 4, then 15m longer break",
			"Write a 3-item priority list for tomorrow",
		]

	return recs


