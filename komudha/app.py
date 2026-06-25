"""
KOMUDHA Boutique - Main Flask Application
Production-Ready E-Commerce Backend
"""
import os, json, random, hashlib, hmac, time
from datetime import datetime, timedelta
from functools import wraps
from math import ceil

import mysql.connector
import razorpay
import requests
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash, abort)
from werkzeug.utils import secure_filename
from config import config

# ── App Factory ────────────────────────────────────────────────────────────────
app = Flask(__name__)
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'banners'), exist_ok=True)


# ── Database ───────────────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        database=app.config['DB_NAME'],
        charset='utf8mb4'
    )


def query(sql, params=None, fetchone=False, commit=False):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(sql, params or ())
    if commit:
        db.commit()
        last_id = cur.lastrowid
        cur.close(); db.close()
        return last_id
    result = cur.fetchone() if fetchone else cur.fetchall()
    cur.close(); db.close()
    return result


def get_setting(key):
    row = query("SELECT setting_value FROM settings WHERE setting_key=%s", (key,), fetchone=True)
    return row['setting_value'] if row else None


# ── Helpers ───────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp(mobile, otp):
    """Send OTP via Fast2SMS. In DEV_MODE uses console."""
    if app.config.get('DEV_MODE_OTP'):
        print(f"\n{'='*40}\nDEV OTP for {mobile}: {otp}\n{'='*40}\n")
        return True
    try:
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {"authorization": app.config['SMS_API_KEY']}
        payload = {
            "variables_values": otp,
            "route": "otp",
            "numbers": mobile,
        }
        resp = requests.post(url, headers=headers, data=payload, timeout=10)
        return resp.json().get('return', False)
    except Exception as e:
        print(f"SMS error: {e}")
        return False


def save_otp(mobile, otp):
    expires = datetime.now() + timedelta(minutes=app.config['OTP_EXPIRY_MINUTES'])
    query("DELETE FROM otp_verifications WHERE mobile=%s", (mobile,), commit=True)
    query("INSERT INTO otp_verifications (mobile,otp,expires_at) VALUES(%s,%s,%s)",
          (mobile, otp, expires), commit=True)


def verify_otp_db(mobile, otp):
    row = query(
        "SELECT * FROM otp_verifications WHERE mobile=%s AND otp=%s AND is_used=0 AND expires_at>NOW()",
        (mobile, otp), fetchone=True)
    if row:
        query("UPDATE otp_verifications SET is_used=1 WHERE id=%s", (row['id'],), commit=True)
        return True
    return False


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth_page', next=request.url))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def get_cart_count():
    if 'user_id' not in session:
        return 0
    row = query("SELECT SUM(quantity) as cnt FROM cart WHERE user_id=%s",
                (session['user_id'],), fetchone=True)
    return int(row['cnt'] or 0) if row else 0


def get_wishlist_ids():
    if 'user_id' not in session:
        return []
    rows = query("SELECT product_id FROM wishlist WHERE user_id=%s", (session['user_id'],))
    return [r['product_id'] for r in rows]


def get_product_primary_image(product_id):
    row = query("SELECT image_path FROM product_images WHERE product_id=%s AND is_primary=1 LIMIT 1",
                (product_id,), fetchone=True)
    return row['image_path'] if row else 'placeholder.jpg'


def slugify(text):
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


def format_currency(amount):
    return f"₹{amount:,.2f}"


app.jinja_env.globals.update(
    get_cart_count=get_cart_count,
    get_wishlist_ids=get_wishlist_ids,
    format_currency=format_currency,
    get_setting=get_setting,
    enumerate=enumerate,
    len=len,
    ceil=ceil,
)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    featured = query("SELECT p.*, pi.image_path FROM products p LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1 WHERE p.is_active=1 AND p.is_featured=1 ORDER BY p.created_at DESC LIMIT 8")
    new_arrivals = query("SELECT p.*, pi.image_path FROM products p LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1 WHERE p.is_active=1 AND p.is_new_arrival=1 ORDER BY p.created_at DESC LIMIT 8")
    best_sellers = query("SELECT p.*, pi.image_path FROM products p LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1 WHERE p.is_active=1 AND p.is_best_seller=1 ORDER BY p.created_at DESC LIMIT 8")
    trending = query("SELECT p.*, pi.image_path FROM products p LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1 WHERE p.is_active=1 AND p.is_trending=1 ORDER BY p.created_at DESC LIMIT 8")
    flash_sales = query("SELECT p.*, pi.image_path FROM products p LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1 WHERE p.is_active=1 AND p.is_flash_sale=1 AND p.flash_sale_ends>NOW() LIMIT 4")
    categories = query("SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order LIMIT 8")
    reviews = query("SELECT r.*, u.name as user_name, p.name as product_name FROM reviews r JOIN users u ON r.user_id=u.id JOIN products p ON r.product_id=p.id WHERE r.is_approved=1 ORDER BY r.created_at DESC LIMIT 6")
    return render_template('index.html', featured=featured, new_arrivals=new_arrivals,
                           best_sellers=best_sellers, trending=trending, flash_sales=flash_sales,
                           categories=categories, reviews=reviews)


