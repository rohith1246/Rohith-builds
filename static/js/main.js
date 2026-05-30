"use strict";

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const isCompactViewport = window.matchMedia("(max-width: 768px)").matches;
const performanceMode = prefersReducedMotion || isCompactViewport;

/* ════════════════════════════════════════════════
   PromptVault — Premium Interactions
   ════════════════════════════════════════════════ */

/* ── Particle Canvas ────────────────────────────── */
(function initParticles() {
  const canvas = document.getElementById("particleCanvas");
  if (!canvas) return;
  if (performanceMode) {
    canvas.style.display = "none";
    return;
  }
  const ctx = canvas.getContext("2d");
  let W, H, particles = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  const COLORS = ["#3b82f6","#8b5cf6","#ec4899","#06b6d4"];
  class Particle {
    constructor() { this.reset(true) }
    reset(init) {
      this.x  = Math.random() * W;
      this.y  = init ? Math.random() * H : H + 10;
      this.r  = Math.random() * 1.5 + .3;
      this.vx = (Math.random() - .5) * .3;
      this.vy = -(Math.random() * .6 + .2);
      this.alpha = Math.random() * .5 + .1;
      this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
    }
    update() {
      this.x += this.vx; this.y += this.vy;
      if (this.y < -10) this.reset(false);
    }
    draw() {
      ctx.save();
      ctx.globalAlpha = this.alpha;
      ctx.fillStyle = this.color;
      ctx.shadowBlur = 6;
      ctx.shadowColor = this.color;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  const COUNT = window.innerWidth < 700 ? 20 : 40;
  for (let i = 0; i < COUNT; i++) particles.push(new Particle());

  function loop() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(loop);
  }
  loop();
})();

/* ── Navbar scroll shadow ───────────────────────── */
const mainNav = document.getElementById("mainNav");
let navScrollRaf = null;
window.addEventListener("scroll", () => {
  if (navScrollRaf) return;
  navScrollRaf = requestAnimationFrame(() => {
    if (mainNav) mainNav.classList.toggle("scrolled", window.scrollY > 20);
    navScrollRaf = null;
  });
}, { passive: true });
if (mainNav) mainNav.classList.toggle("scrolled", window.scrollY > 20);

/* ── Mobile Nav ─────────────────────────────────── */
const navToggle  = document.getElementById("navToggle");
const mobileMenu = document.getElementById("mobileMenu");
if (navToggle && mobileMenu) {
  navToggle.addEventListener("click", () => {
    const open = mobileMenu.classList.toggle("open");
    const s = navToggle.querySelectorAll("span");
    s[0].style.transform = open ? "rotate(45deg) translate(5px,5px)"  : "";
    s[1].style.opacity   = open ? "0" : "1";
    s[2].style.transform = open ? "rotate(-45deg) translate(5px,-5px)" : "";
  });
}

/* ── Scroll-triggered entrance animations ───────── */
const scrollObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const delay = entry.target.dataset.delay || 0;
      setTimeout(() => entry.target.classList.add("visible"), +delay);
      scrollObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll("[data-animate]").forEach(el => scrollObserver.observe(el));

/* ── Animated stat counters ─────────────────────── */
function animateCount(el, target, duration = 1200) {
  const start = performance.now();
  const update = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(eased * target);
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = target;
  };
  requestAnimationFrame(update);
}

const statObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const target = parseInt(entry.target.dataset.count);
      if (!isNaN(target)) animateCount(entry.target, target);
      statObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll("[data-count]").forEach(el => statObserver.observe(el));

/* ── Typewriter Hero ────────────────────────────── */
const TW_WORDS = [
  "supercharge your work",
  "unlock creativity",
  "10x your output",
  "spark ideas instantly",
  "write like a pro",
  "code smarter"
];
let twIndex = 0, twChar = 0, twDeleting = false;
const twEl = document.getElementById("typewriterText");

function typewriterTick() {
  if (!twEl) return;
  const word = TW_WORDS[twIndex];
  if (!twDeleting) {
    twEl.textContent = word.slice(0, ++twChar);
    if (twChar === word.length) {
      twDeleting = true;
      setTimeout(typewriterTick, 2000);
      return;
    }
    setTimeout(typewriterTick, 55);
  } else {
    twEl.textContent = word.slice(0, --twChar);
    if (twChar === 0) {
      twDeleting = false;
      twIndex = (twIndex + 1) % TW_WORDS.length;
      setTimeout(typewriterTick, 400);
      return;
    }
    setTimeout(typewriterTick, 30);
  }
}
if (twEl) {
  if (performanceMode) {
    twEl.textContent = TW_WORDS[0];
  } else {
    setTimeout(typewriterTick, 800);
  }
}

