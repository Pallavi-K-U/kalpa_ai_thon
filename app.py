from flask import Flask, render_template, request, redirect, url_for, flash
from nlp.analyze import analyze_text
from recommendations import generate_recommendations
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from flask import jsonify
from cryptography.fernet import Fernet, InvalidToken
import os


app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # replace with env var in production

# --- Database setup ---
DB_PATH = Path(__file__).resolve().parent / "app.db"

# --- Encryption (Fernet) setup ---
FERNET_KEY_PATH = Path(__file__).resolve().parent / "fernet.key"


def _load_or_create_fernet() -> Fernet:
	# Priority 1: env var FERNET_KEY (base64 urlsafe 32-byte key)
	key_env = os.getenv("FERNET_KEY")
	if key_env:
		try:
			return Fernet(key_env.encode("utf-8"))
		except Exception:
			pass
	# Priority 2: local key file alongside app.py
	if FERNET_KEY_PATH.exists():
		key_bytes = FERNET_KEY_PATH.read_bytes()
		return Fernet(key_bytes)
	# Create and persist a new key (development convenience)
	new_key = Fernet.generate_key()
	FERNET_KEY_PATH.write_bytes(new_key)
	return Fernet(new_key)


fernet = _load_or_create_fernet()


def encrypt_text(plain_text: str) -> str:
	try:
		cipher = fernet.encrypt(plain_text.encode("utf-8"))
		return cipher.decode("utf-8")
	except Exception:
		# As a last resort, store plaintext (should rarely happen)
		return plain_text


def decrypt_text(maybe_cipher_text: str) -> str:
	if not maybe_cipher_text:
		return maybe_cipher_text
	try:
		plain = fernet.decrypt(maybe_cipher_text.encode("utf-8"))
		return plain.decode("utf-8")
	except (InvalidToken, ValueError, TypeError):
		# Backward compatibility: not encrypted, return as-is
		return maybe_cipher_text


def get_db():
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def init_db():
	with get_db() as conn:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT UNIQUE NOT NULL,
				password_hash TEXT NOT NULL
			);
			"""
		)
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS entries (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				text TEXT NOT NULL,
				stress_score REAL NOT NULL,
				sentiment TEXT NOT NULL,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY(user_id) REFERENCES users(id)
			);
			"""
		)
		conn.commit()


init_db()


# --- Auth setup ---
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin):
	def __init__(self, user_id: int, username: str):
		self.id = str(user_id)
		self.username = username

	@staticmethod
	def from_row(row):
		return User(row["id"], row["username"]) if row else None


@login_manager.user_loader
def load_user(user_id: str):
	with get_db() as conn:
		row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
		return User.from_row(row)


@app.route("/")
def index():
	return render_template("index.html")


@app.route("/journal", methods=["GET", "POST"])
def journal():
	if request.method == "POST":
		journal_text = request.form.get("journal_text", "").strip()
		if not journal_text:
			return render_template("journal.html", error_message="Please write something to analyze.")

		analysis = analyze_text(journal_text)
		recs = generate_recommendations(analysis)
		# Save entry if logged in
		try:
			if current_user.is_authenticated:
				with get_db() as conn:
					cipher_text = encrypt_text(journal_text)
					conn.execute(
						"INSERT INTO entries (user_id, text, stress_score, sentiment) VALUES (?, ?, ?, ?)",
						(current_user.id, cipher_text, analysis["stress_score"], analysis["sentiment"]),
					)
					conn.commit()
		except Exception:
			pass
		return render_template(
			"result_card.html",
			journal_text=journal_text,
			analysis=analysis,
			recommendations=recs,
		)

	return render_template("journal.html")


@app.route("/privacy")
def privacy():
	return render_template("privacy.html")


@app.route("/history")
@login_required
def history():
	with get_db() as conn:
		rows = conn.execute(
			"SELECT id, text, stress_score, sentiment, created_at FROM entries WHERE user_id = ? ORDER BY created_at DESC",
			(current_user.id,),
		).fetchall()
	# Decrypt text values (supports plaintext fallback)
	decrypted = []
	for r in rows:
		decrypted.append({
			"id": r["id"],
			"text": decrypt_text(r["text"]),
			"stress_score": r["stress_score"],
			"sentiment": r["sentiment"],
			"created_at": r["created_at"],
		})
	return render_template("history.html", entries=decrypted)


@app.post("/history/delete/<int:entry_id>")
@login_required
def delete_entry(entry_id: int):
	with get_db() as conn:
		conn.execute("DELETE FROM entries WHERE id = ? AND user_id = ?", (entry_id, current_user.id))
		conn.commit()
	return redirect(url_for("history"))


# --- Chat bot ---
@app.route("/chat")
def chat():
	return render_template("chat.html")


@app.post("/api/chat")
def api_chat():
	user_text = request.form.get("message", "").strip()
	if not user_text:
		return jsonify({"reply": "I'm here to listen. Tell me what's on your mind."})
	analysis = analyze_text(user_text)
	stress = analysis.get("stress_score", 0)
	sent = analysis.get("sentiment", "neutral")

	if stress >= 0.5 or sent == "negative":
		reply = (
			"I hear that things feel heavy. Let's take one small step together. "
			"Try box-breathing (inhale 4s, hold 4s, exhale 4s, hold 4s × 4). "
			"After that, what feels most in your control right now?"
		)
	elif stress >= 0.2:
		reply = (
			"Thanks for sharing. Sounds like there's some pressure. "
			"Would a 5-minute reset help? Stand, stretch, sip water, then write 3 priorities."
		)
	else:
		reply = (
			"Love the momentum. What's one small win you can celebrate today? "
			"If you'd like, we can plan a focused 25-minute session."
		)

	return jsonify({"reply": reply, "analysis": analysis})


# --- Auth routes ---
@app.route("/signup", methods=["GET", "POST"])
def signup():
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "")
		if not username or not password:
			flash("Username and password are required", "error")
			return render_template("signup.html")
		with get_db() as conn:
			try:
				conn.execute(
					"INSERT INTO users (username, password_hash) VALUES (?, ?)",
					(username, generate_password_hash(password)),
				)
				conn.commit()
			except sqlite3.IntegrityError:
				flash("Username already exists", "error")
				return render_template("signup.html")
			row = conn.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
			user = User.from_row(row)
			login_user(user)
			return redirect(url_for("index"))
	return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "")
		with get_db() as conn:
			row = conn.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,)).fetchone()
			if not row or not check_password_hash(row["password_hash"], password):
				flash("Invalid credentials", "error")
				return render_template("login.html")
			user = User(row["id"], row["username"])
			login_user(user)
			return redirect(url_for("index"))
	return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("index"))


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)