@app.route('/shop')
def shop():
    page = int(request.args.get('page', 1))
    per_page = app.config['PRODUCTS_PER_PAGE']
    category = request.args.get('category', '')
    search = request.args.get('q', '')
    sort = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    where = ["p.is_active=1"]
    params = []

    if category:
        where.append("c.slug=%s")
        params.append(category)
    if search:
        where.append("(p.name LIKE %s OR p.description LIKE %s OR p.tags LIKE %s)")
        params.extend([f'%{search}%'] * 3)
    if min_price:
        where.append("COALESCE(p.sale_price,p.price)>=%s")
        params.append(min_price)
    if max_price:
        where.append("COALESCE(p.sale_price,p.price)<=%s")
        params.append(max_price)

    order = {
        'newest': 'p.created_at DESC',
        'price_low': 'COALESCE(p.sale_price,p.price) ASC',
        'price_high': 'COALESCE(p.sale_price,p.price) DESC',
        'popular': 'p.views DESC',
    }.get(sort, 'p.created_at DESC')

    where_str = " AND ".join(where)
    base_sql = f"""FROM products p LEFT JOIN categories c ON p.category_id=c.id
                   LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                   WHERE {where_str}"""

    total_row = query(f"SELECT COUNT(*) as cnt {base_sql}", params, fetchone=True)
    total = total_row['cnt'] if total_row else 0
    total_pages = ceil(total / per_page)
    offset = (page - 1) * per_page

    products = query(f"SELECT p.*, c.name as cat_name, pi.image_path {base_sql} ORDER BY {order} LIMIT %s OFFSET %s",
                     params + [per_page, offset])
    categories = query("SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order")

    return render_template('shop.html', products=products, categories=categories,
                           page=page, total_pages=total_pages, total=total,
                           current_category=category, search=search, sort=sort,
                           min_price=min_price, max_price=max_price)


@app.route('/product/<slug>')
def product_detail(slug):
    product = query("""SELECT p.*, c.name as cat_name, c.slug as cat_slug,
                       AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
                       FROM products p LEFT JOIN categories c ON p.category_id=c.id
                       LEFT JOIN reviews r ON p.id=r.product_id AND r.is_approved=1
                       WHERE p.slug=%s AND p.is_active=1 GROUP BY p.id""",
                    (slug,), fetchone=True)
    if not product:
        abort(404)

    # Increment view count
    query("UPDATE products SET views=views+1 WHERE id=%s", (product['id'],), commit=True)

    # Track recently viewed
    if 'user_id' in session:
        query("INSERT INTO recently_viewed (user_id,product_id) VALUES(%s,%s) ON DUPLICATE KEY UPDATE viewed_at=NOW()",
              (session['user_id'], product['id']), commit=True)

    images = query("SELECT * FROM product_images WHERE product_id=%s ORDER BY sort_order", (product['id'],))
    sizes = query("SELECT * FROM product_sizes WHERE product_id=%s", (product['id'],))
    colors = query("SELECT * FROM product_colors WHERE product_id=%s", (product['id'],))
    reviews = query("""SELECT r.*, u.name as user_name FROM reviews r
                       JOIN users u ON r.user_id=u.id WHERE r.product_id=%s AND r.is_approved=1
                       ORDER BY r.created_at DESC""", (product['id'],))
    related = query("""SELECT p.*, pi.image_path FROM products p
                       LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                       WHERE p.category_id=%s AND p.id!=%s AND p.is_active=1
                       ORDER BY RAND() LIMIT 4""",
                    (product['category_id'], product['id']))

    return render_template('product.html', product=product, images=images,
                           sizes=sizes, colors=colors, reviews=reviews, related=related)


@app.route('/category/<slug>')
def category(slug):
    return redirect(url_for('shop', category=slug))


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/auth')
def auth_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')


@app.route('/api/send-otp', methods=['POST'])
def api_send_otp():
    data = request.get_json()
    mobile = data.get('mobile', '').strip()
    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return jsonify({'success': False, 'message': 'Invalid mobile number'})
    otp = app.config['DEV_OTP'] if app.config.get('DEV_MODE_OTP') else generate_otp()
    save_otp(mobile, otp)
    sent = send_otp(mobile, otp)
    if sent:
        return jsonify({'success': True, 'message': 'OTP sent successfully'})
    return jsonify({'success': False, 'message': 'Failed to send OTP. Try again.'})


