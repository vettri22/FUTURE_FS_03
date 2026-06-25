# 🌸 KOMUDHA Boutique — Production-Ready E-Commerce

A complete luxury women's fashion e-commerce platform built with Flask, MySQL, and Razorpay.

---

## 🚀 Quick Start (5 Steps)

### Step 1 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Set up MySQL database
```bash
mysql -u root -p < database.sql
```

### Step 3 — Configure environment
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### Step 4 — Run the server
```bash
python run.py
```

### Step 5 — Open in browser
- **Store:**  http://localhost:5000
- **Admin:**  http://localhost:5000/admin

**Dev login:** Any 10-digit mobile number + OTP `123456`  
**Admin login:** Mobile `9876543210` + OTP `123456`

---

## 📁 Project Structure

```
komudha/
├── app.py                  # Main Flask application (all routes)
├── config.py               # Configuration (dev/prod)
├── run.py                  # Development server starter
├── database.sql            # Complete MySQL schema + seed data
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
│
├── static/
│   ├── css/
│   │   ├── main.css        # Full storefront styles
│   │   └── admin.css       # Admin panel styles
│   ├── js/
│   │   ├── main.js         # Storefront JavaScript
│   │   └── admin.js        # Admin panel JavaScript
│   └── uploads/
│       ├── products/       # Product images (auto-created)
│       └── banners/        # Banner images (auto-created)
│
└── templates/
    ├── base.html           # Storefront base layout
    ├── index.html          # Homepage
    ├── shop.html           # Shop / product listing
    ├── product.html        # Product detail page
    ├── auth.html           # Login / Register (OTP)
    ├── cart.html           # Shopping cart
    ├── checkout.html       # Checkout + Razorpay
    ├── order_confirmation.html
    ├── dashboard.html      # User dashboard
    ├── my_orders.html      # Order history
    ├── order_detail.html   # Order tracking
    ├── wishlist.html       # Wishlist page
    ├── 404.html            # Error page
    └── admin/
        ├── base.html       # Admin base layout
        ├── login.html      # Admin OTP login
        ├── dashboard.html  # Analytics dashboard
        ├── products.html   # Product list
        ├── add_product.html
        ├── edit_product.html
        ├── orders.html     # Order management
        ├── order_detail.html
        ├── customers.html
        ├── categories.html
        ├── coupons.html
        ├── reviews.html
        ├── newsletter.html
        └── settings.html
```

---

## ✨ Features

### Storefront
| Feature | Details |
|---|---|
| Homepage | Hero, Categories, Flash Sale, New Arrivals, Featured, Trending, Best Sellers, Reviews, Newsletter, Instagram |
| Shop | Grid layout, Category/Price/Sort filters, Search with suggestions, Pagination |
| Product | Multi-image gallery with zoom, Sizes, Colors, Quantity, Add to Cart, Wishlist, Reviews |
| Authentication | Mobile OTP login (passwordless), Registration, Session management |
| Cart | Add/Remove/Update, Coupon codes, Live price recalculation |
| Checkout | Address management, Razorpay integration (Cards/UPI/NetBanking/Wallets) |
| User Dashboard | Profile, Order history, Order tracking, Wishlist, Recently Viewed |
| AI Stylist | Chatbot with fashion recommendations (rule-based + extensible) |
| WhatsApp | Floating support button |

### Admin Panel
| Feature | Details |
|---|---|
| Dashboard | Revenue/orders/customers/products stats, Monthly chart, Top products |
| Products | Full CRUD, Multi-image upload, Size/color variants, Labels (featured/new/trending etc.) |
| Orders | List with status filters, Full detail view, Status update with timeline |
| Customers | Customer list with order history and spend |
| Categories | Add/manage categories |
| Coupons | Create percentage/fixed coupons with limits, expiry, and min-order rules |
| Reviews | Approve/reject customer reviews |
| Newsletter | Subscriber list with CSV export |
| Settings | Store info, Shipping, Razorpay keys, Social media, Admin mobile |

---

## 🔐 Security

- **Passwordless auth** — Mobile OTP only (no password storage)
- **OTP expiry** — 10 minutes, single-use, stored hashed
- **Admin isolation** — Only whitelisted mobile can access admin
- **Razorpay signature verification** — Server-side payment validation
- **SQL injection protection** — Parameterised queries throughout
- **XSS protection** — Jinja2 auto-escaping enabled
- **Session security** — HttpOnly cookies, 30-day persistence

---

## 💳 Razorpay Setup

1. Sign up at [razorpay.com](https://razorpay.com)
2. Go to **Settings → API Keys → Generate Test Key**
3. Copy `Key ID` and `Key Secret` to `.env`
4. For production: activate account and switch to live keys

Supported payment methods: Credit/Debit Cards, UPI, Net Banking, Wallets, EMI.

---

## 📱 SMS OTP Setup (Fast2SMS)

1. Sign up at [fast2sms.com](https://fast2sms.com)
2. Get your API key from the dashboard
3. Add to `.env` as `SMS_API_KEY`
4. Set `DEV_MODE_OTP=False` in production

**Dev mode** (`DEV_MODE_OTP=True`): OTP is always `123456`, printed to console. No SMS sent.

---

## 🗄️ Database Tables

| Table | Purpose |
|---|---|
| users | Customer accounts |
| otp_verifications | OTP storage with expiry |
| categories | Product categories |
| products | Product catalogue |
| product_images | Multiple images per product |
| product_sizes | Size variants with stock |
| product_colors | Color variants |
| addresses | Saved delivery addresses |
| cart | Shopping cart |
| wishlist | Saved products |
| orders | Order records |
| order_items | Line items per order |
| order_tracking | Status timeline |
| coupons | Discount codes |
| reviews | Product reviews |
| banners | Homepage banners |
| newsletter_subscribers | Email list |
| recently_viewed | Browsing history |
| settings | Store configuration |

---

## 🎨 Design System

| Token | Value |
|---|---|
| Primary | Rose Gold `#B76E79` |
| Accent | Gold `#C8A96E` |
| Background | Warm White `#FFFAF8` |
| Text | Charcoal `#2C2C2C` |
| Display Font | Playfair Display |
| Body Font | Poppins |

---

## 🚀 Production Deployment

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Or with nginx reverse proxy (recommended)
gunicorn -w 4 --bind unix:/tmp/komudha.sock app:app
```

**Checklist before going live:**
- [ ] Change `SECRET_KEY` to a long random string
- [ ] Set `DEV_MODE_OTP=False`
- [ ] Add real Fast2SMS API key
- [ ] Switch to Razorpay live keys
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set up database backups
- [ ] Configure a proper SMTP for emails

---

## 📞 Support

- WhatsApp: Floating button in the store
- Admin: /admin panel → Settings to update contact info

---

*Built with ♡ for Indian Women's Fashion*
