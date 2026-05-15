-- ============================================================
-- 校园二手交易平台 — SQLite 初始化脚本
-- 基于 SQLAlchemy ORM 模型 (models.py) 生成
-- 使用方法: sqlite3 backend.db < sqlite_init.sql
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 如果表已存在则先删除（注意：生产环境请勿使用）
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS item_views;
DROP TABLE IF EXISTS item_images;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- ── 用户表 ──
CREATE TABLE users (
    id            INTEGER       NOT NULL,
    username      VARCHAR(50)   NOT NULL,
    email         VARCHAR(120)  DEFAULT NULL,
    nickname      VARCHAR(80)   NOT NULL DEFAULT '',
    password_hash VARCHAR(255)  NOT NULL,
    role          VARCHAR(20)   NOT NULL DEFAULT 'user',
    is_active     BOOLEAN       NOT NULL DEFAULT 1,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email    UNIQUE (email)
);

CREATE INDEX idx_users_role       ON users (role);
CREATE INDEX idx_users_created_at ON users (created_at);

-- ── 分类表 ──
CREATE TABLE categories (
    id         INTEGER     NOT NULL,
    name       VARCHAR(60) NOT NULL,
    slug       VARCHAR(80) NOT NULL,
    sort_order INTEGER     NOT NULL DEFAULT 0,
    is_active  BOOLEAN     NOT NULL DEFAULT 1,
    created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_categories_name UNIQUE (name),
    CONSTRAINT uq_categories_slug UNIQUE (slug)
);

CREATE INDEX idx_categories_sort_order ON categories (sort_order);
CREATE INDEX idx_categories_active     ON categories (is_active);

-- ── 物品表 ──
CREATE TABLE items (
    id          INTEGER       NOT NULL,
    title       VARCHAR(120)  NOT NULL,
    description TEXT          NOT NULL,
    price       NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    condition   VARCHAR(30)   NOT NULL DEFAULT '九成新',
    location    VARCHAR(120)  NOT NULL DEFAULT '校园',
    status      VARCHAR(20)   NOT NULL DEFAULT 'active',
    views       INTEGER       NOT NULL DEFAULT 0,
    is_featured BOOLEAN       NOT NULL DEFAULT 0,
    seller_id   INTEGER       NOT NULL,
    category_id INTEGER       NOT NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_items_seller   FOREIGN KEY (seller_id)   REFERENCES users(id)      ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_items_category FOREIGN KEY (category_id) REFERENCES categories(id)  ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_items_price_non_negative CHECK (price >= 0)
);

CREATE INDEX idx_items_title       ON items (title);
CREATE INDEX idx_items_status      ON items (status);
CREATE INDEX idx_items_seller_id   ON items (seller_id);
CREATE INDEX idx_items_category_id ON items (category_id);
CREATE INDEX idx_items_created_at  ON items (created_at);
CREATE INDEX idx_items_views       ON items (views);