@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    data = request.get_json()
    mobile = data.get('mobile', '').strip()
    otp = data.get('otp', '').strip()
    name = data.get('name', '').strip()

    if not verify_otp_db(mobile, otp):
        return jsonify({'success': False, 'message': 'Invalid or expired OTP'})

    user = query("SELECT * FROM users WHERE mobile=%s", (mobile,), fetchone=True)
    if not user:
        user_id = query("INSERT INTO users (mobile,name) VALUES(%s,%s)", (mobile, name or mobile), commit=True)
        user = query("SELECT * FROM users WHERE id=%s", (user_id,), fetchone=True)

    session.permanent = True
    session['user_id'] = user['id']
    session['user_name'] = user['name'] or mobile
    session['user_mobile'] = user['mobile']
    session['is_admin'] = bool(user['is_admin'])

    redirect_url = url_for('admin_dashboard') if user['is_admin'] else url_for('index')
    return jsonify({'success': True, 'message': 'Login successful', 'redirect': redirect_url})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ══════════════════════════════════════════════════════════════════════════════
# CART
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/cart')
@login_required
def cart():
    items = query("""SELECT c.*, p.name, p.price, p.sale_price, p.stock_quantity,
                     pi.image_path FROM cart c JOIN products p ON c.product_id=p.id
                     LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                     WHERE c.user_id=%s""", (session['user_id'],))
    subtotal = sum((i['sale_price'] or i['price']) * i['quantity'] for i in items)
    shipping = 0 if subtotal >= app.config['FREE_SHIPPING_ABOVE'] else app.config['SHIPPING_CHARGE']
    return render_template('cart.html', items=items, subtotal=subtotal,
                           shipping=shipping, total=subtotal + shipping)


@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_cart_add():
    data = request.get_json()
    product_id = data.get('product_id')
    size = data.get('size', '')
    color = data.get('color', '')
    qty = int(data.get('quantity', 1))

    product = query("SELECT * FROM products WHERE id=%s AND is_active=1", (product_id,), fetchone=True)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})

    existing = query("SELECT * FROM cart WHERE user_id=%s AND product_id=%s AND size=%s AND color=%s",
                     (session['user_id'], product_id, size, color), fetchone=True)
    if existing:
        query("UPDATE cart SET quantity=quantity+%s WHERE id=%s", (qty, existing['id']), commit=True)
    else:
        query("INSERT INTO cart (user_id,product_id,size,color,quantity) VALUES(%s,%s,%s,%s,%s)",
              (session['user_id'], product_id, size, color, qty), commit=True)

    count = get_cart_count()
    return jsonify({'success': True, 'message': 'Added to cart!', 'cart_count': count})


@app.route('/api/cart/update', methods=['POST'])
@login_required
def api_cart_update():
    data = request.get_json()
    cart_id = data.get('cart_id')
    qty = int(data.get('quantity', 1))
    if qty < 1:
        query("DELETE FROM cart WHERE id=%s AND user_id=%s", (cart_id, session['user_id']), commit=True)
    else:
        query("UPDATE cart SET quantity=%s WHERE id=%s AND user_id=%s",
              (qty, cart_id, session['user_id']), commit=True)
    return jsonify({'success': True})


@app.route('/api/cart/remove', methods=['POST'])
@login_required
def api_cart_remove():
    cart_id = request.get_json().get('cart_id')
    query("DELETE FROM cart WHERE id=%s AND user_id=%s", (cart_id, session['user_id']), commit=True)
    return jsonify({'success': True})


@app.route('/api/coupon/apply', methods=['POST'])
@login_required
def api_apply_coupon():
    code = request.get_json().get('code', '').upper()
    coupon = query("""SELECT * FROM coupons WHERE code=%s AND is_active=1
                      AND (expires_at IS NULL OR expires_at>NOW())
                      AND (usage_limit IS NULL OR used_count<usage_limit)""",
                   (code,), fetchone=True)
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid or expired coupon'})

    items = query("""SELECT c.quantity, p.price, p.sale_price FROM cart c
                     JOIN products p ON c.product_id=p.id WHERE c.user_id=%s""",
                  (session['user_id'],))
    subtotal = sum((i['sale_price'] or i['price']) * i['quantity'] for i in items)

    if subtotal < float(coupon['min_order_amount']):
        return jsonify({'success': False, 'message': f"Minimum order ₹{coupon['min_order_amount']} required"})

    if coupon['discount_type'] == 'percentage':
        disc = subtotal * float(coupon['discount_value']) / 100
        if coupon['max_discount']:
            disc = min(disc, float(coupon['max_discount']))
    else:
        disc = float(coupon['discount_value'])

    session['coupon_id'] = coupon['id']
    session['coupon_code'] = code
    session['coupon_discount'] = round(disc, 2)
    return jsonify({'success': True, 'discount': round(disc, 2), 'message': f'Coupon applied! You save ₹{disc:.2f}'})


# ══════════════════════════════════════════════════════════════════════════════
# WISHLIST
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/wishlist')
@login_required
def wishlist():
    items = query("""SELECT p.*, pi.image_path FROM wishlist w JOIN products p ON w.product_id=p.id
                     LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                     WHERE w.user_id=%s""", (session['user_id'],))
    return render_template('wishlist.html', items=items)


