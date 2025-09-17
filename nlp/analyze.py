import re
from collections import Counter
from pathlib import Path


NEGATIVE_KEYWORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "stress_keywords.txt"


def _load_negative_keywords() -> set:
	if NEGATIVE_KEYWORDS_PATH.exists():
		with open(NEGATIVE_KEYWORDS_PATH, "r", encoding="utf-8") as f:
			words = [w.strip().lower() for w in f.readlines() if w.strip()]
			return set(words)
	# Fallback defaults
	return {
		"stress",
		"stressed",
		"anxiety",
		"anxious",
		"panic",
		"tired",
		"exhausted",
		"overwhelmed",
		"sad",
		"depressed",
		"burnout",
		"worry",
		"worried",
		"pressure",
		"stress",
"stressed",
"anxiety",
"anxious",
"panic",
"panic_attack",
"overwhelmed",
"pressure",
"burnout",
"exhausted",
"tired",
"insomnia",
"restless",
"sad",
"depressed",
"low",
"worried",
"worry",
"fear",
"fearful",
"nervous",
"tense",
"frustrated",
"angry",
"irritable",
"lonely",
"hopeless",
"helpless",
"deadline",
"exam",
"assignment",
"fail",
"failure",
"disappointment",
"rejection",
"insecure",
"ashamed",
"guilty",
"regretful",
"jealous",
"envious",
"bitter",
"grief",
"mourning",
"heartbreak",
"loss",
"misery",
"uneasy",
"distressed",
"vulnerable",
"abandoned",
"worthless",
"broken",
"emptiness",
"drained",
"fatigued",
"trapped",
"pressured",
"shaken",
"confused",
"doubtful",
"uncertain",
"skeptical",
"weak",
"isolated",
"embarrassed",
"withdrawn",
"gloomy",
"melancholy",
"lost",
"disheartened",
"discouraged",
"resentful",
"mistrustful",
"unstable",
"happy",
"joy",
"joyful",
"cheerful",
"excited",
"hopeful",
"calm",
"relaxed",
"peaceful",
"love",
"loved",
"loving",
"grateful",
"thankful",
"blessed",
"content",
"satisfied",
"proud",
"confident",
"optimistic",
"strong",
"brave",
"energetic",
"motivated",
"inspired",
"focused",
"determined",
"relieved",
"free",
"safe",
"secure",
"valued",
"appreciated",
"cared",
"supported",
"enthusiastic",
"playful",
"silly",
"fun",
"thrilled",
"adventurous",
"curious",
"passionate",
"compassionate",
"kind",
"empathetic",
"caring",
"helpful",
"generous",
"forgiving",
"patient",
"mindful",
"resilient",
"healing",
"accepted",
"understood",
"connected",
"belonging",
"fulfilled",
"accomplished",
"successful",
"growth",
"learning",
"clarity",
"balanced",
"harmony",
"refreshed",
"renewed",
"grounded",
"open",
"trusting",
"bored",
"blank",
"numb",
"indifferent",
"neutral",
"distracted",
"unsettled",
"thoughtful",
"reflective",
"uncertain",
"daydreaming",
"nostalgic",
"cautious",
"hesitant",
"mixed",
"ambiguous",
"longing",
"expecting",
"anticipating",
"unsure",
"contemplative",
"pensive",
"observant",
"analytical",
"questioning",
"undecided",
"exploring",

	}


NEGATIVE_KEYWORDS = _load_negative_keywords()


def _tokenize(text: str) -> list:
	text = text.lower()
	text = re.sub(r"[^a-z\s]", " ", text)
	return [t for t in text.split() if t]


def analyze_text(text: str) -> dict:
	"""Return lightweight sentiment, stress score, and key themes.

	This is a simple, local analysis to avoid external services.
	"""
	text_lc = text.lower()
	tokens = _tokenize(text)
	word_counts = Counter(tokens)
	total = max(1, sum(word_counts.values()))

	negative_hits = sum(count for word, count in word_counts.items() if word in NEGATIVE_KEYWORDS)

	# Phrase-based negatives to catch expressions like "very bad", "feeling awful"
	phrase_patterns = [
		r"very\s+bad",
		r"so\s+bad",
		r"really\s+bad",
		r"not\s+good",
		r"feel(?:ing)?\s+bad",
		r"feel(?:ing)?\s+awful",
		r"feel(?:ing)?\s+terrible",
	]
	for pat in phrase_patterns:
		if re.search(pat, text_lc):
			negative_hits += 2

	stress_score = min(1.0, negative_hits / total)

	# Adjust threshold so mild negatives tip to neutral sooner
	sentiment = "positive" if stress_score < 0.2 else ("neutral" if stress_score < 0.4 else "negative")

	# Extract top keywords excluding very common filler words
	stop = {"the", "and", "a", "to", "of", "in", "it", "is", "that", "for", "on", "with", "was", "as", "but", "are", "this", "be", "have", "at", "or", "by", "an", "from", "so"}
	keywords = [w for w, _ in word_counts.most_common() if w not in stop][:8]

	return {
		"stress_score": round(stress_score, 3),
		"sentiment": sentiment,
		"negative_hits": int(negative_hits),
		"total_tokens": int(total),
		"top_keywords": keywords,
	}


