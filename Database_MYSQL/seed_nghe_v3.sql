-- ============================================================
-- SEED DATA HỆ THỐNG NGHỀ
-- ============================================================

USE tu_tien_db;

-- ============================================================
-- 1. QUAN HỆ NGŨ HÀNH
-- ============================================================

INSERT INTO tmpl_he_quan_he (he_nguon, he_dich, quan_he) VALUES
-- Tương sinh
('Kim','Thuy','TuongSinh'), ('Thuy','Moc','TuongSinh'),
('Moc','Hoa','TuongSinh'), ('Hoa','Tho','TuongSinh'),
('Tho','Kim','TuongSinh'),
-- Tương khắc
('Kim','Moc','TuongKhac'), ('Moc','Tho','TuongKhac'),
('Tho','Thuy','TuongKhac'), ('Thuy','Hoa','TuongKhac'),
('Hoa','Kim','TuongKhac'),
-- Trung tính trong ngũ hành
('Kim','Hoa','TrungTinh'), ('Kim','Tho','TrungTinh'),
('Moc','Kim','TrungTinh'), ('Moc','Thuy','TrungTinh'),
('Thuy','Kim','TrungTinh'), ('Thuy','Tho','TrungTinh'),
('Hoa','Moc','TrungTinh'), ('Hoa','Thuy','TrungTinh'),
('Tho','Hoa','TrungTinh'), ('Tho','Moc','TrungTinh'),
-- Dị hệ tự thân
('Loi','Loi','TrungTinh'), ('Bang','Bang','TrungTinh'),
('Phong','Phong','TrungTinh'), ('Duong','Duong','TrungTinh'),
('Am','Am','TrungTinh');

-- Dị hệ với ngũ hành
INSERT IGNORE INTO tmpl_he_quan_he (he_nguon, he_dich, quan_he)
SELECT h1.he, h2.he, 'TrungTinh'
FROM (SELECT 'Kim' AS he UNION SELECT 'Moc' UNION SELECT 'Thuy' 
      UNION SELECT 'Hoa' UNION SELECT 'Tho') h1
CROSS JOIN (SELECT 'Loi' AS he UNION SELECT 'Bang' UNION SELECT 'Phong' 
            UNION SELECT 'Duong' UNION SELECT 'Am') h2;

INSERT IGNORE INTO tmpl_he_quan_he (he_nguon, he_dich, quan_he)
SELECT h1.he, h2.he, 'TrungTinh'
FROM (SELECT 'Loi' AS he UNION SELECT 'Bang' UNION SELECT 'Phong' 
      UNION SELECT 'Duong' UNION SELECT 'Am') h1
CROSS JOIN (SELECT 'Kim' AS he UNION SELECT 'Moc' UNION SELECT 'Thuy' 
            UNION SELECT 'Hoa' UNION SELECT 'Tho') h2;

-- ============================================================
-- 2. MÁU YÊU THÚ
-- ============================================================

INSERT INTO tmpl_mau_yeu_thu (code, ten, pham_cap, he, mo_ta) VALUES
('mau_lon_rung', 'Máu Lợn Rừng', 'Pham', 'Tho', 'Máu yêu thú cấp thấp'),
('mau_ho_van', 'Máu Hổ Vằn', 'Pham', 'Kim', 'Máu mãnh thú'),
('mau_xa_tinh', 'Máu Xà Tinh', 'Pham', 'Am', 'Máu xà tinh'),
('mau_yeu_xa', 'Máu Yêu Xà', 'Linh', 'Am', 'Máu yêu thú cấp trung'),
('mau_lang_vuong', 'Máu Lang Vương', 'Linh', 'Phong', 'Máu sói đầu đàn'),
('mau_hoa_linh', 'Máu Hỏa Linh', 'Linh', 'Hoa', 'Máu hỏa linh'),
('mau_giao_long', 'Máu Giao Long', 'Bao', 'Thuy', 'Máu giao long'),
('mau_phuong_hoang', 'Máu Phượng Hoàng', 'Bao', 'Hoa', 'Máu phượng hoàng'),
('mau_huyen_vu', 'Máu Huyền Vũ', 'Bao', 'Tho', 'Máu thần thú Huyền Vũ'),
('mau_ky_lan', 'Máu Kỳ Lân', 'Tien', 'Duong', 'Máu kỳ lân'),
('mau_than_long', 'Máu Thần Long', 'Tien', 'Loi', 'Máu thần long'),
('mau_hon_don', 'Máu Hỗn Độn Thú', 'Than', NULL, 'Máu hỗn độn thú');