@app.route('/api/wishlist/toggle', methods=['POST'])
@login_required
def api_wishlist_toggle():
    product_id = request.get_json().get('product_id')
    existing = query("SELECT id FROM wishlist WHERE user_id=%s AND product_id=%s",
                     (session['user_id'], product_id), fetchone=True)
    if existing:
        query("DELETE FROM wishlist WHERE id=%s", (existing['id'],), commit=True)
        return jsonify({'success': True, 'action': 'removed'})
    else:
        query("INSERT INTO wishlist (user_id,product_id) VALUES(%s,%s)",
              (session['user_id'], product_id), commit=True)
        return jsonify({'success': True, 'action': 'added'})


# ══════════════════════════════════════════════════════════════════════════════
# CHECKOUT & ORDERS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/checkout')
@login_required
def checkout():
    items = query("""SELECT c.*, p.name, p.price, p.sale_price, pi.image_path
                     FROM cart c JOIN products p ON c.product_id=p.id
                     LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                     WHERE c.user_id=%s""", (session['user_id'],))
    if not items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))

    addresses = query("SELECT * FROM addresses WHERE user_id=%s ORDER BY is_default DESC",
                      (session['user_id'],))
    subtotal = sum((i['sale_price'] or i['price']) * i['quantity'] for i in items)
    discount = session.get('coupon_discount', 0)
    shipping = 0 if (subtotal - discount) >= app.config['FREE_SHIPPING_ABOVE'] else app.config['SHIPPING_CHARGE']
    total = subtotal - discount + shipping

    rz_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
    try:
        rz_order = rz_client.order.create({'amount': int(total * 100), 'currency': 'INR', 'payment_capture': 1})
        rz_order_id = rz_order['id']
    except Exception:
        rz_order_id = 'rz_dev_' + str(int(time.time()))

    return render_template('checkout.html', items=items, addresses=addresses,
                           subtotal=subtotal, discount=discount, shipping=shipping, total=total,
                           rz_order_id=rz_order_id, razorpay_key=app.config['RAZORPAY_KEY_ID'])


