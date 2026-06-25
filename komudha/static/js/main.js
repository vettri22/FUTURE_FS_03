/* ============================================================
   KOMUDHA BOUTIQUE - Main JavaScript
   ============================================================ */

'use strict';

// ── Toast Notifications ────────────────────────────────────
const Toast = {
  container: null,
  init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  },
  show(message, type = 'info', duration = 3500) {
    const icons = { success: '✓', error: '✕', info: '♡', warning: '!' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span>${message}</span>`;
    this.container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(40px)'; toast.style.transition = '0.3s'; setTimeout(() => toast.remove(), 300); }, duration);
  }
};

// ── API Helper ─────────────────────────────────────────────
async function apiPost(url, data = {}) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await res.json();
  } catch (e) {
    return { success: false, message: 'Network error. Please try again.' };
  }
}

async function apiGet(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (e) {
    return null;
  }
}

// ── Navbar ─────────────────────────────────────────────────
function initNavbar() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;

  const isTransparent = navbar.classList.contains('transparent');

  window.addEventListener('scroll', () => {
    if (isTransparent) {
      navbar.classList.toggle('scrolled', window.scrollY > 60);
    }
  }, { passive: true });

  // Hamburger menu
  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      const open = mobileMenu.classList.toggle('open');
      hamburger.classList.toggle('open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    });
  }

  // Search
  const searchToggle = document.querySelector('[data-search-toggle]');
  const searchWrap = document.querySelector('.navbar-search-wrap');
  const searchInput = document.querySelector('.navbar-search-input');
  if (searchToggle && searchWrap) {
    searchToggle.addEventListener('click', () => {
      searchWrap.classList.toggle('open');
      if (searchWrap.classList.contains('open')) searchInput?.focus();
    });
  }

  // Search suggestions
  if (searchInput) {
    let debounceTimer;
    const suggestionsBox = document.querySelector('.search-suggestions');
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async () => {
        const q = searchInput.value.trim();
        if (q.length < 2) { suggestionsBox && (suggestionsBox.innerHTML = '', suggestionsBox.style.display = 'none'); return; }
        const results = await apiGet(`/api/search/suggestions?q=${encodeURIComponent(q)}`);
        if (results && results.length && suggestionsBox) {
          suggestionsBox.innerHTML = results.map(r => `<a href="/product/${r.slug}" class="search-suggestion-item">${r.name}</a>`).join('');
          suggestionsBox.style.display = 'block';
        } else if (suggestionsBox) { suggestionsBox.style.display = 'none'; }
      }, 300);
    });
    document.addEventListener('click', e => {
      if (!searchWrap?.contains(e.target)) { searchWrap?.classList.remove('open'); suggestionsBox && (suggestionsBox.style.display = 'none'); }
    });
  }
}

// ── Cart Functions ─────────────────────────────────────────
async function addToCart(productId, size, color, quantity = 1) {
  if (!size) { Toast.show('Please select a size', 'warning'); return; }
  const btn = document.querySelector('[data-add-cart]');
  if (btn) { btn.classList.add('btn-loading'); btn.textContent = 'Adding...'; }
  const res = await apiPost('/api/cart/add', { product_id: productId, size, color, quantity });
  if (btn) { btn.classList.remove('btn-loading'); btn.innerHTML = '<i class="fas fa-shopping-bag"></i> Add to Cart'; }
  if (res.success) {
    Toast.show(res.message, 'success');
    updateCartCount(res.cart_count);
  } else {
    Toast.show(res.message, 'error');
  }
}

function updateCartCount(count) {
  document.querySelectorAll('.cart-count-badge').forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? 'flex' : 'none';
  });
}

async function removeCartItem(cartId, rowEl) {
  const res = await apiPost('/api/cart/remove', { cart_id: cartId });
  if (res.success) {
    rowEl?.remove();
    Toast.show('Item removed', 'info');
    recalcCart();
  }
}

async function updateCartQty(cartId, newQty, priceEl, rowEl) {
  const res = await apiPost('/api/cart/update', { cart_id: cartId, quantity: newQty });
  if (res.success) {
    if (newQty < 1) { rowEl?.remove(); recalcCart(); return; }
    recalcCart();
  }
}

function recalcCart() {
  let subtotal = 0;
  document.querySelectorAll('.cart-item[data-price]').forEach(item => {
    const qty = parseInt(item.querySelector('.qty-input')?.value || 0);
    const price = parseFloat(item.dataset.price || 0);
    const lineEl = item.querySelector('.cart-line-total');
    if (lineEl) lineEl.textContent = '₹' + (price * qty).toLocaleString('en-IN', { minimumFractionDigits: 2 });
    subtotal += price * qty;
  });
  const subtotalEl = document.getElementById('cart-subtotal');
  const totalEl = document.getElementById('cart-total');
  const shippingEl = document.getElementById('cart-shipping');
  const freeShipping = 999;
  const shippingCost = subtotal >= freeShipping ? 0 : 99;
  if (subtotalEl) subtotalEl.textContent = '₹' + subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 });
  if (shippingEl) shippingEl.textContent = shippingCost === 0 ? 'FREE' : '₹' + shippingCost;
  const discount = parseFloat(document.getElementById('cart-discount')?.dataset.amount || 0);
  if (totalEl) totalEl.textContent = '₹' + (subtotal - discount + shippingCost).toLocaleString('en-IN', { minimumFractionDigits: 2 });
}

// ── Wishlist ───────────────────────────────────────────────
async function toggleWishlist(productId, btn) {
  const res = await apiPost('/api/wishlist/toggle', { product_id: productId });
  if (res.success) {
    btn.classList.toggle('active', res.action === 'added');
    Toast.show(res.action === 'added' ? 'Added to wishlist ♡' : 'Removed from wishlist', res.action === 'added' ? 'success' : 'info');
  } else if (res.message === 'Login required') {
    window.location.href = '/auth';
  }
}

// ── Product Detail Page ────────────────────────────────────
function initProductDetail() {
  const detail = document.querySelector('.product-detail-grid');
  if (!detail) return;

  // Gallery
  const mainImg = document.querySelector('.gallery-main img');
  const thumbs = document.querySelectorAll('.gallery-thumb');
  thumbs.forEach(thumb => {
    thumb.addEventListener('click', () => {
      thumbs.forEach(t => t.classList.remove('active'));
      thumb.classList.add('active');
      const src = thumb.dataset.src;
      if (mainImg && src) { mainImg.style.opacity = '0'; setTimeout(() => { mainImg.src = src; mainImg.style.opacity = '1'; }, 150); mainImg.style.transition = 'opacity 0.15s'; }
    });
  });

  // Size selection
  const sizeBtns = document.querySelectorAll('.size-btn:not(.out-of-stock)');
  let selectedSize = '';
  sizeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      sizeBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedSize = btn.dataset.size;
    });
  });

  // Color selection
  const colorBtns = document.querySelectorAll('.color-btn');
  let selectedColor = '';
  colorBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      colorBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedColor = btn.dataset.color;
    });
  });

  // Quantity
  const qtyInput = document.querySelector('.qty-input');
  document.querySelector('.qty-increase')?.addEventListener('click', () => {
    if (qtyInput) qtyInput.value = Math.min(10, parseInt(qtyInput.value) + 1);
  });
  document.querySelector('.qty-decrease')?.addEventListener('click', () => {
    if (qtyInput) qtyInput.value = Math.max(1, parseInt(qtyInput.value) - 1);
  });

  // Add to Cart
  document.querySelector('[data-add-cart]')?.addEventListener('click', function () {
    const productId = this.dataset.productId;
    const qty = parseInt(qtyInput?.value || 1);
    addToCart(productId, selectedSize, selectedColor, qty);
  });

  // Wishlist
  document.querySelector('[data-wishlist-btn]')?.addEventListener('click', function () {
    toggleWishlist(this.dataset.productId, this);
  });

  // Accordion
  document.querySelectorAll('.accordion-trigger').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const body = trigger.nextElementSibling;
      const isOpen = body.classList.contains('open');
      document.querySelectorAll('.accordion-body').forEach(b => { b.classList.remove('open'); b.previousElementSibling?.classList.remove('open'); });
      if (!isOpen) { body.classList.add('open'); trigger.classList.add('open'); }
    });
  });

  // Quick wishlist on product cards
  document.querySelectorAll('[data-quick-wishlist]').forEach(btn => {
    btn.addEventListener('click', (e) => { e.preventDefault(); toggleWishlist(btn.dataset.productId, btn); });
  });
}

// ── Flash Sale Countdown ───────────────────────────────────
function initFlashSaleTimer() {
  const timer = document.getElementById('flash-timer');
  if (!timer) return;
  const endTime = new Date(timer.dataset.ends).getTime();
  function update() {
    const now = Date.now();
    const diff = Math.max(0, endTime - now);
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    const pad = n => String(n).padStart(2, '0');
    document.getElementById('timer-h') && (document.getElementById('timer-h').textContent = pad(h));
    document.getElementById('timer-m') && (document.getElementById('timer-m').textContent = pad(m));
    document.getElementById('timer-s') && (document.getElementById('timer-s').textContent = pad(s));
    if (diff > 0) setTimeout(update, 1000);
  }
  update();
}

// ── Newsletter ─────────────────────────────────────────────
function initNewsletter() {
  document.querySelectorAll('.newsletter-form-el').forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const email = form.querySelector('[name="email"]')?.value;
      const name = form.querySelector('[name="name"]')?.value;
      if (!email) { Toast.show('Please enter your email', 'warning'); return; }
      const btn = form.querySelector('button');
      if (btn) { btn.textContent = 'Subscribing...'; btn.disabled = true; }
      const res = await apiPost('/api/newsletter/subscribe', { email, name });
      if (btn) { btn.textContent = 'Subscribe'; btn.disabled = false; }
      Toast.show(res.message, res.success ? 'success' : 'error');
      if (res.success) form.reset();
    });
  });
}

// ── Coupon ─────────────────────────────────────────────────
function initCoupon() {
  const btn = document.getElementById('apply-coupon-btn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const code = document.getElementById('coupon-input')?.value.trim();
    if (!code) { Toast.show('Enter a coupon code', 'warning'); return; }
    btn.textContent = 'Applying...';
    const res = await apiPost('/api/coupon/apply', { code });
    btn.textContent = 'Apply';
    if (res.success) {
      Toast.show(res.message, 'success');
      const discountEl = document.getElementById('cart-discount');
      if (discountEl) { discountEl.textContent = '-₹' + res.discount.toFixed(2); discountEl.dataset.amount = res.discount; }
      recalcCart();
    } else {
      Toast.show(res.message, 'error');
    }
  });
}

// ── Review Submission ──────────────────────────────────────
function initReviewForm() {
  const form = document.getElementById('review-form');
  if (!form) return;
  let selectedRating = 5;
  document.querySelectorAll('.rating-star').forEach(star => {
    star.addEventListener('click', () => {
      selectedRating = parseInt(star.dataset.rating);
      document.querySelectorAll('.rating-star').forEach((s, i) => s.classList.toggle('active', i < selectedRating));
    });
    star.addEventListener('mouseenter', () => {
      const hov = parseInt(star.dataset.rating);
      document.querySelectorAll('.rating-star').forEach((s, i) => s.classList.toggle('hover', i < hov));
    });
    star.addEventListener('mouseleave', () => {
      document.querySelectorAll('.rating-star').forEach(s => s.classList.remove('hover'));
    });
  });
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const productId = form.dataset.productId;
    const review = form.querySelector('[name="review"]')?.value;
    const title = form.querySelector('[name="title"]')?.value;
    const res = await apiPost('/api/review/submit', { product_id: productId, rating: selectedRating, review, title });
    Toast.show(res.message, res.success ? 'success' : 'error');
    if (res.success) form.reset();
  });
}

// ── Chatbot ────────────────────────────────────────────────
function initChatbot() {
  const widget = document.getElementById('chatbot-widget');
  const toggle = document.getElementById('chatbot-toggle');
  const closeBtn = document.getElementById('chatbot-close');
  const input = document.getElementById('chatbot-input');
  const sendBtn = document.getElementById('chatbot-send');
  const messages = document.getElementById('chatbot-messages');
  if (!widget || !toggle) return;

  function addMessage(text, isBot = true) {
    const div = document.createElement('div');
    div.className = `chat-msg ${isBot ? 'bot' : 'user'}`;
    div.innerHTML = `<div class="chat-bubble">${text}</div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  toggle.addEventListener('click', () => { widget.classList.toggle('open'); if (widget.classList.contains('open')) input?.focus(); });
  closeBtn?.addEventListener('click', () => widget.classList.remove('open'));

  async function sendMessage() {
    const msg = input?.value.trim();
    if (!msg) return;
    addMessage(msg, false);
    input.value = '';
    const res = await apiPost('/api/stylist/chat', { message: msg });
    addMessage(res.reply || 'I\'m here to help! 💕');
  }

  sendBtn?.addEventListener('click', sendMessage);
  input?.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });
}

