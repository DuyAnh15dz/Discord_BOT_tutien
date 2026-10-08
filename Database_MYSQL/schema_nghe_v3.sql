-- ============================================================
-- SCHEMA HỆ THỐNG NGHỀ - FULL
-- Chạy SAU: sơ đồ db.sql + seed_data.sql
-- ============================================================

USE tu_tien_db;

-- ============================================================
-- 1. NGUYÊN LIỆU MỚI
-- ============================================================

CREATE TABLE tmpl_mau_yeu_thu (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  ten VARCHAR(100) NOT NULL,
  pham_cap ENUM('Pham','Linh','Bao','Tien','Than') NOT NULL,
  he ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NULL,
  mo_ta TEXT,
  PRIMARY KEY (id),
  UNIQUE KEY uk_mau_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tmpl_linh_dich (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  ten VARCHAR(100) NOT NULL,
  pham_cap ENUM('Pham','Linh','Bao','Tien','Than') NOT NULL,
  he ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NOT NULL,
  bonus_ti_le DECIMAL(5,2) NOT NULL DEFAULT 0,
  mo_ta TEXT,
  PRIMARY KEY (id),
  UNIQUE KEY uk_ld_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. ĐẠO CỤ TRẬN PHÁP
-- ============================================================

CREATE TABLE tmpl_tran_cu (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  ten VARCHAR(100) NOT NULL,
  loai ENUM('TranCo','TranBan','TranNhan') NOT NULL,
  pham_cap ENUM('Pham','Linh','Bao','Tien','Than') NOT NULL,
  he ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NULL,
  gia_linh_thach INT UNSIGNED NOT NULL DEFAULT 0,
  gia_tien_ngoc INT UNSIGNED NOT NULL DEFAULT 0,
  mo_ta TEXT,
  PRIMARY KEY (id),
  UNIQUE KEY uk_tran_cu_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. QUAN HỆ NGŨ HÀNH
-- ============================================================

CREATE TABLE tmpl_he_quan_he (
  he_nguon ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NOT NULL,
  he_dich ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NOT NULL,
  quan_he ENUM('TuongSinh','TuongKhac','TrungTinh') NOT NULL,
  PRIMARY KEY (he_nguon, he_dich)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. PHÁP KHÍ
-- ============================================================

CREATE TABLE tmpl_phap_khi (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  ten VARCHAR(100) NOT NULL,
  loai ENUM('VuKhi','Ao','Non','Giay','Nhan') NOT NULL,
  he ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NULL,
  pham_cap ENUM('Pham','Linh','Bao','Tien','Than') NOT NULL,
  yeu_cau_canh_gioi_id TINYINT UNSIGNED NULL,
  yeu_cau_nghe_cap TINYINT UNSIGNED NOT NULL DEFAULT 1,
  cap_toi_da TINYINT UNSIGNED NOT NULL DEFAULT 5,
  effect_moi_cap JSON NOT NULL,
  khoang_thach_id SMALLINT UNSIGNED NULL,
  mo_ta TEXT,
  PRIMARY KEY (id),
  UNIQUE KEY uk_phap_khi_code (code),
  KEY idx_loai_pham (loai, pham_cap),
  CONSTRAINT fk_pk_canh_gioi FOREIGN KEY (yeu_cau_canh_gioi_id)
    REFERENCES canh_gioi (id) ON DELETE SET NULL,
  CONSTRAINT fk_pk_khoang_thach FOREIGN KEY (khoang_thach_id)
    REFERENCES tmpl_khoang_thach (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tmpl_phap_khi_cong_thuc (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  phap_khi_id INT UNSIGNED NOT NULL,
  khoang_thach_id SMALLINT UNSIGNED NOT NULL,
  so_luong SMALLINT UNSIGNED NOT NULL,
  ti_le_thanh_cong_max DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_pkct (phap_khi_id, khoang_thach_id),
  CONSTRAINT fk_pkct_phap_khi FOREIGN KEY (phap_khi_id)
    REFERENCES tmpl_phap_khi (id) ON DELETE CASCADE,
  CONSTRAINT fk_pkct_khoang_thach FOREIGN KEY (khoang_thach_id)
    REFERENCES tmpl_khoang_thach (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. BÙA CHÚ (TẠO BẢNG CHÍNH TRƯỚC)
-- ============================================================

CREATE TABLE tmpl_bua_chu (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  ten VARCHAR(100) NOT NULL,
  loai ENUM('TanCong','PhongThu','HoTro','KhongChe') NOT NULL,
  he ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NULL,
  pham_cap ENUM('Pham','Linh','Bao','Tien','Than') NOT NULL,
  yeu_cau_nghe_cap TINYINT UNSIGNED NOT NULL DEFAULT 1,
  effect JSON NOT NULL,
  -- Nguyên liệu vẽ bùa
  mp_cost INT UNSIGNED NOT NULL DEFAULT 50,
  khoang_thach_id SMALLINT UNSIGNED NULL,
  so_luong_khoang_thach SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  mau_yeu_thu_id SMALLINT UNSIGNED NULL,
  mau_yeu_thu_so_luong SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  linh_dich_id SMALLINT UNSIGNED NULL,
  linh_dich_so_luong SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  exp_base INT UNSIGNED NOT NULL DEFAULT 100,
  mo_ta TEXT,
  PRIMARY KEY (id),
  UNIQUE KEY uk_bua_chu_code (code),
  CONSTRAINT fk_bc_khoang_thach FOREIGN KEY (khoang_thach_id)
    REFERENCES tmpl_khoang_thach (id) ON DELETE SET NULL,
  CONSTRAINT fk_bc_mau FOREIGN KEY (mau_yeu_thu_id)
    REFERENCES tmpl_mau_yeu_thu (id) ON DELETE SET NULL,
  CONSTRAINT fk_bc_linh_dich FOREIGN KEY (linh_dich_id)
    REFERENCES tmpl_linh_dich (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. SỬA BẢNG TRẬN PHÁP (dùng IF để tránh lỗi nếu đã có cột)
-- ============================================================

-- Kiểm tra và thêm cột (an toàn nếu chạy lại)
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = 'tu_tien_db'
    AND TABLE_NAME = 'tmpl_tran_phap'
    AND COLUMN_NAME = 'tran_co_id');

SET @sql := IF(@exist = 0,
  'ALTER TABLE tmpl_tran_phap
   ADD COLUMN tran_co_id SMALLINT UNSIGNED NULL,
   ADD COLUMN tran_co_so_luong SMALLINT UNSIGNED NOT NULL DEFAULT 1,
   ADD COLUMN tran_ban_id SMALLINT UNSIGNED NULL,
   ADD COLUMN tran_ban_so_luong SMALLINT UNSIGNED NOT NULL DEFAULT 1,
   ADD COLUMN tran_nhan_id SMALLINT UNSIGNED NULL,
   ADD COLUMN tran_nhan_so_luong SMALLINT UNSIGNED NOT NULL DEFAULT 1,
   ADD COLUMN do_kho_quiz TINYINT UNSIGNED NOT NULL DEFAULT 3,
   ADD COLUMN bonus_moi_cau_dung DECIMAL(5,2) NOT NULL DEFAULT 5.0,
   ADD COLUMN bonus_thoi_gian_moi_cau DECIMAL(5,2) NOT NULL DEFAULT 10.0,
   ADD COLUMN exp_base INT UNSIGNED NOT NULL DEFAULT 200,
   ADD CONSTRAINT fk_tp_tran_co FOREIGN KEY (tran_co_id)
     REFERENCES tmpl_tran_cu (id) ON DELETE SET NULL,
   ADD CONSTRAINT fk_tp_tran_ban FOREIGN KEY (tran_ban_id)
     REFERENCES tmpl_tran_cu (id) ON DELETE SET NULL,
   ADD CONSTRAINT fk_tp_tran_nhan FOREIGN KEY (tran_nhan_id)
     REFERENCES tmpl_tran_cu (id) ON DELETE SET NULL',
  'SELECT "Cột đã tồn tại, bỏ qua" AS note');

USE tu_tien_db;

-- ============================================================
-- TẠO BẢNG TRẬN PHÁP GỐC (nếu chưa có)
-- ============================================================

CREATE TABLE IF NOT EXISTS tmpl_tran_phap (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  ten VARCHAR(100) NOT NULL,
  loai ENUM('Buff','Debuff','HonHop') NOT NULL,
  he ENUM('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') NULL,
  pham_cap ENUM('Pham','Linh','Bao','Tien','Than') NOT NULL,
  yeu_cau_nghe_cap TINYINT UNSIGNED NOT NULL DEFAULT 1,
  effect JSON NOT NULL,
  thoi_gian_hieu_luc INT UNSIGNED NOT NULL,
  ban_kinh INT UNSIGNED NOT NULL DEFAULT 0,
  khoang_thach_id SMALLINT UNSIGNED NULL,
  so_luong_khoang_thach SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  mo_ta TEXT,
  PRIMARY KEY (id),
  UNIQUE KEY uk_tran_phap_code (code),
  CONSTRAINT fk_tp_khoang_thach FOREIGN KEY (khoang_thach_id)
    REFERENCES tmpl_khoang_thach (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT '✅ Đã tạo bảng tmpl_tran_phap gốc' AS ket_qua;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================
-- 7. SỬA BẢNG SHOP
-- ============================================================

ALTER TABLE tmpl_shop_item
  MODIFY COLUMN item_type ENUM(
    'DanDuoc','DaoCu','LinhThao','KhoangThach',
    'DacBiet','CongPhap','TranCu','MauYeuThu','LinhDich'
  ) NOT NULL;

-- ============================================================
-- 8. KHO ĐỒ PLAYER
-- ============================================================

CREATE TABLE player_phap_khi (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id BIGINT UNSIGNED NOT NULL,
  phap_khi_id INT UNSIGNED NOT NULL,
  cap_do TINYINT UNSIGNED NOT NULL DEFAULT 1,
  dang_trang_bi TINYINT NOT NULL DEFAULT 0,
  slot ENUM('VuKhi','Ao','Non','Giay','Nhan') NULL,
  ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
  cap_nhat_luc DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_player_slot (player_id, slot),
  KEY idx_player (player_id),
  CONSTRAINT fk_ppk_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE,
  CONSTRAINT fk_ppk_phap_khi FOREIGN KEY (phap_khi_id)
    REFERENCES tmpl_phap_khi (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE player_mau_yeu_thu (
  player_id BIGINT UNSIGNED NOT NULL,
  mau_yeu_thu_id SMALLINT UNSIGNED NOT NULL,
  so_luong INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (player_id, mau_yeu_thu_id),
  CONSTRAINT fk_pmyt_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE,
  CONSTRAINT fk_pmyt_mau FOREIGN KEY (mau_yeu_thu_id)
    REFERENCES tmpl_mau_yeu_thu (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE player_linh_dich (
  player_id BIGINT UNSIGNED NOT NULL,
  linh_dich_id SMALLINT UNSIGNED NOT NULL,
  so_luong INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (player_id, linh_dich_id),
  CONSTRAINT fk_pld_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE,
  CONSTRAINT fk_pld_linh_dich FOREIGN KEY (linh_dich_id)
    REFERENCES tmpl_linh_dich (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE player_tran_cu (
  player_id BIGINT UNSIGNED NOT NULL,
  tran_cu_id SMALLINT UNSIGNED NOT NULL,
  so_luong INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (player_id, tran_cu_id),
  CONSTRAINT fk_ptc_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE,
  CONSTRAINT fk_ptc_tran_cu FOREIGN KEY (tran_cu_id)
    REFERENCES tmpl_tran_cu (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE player_bua_chu (
  player_id BIGINT UNSIGNED NOT NULL,
  bua_chu_id INT UNSIGNED NOT NULL,
  so_luong INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (player_id, bua_chu_id),
  CONSTRAINT fk_pbc_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE,
  CONSTRAINT fk_pbc_bua_chu FOREIGN KEY (bua_chu_id)
    REFERENCES tmpl_bua_chu (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE player_bua_chu_thuan_thuc (
  player_id BIGINT UNSIGNED NOT NULL,
  bua_chu_id INT UNSIGNED NOT NULL,
  do_thuan_thuc TINYINT UNSIGNED NOT NULL DEFAULT 0,
  so_lan_ve INT UNSIGNED NOT NULL DEFAULT 0,
  cap_nhat_luc DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (player_id, bua_chu_id),
  CONSTRAINT fk_pbctt_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE,
  CONSTRAINT fk_pbctt_bua FOREIGN KEY (bua_chu_id)
    REFERENCES tmpl_bua_chu (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 9. LOG
-- ============================================================

CREATE TABLE log_luyen_khi (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id BIGINT UNSIGNED NOT NULL,
  phap_khi_id INT UNSIGNED NOT NULL,
  ket_qua JSON NOT NULL,
  thanh_cong TINYINT NOT NULL,
  exp_nhan INT UNSIGNED NOT NULL DEFAULT 0,
  thoi_diem DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_llk_player (player_id, thoi_diem),
  CONSTRAINT fk_llk_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE log_bay_tran (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id BIGINT UNSIGNED NOT NULL,
  tran_phap_id INT UNSIGNED NOT NULL,
  thanh_cong TINYINT NOT NULL,
  thoi_diem DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_lbt_player (player_id, thoi_diem),
  CONSTRAINT fk_lbt_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE log_ve_bua (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id BIGINT UNSIGNED NOT NULL,
  bua_chu_id INT UNSIGNED NOT NULL,
  so_luong_thanh_cong INT UNSIGNED NOT NULL DEFAULT 0,
  exp_nhan INT UNSIGNED NOT NULL DEFAULT 0,
  thoi_diem DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_lvb_player (player_id, thoi_diem),
  CONSTRAINT fk_lvb_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE log_tran_phap_quiz (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id BIGINT UNSIGNED NOT NULL,
  tran_phap_id INT UNSIGNED NOT NULL,
  so_cau_dung INT UNSIGNED NOT NULL,
  tong_cau INT UNSIGNED NOT NULL,
  ket_qua JSON NOT NULL,
  thoi_diem DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ltpq_player (player_id, thoi_diem),
  CONSTRAINT fk_ltpq_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

USE  tu_tien_db;

CREATE TABLE IF NOT EXISTS player_tran_phap_active (
  player_id BIGINT UNSIGNED NOT NULL,
  tran_phap_id INT UNSIGNED NOT NULL,
  effect JSON NOT NULL,
  bat_dau_luc DATETIME DEFAULT CURRENT_TIMESTAMP,
  het_han_luc DATETIME NOT NULL,
  PRIMARY KEY (player_id),
  CONSTRAINT fk_ptpa_player FOREIGN KEY (player_id)
    REFERENCES player (player_id) ON DELETE CASCADE,
  CONSTRAINT fk_ptpa_tran_phap FOREIGN KEY (tran_phap_id)
    REFERENCES tmpl_tran_phap (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Mỗi player chỉ có 1 trận pháp active';

-- Verify
SHOW TABLES LIKE 'player_tran_phap_active';
DESCRIBE player_tran_phap_active;

SELECT '✅ Schema nghề đã tạo thành công!' AS ket_qua;

