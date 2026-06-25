-- ============================================================
-- KOMUDHA BOUTIQUE - MySQL Database Schema
-- Production-Ready E-Commerce Database
-- ============================================================

CREATE DATABASE IF NOT EXISTS komudha_boutique CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE komudha_boutique;

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mobile VARCHAR(15) NOT NULL UNIQUE,
    name VARCHAR(100),
    email VARCHAR(150),
    profile_image VARCHAR(255),
    is_active TINYINT(1) DEFAULT 1,
    is_admin TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_mobile (mobile)
) ENGINE=InnoDB;

-- ============================================================
-- OTP TABLE
-- ============================================================
CREATE TABLE otp_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mobile VARCHAR(15) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    purpose ENUM('login','register') DEFAULT 'login',
    is_used TINYINT(1) DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mobile_otp (mobile, otp)
) ENGINE=InnoDB;

-- ============================================================
-- CATEGORIES TABLE
-- ============================================================
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    description TEXT,
    image VARCHAR(255),
    is_active TINYINT(1) DEFAULT 1,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCTS TABLE
-- ============================================================
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(220) NOT NULL UNIQUE,
    description TEXT,
    short_description VARCHAR(500),
    price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2),
    sku VARCHAR(100) UNIQUE,
    stock_quantity INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    is_featured TINYINT(1) DEFAULT 0,
    is_new_arrival TINYINT(1) DEFAULT 0,
    is_best_seller TINYINT(1) DEFAULT 0,
    is_trending TINYINT(1) DEFAULT 0,
    is_flash_sale TINYINT(1) DEFAULT 0,
    flash_sale_price DECIMAL(10,2),
    flash_sale_ends TIMESTAMP NULL,
    fabric VARCHAR(100),
    care_instructions TEXT,
    tags VARCHAR(500),
    views INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    INDEX idx_category (category_id),
    INDEX idx_slug (slug),
    FULLTEXT INDEX ft_search (name, description, tags)
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCT IMAGES TABLE
-- ============================================================
CREATE TABLE product_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    is_primary TINYINT(1) DEFAULT 0,
    sort_order INT DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCT SIZES TABLE
-- ============================================================
CREATE TABLE product_sizes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    size VARCHAR(20) NOT NULL,
    stock INT DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCT COLORS TABLE
-- ============================================================
CREATE TABLE product_colors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    color_name VARCHAR(50) NOT NULL,
    color_hex VARCHAR(10) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- ADDRESSES TABLE
-- ============================================================
CREATE TABLE addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    is_default TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- COUPONS TABLE
-- ============================================================
CREATE TABLE coupons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    discount_type ENUM('percentage','fixed') DEFAULT 'percentage',
    discount_value DECIMAL(10,2) NOT NULL,
    min_order_amount DECIMAL(10,2) DEFAULT 0,
    max_discount DECIMAL(10,2),
    usage_limit INT,
    used_count INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- ORDERS TABLE
