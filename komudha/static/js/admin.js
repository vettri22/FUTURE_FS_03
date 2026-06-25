/* ============================================================
   KOMUDHA BOUTIQUE - Admin JavaScript
   ============================================================ */
'use strict';

// ── Toast ──────────────────────────────────────────────────
function adminToast(msg, type = 'success') {
  const existing = document.querySelector('.admin-toast');
  existing?.remove();
  const t = document.createElement('div');
  t.className = `admin-toast admin-alert admin-alert-${type === 'success' ? 'success' : type === 'error' ? 'error' : 'info'}`;
  t.style.cssText = 'position:fixed;top:80px;right:24px;z-index:9999;min-width:280px;animation:slideInRight 0.3s ease;';
  t.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle'}"></i> ${msg}`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

async function adminApiPost(url, data = {}) {
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  return await res.json();
}

// ── Sidebar Toggle (Mobile) ────────────────────────────────
function initSidebar() {
  const menuBtn = document.getElementById('admin-menu-toggle');
  const sidebar = document.querySelector('.admin-sidebar');
  menuBtn?.addEventListener('click', () => sidebar?.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (window.innerWidth < 768 && sidebar && !sidebar.contains(e.target) && e.target !== menuBtn) {
      sidebar.classList.remove('open');
    }
  });
}

// ── OTP Login (Admin) ──────────────────────────────────────
function initAdminLogin() {
  const step1 = document.getElementById('admin-step1');
  const step2 = document.getElementById('admin-step2');
  const sendBtn = document.getElementById('admin-send-otp');
  const verifyBtn = document.getElementById('admin-verify-otp');
  const mobileInput = document.getElementById('admin-mobile');
  let adminMobile = '';

  sendBtn?.addEventListener('click', async () => {
    adminMobile = mobileInput?.value.trim();
    if (!adminMobile || adminMobile.length !== 10) { adminToast('Enter valid 10-digit mobile', 'error'); return; }
    sendBtn.textContent = 'Sending...';
    const res = await adminApiPost('/api/send-otp', { mobile: adminMobile });
    sendBtn.textContent = 'Send OTP';
    if (res.success) { step1.style.display = 'none'; step2.style.display = 'block'; adminToast('OTP sent!'); }
    else adminToast(res.message, 'error');
  });

  const digits = document.querySelectorAll('.admin-otp-digit');
  digits.forEach((d, i) => {
    d.addEventListener('input', () => { if (d.value.length === 1 && digits[i + 1]) digits[i + 1].focus(); });
    d.addEventListener('keydown', e => { if (e.key === 'Backspace' && !d.value && digits[i - 1]) digits[i - 1].focus(); });
  });

  verifyBtn?.addEventListener('click', async () => {
    const otp = Array.from(digits).map(d => d.value).join('');
    if (otp.length !== 6) { adminToast('Enter 6-digit OTP', 'error'); return; }
    verifyBtn.textContent = 'Verifying...';
    const res = await adminApiPost('/api/verify-otp', { mobile: adminMobile, otp });
    verifyBtn.textContent = 'Verify & Login';
    if (res.success) { adminToast('Login successful!'); window.location.href = res.redirect; }
    else adminToast(res.message, 'error');
  });

  document.getElementById('admin-resend')?.addEventListener('click', () => sendBtn?.click());
}

// ── Delete Product ─────────────────────────────────────────
function initProductActions() {
  document.querySelectorAll('[data-delete-product]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this product?')) return;
      const id = btn.dataset.deleteProduct;
      const res = await adminApiPost(`/admin/products/delete/${id}`);
      if (res.success) { btn.closest('tr')?.remove(); adminToast('Product deleted'); }
    });
  });
}

// ── Image Upload Preview ───────────────────────────────────
function initImageUpload() {
  const input = document.getElementById('product-images');
  const preview = document.getElementById('image-preview');
  if (!input || !preview) return;

  input.addEventListener('change', () => {
    preview.innerHTML = '';
    Array.from(input.files).forEach(file => {
      const reader = new FileReader();
      reader.onload = e => {
        const div = document.createElement('div');
        div.className = 'img-preview-item';
        div.innerHTML = `<img src="${e.target.result}" alt=""><button class="img-preview-remove" type="button">×</button>`;
        preview.appendChild(div);
        div.querySelector('.img-preview-remove').onclick = () => div.remove();
      };
      reader.readAsDataURL(file);
    });
  });

  const uploadArea = document.querySelector('.upload-area');
  uploadArea?.addEventListener('click', () => input.click());
  uploadArea?.addEventListener('dragover', e => { e.preventDefault(); uploadArea.style.background = 'rgba(183,110,121,0.12)'; });
  uploadArea?.addEventListener('dragleave', () => uploadArea.style.background = '');
  uploadArea?.addEventListener('drop', e => {
    e.preventDefault(); uploadArea.style.background = '';
    const dt = new DataTransfer();
    Array.from(e.dataTransfer.files).forEach(f => dt.items.add(f));
    input.files = dt.files;
    input.dispatchEvent(new Event('change'));
  });
}