-- ============================================================
-- 3. LINH DỊCH
-- ============================================================

INSERT INTO tmpl_linh_dich (code, ten, pham_cap, he, bonus_ti_le, mo_ta) VALUES
('ld_kim_pham', 'Linh Dịch Kim - Phàm', 'Pham', 'Kim', 5, 'Tăng 5% tỉ lệ'),
('ld_moc_pham', 'Linh Dịch Mộc - Phàm', 'Pham', 'Moc', 5, 'Tăng 5% tỉ lệ'),
('ld_thuy_pham', 'Linh Dịch Thủy - Phàm', 'Pham', 'Thuy', 5, 'Tăng 5% tỉ lệ'),
('ld_hoa_pham', 'Linh Dịch Hỏa - Phàm', 'Pham', 'Hoa', 5, 'Tăng 5% tỉ lệ'),
('ld_tho_pham', 'Linh Dịch Thổ - Phàm', 'Pham', 'Tho', 5, 'Tăng 5% tỉ lệ'),
('ld_kim_linh', 'Linh Dịch Kim - Linh', 'Linh', 'Kim', 15, 'Tăng 15% tỉ lệ'),
('ld_hoa_linh', 'Linh Dịch Hỏa - Linh', 'Linh', 'Hoa', 15, 'Tăng 15% tỉ lệ'),
('ld_loi_linh', 'Linh Dịch Lôi - Linh', 'Linh', 'Loi', 18, 'Tăng 18% tỉ lệ'),
('ld_kim_bao', 'Linh Dịch Kim - Bảo', 'Bao', 'Kim', 30, 'Tăng 30% tỉ lệ'),
('ld_bang_bao', 'Linh Dịch Băng - Bảo', 'Bao', 'Bang', 32, 'Tăng 32% tỉ lệ'),
('ld_duong_tien', 'Linh Dịch Dương - Tiên', 'Tien', 'Duong', 50, 'Tăng 50% tỉ lệ'),
('ld_am_tien', 'Linh Dịch Âm - Tiên', 'Tien', 'Am', 50, 'Tăng 50% tỉ lệ');

-- ============================================================
-- 4. TRẬN CỜ, TRẬN BÀN, TRẬN NHÃN
-- ============================================================

INSERT INTO tmpl_tran_cu (code, ten, loai, pham_cap, he, gia_linh_thach, gia_tien_ngoc, mo_ta) VALUES
-- Trận Cờ
('co_pham', 'Trận Cờ Phàm', 'TranCo', 'Pham', NULL, 500, 0, 'Trận cờ cơ bản'),
('co_linh', 'Trận Cờ Linh', 'TranCo', 'Linh', NULL, 2500, 0, 'Trận cờ linh cấp'),
('co_bao', 'Trận Cờ Bảo', 'TranCo', 'Bao', NULL, 10000, 0, 'Trận cờ bảo cấp'),
('co_tien', 'Trận Cờ Tiên', 'TranCo', 'Tien', NULL, 0, 50, 'Trận cờ tiên cấp'),
('co_than', 'Trận Cờ Thần', 'TranCo', 'Than', NULL, 0, 200, 'Trận cờ thần cấp'),
-- Trận Bàn
('ban_pham', 'Trận Bàn Phàm', 'TranBan', 'Pham', NULL, 500, 0, 'Trận bàn cơ bản'),
('ban_linh', 'Trận Bàn Linh', 'TranBan', 'Linh', NULL, 2500, 0, 'Trận bàn linh cấp'),
('ban_bao', 'Trận Bàn Bảo', 'TranBan', 'Bao', NULL, 10000, 0, 'Trận bàn bảo cấp'),
('ban_tien', 'Trận Bàn Tiên', 'TranBan', 'Tien', NULL, 0, 50, 'Trận bàn tiên cấp'),
('ban_than', 'Trận Bàn Thần', 'TranBan', 'Than', NULL, 0, 200, 'Trận bàn thần cấp'),
-- Trận Nhãn
('nhan_kim_pham', 'Kim Nhãn - Phàm', 'TranNhan', 'Pham', 'Kim', 300, 0, 'Trận nhãn Kim hệ'),
('nhan_moc_pham', 'Mộc Nhãn - Phàm', 'TranNhan', 'Pham', 'Moc', 300, 0, 'Trận nhãn Mộc hệ'),
('nhan_thuy_pham', 'Thủy Nhãn - Phàm', 'TranNhan', 'Pham', 'Thuy', 300, 0, 'Trận nhãn Thủy hệ'),
('nhan_hoa_pham', 'Hỏa Nhãn - Phàm', 'TranNhan', 'Pham', 'Hoa', 300, 0, 'Trận nhãn Hỏa hệ'),
('nhan_tho_pham', 'Thổ Nhãn - Phàm', 'TranNhan', 'Pham', 'Tho', 300, 0, 'Trận nhãn Thổ hệ'),
('nhan_loi_linh', 'Lôi Nhãn - Linh', 'TranNhan', 'Linh', 'Loi', 1500, 0, 'Trận nhãn Lôi hệ'),
('nhan_bang_linh', 'Băng Nhãn - Linh', 'TranNhan', 'Linh', 'Bang', 1500, 0, 'Trận nhãn Băng hệ'),
('nhan_phong_linh', 'Phong Nhãn - Linh', 'TranNhan', 'Linh', 'Phong', 1500, 0, 'Trận nhãn Phong hệ'),
('nhan_duong_bao', 'Dương Nhãn - Bảo', 'TranNhan', 'Bao', 'Duong', 6000, 0, 'Trận nhãn Dương hệ'),
('nhan_am_bao', 'Âm Nhãn - Bảo', 'TranNhan', 'Bao', 'Am', 6000, 0, 'Trận nhãn Âm hệ'),
('nhan_hon_don', 'Hỗn Độn Nhãn', 'TranNhan', 'Than', NULL, 0, 300, 'Trận nhãn vạn năng');