-- ============================================================
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    address_id INT,
    subtotal DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    coupon_id INT,
    status ENUM('pending','confirmed','processing','shipped','delivered','cancelled','returned') DEFAULT 'pending',
    payment_status ENUM('pending','paid','failed','refunded') DEFAULT 'pending',
    payment_method VARCHAR(50),
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    tracking_number VARCHAR(100),
    shipping_partner VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (address_id) REFERENCES addresses(id),
    FOREIGN KEY (coupon_id) REFERENCES coupons(id),
    INDEX idx_user (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ============================================================
-- ORDER ITEMS TABLE
-- ============================================================
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_image VARCHAR(255),
    size VARCHAR(20),
    color VARCHAR(50),
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

-- ============================================================
-- ORDER TRACKING TABLE
-- ============================================================
CREATE TABLE order_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    status VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- WISHLIST TABLE
-- ============================================================
CREATE TABLE wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_wishlist (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- CART TABLE
-- ============================================================
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    size VARCHAR(20),
    color VARCHAR(50),
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- REVIEWS TABLE
-- ============================================================
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    review TEXT,
    is_approved TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_review (product_id, user_id)
) ENGINE=InnoDB;

-- ============================================================
-- BANNERS TABLE
-- ============================================================
CREATE TABLE banners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    subtitle VARCHAR(300),
    image VARCHAR(255) NOT NULL,
    link VARCHAR(255),
    button_text VARCHAR(50),
    position ENUM('hero','middle','sidebar') DEFAULT 'hero',
    is_active TINYINT(1) DEFAULT 1,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- NEWSLETTER TABLE
-- ============================================================
CREATE TABLE newsletter_subscribers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    name VARCHAR(100),
    is_active TINYINT(1) DEFAULT 1,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- RECENTLY VIEWED TABLE
-- ============================================================
CREATE TABLE recently_viewed (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_viewed (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- SETTINGS TABLE
-- ============================================================
CREATE TABLE settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default Settings
INSERT INTO settings (setting_key, setting_value) VALUES
('store_name', 'KOMUDHA Boutique'),
('store_email', 'hello@komudha.com'),
('store_mobile', '+91 98765 43210'),
('store_address', 'Chennai, Tamil Nadu, India'),
('shipping_charge', '99'),
('free_shipping_above', '999'),
('razorpay_key_id', 'rzp_test_your_key_here'),
('razorpay_key_secret', 'your_secret_here'),
('whatsapp_number', '919876543210'),
('admin_mobile', '9876543210'),
('instagram_url', 'https://instagram.com/komudha'),
('facebook_url', 'https://facebook.com/komudha'),
('currency', 'INR'),
('currency_symbol', '₹');

-- Categories
INSERT INTO categories (name, slug, description, sort_order) VALUES
('Sarees', 'sarees', 'Elegant traditional and contemporary sarees', 1),
('Kurtis', 'kurtis', 'Stylish kurtis for every occasion', 2),
('Lehengas', 'lehengas', 'Bridal and festive lehengas', 3),
('Salwar Suits', 'salwar-suits', 'Traditional and fusion salwar suits', 4),
('Gowns', 'gowns', 'Glamorous party and evening gowns', 5),
('Tops & Tunics', 'tops-tunics', 'Modern tops and tunics', 6),
('Dresses', 'dresses', 'Casual and formal dresses', 7),
('Accessories', 'accessories', 'Fashion accessories and jewelry', 8);

-- Sample Products
INSERT INTO products (category_id, name, slug, description, short_description, price, sale_price, sku, stock_quantity, is_featured, is_new_arrival, is_best_seller, is_trending) VALUES
(1, 'Royal Banarasi Silk Saree', 'royal-banarasi-silk-saree', 'Exquisite Banarasi silk saree with intricate gold zari work. Perfect for weddings and festive occasions. Comes with matching blouse piece.', 'Luxurious Banarasi silk with gold zari', 8999.00, 6999.00, 'SAR001', 15, 1, 1, 1, 1),
(2, 'Floral Embroidery Kurti', 'floral-embroidery-kurti', 'Beautiful floral embroidery kurti in soft cotton fabric. Ideal for casual and semi-formal occasions.', 'Soft cotton with floral embroidery', 1299.00, 999.00, 'KUR001', 50, 1, 1, 0, 1),
(3, 'Bridal Lehenga Choli', 'bridal-lehenga-choli', 'Stunning bridal lehenga in rich velvet with heavy embroidery. A dream outfit for your special day.', 'Rich velvet bridal lehenga', 24999.00, 19999.00, 'LEH001', 5, 1, 0, 1, 1),
(1, 'Kanjivaram Pure Silk Saree', 'kanjivaram-pure-silk-saree', 'Authentic Kanjivaram pure silk saree with traditional temple border. A timeless heirloom piece.', 'Authentic Kanjivaram pure silk', 12999.00, NULL, 'SAR002', 8, 1, 0, 1, 0),
(2, 'Indo-Western Palazzo Kurti Set', 'indo-western-palazzo-kurti-set', 'Trendy Indo-western palazzo kurti set in georgette fabric. Perfect for festive and casual wear.', 'Georgette palazzo kurti set', 2499.00, 1899.00, 'KUR002', 30, 0, 1, 0, 1),
(5, 'Sequin Evening Gown', 'sequin-evening-gown', 'Glamorous sequin evening gown for parties and special occasions. Floor-length with elegant drape.', 'Glamorous sequin party gown', 4999.00, 3999.00, 'GOW001', 12, 1, 1, 1, 1),
(4, 'Anarkali Suit Set', 'anarkali-suit-set', 'Beautiful Anarkali suit in chiffon fabric with dupatta. Great for festive and formal occasions.', 'Chiffon Anarkali with dupatta', 3499.00, 2799.00, 'SAL001', 20, 0, 1, 1, 0),
(7, 'Floral Wrap Dress', 'floral-wrap-dress', 'Chic floral wrap dress in crepe fabric. Versatile and comfortable for everyday wear.', 'Crepe floral wrap dress', 1799.00, 1399.00, 'DRE001', 35, 1, 1, 0, 1);

-- Product Images (using placeholder paths - actual images uploaded separately)
INSERT INTO product_images (product_id, image_path, is_primary, sort_order) VALUES
(1, 'products/saree1_1.jpg', 1, 1),
(1, 'products/saree1_2.jpg', 0, 2),
(2, 'products/kurti1_1.jpg', 1, 1),
(2, 'products/kurti1_2.jpg', 0, 2),
(3, 'products/lehenga1_1.jpg', 1, 1),
(3, 'products/lehenga1_2.jpg', 0, 2),
(4, 'products/saree2_1.jpg', 1, 1),
(5, 'products/kurti2_1.jpg', 1, 1),
(6, 'products/gown1_1.jpg', 1, 1),
(7, 'products/anarkali1_1.jpg', 1, 1),
(8, 'products/dress1_1.jpg', 1, 1);

-- Product Sizes
INSERT INTO product_sizes (product_id, size, stock) VALUES
(1, 'Free Size', 15),(2, 'XS', 10),(2, 'S', 15),(2, 'M', 15),(2, 'L', 10),
(3, 'XS', 1),(3, 'S', 2),(3, 'M', 1),(3, 'L', 1),
(4, 'Free Size', 8),(5, 'S', 10),(5, 'M', 10),(5, 'L', 10),
(6, 'XS', 3),(6, 'S', 4),(6, 'M', 3),(6, 'L', 2),
(7, 'XS', 5),(7, 'S', 7),(7, 'M', 5),(7, 'L', 3),
(8, 'XS', 8),(8, 'S', 10),(8, 'M', 10),(8, 'L', 7);

-- Product Colors
INSERT INTO product_colors (product_id, color_name, color_hex) VALUES
(1, 'Royal Red', '#8B0000'),(1, 'Deep Blue', '#003366'),(1, 'Forest Green', '#228B22'),
(2, 'Rose Pink', '#FF69B4'),(2, 'Sky Blue', '#87CEEB'),(2, 'Mint Green', '#98FF98'),
(3, 'Maroon', '#800000'),(3, 'Royal Blue', '#4169E1'),
(6, 'Gold', '#FFD700'),(6, 'Silver', '#C0C0C0'),(6, 'Rose Gold', '#B76E79'),
(8, 'Floral Blue', '#6699CC'),(8, 'Floral Pink', '#FFB6C1');

-- Sample Coupons
INSERT INTO coupons (code, description, discount_type, discount_value, min_order_amount, max_discount) VALUES
('WELCOME10', 'Welcome discount 10% off', 'percentage', 10.00, 500.00, 500.00),
('FLAT200', 'Flat ₹200 off on orders above ₹1500', 'fixed', 200.00, 1500.00, 200.00),
('FESTIVE20', 'Festive season 20% off', 'percentage', 20.00, 2000.00, 1000.00);

-- Admin User (mobile: 9876543210)
INSERT INTO users (mobile, name, email, is_admin) VALUES
('9876543210', 'Admin', 'admin@komudha.com', 1);