// ── Size Builder ───────────────────────────────────────────
function initSizeBuilder() {
  const container = document.getElementById('sizes-container');
  const addBtn = document.getElementById('add-size-btn');
  if (!container || !addBtn) return;
  addBtn.addEventListener('click', () => {
    const row = document.createElement('div');
    row.className = 'size-row';
    row.innerHTML = `<input type="text" name="sizes" placeholder="e.g. S, M, L, XL" class="form-control">
      <input type="number" name="size_stocks" placeholder="Stock" class="form-control" min="0">
      <button type="button" class="remove-row-btn"><i class="fas fa-times"></i></button>`;
    row.querySelector('.remove-row-btn').onclick = () => row.remove();
    container.appendChild(row);
  });
  container.addEventListener('click', e => {
    if (e.target.closest('.remove-row-btn')) e.target.closest('.size-row')?.remove();
  });
}

// ── Color Builder ──────────────────────────────────────────
function initColorBuilder() {
  const container = document.getElementById('colors-container');
  const addBtn = document.getElementById('add-color-btn');
  if (!container || !addBtn) return;
  addBtn.addEventListener('click', () => {
    const row = document.createElement('div');
    row.className = 'color-row';
    row.innerHTML = `<input type="text" name="color_names" placeholder="Color name" class="form-control">
      <input type="color" name="color_hexes" class="form-control" style="padding:4px;height:42px;">
      <button type="button" class="remove-row-btn"><i class="fas fa-times"></i></button>`;
    row.querySelector('.remove-row-btn').onclick = () => row.remove();
    container.appendChild(row);
  });
}

// ── Order Status Update ────────────────────────────────────
function initOrderStatusUpdate() {
  const btn = document.getElementById('update-status-btn');
  btn?.addEventListener('click', async () => {
    const orderId = btn.dataset.orderId;
    const status = document.getElementById('order-status-select')?.value;
    const desc = document.getElementById('order-status-desc')?.value || '';
    if (!status) { adminToast('Select a status', 'error'); return; }
    const res = await adminApiPost(`/admin/orders/${orderId}/update-status`, { status, description: desc });
    if (res.success) { adminToast('Order status updated!'); setTimeout(() => location.reload(), 800); }
    else adminToast('Error updating status', 'error');
  });
}

// ── Review Actions ─────────────────────────────────────────
function initReviewActions() {
  document.querySelectorAll('[data-approve-review]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.dataset.approveReview;
      const res = await adminApiPost(`/admin/reviews/${id}/approve`);
      if (res.success) { btn.closest('tr')?.querySelector('.review-status')?.replaceWith(Object.assign(document.createElement('span'), { className: 'admin-badge badge-active', textContent: 'Approved' })); btn.remove(); adminToast('Review approved!'); }
    });
  });
  document.querySelectorAll('[data-delete-review]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this review?')) return;
      const id = btn.dataset.deleteReview;
      const res = await adminApiPost(`/admin/reviews/${id}/delete`);
      if (res.success) { btn.closest('tr')?.remove(); adminToast('Review deleted'); }
    });
  });
}

// ── Revenue Chart ──────────────────────────────────────────
function initRevenueChart() {
  const canvas = document.getElementById('revenue-chart');
  if (!canvas || typeof Chart === 'undefined') return;
  const labels = JSON.parse(canvas.dataset.labels || '[]');
  const values = JSON.parse(canvas.dataset.values || '[]');
  new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Revenue (₹)',
        data: values,
        borderColor: '#B76E79',
        backgroundColor: 'rgba(183,110,121,0.08)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#B76E79',
        pointRadius: 4,
        pointHoverRadius: 7,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => '₹' + ctx.parsed.y.toLocaleString('en-IN') } } },
      scales: {
        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { callback: v => '₹' + (v / 1000).toFixed(0) + 'k', font: { size: 11 } } },
        x: { grid: { display: false }, ticks: { font: { size: 11 } } }
      }
    }
  });
}

// ── Table Search ───────────────────────────────────────────
function initTableSearch() {
  document.querySelectorAll('[data-search-table]').forEach(input => {
    const tableId = input.dataset.searchTable;
    const table = document.getElementById(tableId);
    input.addEventListener('input', () => {
      const q = input.value.toLowerCase();
      table?.querySelectorAll('tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  });
}

// ── Confirm Modals ─────────────────────────────────────────
function initConfirmActions() {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
    });
  });
}

// ── Category Toggle ────────────────────────────────────────
function initCategoryToggle() {
  document.querySelectorAll('[data-toggle-category]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.dataset.toggleCategory;
      adminToast('Category updated!');
    });
  });
}

// ── Coupon Toggle ──────────────────────────────────────────
function initCouponActions() {
  document.querySelectorAll('[data-toggle-coupon]').forEach(btn => {
    btn.addEventListener('click', () => adminToast('Coupon status updated'));
  });
}

// ── Init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initAdminLogin();
  initProductActions();
  initImageUpload();
  initSizeBuilder();
  initColorBuilder();
  initOrderStatusUpdate();
  initReviewActions();
  initRevenueChart();
  initTableSearch();
  initConfirmActions();
  initCategoryToggle();
  initCouponActions();
});