-- ============================================================
-- 5. PHÁP KHÍ TEMPLATES
-- ============================================================

INSERT INTO tmpl_phap_khi 
(code, ten, loai, he, pham_cap, yeu_cau_canh_gioi_id, yeu_cau_nghe_cap, cap_toi_da, effect_moi_cap, khoang_thach_id, mo_ta) 
VALUES
('kiem_pham_kim', 'Kiếm Sắt', 'VuKhi', 'Kim', 'Pham', 1, 1, 5,
 CAST('{"atk": 10, "ti_le_chi_mang": 0.5}' AS JSON),
 (SELECT id FROM tmpl_khoang_thach WHERE code='huyen_thiet'),
 'Vũ khí cơ bản'),

('kiem_linh_kim', 'Linh Kiếm', 'VuKhi', 'Kim', 'Linh', 2, 2, 5,
 CAST('{"atk": 30, "ti_le_chi_mang": 1, "ti_le_xuyen_giap": 1}' AS JSON),
 (SELECT id FROM tmpl_khoang_thach WHERE code='tinh_kim'),
 'Linh kiếm tăng xuyên giáp'),

('kiem_bao_kim', 'Bảo Kiếm', 'VuKhi', 'Kim', 'Bao', 3, 4, 5,
 CAST('{"atk": 80, "ti_le_chi_mang": 2, "ti_le_xuyen_giap": 2, "sat_thuong_chi_mang": 5}' AS JSON),
 (SELECT id FROM tmpl_khoang_thach WHERE code='tu_Kim'),
 'Bảo kiếm'),

('ao_pham_tho', 'Áo Vải', 'Ao', 'Tho', 'Pham', 1, 1, 5,
 CAST('{"def": 5, "hp_max": 50}' AS JSON),
 (SELECT id FROM tmpl_khoang_thach WHERE code='huyen_thiet'),
 'Áo vải'),

('non_pham', 'Mũ Lông', 'Non', 'Phong', 'Pham', 1, 1, 5,
 CAST('{"mdef": 3, "ti_le_ne": 1}' AS JSON),
 (SELECT id FROM tmpl_khoang_thach WHERE code='thanh_tung'),
 'Mũ nhẹ'),

('giay_pham', 'Giày Da', 'Giay', 'Phong', 'Pham', 1, 1, 5,
 CAST('{"def": 3, "ti_le_ne": 1}' AS JSON),
 (SELECT id FROM tmpl_khoang_thach WHERE code='thanh_tung'),
 'Giày da'),