@app.route('/api/address/save', methods=['POST'])
@login_required
def api_save_address():
    data = request.get_json()
    required = ['name', 'mobile', 'address_line1', 'city', 'state', 'pincode']
    for f in required:
        if not data.get(f):
            return jsonify({'success': False, 'message': f'Missing {f}'})
    if data.get('is_default'):
        query("UPDATE addresses SET is_default=0 WHERE user_id=%s", (session['user_id'],), commit=True)
    addr_id = query("""INSERT INTO addresses (user_id,name,mobile,address_line1,address_line2,city,state,pincode,is_default)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (session['user_id'], data['name'], data['mobile'], data['address_line1'],
                     data.get('address_line2', ''), data['city'], data['state'], data['pincode'],
                     1 if data.get('is_default') else 0), commit=True)
    addr = query("SELECT * FROM addresses WHERE id=%s", (addr_id,), fetchone=True)
    return jsonify({'success': True, 'address': addr})


@app.route('/api/order/place', methods=['POST'])
@login_required
def api_place_order():
    data = request.get_json()
    address_id = data.get('address_id')
    razorpay_payment_id = data.get('razorpay_payment_id', '')
    razorpay_order_id = data.get('razorpay_order_id', '')
    razorpay_signature = data.get('razorpay_signature', '')

    # Verify Razorpay signature
    if razorpay_payment_id and not app.config.get('DEV_MODE_OTP'):
        body = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_sig = hmac.new(app.config['RAZORPAY_KEY_SECRET'].encode(), body.encode(), hashlib.sha256).hexdigest()
        if expected_sig != razorpay_signature:
            return jsonify({'success': False, 'message': 'Payment verification failed'})

    items = query("""SELECT c.*, p.name, p.price, p.sale_price, p.stock_quantity, pi.image_path
                     FROM cart c JOIN products p ON c.product_id=p.id
                     LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                     WHERE c.user_id=%s""", (session['user_id'],))
    if not items:
        return jsonify({'success': False, 'message': 'Cart is empty'})

    subtotal = sum((i['sale_price'] or i['price']) * i['quantity'] for i in items)
    discount = session.get('coupon_discount', 0)
    shipping = 0 if (subtotal - discount) >= app.config['FREE_SHIPPING_ABOVE'] else app.config['SHIPPING_CHARGE']
    total = subtotal - discount + shipping
    order_number = f"KMD{int(time.time())}"

    order_id = query("""INSERT INTO orders (order_number,user_id,address_id,subtotal,discount,shipping_cost,total,
                        coupon_id,payment_status,payment_method,razorpay_order_id,razorpay_payment_id)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                     (order_number, session['user_id'], address_id, subtotal, discount, shipping, total,
                      session.get('coupon_id'), 'paid' if razorpay_payment_id else 'pending',
                      'razorpay', razorpay_order_id, razorpay_payment_id), commit=True)

    for item in items:
        price = item['sale_price'] or item['price']
        query("""INSERT INTO order_items (order_id,product_id,product_name,product_image,size,color,quantity,price,total)
                 VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
              (order_id, item['product_id'], item['name'], item.get('image_path', ''),
               item.get('size', ''), item.get('color', ''), item['quantity'], price, price * item['quantity']),
              commit=True)
        query("UPDATE products SET stock_quantity=stock_quantity-%s WHERE id=%s",
              (item['quantity'], item['product_id']), commit=True)

    query("INSERT INTO order_tracking (order_id,status,description) VALUES(%s,%s,%s)",
          (order_id, 'Order Placed', 'Your order has been successfully placed'), commit=True)

    if session.get('coupon_id'):
        query("UPDATE coupons SET used_count=used_count+1 WHERE id=%s", (session['coupon_id'],), commit=True)

    query("DELETE FROM cart WHERE user_id=%s", (session['user_id'],), commit=True)
    for k in ['coupon_id', 'coupon_code', 'coupon_discount']:
        session.pop(k, None)

    return jsonify({'success': True, 'order_id': order_id, 'order_number': order_number,
                    'redirect': url_for('order_confirmation', order_id=order_id)})


@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = query("""SELECT o.*, a.name as ship_name, a.mobile as ship_mobile, a.address_line1,
                     a.address_line2, a.city, a.state, a.pincode
                     FROM orders o LEFT JOIN addresses a ON o.address_id=a.id
                     WHERE o.id=%s AND o.user_id=%s""",
                  (order_id, session['user_id']), fetchone=True)
    if not order:
        abort(404)
    items = query("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
    return render_template('order_confirmation.html', order=order, items=items)


# ══════════════════════════════════════════════════════════════════════════════
# USER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    user = query("SELECT * FROM users WHERE id=%s", (session['user_id'],), fetchone=True)
    orders = query("""SELECT o.*, COUNT(oi.id) as item_count FROM orders o
                      LEFT JOIN order_items oi ON o.id=oi.order_id
                      WHERE o.user_id=%s GROUP BY o.id ORDER BY o.created_at DESC LIMIT 5""",
                   (session['user_id'],))
    addresses = query("SELECT * FROM addresses WHERE user_id=%s ORDER BY is_default DESC",
                      (session['user_id'],))
    recently_viewed = query("""SELECT p.*, pi.image_path FROM recently_viewed rv
                               JOIN products p ON rv.product_id=p.id
                               LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                               WHERE rv.user_id=%s ORDER BY rv.viewed_at DESC LIMIT 8""",
                            (session['user_id'],))
    return render_template('dashboard.html', user=user, orders=orders,
                           addresses=addresses, recently_viewed=recently_viewed)


@app.route('/dashboard/orders')
@login_required
def my_orders():
    orders = query("""SELECT o.*, COUNT(oi.id) as item_count FROM orders o
                      LEFT JOIN order_items oi ON o.id=oi.order_id
                      WHERE o.user_id=%s GROUP BY o.id ORDER BY o.created_at DESC""",
                   (session['user_id'],))
    return render_template('my_orders.html', orders=orders)


@app.route('/dashboard/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = query("SELECT * FROM orders WHERE id=%s AND user_id=%s", (order_id, session['user_id']), fetchone=True)
    if not order:
        abort(404)
    items = query("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
    tracking = query("SELECT * FROM order_tracking WHERE order_id=%s ORDER BY created_at", (order_id,))
    address = query("SELECT * FROM addresses WHERE id=%s", (order['address_id'],), fetchone=True) if order['address_id'] else None
    return render_template('order_detail.html', order=order, items=items, tracking=tracking, address=address)


@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_update_profile():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    query("UPDATE users SET name=%s, email=%s WHERE id=%s",
          (name, email, session['user_id']), commit=True)
    session['user_name'] = name
    return jsonify({'success': True, 'message': 'Profile updated'})


@app.route('/api/review/submit', methods=['POST'])
@login_required
def api_submit_review():
    data = request.get_json()
    product_id = data.get('product_id')
    rating = int(data.get('rating', 5))
    review_text = data.get('review', '').strip()
    title = data.get('title', '').strip()
    existing = query("SELECT id FROM reviews WHERE product_id=%s AND user_id=%s",
                     (product_id, session['user_id']), fetchone=True)
    if existing:
        return jsonify({'success': False, 'message': 'You already reviewed this product'})
    query("INSERT INTO reviews (product_id,user_id,rating,title,review) VALUES(%s,%s,%s,%s,%s)",
          (product_id, session['user_id'], rating, title, review_text), commit=True)
    return jsonify({'success': True, 'message': 'Review submitted for approval'})


@app.route('/api/newsletter/subscribe', methods=['POST'])
def api_newsletter():
    data = request.get_json()
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    if not email:
        return jsonify({'success': False, 'message': 'Email required'})
    try:
        query("INSERT INTO newsletter_subscribers (email,name) VALUES(%s,%s)", (email, name), commit=True)
        return jsonify({'success': True, 'message': 'Subscribed successfully!'})
    except Exception:
        return jsonify({'success': False, 'message': 'Already subscribed!'})


@app.route('/api/search/suggestions')
def api_search_suggestions():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    products = query("SELECT name, slug FROM products WHERE name LIKE %s AND is_active=1 LIMIT 5",
                     (f'%{q}%',))
    return jsonify([{'name': p['name'], 'slug': p['slug']} for p in products])


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin')
def admin_root():
    return redirect(url_for('admin_dashboard') if session.get('is_admin') else url_for('admin_login'))


@app.route('/admin/login')
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_orders': query("SELECT COUNT(*) as cnt FROM orders", fetchone=True)['cnt'],
        'total_revenue': query("SELECT COALESCE(SUM(total),0) as rev FROM orders WHERE payment_status='paid'", fetchone=True)['rev'],
        'total_customers': query("SELECT COUNT(*) as cnt FROM users WHERE is_admin=0", fetchone=True)['cnt'],
        'total_products': query("SELECT COUNT(*) as cnt FROM products WHERE is_active=1", fetchone=True)['cnt'],
        'pending_orders': query("SELECT COUNT(*) as cnt FROM orders WHERE status='pending'", fetchone=True)['cnt'],
        'today_orders': query("SELECT COUNT(*) as cnt FROM orders WHERE DATE(created_at)=CURDATE()", fetchone=True)['cnt'],
        'today_revenue': query("SELECT COALESCE(SUM(total),0) as rev FROM orders WHERE DATE(created_at)=CURDATE() AND payment_status='paid'", fetchone=True)['rev'],
    }
    recent_orders = query("""SELECT o.*, u.name as customer_name, u.mobile as customer_mobile
                             FROM orders o JOIN users u ON o.user_id=u.id
                             ORDER BY o.created_at DESC LIMIT 10""")
    monthly_revenue = query("""SELECT DATE_FORMAT(created_at,'%Y-%m') as month,
                               SUM(total) as revenue, COUNT(*) as orders
                               FROM orders WHERE payment_status='paid'
                               GROUP BY month ORDER BY month DESC LIMIT 12""")
    top_products = query("""SELECT p.name, SUM(oi.quantity) as sold, SUM(oi.total) as revenue
                            FROM order_items oi JOIN products p ON oi.product_id=p.id
                            GROUP BY p.id ORDER BY sold DESC LIMIT 5""")
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders,
                           monthly_revenue=monthly_revenue, top_products=top_products)


@app.route('/admin/products')
@admin_required
def admin_products():
    products = query("""SELECT p.*, c.name as cat_name, pi.image_path
                        FROM products p LEFT JOIN categories c ON p.category_id=c.id
                        LEFT JOIN product_images pi ON p.id=pi.product_id AND pi.is_primary=1
                        ORDER BY p.created_at DESC""")
    categories = query("SELECT * FROM categories ORDER BY sort_order")
    return render_template('admin/products.html', products=products, categories=categories)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    categories = query("SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order")
    if request.method == 'POST':
        name = request.form['name']
        slug = slugify(name) + '-' + str(int(time.time()))[-4:]
        category_id = request.form['category_id']
        price = request.form['price']
        sale_price = request.form.get('sale_price') or None
        description = request.form.get('description', '')
        short_desc = request.form.get('short_description', '')
        stock = request.form.get('stock_quantity', 0)
        sku = request.form.get('sku') or f'SKU{int(time.time())}'
        fabric = request.form.get('fabric', '')
        tags = request.form.get('tags', '')
        is_featured = 1 if request.form.get('is_featured') else 0
        is_new = 1 if request.form.get('is_new_arrival') else 0
        is_best = 1 if request.form.get('is_best_seller') else 0
        is_trending = 1 if request.form.get('is_trending') else 0

        prod_id = query("""INSERT INTO products (category_id,name,slug,description,short_description,price,
                           sale_price,sku,stock_quantity,fabric,tags,is_featured,is_new_arrival,is_best_seller,is_trending)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (category_id, name, slug, description, short_desc, price, sale_price, sku,
                         stock, fabric, tags, is_featured, is_new, is_best, is_trending), commit=True)

        # Handle images
        images = request.files.getlist('images')
        for i, img in enumerate(images):
            if img and allowed_file(img.filename):
                fname = secure_filename(f"p{prod_id}_{i}_{img.filename}")
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], 'products', fname))
                query("INSERT INTO product_images (product_id,image_path,is_primary,sort_order) VALUES(%s,%s,%s,%s)",
                      (prod_id, f'products/{fname}', 1 if i == 0 else 0, i), commit=True)

        # Sizes
        sizes = request.form.getlist('sizes')
        size_stocks = request.form.getlist('size_stocks')
        for sz, st in zip(sizes, size_stocks):
            if sz:
                query("INSERT INTO product_sizes (product_id,size,stock) VALUES(%s,%s,%s)",
                      (prod_id, sz, st or 0), commit=True)

        # Colors
        color_names = request.form.getlist('color_names')
        color_hexes = request.form.getlist('color_hexes')
        for cn, ch in zip(color_names, color_hexes):
            if cn and ch:
                query("INSERT INTO product_colors (product_id,color_name,color_hex) VALUES(%s,%s,%s)",
                      (prod_id, cn, ch), commit=True)

        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html', categories=categories)