// ── Scroll Animation ───────────────────────────────────────
function initScrollAnimation() {
  if (!('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
}

// ── Scroll Row Controls ────────────────────────────────────
function initScrollRows() {
  document.querySelectorAll('[data-scroll-row]').forEach(wrap => {
    const row = wrap.querySelector('.scroll-row');
    const prevBtn = wrap.querySelector('[data-scroll-prev]');
    const nextBtn = wrap.querySelector('[data-scroll-next]');
    if (!row) return;
    const scrollAmt = 300;
    prevBtn?.addEventListener('click', () => row.scrollBy({ left: -scrollAmt, behavior: 'smooth' }));
    nextBtn?.addEventListener('click', () => row.scrollBy({ left: scrollAmt, behavior: 'smooth' }));
  });
}

// ── Quick Add to Cart (from cards) ────────────────────────
function initQuickAdd() {
  document.querySelectorAll('.quick-add-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.preventDefault();
      const productId = btn.dataset.productId;
      const res = await apiPost('/api/cart/add', { product_id: productId, size: 'Default', quantity: 1 });
      if (res.success) { Toast.show('Added to cart!', 'success'); updateCartCount(res.cart_count); }
      else if (res.message && res.message.includes('size')) { window.location.href = btn.dataset.href || '#'; }
      else Toast.show(res.message || 'Error', 'error');
    });
  });
}