('nhan_pham', 'Nhẫn Đồng', 'Nhan', 'Kim', 'Pham', 1, 1, 5,
 CAST('{"atk": 3, "matk": 3}' AS JSON),
 (SELECT id FROM tmpl_khoang_thach WHERE code='huyen_thiet'),
 'Nhẫn đồng');

-- ============================================================
-- 6. CÔNG THỨC LUYỆN PHÁP KHÍ
-- ============================================================

INSERT INTO tmpl_phap_khi_cong_thuc (phap_khi_id, khoang_thach_id, so_luong, ti_le_thanh_cong_max) VALUES
-- Kiếm Sắt
((SELECT id FROM tmpl_phap_khi WHERE code='kiem_pham_kim'),
 (SELECT id FROM tmpl_khoang_thach WHERE code='huyen_thiet'), 5, 90),
((SELECT id FROM tmpl_phap_khi WHERE code='kiem_pham_kim'),
 (SELECT id FROM tmpl_khoang_thach WHERE code='thanh_tung'), 3, 90),
-- Linh Kiếm
((SELECT id FROM tmpl_phap_khi WHERE code='kiem_linh_kim'),
 (SELECT id FROM tmpl_khoang_thach WHERE code='tinh_kim'), 5, 75),
((SELECT id FROM tmpl_phap_khi WHERE code='kiem_linh_kim'),
 (SELECT id FROM tmpl_khoang_thach WHERE code='kim_ngoc'), 3, 75),
-- Bảo Kiếm
((SELECT id FROM tmpl_phap_khi WHERE code='kiem_bao_kim'),
 (SELECT id FROM tmpl_khoang_thach WHERE code='tu_Kim'), 10, 60),
((SELECT id FROM tmpl_phap_khi WHERE code='kiem_bao_kim'),
 (SELECT id FROM tmpl_khoang_thach WHERE code='kim_ngoc'), 5, 60);

-- ============================================================
-- 7. BÙA CHÚ TEMPLATES
-- ============================================================

INSERT INTO tmpl_bua_chu 
(code, ten, loai, he, pham_cap, yeu_cau_nghe_cap, effect, 
 mp_cost, khoang_thach_id, so_luong_khoang_thach,
 mau_yeu_thu_id, mau_yeu_thu_so_luong,
 linh_dich_id, linh_dich_so_luong,
 exp_base, mo_ta)
VALUES
-- BÙA PHÀM
('bua_hoa_cau', 'Hỏa Cầu Phù', 'TanCong', 'Hoa', 'Pham', 1,
 CAST('{"dmg": 200, "element": "Hoa"}' AS JSON),
 50,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_pham'), 1,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_ho_van'), 5,
 NULL, 0,
 50,
 'Gây 200 sát thương Hỏa hệ'),

('bua_ho_the', 'Hộ Thể Phù', 'PhongThu', 'Tho', 'Pham', 1,
 CAST('{"shield": 500, "turns": 3}' AS JSON),
 50,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_pham'), 1,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_lon_rung'), 5,
 NULL, 0,
 50,
 'Tạo khiên 500 HP trong 3 lượt'),

('bua_hoi_xuan', 'Hồi Xuân Phù', 'HoTro', 'Moc', 'Pham', 1,
 CAST('{"hp_hoi": 500, "mp_hoi": 100}' AS JSON),
 50,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_pham'), 1,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_lon_rung'), 3,
 NULL, 0,
 50,
 'Hồi 500 HP và 100 MP'),

-- BÙA LINH
('bua_loi_dinh', 'Lôi Đình Phù', 'TanCong', 'Loi', 'Linh', 3,
 CAST('{"dmg": 800, "element": "Loi", "ti_le_te_liet": 30}' AS JSON),
 200,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_linh'), 2,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_yeu_xa'), 10,
 (SELECT id FROM tmpl_linh_dich WHERE code='ld_loi_linh'), 1,
 150,
 'Gây 800 sát thương Lôi + 30% tê liệt'),

('bua_kim_quang', 'Kim Quang Phù', 'PhongThu', 'Kim', 'Linh', 3,
 CAST('{"shield": 2000, "turns": 5}' AS JSON),
 200,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_linh'), 2,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_lang_vuong'), 10,
 (SELECT id FROM tmpl_linh_dich WHERE code='ld_kim_linh'), 1,
 150,
 'Tạo khiên 2000 HP trong 5 lượt'),