/* ── Terminal Showcase ──────────────────────────── */
const SHOWCASE_PROMPTS = [
  { cat: "prompt-vault › coding", text: "You are a senior code reviewer. Analyze this code for bugs, security vulnerabilities, and performance issues. Provide specific, actionable feedback with examples..." },
  { cat: "prompt-vault › marketing", text: "Create a viral Twitter thread about [TOPIC]. Hook readers with the first tweet, use punchy sentences, include surprising insights, and end with a strong call-to-action..." },
  { cat: "prompt-vault › writing", text: "You are an award-winning editor. Rewrite this text to be 50% shorter while preserving all key information. Use active voice, cut filler words, and make every sentence count..." },
  { cat: "prompt-vault › business", text: "Act as a startup advisor. Evaluate my idea: [IDEA]. Give me strengths, weaknesses, target market estimate, MVP suggestion, and a score out of 10..." },
  { cat: "prompt-vault › education", text: "You are a world-class tutor. Teach me [CONCEPT] using: a simple real-world analogy, step-by-step explanation, 2 practical examples, and a quick quiz question..." },
];

let scIndex = 0, scTyping = false;
const termOutput   = document.getElementById("termOutput");
const termCategory = document.getElementById("termCategory");
const dotsWrap     = document.getElementById("showcaseDots");

if (dotsWrap) {
  SHOWCASE_PROMPTS.forEach((_, i) => {
    const d = document.createElement("div");
    d.className = "sdot" + (i === 0 ? " active" : "");
    d.addEventListener("click", () => loadShowcase(i));
    dotsWrap.appendChild(d);
  });
}

function updateDots(index) {
  document.querySelectorAll(".sdot").forEach((d, i) =>
    d.classList.toggle("active", i === index));
}

function typeTerminal(text, callback) {
  if (!termOutput) return;
  termOutput.textContent = "";
  let i = 0;
  const tick = () => {
    if (i < text.length) {
      termOutput.textContent += text[i++];
      setTimeout(tick, Math.random() * 18 + 8);
    } else if (callback) {
      setTimeout(callback, 2800);
    }
  };
  tick();
}

function loadShowcase(index) {
  if (scTyping) return;
  scTyping = true;
  scIndex = index;
  const p = SHOWCASE_PROMPTS[index];
  if (termCategory) termCategory.textContent = p.cat;
  updateDots(index);
  if (termOutput) termOutput.textContent = "";
  typeTerminal(p.text, () => {
    scTyping = false;
    scIndex  = (scIndex + 1) % SHOWCASE_PROMPTS.length;
    setTimeout(() => loadShowcase(scIndex), 400);
  });
}

if (termOutput) {
  if (performanceMode) {
    const firstPrompt = SHOWCASE_PROMPTS[0];
    if (termCategory) termCategory.textContent = firstPrompt.cat;
    termOutput.textContent = firstPrompt.text;
    updateDots(0);
  } else {
    setTimeout(() => loadShowcase(0), 600);
  }
}

/* ── Flash auto-dismiss ─────────────────────────── */
document.querySelectorAll(".flash").forEach(el => {
  if (el.classList.contains("flash-sticky")) return;
  setTimeout(() => {
    el.style.transition = "opacity .4s, transform .4s";
    el.style.opacity = "0";
    el.style.transform = "translateX(20px) scale(.95)";
    setTimeout(() => el.remove(), 400);
  }, 4500);
});

/* ── Like prompt (grid) ─────────────────────────── */
function likePrompt(id, btn) {

    fetch(`/api/like/${id}`, {
        method: "POST"
    })
    .then(r => {

        if (r.status === 401) {
            location.href = "/login";
            return null;
        }

        if (r.status === 403) {
            alert("Please verify your email to like prompts.");
            return null;
        }

        return r.json();

    })
    .then(d => {

        if (!d) return;

        btn.querySelector(".like-num").textContent = d.likes;

        if (d.liked) {
            btn.classList.add("liked");
        } else {
            btn.classList.remove("liked");
        }

    })
    .catch(console.error);
}

/* ── Like prompt (detail) ───────────────────────── */
function likePromptDetail(id, btn) {

    fetch(`/api/like/${id}`, {
        method: "POST"
    })
    .then(r => {

        if (r.status === 401) {
            location.href = "/login";
            return null;
        }

        if (r.status === 403) {
            alert("Please verify your email to like prompts.");
            return null;
        }

        return r.json();

    })
    .then(d => {

        if (!d) return;

        document.getElementById("likeCount").textContent = d.likes;

        if (d.liked) {
            btn.classList.add("liked");
        } else {
            btn.classList.remove("liked");
        }

    })
    .catch(console.error);
}