@app.route('/admin/products/edit/<int:prod_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(prod_id):
    product = query("SELECT * FROM products WHERE id=%s", (prod_id,), fetchone=True)
    if not product:
        abort(404)
    categories = query("SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order")
    images = query("SELECT * FROM product_images WHERE product_id=%s ORDER BY sort_order", (prod_id,))
    sizes = query("SELECT * FROM product_sizes WHERE product_id=%s", (prod_id,))
    colors = query("SELECT * FROM product_colors WHERE product_id=%s", (prod_id,))

    if request.method == 'POST':
        query("""UPDATE products SET category_id=%s,name=%s,description=%s,short_description=%s,
                 price=%s,sale_price=%s,stock_quantity=%s,fabric=%s,tags=%s,
                 is_featured=%s,is_new_arrival=%s,is_best_seller=%s,is_trending=%s,is_active=%s
                 WHERE id=%s""",
              (request.form['category_id'], request.form['name'], request.form.get('description', ''),
               request.form.get('short_description', ''), request.form['price'],
               request.form.get('sale_price') or None, request.form.get('stock_quantity', 0),
               request.form.get('fabric', ''), request.form.get('tags', ''),
               1 if request.form.get('is_featured') else 0, 1 if request.form.get('is_new_arrival') else 0,
               1 if request.form.get('is_best_seller') else 0, 1 if request.form.get('is_trending') else 0,
               1 if request.form.get('is_active') else 0, prod_id), commit=True)

        # New images
        new_images = request.files.getlist('new_images')
        for i, img in enumerate(new_images):
            if img and allowed_file(img.filename):
                fname = secure_filename(f"p{prod_id}_e{i}_{img.filename}")
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], 'products', fname))
                query("INSERT INTO product_images (product_id,image_path,is_primary,sort_order) VALUES(%s,%s,0,%s)",
                      (prod_id, f'products/{fname}', i + 10), commit=True)

        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/edit_product.html', product=product, categories=categories,
                           images=images, sizes=sizes, colors=colors)