-- BÙA BẢO
('bua_bang_phong', 'Băng Phong Phù', 'TanCong', 'Bang', 'Bao', 5,
 CAST('{"dmg": 2000, "element": "Bang", "ti_le_dong_bang": 50}' AS JSON),
 800,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_bao'), 3,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_giao_long'), 20,
 (SELECT id FROM tmpl_linh_dich WHERE code='ld_bang_bao'), 2,
 500,
 'Gây 2000 sát thương Băng + 50% đóng băng'),

('bua_dai_bo', 'Đại Bổ Phù', 'HoTro', 'Moc', 'Bao', 5,
 CAST('{"hp_hoi": 5000, "mp_hoi": 2000}' AS JSON),
 800,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_bao'), 3,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_phuong_hoang'), 20,
 (SELECT id FROM tmpl_linh_dich WHERE code='ld_kim_bao'), 2,
 500,
 'Hồi 5000 HP và 2000 MP'),

-- BÙA TIÊN
('bua_thien_loi', 'Thiên Lôi Phù', 'TanCong', 'Loi', 'Tien', 7,
 CAST('{"dmg": 20000, "element": "Loi", "ti_le_te_liet": 70}' AS JSON),
 3000,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_tien'), 5,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_than_long'), 50,
 (SELECT id FROM tmpl_linh_dich WHERE code='ld_duong_tien'), 5,
 2500,
 'Gây 20000 sát thương Lôi + 70% tê liệt'),

-- BÙA THẦN
('bua_huy_diet', 'Hủy Diệt Phù', 'TanCong', NULL, 'Than', 9,
 CAST('{"dmg": 200000, "ignore_def": true}' AS JSON),
 10000,
 (SELECT id FROM tmpl_khoang_thach WHERE code='chu_sa_than'), 10,
 (SELECT id FROM tmpl_mau_yeu_thu WHERE code='mau_hon_don'), 100,
 (SELECT id FROM tmpl_linh_dich WHERE code='ld_hon_don_than'), 10,
 10000,
 'Gây 200000 sát thương, bỏ qua phòng ngự');

-- ============================================================
-- ============================================================
-- 8. CẬP NHẬT TRẬN PHÁP (gán đạo cụ + quiz)
-- ============================================================

USE tu_tien_db;

-- Trận Phàm — đơn giản nhất
UPDATE tmpl_tran_phap SET 
  tran_co_id = (SELECT id FROM tmpl_tran_cu WHERE code='co_pham'),
  tran_co_so_luong = 1,
  tran_ban_id = (SELECT id FROM tmpl_tran_cu WHERE code='ban_pham'),
  tran_ban_so_luong = 1,
  tran_nhan_id = (SELECT id FROM tmpl_tran_cu WHERE code='nhan_kim_pham'),
  tran_nhan_so_luong = 1,
  do_kho_quiz = 3,
  bonus_moi_cau_dung = 5.0,
  bonus_thoi_gian_moi_cau = 10.0,
  exp_base = 200
WHERE pham_cap = 'Pham';

-- Trận Linh
UPDATE tmpl_tran_phap SET 
  tran_co_id = (SELECT id FROM tmpl_tran_cu WHERE code='co_linh'),
  tran_co_so_luong = 2,
  tran_ban_id = (SELECT id FROM tmpl_tran_cu WHERE code='ban_linh'),
  tran_ban_so_luong = 2,
  tran_nhan_id = (SELECT id FROM tmpl_tran_cu WHERE code='nhan_loi_linh'),
  tran_nhan_so_luong = 1,
  do_kho_quiz = 4,
  bonus_moi_cau_dung = 6.0,
  bonus_thoi_gian_moi_cau = 12.0,
  exp_base = 500
WHERE pham_cap = 'Linh';

-- Trận Bảo
UPDATE tmpl_tran_phap SET 
  tran_co_id = (SELECT id FROM tmpl_tran_cu WHERE code='co_bao'),
  tran_co_so_luong = 3,
  tran_ban_id = (SELECT id FROM tmpl_tran_cu WHERE code='ban_bao'),
  tran_ban_so_luong = 3,
  tran_nhan_id = (SELECT id FROM tmpl_tran_cu WHERE code='nhan_duong_bao'),
  tran_nhan_so_luong = 2,
  do_kho_quiz = 5,
  bonus_moi_cau_dung = 7.0,
  bonus_thoi_gian_moi_cau = 13.0,
  exp_base = 1500