-- ── 物品图片表 ──
CREATE TABLE item_images (
    id         INTEGER      NOT NULL,
    item_id    INTEGER      NOT NULL,
    url        VARCHAR(255) NOT NULL,
    sort_order INTEGER      NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_item_images_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_item_images_item_id    ON item_images (item_id);
CREATE INDEX idx_item_images_sort_order ON item_images (sort_order);

-- ── 浏览记录表 ──
CREATE TABLE item_views (
    id         INTEGER       NOT NULL,
    item_id    INTEGER       NOT NULL,
    viewer_key VARCHAR(128)  NOT NULL,
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_item_view_item_viewer UNIQUE (item_id, viewer_key),
    CONSTRAINT fk_item_views_item       FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_item_views_item_id    ON item_views (item_id);
CREATE INDEX idx_item_views_viewer_key ON item_views (viewer_key);

-- ── 购买订单表 ──
CREATE TABLE purchase_orders (
    id         INTEGER       NOT NULL,
    item_id    INTEGER       NOT NULL,
    buyer_id   INTEGER       NOT NULL,
    seller_id  INTEGER       NOT NULL,
    amount     NUMERIC(10,2) NOT NULL,
    status     VARCHAR(20)   NOT NULL DEFAULT 'completed',
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_purchase_orders_item   UNIQUE (item_id),
    CONSTRAINT fk_purchase_orders_item   FOREIGN KEY (item_id)   REFERENCES items(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_purchase_orders_buyer  FOREIGN KEY (buyer_id)  REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_purchase_orders_seller FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_purchase_orders_buyer_id  ON purchase_orders (buyer_id);
CREATE INDEX idx_purchase_orders_seller_id ON purchase_orders (seller_id);

-- ── 会话表 ──
CREATE TABLE conversations (
    id                    INTEGER       NOT NULL,
    item_id               INTEGER       NOT NULL,
    buyer_id              INTEGER       NOT NULL,
    seller_id             INTEGER       NOT NULL,
    last_message_preview  VARCHAR(255)  NOT NULL DEFAULT '',
    last_message_at       DATETIME      DEFAULT NULL,
    unread_buyer_count    INTEGER       NOT NULL DEFAULT 0,
    unread_seller_count   INTEGER       NOT NULL DEFAULT 0,
    created_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_conversations_triplet UNIQUE (item_id, buyer_id, seller_id),
    CONSTRAINT fk_conversations_item    FOREIGN KEY (item_id)   REFERENCES items(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_conversations_buyer   FOREIGN KEY (buyer_id)  REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_conversations_seller  FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_conversations_item_id         ON conversations (item_id);
CREATE INDEX idx_conversations_buyer_id        ON conversations (buyer_id);
CREATE INDEX idx_conversations_seller_id       ON conversations (seller_id);
CREATE INDEX idx_conversations_last_message_at ON conversations (last_message_at);

-- ── 聊天消息表 ──
CREATE TABLE chat_messages (
    id              INTEGER  NOT NULL,
    conversation_id INTEGER  NOT NULL,
    sender_id       INTEGER  NOT NULL,
    content         TEXT     NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_chat_messages_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_chat_messages_sender       FOREIGN KEY (sender_id)       REFERENCES users(id)         ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_chat_messages_conversation_id ON chat_messages (conversation_id);
CREATE INDEX idx_chat_messages_sender_id      ON chat_messages (sender_id);
CREATE INDEX idx_chat_messages_created_at     ON chat_messages (created_at);

-- ── 通知表 ──
CREATE TABLE notifications (
    id              INTEGER       NOT NULL,
    user_id         INTEGER       NOT NULL,
    kind            VARCHAR(30)   NOT NULL,
    title           VARCHAR(120)  NOT NULL,
    content         VARCHAR(255)  NOT NULL,
    is_read         BOOLEAN       NOT NULL DEFAULT 0,
    item_id         INTEGER       DEFAULT NULL,
    order_id        INTEGER       DEFAULT NULL,
    conversation_id INTEGER       DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_notifications_user         FOREIGN KEY (user_id)         REFERENCES users(id)             ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_item         FOREIGN KEY (item_id)         REFERENCES items(id)             ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_order        FOREIGN KEY (order_id)        REFERENCES purchase_orders(id)   ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id)     ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_notifications_user_id         ON notifications (user_id);
CREATE INDEX idx_notifications_is_read         ON notifications (is_read);
CREATE INDEX idx_notifications_kind            ON notifications (kind);
CREATE INDEX idx_notifications_item_id         ON notifications (item_id);
CREATE INDEX idx_notifications_order_id        ON notifications (order_id);
CREATE INDEX idx_notifications_conversation_id ON notifications (conversation_id);
CREATE INDEX idx_notifications_created_at      ON notifications (created_at);

-- ── 收藏表 ──
CREATE TABLE favorites (
    id         INTEGER  NOT NULL,
    user_id    INTEGER  NOT NULL,
    item_id    INTEGER  NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_user_item_favorite UNIQUE (user_id, item_id),
    CONSTRAINT fk_favorites_user     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_favorites_item     FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_favorites_user_id ON favorites (user_id);
CREATE INDEX idx_favorites_item_id ON favorites (item_id);

-- ============================================================
-- 种子数据
-- ============================================================

-- 分类
INSERT INTO categories (id, name, slug, sort_order, is_active) VALUES
    (1, '教材书籍', 'books',  0, 1),
    (2, '电子数码', 'digital', 1, 1),
    (3, '生活用品', 'daily',  2, 1),
    (4, '服饰鞋包', 'fashion', 3, 1),
    (5, '运动器材', 'sports',  4, 1),
    (6, '家具家电', 'home',    5, 1),
    (7, '美妆护理', 'beauty',  6, 1),
    (8, '其他',     'other',   7, 1);

-- 用户（密码均为 123456，使用后端 bcrypt 哈希）
-- 注意：此处密码哈希需要通过后端注册接口生成，下方的哈希值仅为占位
-- 正确做法：启动后端后调用 POST /auth/register 创建用户
INSERT INTO users (id, username, email, nickname, password_hash, role, is_active) VALUES
    (1, 'admin', 'admin@example.com', '管理员', '$2b$12$placeholder_admin_hash_replace_via_api', 'admin', 1),
    (2, 'alice', 'alice@example.com', 'Alice',  '$2b$12$placeholder_alice_hash_replace_via_api', 'user',  1),
    (3, 'bob',   'bob@example.com',   'Bob',    '$2b$12$placeholder_bob_hash_replace_via_api',   'user',  1);

-- 物品
INSERT INTO items (id, title, description, price, condition, location, status, views, is_featured, seller_id, category_id) VALUES
    (1, '高数教材九成新', '适合下学期复习使用，笔记完整，价格可小刀。', 18.00, '九成新', '南区宿舍',   'active', 35, 1, 2, 1),
    (2, '蓝牙耳机',     '续航还不错，适合上课和跑步使用。',         65.00, '八成新', '北区快递点', 'active', 88, 1, 3, 2),
    (3, '小风扇',       '夏天宿舍必备，风力足，支持三档调节。',     12.00, '九成新', '校内自提',   'active', 42, 0, 2, 3);

-- 物品图片
INSERT INTO item_images (id, item_id, url, sort_order) VALUES
    (1, 1, '/uploads/sample-book.svg',     0),
    (2, 2, '/uploads/sample-earphone.svg', 0),
    (3, 3, '/uploads/sample-fan.svg',      0);

-- 收藏
INSERT INTO favorites (id, user_id, item_id) VALUES
    (1, 2, 2),
    (2, 3, 1);