@app.route('/admin/products/delete/<int:prod_id>', methods=['POST'])
@admin_required
def admin_delete_product(prod_id):
    query("UPDATE products SET is_active=0 WHERE id=%s", (prod_id,), commit=True)
    return jsonify({'success': True})


@app.route('/admin/orders')
@admin_required
def admin_orders():
    status_filter = request.args.get('status', '')
    where = "WHERE 1=1"
    params = []
    if status_filter:
        where += " AND o.status=%s"
        params.append(status_filter)
    orders = query(f"""SELECT o.*, u.name as customer_name, u.mobile as customer_mobile,
                       COUNT(oi.id) as item_count FROM orders o
                       JOIN users u ON o.user_id=u.id
                       LEFT JOIN order_items oi ON o.id=oi.order_id
                       {where} GROUP BY o.id ORDER BY o.created_at DESC""", params)
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)


@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    order = query("""SELECT o.*, u.name as customer_name, u.mobile as customer_mobile,
                     a.name as ship_name, a.address_line1, a.address_line2, a.city, a.state, a.pincode
                     FROM orders o JOIN users u ON o.user_id=u.id
                     LEFT JOIN addresses a ON o.address_id=a.id WHERE o.id=%s""",
                  (order_id,), fetchone=True)
    items = query("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
    tracking = query("SELECT * FROM order_tracking WHERE order_id=%s ORDER BY created_at", (order_id,))
    return render_template('admin/order_detail.html', order=order, items=items, tracking=tracking)


@app.route('/admin/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    data = request.get_json()
    status = data.get('status')
    description = data.get('description', '')
    query("UPDATE orders SET status=%s WHERE id=%s", (status, order_id), commit=True)
    query("INSERT INTO order_tracking (order_id,status,description) VALUES(%s,%s,%s)",
          (order_id, status.title(), description), commit=True)
    return jsonify({'success': True})


@app.route('/admin/customers')
@admin_required
def admin_customers():
    customers = query("""SELECT u.*, COUNT(DISTINCT o.id) as order_count,
                         COALESCE(SUM(o.total),0) as total_spent FROM users u
                         LEFT JOIN orders o ON u.id=o.user_id
                         WHERE u.is_admin=0 GROUP BY u.id ORDER BY u.created_at DESC""")
    return render_template('admin/customers.html', customers=customers)


@app.route('/admin/coupons')
@admin_required
def admin_coupons():
    coupons = query("SELECT * FROM coupons ORDER BY created_at DESC")
    return render_template('admin/coupons.html', coupons=coupons)


@app.route('/admin/coupons/add', methods=['POST'])
@admin_required
def admin_add_coupon():
    data = request.form
    try:
        query("""INSERT INTO coupons (code,description,discount_type,discount_value,min_order_amount,max_discount,usage_limit,expires_at)
                 VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
              (data['code'].upper(), data.get('description'), data['discount_type'], data['discount_value'],
               data.get('min_order_amount', 0), data.get('max_discount') or None,
               data.get('usage_limit') or None, data.get('expires_at') or None), commit=True)
        flash('Coupon created!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin_coupons'))


@app.route('/admin/categories')
@admin_required
def admin_categories():
    categories = query("SELECT * FROM categories ORDER BY sort_order")
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/categories/add', methods=['POST'])
@admin_required
def admin_add_category():
    name = request.form['name']
    slug = slugify(name)
    description = request.form.get('description', '')
    query("INSERT INTO categories (name,slug,description) VALUES(%s,%s,%s)",
          (name, slug, description), commit=True)
    flash('Category added!', 'success')
    return redirect(url_for('admin_categories'))


@app.route('/admin/newsletter')
@admin_required
def admin_newsletter():
    subscribers = query("SELECT * FROM newsletter_subscribers ORDER BY subscribed_at DESC")
    return render_template('admin/newsletter.html', subscribers=subscribers)


@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    reviews = query("""SELECT r.*, u.name as user_name, p.name as product_name
                       FROM reviews r JOIN users u ON r.user_id=u.id JOIN products p ON r.product_id=p.id
                       ORDER BY r.created_at DESC""")
    return render_template('admin/reviews.html', reviews=reviews)


@app.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
@admin_required
def admin_approve_review(review_id):
    query("UPDATE reviews SET is_approved=1 WHERE id=%s", (review_id,), commit=True)
    return jsonify({'success': True})


@app.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@admin_required
def admin_delete_review(review_id):
    query("DELETE FROM reviews WHERE id=%s", (review_id,), commit=True)
    return jsonify({'success': True})


@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        for key in ['store_name', 'store_email', 'store_mobile', 'whatsapp_number',
                    'shipping_charge', 'free_shipping_above', 'razorpay_key_id']:
            val = request.form.get(key, '')
            query("UPDATE settings SET setting_value=%s WHERE setting_key=%s", (val, key), commit=True)
        flash('Settings saved!', 'success')
    settings_rows = query("SELECT * FROM settings")
    settings = {r['setting_key']: r['setting_value'] for r in settings_rows}
    return render_template('admin/settings.html', settings=settings)


# ── Error Handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('404.html', error=str(e)), 500


# ── AI Stylist Chatbot API ────────────────────────────────────────────────────
@app.route('/api/stylist/chat', methods=['POST'])
def api_stylist_chat():
    """Simple rule-based fashion stylist chatbot."""
    message = request.get_json().get('message', '').lower()
    responses = {
        'saree': "✨ For sarees, I'd recommend Banarasi silk for weddings, and cotton sarees for daily wear. Our Kanjivaram collection is perfect for festivities!",
        'lehenga': "👗 Lehengas are gorgeous for weddings! Consider velvet for winters and georgette for summers. Our bridal lehengas have stunning embroidery work.",
        'kurti': "💕 Kurtis are so versatile! Cotton kurtis for casual days, silk or georgette for festive occasions. Our embroidered kurtis are trending right now!",
        'color': "🎨 For fair skin: pastels, peach, and coral work beautifully. For medium skin: jewel tones like royal blue and emerald. For dark skin: bright colors and whites look stunning!",
        'wedding': "💍 For weddings, I recommend: Lehengas for the bride, Sarees for relatives, and Anarkali suits for guests. Our bridal collection is breathtaking!",
        'party': "🎉 Party wear? Go for sequin gowns, stylish co-ord sets, or a chic printed maxi dress. Our evening gown collection is perfect!",
        'size': "📏 Our size guide: XS (32-34), S (34-36), M (36-38), L (38-40), XL (40-42). For sarees, free size fits all. Need help with a specific item?",
        'offer': "🏷️ Use code WELCOME10 for 10% off your first order! Also check our Flash Sale section for amazing deals!",
        'hello': "Hello gorgeous! 👋 I'm your personal fashion stylist. Ask me about outfit suggestions, styling tips, size guidance, or anything fashion!",
        'help': "I can help you with: outfit suggestions for occasions, color combinations, size guidance, styling tips, and finding the perfect piece for you! What are you looking for? 💃",
    }
    for keyword, response in responses.items():
        if keyword in message:
            return jsonify({'reply': response})
    return jsonify({'reply': "I love your fashion curiosity! 💕 Tell me more about the occasion, your style preference, or the type of outfit you're looking for, and I'll give you my best recommendations!"})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