WHERE pham_cap = 'Bao';

-- Trận Tiên
UPDATE tmpl_tran_phap SET 
  tran_co_id = (SELECT id FROM tmpl_tran_cu WHERE code='co_tien'),
  tran_co_so_luong = 5,
  tran_ban_id = (SELECT id FROM tmpl_tran_cu WHERE code='ban_tien'),
  tran_ban_so_luong = 5,
  tran_nhan_id = (SELECT id FROM tmpl_tran_cu WHERE code='nhan_hon_don'),
  tran_nhan_so_luong = 3,
  do_kho_quiz = 6,
  bonus_moi_cau_dung = 8.0,
  bonus_thoi_gian_moi_cau = 15.0,
  exp_base = 5000
WHERE pham_cap = 'Tien';

-- Trận Thần — phức tạp nhất
UPDATE tmpl_tran_phap SET 
  tran_co_id = (SELECT id FROM tmpl_tran_cu WHERE code='co_than'),
  tran_co_so_luong = 9,
  tran_ban_id = (SELECT id FROM tmpl_tran_cu WHERE code='ban_than'),
  tran_ban_so_luong = 9,
  tran_nhan_id = (SELECT id FROM tmpl_tran_cu WHERE code='nhan_hon_don'),
  tran_nhan_so_luong = 5,
  do_kho_quiz = 8,
  bonus_moi_cau_dung = 10.0,
  bonus_thoi_gian_moi_cau = 20.0,
  exp_base = 20000
WHERE pham_cap = 'Than';

USE tutien;

-- ============================================================
-- FIX: Gán trận nhãn khớp hệ với trận pháp
-- ============================================================

-- 1. Xem trạng thái hiện tại
SELECT id, ten, he, pham_cap, 
       (SELECT ten FROM tmpl_tran_cu WHERE id = tran_nhan_id) AS nhan_hien_tai
FROM tmpl_tran_phap;

-- 2. Update lại trận nhãn theo hệ

-- Phàm phẩm
UPDATE tmpl_tran_phap 
SET tran_nhan_id = (
  SELECT id FROM tmpl_tran_cu 
  WHERE loai = 'TranNhan' AND he = tmpl_tran_phap.he AND pham_cap = 'Pham'
  LIMIT 1
)
WHERE pham_cap = 'Pham' AND he IS NOT NULL;

-- Linh phẩm
UPDATE tmpl_tran_phap 
SET tran_nhan_id = (
  SELECT id FROM tmpl_tran_cu 
  WHERE loai = 'TranNhan' AND he = tmpl_tran_phap.he AND pham_cap = 'Linh'
  LIMIT 1
)
WHERE pham_cap = 'Linh' AND he IS NOT NULL;

-- Bảo phẩm
UPDATE tmpl_tran_phap 
SET tran_nhan_id = (
  SELECT id FROM tmpl_tran_cu 
  WHERE loai = 'TranNhan' AND he = tmpl_tran_phap.he AND pham_cap = 'Bao'
  LIMIT 1
)
WHERE pham_cap = 'Bao' AND he IS NOT NULL;

-- Tiên phẩm
UPDATE tmpl_tran_phap 
SET tran_nhan_id = (
  SELECT id FROM tmpl_tran_cu 
  WHERE loai = 'TranNhan' AND he = tmpl_tran_phap.he AND pham_cap = 'Tien'
  LIMIT 1
)
WHERE pham_cap = 'Tien' AND he IS NOT NULL;

-- Thần phẩm
UPDATE tmpl_tran_phap 
SET tran_nhan_id = (
  SELECT id FROM tmpl_tran_cu 
  WHERE loai = 'TranNhan' AND he = tmpl_tran_phap.he AND pham_cap = 'Than'
  LIMIT 1
)
WHERE pham_cap = 'Than' AND he IS NOT NULL;

-- 3. Verify
SELECT 
  tp.id,
  tp.ten AS tran_phap,
  tp.he AS he_tran,
  tn.ten AS tran_nhan,
  tn.he AS he_nhan,
  CASE 
    WHEN tp.he = tn.he THEN '✅ Khớp'
    WHEN tn.he IS NULL THEN '⚠️ Nhãn vạn năng'
    ELSE '❌ Sai hệ'
  END AS trang_thai
FROM tmpl_tran_phap tp
LEFT JOIN tmpl_tran_cu tn ON tn.id = tp.tran_nhan_id
ORDER BY tp.pham_cap;

