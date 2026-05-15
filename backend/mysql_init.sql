SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP DATABASE IF EXISTS campus_market;
CREATE DATABASE campus_market
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE campus_market;

CREATE TABLE users (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(120) DEFAULT NULL,
  nickname VARCHAR(80) NOT NULL DEFAULT '',
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email),
  KEY idx_users_role (role),
  KEY idx_users_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE categories (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(60) NOT NULL,
  slug VARCHAR(80) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categories_name (name),
  UNIQUE KEY uq_categories_slug (slug),
  KEY idx_categories_sort_order (sort_order),
  KEY idx_categories_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE items (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  title VARCHAR(120) NOT NULL,
  description TEXT NOT NULL,
  price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `condition` VARCHAR(30) NOT NULL DEFAULT '九成新',
  location VARCHAR(120) NOT NULL DEFAULT '校园',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  views INT NOT NULL DEFAULT 0,
  is_featured TINYINT(1) NOT NULL DEFAULT 0,
  seller_id INT UNSIGNED NOT NULL,
  category_id INT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_items_title (title),
  KEY idx_items_status (status),
  KEY idx_items_seller_id (seller_id),
  KEY idx_items_category_id (category_id),
  KEY idx_items_created_at (created_at),
  KEY idx_items_views (views),
  CONSTRAINT fk_items_seller
    FOREIGN KEY (seller_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_items_category
    FOREIGN KEY (category_id) REFERENCES categories(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE item_images (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  item_id INT UNSIGNED NOT NULL,
  url VARCHAR(255) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_item_images_item_id (item_id),
  KEY idx_item_images_sort_order (sort_order),
  CONSTRAINT fk_item_images_item
    FOREIGN KEY (item_id) REFERENCES items(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE item_views (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  item_id INT UNSIGNED NOT NULL,
  viewer_key VARCHAR(128) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_item_view_item_viewer (item_id, viewer_key),
  KEY idx_item_views_item_id (item_id),
  KEY idx_item_views_viewer_key (viewer_key),
  CONSTRAINT fk_item_views_item
    FOREIGN KEY (item_id) REFERENCES items(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchase_orders (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  item_id INT UNSIGNED NOT NULL,
  buyer_id INT UNSIGNED NOT NULL,
  seller_id INT UNSIGNED NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'completed',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_purchase_orders_item (item_id),
  KEY idx_purchase_orders_buyer_id (buyer_id),
  KEY idx_purchase_orders_seller_id (seller_id),
  CONSTRAINT fk_purchase_orders_item
    FOREIGN KEY (item_id) REFERENCES items(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_purchase_orders_buyer
    FOREIGN KEY (buyer_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_purchase_orders_seller
    FOREIGN KEY (seller_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE conversations (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  item_id INT UNSIGNED NOT NULL,
  buyer_id INT UNSIGNED NOT NULL,
  seller_id INT UNSIGNED NOT NULL,
  last_message_preview VARCHAR(255) NOT NULL DEFAULT '',
  last_message_at DATETIME DEFAULT NULL,
  unread_buyer_count INT NOT NULL DEFAULT 0,
  unread_seller_count INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_conversations_triplet (item_id, buyer_id, seller_id),
  KEY idx_conversations_item_id (item_id),
  KEY idx_conversations_buyer_id (buyer_id),
  KEY idx_conversations_seller_id (seller_id),
  KEY idx_conversations_last_message_at (last_message_at),
  CONSTRAINT fk_conversations_item
    FOREIGN KEY (item_id) REFERENCES items(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_conversations_buyer
    FOREIGN KEY (buyer_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_conversations_seller
    FOREIGN KEY (seller_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chat_messages (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  conversation_id INT UNSIGNED NOT NULL,
  sender_id INT UNSIGNED NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_chat_messages_conversation_id (conversation_id),
  KEY idx_chat_messages_sender_id (sender_id),
  KEY idx_chat_messages_created_at (created_at),
  CONSTRAINT fk_chat_messages_conversation
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_chat_messages_sender
    FOREIGN KEY (sender_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE notifications (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id INT UNSIGNED NOT NULL,
  kind VARCHAR(30) NOT NULL,
  title VARCHAR(120) NOT NULL,
  content VARCHAR(255) NOT NULL,
  is_read TINYINT(1) NOT NULL DEFAULT 0,
  item_id INT UNSIGNED DEFAULT NULL,
  order_id INT UNSIGNED DEFAULT NULL,
  conversation_id INT UNSIGNED DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_notifications_user_id (user_id),
  KEY idx_notifications_is_read (is_read),
  KEY idx_notifications_kind (kind),
  KEY idx_notifications_item_id (item_id),
  KEY idx_notifications_order_id (order_id),
  KEY idx_notifications_conversation_id (conversation_id),
  KEY idx_notifications_created_at (created_at),
  CONSTRAINT fk_notifications_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_notifications_item
    FOREIGN KEY (item_id) REFERENCES items(id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_notifications_order
    FOREIGN KEY (order_id) REFERENCES purchase_orders(id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_notifications_conversation
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE favorites (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id INT UNSIGNED NOT NULL,
  item_id INT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_user_item_favorite (user_id, item_id),
  KEY idx_favorites_user_id (user_id),
  KEY idx_favorites_item_id (item_id),
  CONSTRAINT fk_favorites_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_favorites_item
    FOREIGN KEY (item_id) REFERENCES items(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO categories (id, name, slug, sort_order, is_active) VALUES
  (1, '教材书籍', 'books', 0, 1),
  (2, '电子数码', 'digital', 1, 1),
  (3, '生活用品', 'daily', 2, 1),
  (4, '服饰鞋包', 'fashion', 3, 1),
  (5, '运动器材', 'sports', 4, 1),
  (6, '家具家电', 'home', 5, 1),
  (7, '美妆护理', 'beauty', 6, 1),
  (8, '其他', 'other', 7, 1);

INSERT INTO users (id, username, email, nickname, password_hash, role, is_active) VALUES
  (1, 'admin', 'admin@example.com', '管理员', 'pbkdf2_sha256$120000$RxkINkYeK0gq_RLkCHYtHQ$eCfHwDIwWh_gv_VsX1Zt9QYZM_4jTR6xcenAEx_eIxY', 'admin', 1),
  (2, 'alice', 'alice@example.com', 'Alice', 'pbkdf2_sha256$120000$he9hq8dYUjSaOZQPeoTLWA$AkXmSD62Ex58Wpf-8WSPICgngMu_6PKIZK6dm1zx6Tg', 'user', 1),
  (3, 'bob', 'bob@example.com', 'Bob', 'pbkdf2_sha256$120000$aFm4_wNsCMy98LaDfWSRHA$PLuUZ67wc7jvksVdHLBKzDT8k5lPi0b1I5jMCxrTQUY', 'user', 1);

INSERT INTO items (id, title, description, price, `condition`, location, `status`, views, is_featured, seller_id, category_id) VALUES
  (1, '高数教材九成新', '适合下学期复习使用，笔记完整，价格可小刀。', 18.00, '九成新', '南区宿舍', 'active', 35, 1, 2, 1),
  (2, '蓝牙耳机', '续航还不错，适合上课和跑步使用。', 65.00, '八成新', '北区快递点', 'active', 88, 1, 3, 2),
  (3, '小风扇', '夏天宿舍必备，风力足，支持三档调节。', 12.00, '九成新', '校内自提', 'active', 42, 0, 2, 3);

INSERT INTO item_images (id, item_id, url, sort_order) VALUES
  (1, 1, '/uploads/sample-book.svg', 0),
  (2, 2, '/uploads/sample-earphone.svg', 0),
  (3, 3, '/uploads/sample-fan.svg', 0);

INSERT INTO favorites (id, user_id, item_id) VALUES
  (1, 2, 2),
  (2, 3, 1);

SET FOREIGN_KEY_CHECKS = 1;