/* ── Toggle favorite (grid) ─────────────────────── */
function toggleFavorite(id, btn) {
  fetch(`/api/favorite/${id}`, { method: "POST" })
    .then(r => {
      if (r.status === 401) { location.href="/login"; return null; }
      if (r.status === 403) {
        const errorMsg = "Please verify your email to save favorites.";
        alert(errorMsg);
        return null;
      }
      return r.json();
    })
    .then(d => {
      if (!d) return;
      const svg = btn.querySelector("svg");
      if (d.status === "added") {
        btn.classList.add("active");
        svg.setAttribute("fill", "currentColor");
      } else {
        btn.classList.remove("active");
        svg.setAttribute("fill", "none");
        if (location.pathname === "/favorites") {
          const card = btn.closest(".pcard");
          if (card) {
            card.style.transition = "opacity .3s, transform .3s";
            card.style.opacity = "0"; card.style.transform = "scale(.94)";
            setTimeout(() => { card.remove(); if (!document.querySelector(".pcard")) location.reload(); }, 300);
          }
        }
      }
    }).catch(console.error);
}

/* ── Toggle favorite (detail) ───────────────────── */
/* ── Toggle favorite (detail) ───────────────────── */
function toggleFavDetail(id, btn) {
  fetch(`/api/favorite/${id}`, { method: "POST" })
    .then(r => {
      if (r.status === 401) { location.href="/login"; return null; }
      if (r.status === 403) {
        const errorMsg = "Please verify your email to save favorites.";
        alert(errorMsg);
        return null;
      }
      return r.json();
    })
    .then(d => {
      if (!d) return;
      btn.classList.toggle("active", d.status === "added");
      btn.textContent = d.status === "added" ? "♥ Saved" : "♡ Save";
    }).catch(console.error);
}

/* ── Copy prompt (grid) ─────────────────────────── */
function copyPrompt(id, content, btn) {
    const text = content.replace(/\\n/g, "\n");

    if (navigator.clipboard && window.isSecureContext) {

        navigator.clipboard.writeText(text)
            .then(() => {
                const orig = btn.innerHTML;

                btn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span>Copied!</span>`;

                btn.classList.add("copied");

                fetch(`/api/copy/${id}`, {
                    method: "POST"
                }).catch(console.error);

                setTimeout(() => {
                    btn.innerHTML = orig;
                    btn.classList.remove("copied");
                }, 2200);
            });

    } else {

        fallbackCopy(text, btn);

        fetch(`/api/copy/${id}`, {
            method: "POST"
        }).catch(console.error);
    }
}

/* ── Copy prompt (detail) ───────────────────────── */
function copyDetailPrompt(id, btn) {
  const text = document.getElementById("promptContent").textContent;
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = "✓ Copied!";
    btn.classList.add("copied");
    fetch(`/api/copy/${id}`, { method: "POST" }).catch(console.error);
    setTimeout(() => { btn.textContent = orig; btn.classList.remove("copied"); }, 2500);
  }).catch(() => fallbackCopy(text, btn));
}

function fallbackCopy(text, btn) {
  const ta = document.createElement("textarea");
  ta.value = text;
  document.body.appendChild(ta); ta.select();
  document.execCommand("copy"); document.body.removeChild(ta);
  if (btn) { const o = btn.textContent; btn.textContent = "✓ Copied!"; setTimeout(() => btn.textContent = o, 2000); }
}

/* ── Password toggle ────────────────────────────── */
function togglePassword(id, btn) {
  const f = document.getElementById(id);
  if (!f) return;
  f.type = f.type === "password" ? "text" : "password";
  btn.textContent = f.type === "text" ? "🙈" : "👁";
}

/* ── Smooth scroll ──────────────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener("click", e => {
    const t = document.querySelector(a.getAttribute("href"));
    if (t) { e.preventDefault(); t.scrollIntoView({ behavior: "smooth", block: "start" }); }
  });
});

/* ── Improve Prompt ───────────────────────── */

async function improvePrompt(event) {

    event.preventDefault();

    const promptInput = document.getElementById("promptInput");
    const output = document.getElementById("output");
    const loading = document.getElementById("loading");
    const resultBox = document.getElementById("resultBox");

    const prompt = promptInput.value.trim();

    if (!prompt) {
        alert("Please enter a prompt");
        return;
    }

    loading.innerHTML = "Improving...";
    resultBox.style.display = "none";

    try {

        const response = await fetch("/api/improve", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                prompt: prompt
            })
        });

        const data = await response.json();

        console.log(data);

        if (data.error) {

            output.innerHTML = data.error;

        } else {

            output.innerText = data.improved_prompt;

        }

        resultBox.style.display = "block";

    } catch (error) {

        console.error(error);

        output.innerHTML = "Something went wrong.";

        resultBox.style.display = "block";
    }

    loading.innerHTML = "";
}
/* ── Copy Improved Prompt ───────────────────────── */

function copyImprovedPrompt() {

    const output = document.getElementById("output");

    const text = output.innerText;

    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {

        const btn = document.querySelector(".copy-btn");

        const original = btn.innerText;

        btn.innerText = "Copied!";

        setTimeout(() => {

            btn.innerText = original;

        }, 2000);

    });

}