USE tu_tien_db;
SELECT * FROM tmpl_tran_phap;
-- Thêm nhãn Linh cho ngũ hành còn thiếu
INSERT INTO tmpl_tran_cu (code, ten, loai, pham_cap, he, gia_linh_thach, mo_ta)
VALUES
('nhan_kim_linh', 'Kim Nhãn - Linh', 'TranNhan', 'Linh', 'Kim', 1500, 'Trận nhãn Kim hệ linh cấp'),
('nhan_moc_linh', 'Mộc Nhãn - Linh', 'TranNhan', 'Linh', 'Moc', 1500, 'Trận nhãn Mộc hệ linh cấp'),
('nhan_thuy_linh', 'Thủy Nhãn - Linh', 'TranNhan', 'Linh', 'Thuy', 1500, 'Trận nhãn Thủy hệ linh cấp'),
('nhan_hoa_linh', 'Hỏa Nhãn - Linh', 'TranNhan', 'Linh', 'Hoa', 1500, 'Trận nhãn Hỏa hệ linh cấp'),
('nhan_tho_linh', 'Thổ Nhãn - Linh', 'TranNhan', 'Linh', 'Tho', 1500, 'Trận nhãn Thổ hệ linh cấp')
ON DUPLICATE KEY UPDATE ten = VALUES(ten);

-- Thêm nhãn Bảo cho các hệ còn thiếu (đã có Dương, Âm)
INSERT INTO tmpl_tran_cu (code, ten, loai, pham_cap, he, gia_linh_thach, mo_ta)
VALUES
('nhan_kim_bao', 'Kim Nhãn - Bảo', 'TranNhan', 'Bao', 'Kim', 6000, 'Trận nhãn Kim hệ bảo cấp'),
('nhan_moc_bao', 'Mộc Nhãn - Bảo', 'TranNhan', 'Bao', 'Moc', 6000, 'Trận nhãn Mộc hệ bảo cấp'),
('nhan_thuy_bao', 'Thủy Nhãn - Bảo', 'TranNhan', 'Bao', 'Thuy', 6000, 'Trận nhãn Thủy hệ bảo cấp'),
('nhan_hoa_bao', 'Hỏa Nhãn - Bảo', 'TranNhan', 'Bao', 'Hoa', 6000, 'Trận nhãn Hỏa hệ bảo cấp'),
('nhan_tho_bao', 'Thổ Nhãn - Bảo', 'TranNhan', 'Bao', 'Tho', 6000, 'Trận nhãn Thổ hệ bảo cấp')
ON DUPLICATE KEY UPDATE ten = VALUES(ten);

-- Thêm nhãn Tiên (mọi hệ)
INSERT INTO tmpl_tran_cu (code, ten, loai, pham_cap, he, gia_tien_ngoc, mo_ta)
VALUES
('nhan_kim_tien', 'Kim Nhãn - Tiên', 'TranNhan', 'Tien', 'Kim', 50, 'Trận nhãn Kim hệ tiên cấp'),
('nhan_moc_tien', 'Mộc Nhãn - Tiên', 'TranNhan', 'Tien', 'Moc', 50, 'Trận nhãn Mộc hệ tiên cấp'),
('nhan_thuy_tien', 'Thủy Nhãn - Tiên', 'TranNhan', 'Tien', 'Thuy', 50, 'Trận nhãn Thủy hệ tiên cấp'),
('nhan_hoa_tien', 'Hỏa Nhãn - Tiên', 'TranNhan', 'Tien', 'Hoa', 50, 'Trận nhãn Hỏa hệ tiên cấp'),
('nhan_tho_tien', 'Thổ Nhãn - Tiên', 'TranNhan', 'Tien', 'Tho', 50, 'Trận nhãn Thổ hệ tiên cấp'),
('nhan_loi_tien', 'Lôi Nhãn - Tiên', 'TranNhan', 'Tien', 'Loi', 50, 'Trận nhãn Lôi hệ tiên cấp'),
('nhan_bang_tien', 'Băng Nhãn - Tiên', 'TranNhan', 'Tien', 'Bang', 50, 'Trận nhãn Băng hệ tiên cấp'),
('nhan_phong_tien', 'Phong Nhãn - Tiên', 'TranNhan', 'Tien', 'Phong', 50, 'Trận nhãn Phong hệ tiên cấp')
ON DUPLICATE KEY UPDATE ten = VALUES(ten);

