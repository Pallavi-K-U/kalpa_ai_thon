document.addEventListener('DOMContentLoaded', () => {
	const blobs = document.querySelectorAll('.blob');
	let t = 0;
	function animate() {
		t += 0.01;
		blobs.forEach((b, i) => {
			const x = Math.sin(t + i) * 8;
			const y = Math.cos(t + i * 0.7) * 8;
			b.style.transform = `translate(${x}px, ${y}px)`;
		});
		requestAnimationFrame(animate);
	}
	animate();

	// Theme handling
	const root = document.documentElement;
	const key = 'mm-theme';
	const saved = localStorage.getItem(key) || 'dark';
	root.setAttribute('data-theme', saved);

	const themeToggle = document.getElementById('theme-toggle');
	const menuToggle = document.getElementById('menu-toggle');
	const menuPanel = document.getElementById('menu-panel');

	function closeMenu() {
		if (menuPanel && !menuPanel.hasAttribute('hidden')) {
			menuPanel.setAttribute('hidden', '');
			if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
		}
	}

	if (menuToggle && menuPanel) {
		menuToggle.addEventListener('click', (e) => {
			e.stopPropagation();
			const open = menuPanel.hasAttribute('hidden');
			if (open) {
				menuPanel.removeAttribute('hidden');
				menuToggle.setAttribute('aria-expanded', 'true');
			} else {
				closeMenu();
			}
		});
		document.addEventListener('click', (e) => {
			if (!menuPanel.contains(e.target) && e.target !== menuToggle) {
				closeMenu();
			}
		});
	}

	if (themeToggle) {
		themeToggle.addEventListener('click', () => {
			const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
			root.setAttribute('data-theme', next);
			localStorage.setItem(key, next);
		});
	}

	// Floating chat widget
	const fab = document.getElementById('fab-chat');
	const widget = document.getElementById('chat-widget');
	const closeBtn = document.getElementById('chat-close');
	const bodyEl = document.getElementById('chat-body');
	const sendForm = document.getElementById('chat-send');
	const textInput = document.getElementById('chat-text');

	function openWidget() { if (widget) widget.removeAttribute('hidden'); }
	function closeWidget() { if (widget) widget.setAttribute('hidden', ''); }
	function addMsg(role, text) {
		const div = document.createElement('div');
		div.className = 'chat-msg' + (role === 'user' ? ' user' : '');
		div.textContent = text;
		bodyEl.appendChild(div);
		bodyEl.scrollTop = bodyEl.scrollHeight;
	}
	function typing(on) {
		let el = document.getElementById('typing');
		if (on) {
			if (!el) {
				el = document.createElement('div');
				el.id = 'typing';
				el.className = 'chat-msg';
				el.textContent = '… typing';
				bodyEl.appendChild(el);
				bodyEl.scrollTop = bodyEl.scrollHeight;
			}
		} else if (el) { el.remove(); }
	}

	if (fab) {
		fab.addEventListener('click', () => { openWidget(); if (bodyEl.childElementCount === 0) addMsg('bot', "Hi! I'm here to listen."); });
	}
	if (closeBtn) closeBtn.addEventListener('click', closeWidget);
	if (sendForm) {
		sendForm.addEventListener('submit', async (e) => {
			e.preventDefault();
			const msg = textInput.value.trim();
			if (!msg) return;
			addMsg('user', msg);
			textInput.value = '';
			typing(true);
			const formData = new FormData();
			formData.append('message', msg);
			const res = await fetch('/api/chat', { method: 'POST', body: formData });
			const data = await res.json();
			typing(false);
			addMsg('bot', data.reply);
		});
	}
});