// ── Image Lazy Loading ─────────────────────────────────────
function initLazyLoad() {
  if ('loading' in HTMLImageElement.prototype) return;
  if (!('IntersectionObserver' in window)) return;
  const imgObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        if (img.dataset.src) { img.src = img.dataset.src; img.removeAttribute('data-src'); }
        imgObserver.unobserve(img);
      }
    });
  });
  document.querySelectorAll('img[data-src]').forEach(img => imgObserver.observe(img));
}

// ── Cart Page ──────────────────────────────────────────────
function initCartPage() {
  document.querySelectorAll('.qty-increase').forEach(btn => {
    btn.addEventListener('click', () => {
      const row = btn.closest('.cart-item');
      const input = row?.querySelector('.qty-input');
      if (!input) return;
      const newQty = parseInt(input.value) + 1;
      if (newQty > 10) return;
      input.value = newQty;
      updateCartQty(row.dataset.cartId, newQty, null, row);
    });
  });
  document.querySelectorAll('.qty-decrease').forEach(btn => {
    btn.addEventListener('click', () => {
      const row = btn.closest('.cart-item');
      const input = row?.querySelector('.qty-input');
      if (!input) return;
      const newQty = parseInt(input.value) - 1;
      input.value = Math.max(0, newQty);
      updateCartQty(row.dataset.cartId, newQty, null, row);
    });
  });
  document.querySelectorAll('.cart-item-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      const row = btn.closest('.cart-item');
      removeCartItem(row?.dataset.cartId, row);
    });
  });
}

// ── Profile Update ─────────────────────────────────────────
function initProfile() {
  const form = document.getElementById('profile-form');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    const res = await apiPost('/api/profile/update', data);
    Toast.show(res.message, res.success ? 'success' : 'error');
  });
}

// ── Init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Toast.init();
  initNavbar();
  initProductDetail();
  initFlashSaleTimer();
  initNewsletter();
  initCoupon();
  initReviewForm();
  initChatbot();
  initScrollAnimation();
  initScrollRows();
  initQuickAdd();
  initLazyLoad();
  initCartPage();
  initProfile();
});