-- Thêm nhãn Thần (vạn năng)
INSERT INTO tmpl_tran_cu (code, ten, loai, pham_cap, he, gia_tien_ngoc, mo_ta)
VALUES
('nhan_van_nang_than', 'Vạn Năng Nhãn - Thần', 'TranNhan', 'Than', NULL, 300, 'Trận nhãn vạn năng, dùng cho mọi hệ')
ON DUPLICATE KEY UPDATE ten = VALUES(ten);

-- Verify
SELECT loai, pham_cap, COUNT(*) AS so_luong FROM tmpl_tran_cu 
WHERE loai = 'TranNhan' GROUP BY pham_cap;
-- ============================================================
-- 9. SHOP: Thêm trận cụ, máu, linh dịch
-- ============================================================

INSERT INTO tmpl_shop_item (item_type, item_id, gia_linh_thach, gia_tien_ngoc, so_luong_ton, thu_tu_hien_thi)
SELECT 'TranCu', id, gia_linh_thach, gia_tien_ngoc, 100, 600 + id
FROM tmpl_tran_cu;

INSERT INTO tmpl_shop_item (item_type, item_id, gia_linh_thach, gia_tien_ngoc, so_luong_ton, thu_tu_hien_thi)
SELECT 'MauYeuThu', id, 
  CASE pham_cap
    WHEN 'Pham' THEN 100
    WHEN 'Linh' THEN 500
    WHEN 'Bao' THEN 2500
    WHEN 'Tien' THEN 0
    WHEN 'Than' THEN 0
  END,
  CASE pham_cap
    WHEN 'Tien' THEN 20
    WHEN 'Than' THEN 100
    ELSE 0
  END,
  200, 700 + id
FROM tmpl_mau_yeu_thu;

INSERT INTO tmpl_shop_item (item_type, item_id, gia_linh_thach, gia_tien_ngoc, so_luong_ton, thu_tu_hien_thi)
SELECT 'LinhDich', id,
  CASE pham_cap
    WHEN 'Pham' THEN 200
    WHEN 'Linh' THEN 1000
    WHEN 'Bao' THEN 5000
    ELSE 0
  END,
  CASE pham_cap
    WHEN 'Tien' THEN 30
    WHEN 'Than' THEN 150
    ELSE 0
  END,
  100, 800 + id
FROM tmpl_linh_dich;

SELECT '✅ Seed data nghề đã xong!' AS ket_qua;

USE tu_tien_db;

-- ============================================================
-- SEED TRẬN PHÁP (data gốc)
-- ============================================================

INSERT INTO tmpl_tran_phap 
(code, ten, loai, he, pham_cap, yeu_cau_nghe_cap, 
 effect, thoi_gian_hieu_luc, ban_kinh, mo_ta) 
VALUES

-- Phàm phẩm
('tran_cong_kim', 'Kim Cương Trận', 'Buff', 'Kim', 'Pham', 1,
 CAST('{"atk_pct": 10}' AS JSON), 1800, 0,
 'Tăng 10% ATK trong 30 phút'),

('tran_thu_tho', 'Thổ Bích Trận', 'Buff', 'Tho', 'Pham', 1,
 CAST('{"def_pct": 15}' AS JSON), 1800, 0,
 'Tăng 15% DEF trong 30 phút'),

-- Linh phẩm
('tran_hoi_moc', 'Mộc Linh Trận', 'Buff', 'Moc', 'Linh', 2,
 CAST('{"hp_max_pct": 10, "hieu_ung_hoi_phuc_bonus": 20}' AS JSON), 3600, 0,
 'Tăng 10% HP Max và 20% hiệu ứng hồi phục trong 1 giờ'),

('tran_do_huyet', 'Huyết Sát Trận', 'Debuff', 'Hoa', 'Linh', 3,
 CAST('{"atk_pct": -15}' AS JSON), 900, 0,
 'Giảm 15% ATK của kẻ địch trong 15 phút'),

-- Bảo phẩm
('tran_am_duong', 'Âm Dương Trận', 'HonHop', 'Duong', 'Bao', 5,
 CAST('{"atk_pct": 20, "def_pct": 20, "hp_max_pct": 10}' AS JSON), 3600, 0,
 'Tăng 20% ATK, 20% DEF, 10% HP Max trong 1 giờ');