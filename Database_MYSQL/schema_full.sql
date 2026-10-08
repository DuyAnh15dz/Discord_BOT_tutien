
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `canh_gioi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `canh_gioi` (
  `id` tinyint unsigned NOT NULL AUTO_INCREMENT,
  `ten` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `cap_bac` tinyint unsigned NOT NULL,
  `so_tang` tinyint unsigned NOT NULL DEFAULT '9',
  `exp_tang_1` bigint unsigned NOT NULL DEFAULT '100' COMMENT 'Exp cần cho tầng 1 → 2',
  `he_so_tang` decimal(4,3) NOT NULL DEFAULT '1.100' COMMENT 'Hệ số nhân exp mỗi tầng (1.1 = +10%)',
  `he_so_dot_pha` decimal(4,2) NOT NULL DEFAULT '9.00' COMMENT 'Hệ số nhân exp khi đột phá cảnh giới (×9)',
  `ti_le_dot_pha_co_ban` decimal(5,2) NOT NULL DEFAULT '50.00' COMMENT 'Tỉ lệ đột phá cơ bản (%)',
  `ti_le_dot_pha_toi_da` decimal(5,2) NOT NULL DEFAULT '95.00' COMMENT 'Tỉ lệ đột phá tối đa (%)',
  `he_so_suc_manh` decimal(6,2) NOT NULL DEFAULT '1.00' COMMENT 'Hệ số nhân stat theo cảnh giới',
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_canh_gioi_ten` (`ten`),
  UNIQUE KEY `uk_canh_gioi_cap_bac` (`cap_bac`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Cảnh giới tu luyện. cap_bac: 1=Luyện Khí → 10=Tiên Nhân';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `he_thong_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `he_thong_config` (
  `key_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` json NOT NULL,
  `mo_ta` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`key_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Config động, không hardcode vào code bot';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_bay_tran`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_bay_tran` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `tran_phap_id` int unsigned NOT NULL,
  `thanh_cong` tinyint NOT NULL,
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_lbt_player` (`player_id`,`thoi_diem`),
  CONSTRAINT `fk_lbt_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_bxh_thuong`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_bxh_thuong` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `loai_bxh` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `hang` int unsigned NOT NULL,
  `linh_thach` bigint unsigned NOT NULL DEFAULT '0',
  `exp` bigint unsigned NOT NULL DEFAULT '0',
  `tu_vi` bigint unsigned NOT NULL DEFAULT '0',
  `dan_phuong_nhan` json DEFAULT NULL COMMENT 'Danh sách [dan_duoc_id, ...]',
  `dao_cu_nhan` smallint unsigned DEFAULT NULL COMMENT 'ID đạo cụ nhận được',
  `tuan` date NOT NULL COMMENT 'Ngày thứ 2 đầu tuần',
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_lbxh_player` (`player_id`,`tuan`),
  KEY `idx_lbxh_loai_tuan` (`loai_bxh`,`tuan`),
  CONSTRAINT `fk_lbxh_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Log trao thưởng BXH hàng tuần';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_daily` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `ngay` date NOT NULL,
  `streak` int unsigned NOT NULL,
  `linh_thach_nhan` bigint unsigned NOT NULL,
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_log_daily_player` (`player_id`,`thoi_diem`),
  CONSTRAINT `fk_ld_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_dot_pha`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_dot_pha` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `tu_canh_gioi_id` tinyint unsigned NOT NULL,
  `tu_tang` tinyint unsigned NOT NULL,
  `den_canh_gioi_id` tinyint unsigned DEFAULT NULL,
  `den_tang` tinyint unsigned DEFAULT NULL,
  `ti_le_cuoi` decimal(5,2) NOT NULL COMMENT 'Tỉ lệ đột phá cuối cùng sau khi cộng bonus',
  `ti_le_co_ban` decimal(5,2) NOT NULL COMMENT 'Tỉ lệ cơ bản của cảnh giới',
  `bonus_linh_can` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus từ linh căn',
  `bonus_dan_duoc` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus từ đan dược',
  `bonus_dao_cu` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus từ đạo cụ đột phá (%)',
  `bonus_khac` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus từ tâm cảnh, khí vận, thất bại liên tiếp...',
  `dao_cu_id` smallint unsigned DEFAULT NULL COMMENT 'Đạo cụ hỗ trợ đột phá (nếu có)',
  `thanh_cong` tinyint NOT NULL,
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_log_dotpha` (`player_id`,`thoi_diem`),
  KEY `idx_log_dotpha_canh_gioi` (`tu_canh_gioi_id`,`thoi_diem`),
  KEY `idx_log_dotpha_thanh_cong` (`thanh_cong`,`thoi_diem`),
  KEY `fk_ldp_dao_cu` (`dao_cu_id`),
  CONSTRAINT `fk_ldp_dao_cu` FOREIGN KEY (`dao_cu_id`) REFERENCES `tmpl_dao_cu` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_ldp_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_ldp_thanh_cong` CHECK ((`thanh_cong` in (0,1))),
  CONSTRAINT `chk_ldp_ti_le` CHECK ((`ti_le_cuoi` between 0 and 100))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Log đột phá. Lưu chi tiết tỉ lệ để audit và balance.';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_dot_pha_linh_can`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_dot_pha_linh_can` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `linh_can_id_cu` smallint unsigned NOT NULL COMMENT 'Linh căn trước khi đột phá',
  `linh_can_id_moi` smallint unsigned NOT NULL COMMENT 'Linh căn sau khi đột phá (dù thành công hay không)',
  `dao_cu_id` smallint unsigned DEFAULT NULL COMMENT 'Đạo cụ đã dùng (nếu có)',
  `ti_le` decimal(5,2) NOT NULL COMMENT 'Tỉ lệ đột phá cuối cùng (%)',
  `ti_le_co_ban` decimal(5,2) NOT NULL COMMENT 'Tỉ lệ cơ bản',
  `bonus_dao_cu` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus từ đạo cụ',
  `bonus_that_bai` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus từ thất bại liên tiếp',
  `thanh_cong` tinyint NOT NULL,
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_dplc_cu` (`linh_can_id_cu`),
  KEY `fk_dplc_moi` (`linh_can_id_moi`),
  KEY `fk_dplc_dao_cu` (`dao_cu_id`),
  KEY `idx_dplc_player` (`player_id`,`thoi_diem`),
  CONSTRAINT `fk_dplc_cu` FOREIGN KEY (`linh_can_id_cu`) REFERENCES `tmpl_linh_can` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_dplc_dao_cu` FOREIGN KEY (`dao_cu_id`) REFERENCES `tmpl_dao_cu` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_dplc_moi` FOREIGN KEY (`linh_can_id_moi`) REFERENCES `tmpl_linh_can` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_dplc_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_dplc_thanh_cong` CHECK ((`thanh_cong` in (0,1)))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Log đột phá phẩm cấp linh căn. Dùng để audit và balance';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_giao_dich`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_giao_dich` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `loai` enum('Mua','Ban') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_id` int unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL,
  `gia_linh_thach` bigint unsigned NOT NULL DEFAULT '0',
  `gia_tien_ngoc` bigint unsigned NOT NULL DEFAULT '0',
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_log_gd_player` (`player_id`,`thoi_diem`),
  CONSTRAINT `fk_lgd_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_lichluyen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_lichluyen` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `dia_diem_id` tinyint unsigned NOT NULL,
  `ket_qua` json NOT NULL,
  `tong_linh_thach` bigint unsigned NOT NULL DEFAULT '0',
  `tong_tu_vi` bigint unsigned NOT NULL DEFAULT '0',
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_log_ll` (`player_id`,`thoi_diem`),
  KEY `fk_ll_dia_diem` (`dia_diem_id`),
  CONSTRAINT `fk_ll_dia_diem` FOREIGN KEY (`dia_diem_id`) REFERENCES `tmpl_dia_diem` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ll_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_luyen_khi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_luyen_khi` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `phap_khi_id` int unsigned NOT NULL,
  `ket_qua` json NOT NULL,
  `thanh_cong` tinyint NOT NULL,
  `exp_nhan` int unsigned NOT NULL DEFAULT '0',
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_llk_player` (`player_id`,`thoi_diem`),
  CONSTRAINT `fk_llk_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_su_kien`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_su_kien` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned DEFAULT NULL,
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` json NOT NULL,
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_event` (`event_type`,`thoi_diem`),
  KEY `fk_lsk_player` (`player_id`),
  CONSTRAINT `fk_lsk_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Log chung. Ghi mọi event: giao dịch, chiến đấu, sự kiện...';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_tran_phap_quiz`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_tran_phap_quiz` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `tran_phap_id` int unsigned NOT NULL,
  `so_cau_dung` int unsigned NOT NULL,
  `tong_cau` int unsigned NOT NULL,
  `ket_qua` json NOT NULL,
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ltpq_player` (`player_id`,`thoi_diem`),
  CONSTRAINT `fk_ltpq_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `log_ve_bua`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_ve_bua` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `bua_chu_id` int unsigned NOT NULL,
  `so_luong_thanh_cong` int unsigned NOT NULL DEFAULT '0',
  `exp_nhan` int unsigned NOT NULL DEFAULT '0',
  `thoi_diem` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_lvb_player` (`player_id`,`thoi_diem`),
  CONSTRAINT `fk_lvb_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `misc_tui_do`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `misc_tui_do` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `item_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `so_luong` int unsigned NOT NULL,
  `metadata` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tui_do` (`player_id`,`item_code`),
  CONSTRAINT `fk_tui_do_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player` (
  `player_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `discord_id` bigint unsigned NOT NULL,
  `ten_nhan_vat` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `canh_gioi_id` tinyint unsigned NOT NULL,
  `tang_canh_gioi` tinyint unsigned NOT NULL DEFAULT '1',
  `tang_tich_luy` tinyint unsigned NOT NULL DEFAULT '1' COMMENT 'Tầng tích lũy xuyên cảnh giới (1-90)',
  `exp` bigint unsigned NOT NULL DEFAULT '0',
  `tu_vi` bigint unsigned NOT NULL DEFAULT '0',
  `linh_thach` bigint unsigned NOT NULL DEFAULT '0',
  `tien_ngoc` bigint unsigned NOT NULL DEFAULT '0',
  `tam_canh` int NOT NULL DEFAULT '0',
  `khi_van` int NOT NULL DEFAULT '0',
  `so_du_lan_dot_pha` int unsigned NOT NULL DEFAULT '0' COMMENT 'Số lần đột phá thất bại liên tiếp',
  `ti_le_dot_pha_them` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Tỉ lệ đột phá cộng thêm từ thất bại liên tiếp (%)',
  `last_dot_pha` datetime DEFAULT NULL COMMENT 'Lần đột phá cuối cùng',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_active` datetime DEFAULT NULL,
  `is_banned` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`),
  UNIQUE KEY `uk_player_discord` (`discord_id`),
  UNIQUE KEY `uk_player_ten` (`ten_nhan_vat`),
  KEY `idx_canh_gioi` (`canh_gioi_id`,`tang_canh_gioi`),
  KEY `idx_tu_vi` (`tu_vi`),
  CONSTRAINT `fk_player_canh_gioi` FOREIGN KEY (`canh_gioi_id`) REFERENCES `canh_gioi` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='hp_hien_tai/mp_hien_tai đã chuyển vào player_stat';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_backup_20260914`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_backup_20260914` (
  `player_id` bigint unsigned NOT NULL DEFAULT '0',
  `discord_id` bigint unsigned NOT NULL,
  `ten_nhan_vat` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `canh_gioi_id` tinyint unsigned NOT NULL,
  `tang_canh_gioi` tinyint unsigned NOT NULL DEFAULT '1',
  `tang_tich_luy` tinyint unsigned NOT NULL DEFAULT '1' COMMENT 'Tầng tích lũy xuyên cảnh giới (1-90)',
  `exp` bigint unsigned NOT NULL DEFAULT '0',
  `tu_vi` bigint unsigned NOT NULL DEFAULT '0',
  `linh_thach` bigint unsigned NOT NULL DEFAULT '0',
  `tien_ngoc` bigint unsigned NOT NULL DEFAULT '0',
  `tam_canh` int NOT NULL DEFAULT '0',
  `khi_van` int NOT NULL DEFAULT '0',
  `so_du_lan_dot_pha` int unsigned NOT NULL DEFAULT '0' COMMENT 'Số lần đột phá thất bại liên tiếp',
  `ti_le_dot_pha_them` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Tỉ lệ đột phá cộng thêm từ thất bại liên tiếp (%)',
  `last_dot_pha` datetime DEFAULT NULL COMMENT 'Lần đột phá cuối cùng',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_active` datetime DEFAULT NULL,
  `is_banned` tinyint NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_bua_chu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_bua_chu` (
  `player_id` bigint unsigned NOT NULL,
  `bua_chu_id` int unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`bua_chu_id`),
  KEY `fk_pbc_bua_chu` (`bua_chu_id`),
  CONSTRAINT `fk_pbc_bua_chu` FOREIGN KEY (`bua_chu_id`) REFERENCES `tmpl_bua_chu` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pbc_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_bua_chu_thuan_thuc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_bua_chu_thuan_thuc` (
  `player_id` bigint unsigned NOT NULL,
  `bua_chu_id` int unsigned NOT NULL,
  `do_thuan_thuc` tinyint unsigned NOT NULL DEFAULT '0',
  `so_lan_ve` int unsigned NOT NULL DEFAULT '0',
  `cap_nhat_luc` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`,`bua_chu_id`),
  KEY `fk_pbctt_bua` (`bua_chu_id`),
  CONSTRAINT `fk_pbctt_bua` FOREIGN KEY (`bua_chu_id`) REFERENCES `tmpl_bua_chu` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pbctt_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_buff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_buff` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `buff_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Mã buff/debuff (VD: bong, te_liet, buff_atk)',
  `effect` json NOT NULL COMMENT 'Hiệu ứng JSON: {"dmg_per_turn":30,"turns":5}',
  `stack` smallint unsigned NOT NULL DEFAULT '1' COMMENT 'Số stack chồng (tối đa tùy loại buff)',
  `bat_dau_luc` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm bắt đầu buff',
  `het_han_luc` datetime NOT NULL COMMENT 'Thời điểm hết hạn',
  `nguon_goc` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Nguồn gây buff (VD: dan_bao_khi, boss_skill)',
  `cap_nhat_luc` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Lần cập nhật cuối (kéo dài thời gian)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_buff_player_code` (`player_id`,`buff_code`),
  KEY `idx_buff_expire` (`player_id`,`het_han_luc`),
  KEY `idx_buff_code` (`buff_code`,`het_han_luc`),
  CONSTRAINT `fk_buff_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_buff_stack` CHECK ((`stack` >= 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Buff/debuff tạm. Cùng buff_code sẽ KÉO DÀI thời gian thay vì tạo mới';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_bxh_tuan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_bxh_tuan` (
  `player_id` bigint unsigned NOT NULL,
  `loai_bxh` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Mã BXH seasonal',
  `tuan` date NOT NULL COMMENT 'Ngày thứ 2 đầu tuần',
  `gia_tri` bigint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`loai_bxh`,`tuan`),
  KEY `idx_pbt_loai_tuan` (`loai_bxh`,`tuan`,`gia_tri` DESC),
  CONSTRAINT `fk_pbt_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stat tích lũy hàng tuần cho seasonal BXH';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_cong_phap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_cong_phap` (
  `player_id` bigint unsigned NOT NULL,
  `cong_phap_id` int unsigned NOT NULL,
  `tang_hien_tai` tinyint unsigned NOT NULL DEFAULT '1',
  `do_thuan_thuc` decimal(5,2) NOT NULL DEFAULT '0.00',
  `dang_tu_luyen` tinyint NOT NULL DEFAULT '0',
  `ngay_hoc` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`,`cong_phap_id`),
  KEY `fk_pcp_cong_phap` (`cong_phap_id`),
  CONSTRAINT `fk_pcp_cong_phap` FOREIGN KEY (`cong_phap_id`) REFERENCES `tmpl_cong_phap` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pcp_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_cooldown`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_cooldown` (
  `player_id` bigint unsigned NOT NULL,
  `action_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `san_sang_luc` datetime NOT NULL,
  PRIMARY KEY (`player_id`,`action_code`),
  CONSTRAINT `fk_cd_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_daily` (
  `player_id` bigint unsigned NOT NULL,
  `ngay_cuoi` date NOT NULL COMMENT 'Ngày điểm danh cuối (theo múi giờ VN)',
  `streak` int unsigned NOT NULL DEFAULT '0' COMMENT 'Chuỗi ngày điểm danh liên tiếp',
  `tong_linh_thach` bigint unsigned NOT NULL DEFAULT '0' COMMENT 'Tổng linh thạch nhận từ daily',
  `so_lan_diem_danh` int unsigned NOT NULL DEFAULT '0' COMMENT 'Tổng số lần điểm danh',
  PRIMARY KEY (`player_id`),
  CONSTRAINT `fk_pd_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Điểm danh hàng ngày của player';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_dan_duoc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_dan_duoc` (
  `player_id` bigint unsigned NOT NULL,
  `dan_duoc_id` int unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`dan_duoc_id`),
  KEY `fk_pdd_dan_duoc` (`dan_duoc_id`),
  CONSTRAINT `fk_pdd_dan_duoc` FOREIGN KEY (`dan_duoc_id`) REFERENCES `tmpl_dan_duoc` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pdd_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_dan_gioi_han`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_dan_gioi_han` (
  `player_id` bigint unsigned NOT NULL,
  `dan_duoc_id` int unsigned NOT NULL,
  `canh_gioi_id` tinyint unsigned NOT NULL COMMENT 'Cảnh giới đang đột phá khi dùng đan',
  `so_lan_da_dung` int unsigned NOT NULL DEFAULT '1' COMMENT 'Số lần đã dùng cho cảnh giới này',
  `lan_dung_cuoi` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Lần dùng cuối',
  PRIMARY KEY (`player_id`,`dan_duoc_id`,`canh_gioi_id`),
  KEY `fk_pdgh_dan` (`dan_duoc_id`),
  KEY `fk_pdgh_canh_gioi` (`canh_gioi_id`),
  CONSTRAINT `fk_pdgh_canh_gioi` FOREIGN KEY (`canh_gioi_id`) REFERENCES `canh_gioi` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pdgh_dan` FOREIGN KEY (`dan_duoc_id`) REFERENCES `tmpl_dan_duoc` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pdgh_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tracking giới hạn dùng đan theo cảnh giới';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_dan_phuong_hoc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_dan_phuong_hoc` (
  `player_id` bigint unsigned NOT NULL,
  `dan_duoc_id` int unsigned NOT NULL,
  `so_lan_nghien_cuu` int unsigned NOT NULL DEFAULT '0' COMMENT 'Số lần học trùng, mỗi lần +1% tỉ lệ cơ bản',
  `ngay_hoc` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`,`dan_duoc_id`),
  KEY `fk_pdph_dan_duoc` (`dan_duoc_id`),
  CONSTRAINT `fk_pdph_dan_duoc` FOREIGN KEY (`dan_duoc_id`) REFERENCES `tmpl_dan_duoc` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pdph_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_dao_cu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_dao_cu` (
  `player_id` bigint unsigned NOT NULL,
  `dao_cu_id` smallint unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  `ngay_nhan` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Ngày nhận đạo cụ đầu tiên',
  `cap_nhat_luc` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`,`dao_cu_id`),
  KEY `idx_pdc_dao_cu` (`dao_cu_id`),
  CONSTRAINT `fk_pdc_dao_cu` FOREIGN KEY (`dao_cu_id`) REFERENCES `tmpl_dao_cu` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pdc_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_pdc_so_luong` CHECK ((`so_luong` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Đạo cụ player sở hữu';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_khoang_thach`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_khoang_thach` (
  `player_id` bigint unsigned NOT NULL,
  `khoang_thach_id` smallint unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`khoang_thach_id`),
  KEY `idx_pkt_khoang_thach` (`khoang_thach_id`),
  CONSTRAINT `fk_pkt_khoang_thach` FOREIGN KEY (`khoang_thach_id`) REFERENCES `tmpl_khoang_thach` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pkt_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_linh_can`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_linh_can` (
  `player_id` bigint unsigned NOT NULL,
  `linh_can_id` smallint unsigned NOT NULL,
  `do_tinh_khiet` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Độ tinh khiết 0-100%. Đạt 100% có thể đột phá phẩm cấp',
  `so_lan_dung_dao_cu_dot_pha` tinyint unsigned NOT NULL DEFAULT '0' COMMENT 'Số lần đã dùng đạo cụ tăng tỉ lệ (max 2, reset sau đột phá)',
  `san_sang_dot_pha` tinyint NOT NULL DEFAULT '0' COMMENT '1 = đã đủ 100% tinh khiết, sẵn sàng đột phá',
  `so_lan_dot_pha_that_bai` int unsigned NOT NULL DEFAULT '0' COMMENT 'Số lần đột phá thất bại (dùng để cộng tỉ lệ lần sau)',
  `is_active` tinyint NOT NULL DEFAULT '1' COMMENT '1 = đang kích hoạt, 0 = không dùng',
  `ngay_nhan` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Ngày nhận linh căn',
  `cap_nhat_luc` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Lần cập nhật cuối',
  PRIMARY KEY (`player_id`,`linh_can_id`),
  KEY `fk_plc_linh_can` (`linh_can_id`),
  KEY `idx_plc_player_active` (`player_id`,`is_active`),
  KEY `idx_plc_san_sang` (`player_id`,`san_sang_dot_pha`),
  CONSTRAINT `fk_plc_linh_can` FOREIGN KEY (`linh_can_id`) REFERENCES `tmpl_linh_can` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_plc_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_is_active` CHECK ((`is_active` in (0,1))),
  CONSTRAINT `chk_san_sang` CHECK ((`san_sang_dot_pha` in (0,1))),
  CONSTRAINT `chk_tinh_khiet` CHECK ((`do_tinh_khiet` between 0 and 100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Linh căn player sở hữu. Cày độ tinh khiết để đột phá phẩm cấp';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_linh_dich`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_linh_dich` (
  `player_id` bigint unsigned NOT NULL,
  `linh_dich_id` smallint unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`linh_dich_id`),
  KEY `fk_pld_linh_dich` (`linh_dich_id`),
  CONSTRAINT `fk_pld_linh_dich` FOREIGN KEY (`linh_dich_id`) REFERENCES `tmpl_linh_dich` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pld_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_linh_thao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_linh_thao` (
  `player_id` bigint unsigned NOT NULL,
  `linh_thao_id` int unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`linh_thao_id`),
  KEY `fk_plt_linh_thao` (`linh_thao_id`),
  CONSTRAINT `fk_plt_linh_thao` FOREIGN KEY (`linh_thao_id`) REFERENCES `tmpl_linh_thao` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_plt_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_mau_yeu_thu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_mau_yeu_thu` (
  `player_id` bigint unsigned NOT NULL,
  `mau_yeu_thu_id` smallint unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`mau_yeu_thu_id`),
  KEY `fk_pmyt_mau` (`mau_yeu_thu_id`),
  CONSTRAINT `fk_pmyt_mau` FOREIGN KEY (`mau_yeu_thu_id`) REFERENCES `tmpl_mau_yeu_thu` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pmyt_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_nghe_nghiep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_nghe_nghiep` (
  `player_id` bigint unsigned NOT NULL,
  `nghe_nghiep_id` tinyint unsigned NOT NULL,
  `cap_do` tinyint unsigned NOT NULL DEFAULT '1',
  `kinh_nghiem` bigint unsigned NOT NULL DEFAULT '0',
  `danh_vong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`nghe_nghiep_id`),
  KEY `fk_pnn_nghe` (`nghe_nghiep_id`),
  CONSTRAINT `fk_pnn_nghe` FOREIGN KEY (`nghe_nghiep_id`) REFERENCES `tmpl_nghe_nghiep` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pnn_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_phap_khi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_phap_khi` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `player_id` bigint unsigned NOT NULL,
  `phap_khi_id` int unsigned NOT NULL,
  `cap_do` tinyint unsigned NOT NULL DEFAULT '1',
  `dang_trang_bi` tinyint NOT NULL DEFAULT '0',
  `slot` enum('VuKhi','Ao','Non','Giay','Nhan') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  `cap_nhat_luc` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_player_slot` (`player_id`,`slot`),
  KEY `idx_player` (`player_id`),
  KEY `fk_ppk_phap_khi` (`phap_khi_id`),
  CONSTRAINT `fk_ppk_phap_khi` FOREIGN KEY (`phap_khi_id`) REFERENCES `tmpl_phap_khi` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ppk_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_stat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_stat` (
  `player_id` bigint unsigned NOT NULL,
  `hp_max` int unsigned NOT NULL DEFAULT '0',
  `mp_max` int unsigned NOT NULL DEFAULT '0',
  `atk` int unsigned NOT NULL DEFAULT '0',
  `def` int unsigned NOT NULL DEFAULT '0',
  `matk` int unsigned NOT NULL DEFAULT '0',
  `mdef` int unsigned NOT NULL DEFAULT '0',
  `hp_max_pct` decimal(5,2) NOT NULL DEFAULT '0.00',
  `mp_max_pct` decimal(5,2) NOT NULL DEFAULT '0.00',
  `hp_hien_tai` int unsigned NOT NULL DEFAULT '0',
  `mp_hien_tai` int unsigned NOT NULL DEFAULT '0',
  `ti_le_ne` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_chinh_xac` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_chi_mang` decimal(5,2) NOT NULL DEFAULT '5.00',
  `sat_thuong_chi_mang` decimal(5,2) NOT NULL DEFAULT '150.00',
  `ti_le_khang_chi_mang` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_xuyen_giap` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_xuyen_phep` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_hut_mau` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_hoi_mp` decimal(5,2) NOT NULL DEFAULT '0.00',
  `giam_sat_thuong_nhan` decimal(5,2) NOT NULL DEFAULT '0.00',
  `giam_hoi_chieu` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_kim` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_moc` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_thuy` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_hoa` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_tho` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_loi` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_bang` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_phong` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_duong` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khang_am` decimal(5,2) NOT NULL DEFAULT '0.00',
  `toc_do_tu_luyen` decimal(5,2) NOT NULL DEFAULT '100.00',
  `ti_le_dot_pha` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus tỉ lệ đột phá từ stat (%)',
  `ti_le_ngo_dao` decimal(5,2) NOT NULL DEFAULT '0.00',
  `tam_canh_bonus` decimal(5,2) NOT NULL DEFAULT '0.00',
  `khi_van_bonus` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_thanh_cong_do_kiep` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_gay_bong` decimal(5,2) NOT NULL DEFAULT '0.00',
  `sat_thuong_bong_moi_luot` int unsigned NOT NULL DEFAULT '0',
  `ti_le_gay_te_liet` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_gay_dong_bang` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_gay_mu` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_gay_roi_loan` decimal(5,2) NOT NULL DEFAULT '0.00',
  `ti_le_kich_hoat_hoi_hp` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Xác suất kích hoạt hồi HP mỗi lượt (%)',
  `phan_tram_hoi_hp_moi_luot` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '% HP_max hồi mỗi lượt khi kích hoạt',
  `hieu_ung_hoi_phuc_bonus` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Bonus % nhân vào lượng hồi phục',
  `bonus_ti_le_roi_do` decimal(5,2) NOT NULL DEFAULT '0.00',
  `bonus_ti_le_roi_linh_thach` decimal(5,2) NOT NULL DEFAULT '0.00',
  `is_dirty` tinyint NOT NULL DEFAULT '1',
  `cap_nhat_luc` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_hp_update` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm HP được update lần cuối',
  `in_combat` tinyint NOT NULL DEFAULT '0' COMMENT '1 = đang combat (không hồi HP), 0 = ngoài combat (hồi 1%/s)',
  `atk_pct` decimal(5,2) NOT NULL DEFAULT '0.00',
  `def_pct` decimal(5,2) NOT NULL DEFAULT '0.00',
  `matk_pct` decimal(5,2) NOT NULL DEFAULT '0.00',
  `mdef_pct` decimal(5,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`player_id`),
  CONSTRAINT `fk_pstat_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_chi_mang` CHECK ((`ti_le_chi_mang` between 0 and 100)),
  CONSTRAINT `chk_giam_hoi_chieu` CHECK ((`giam_hoi_chieu` between 0 and 45)),
  CONSTRAINT `chk_khang` CHECK (((`khang_kim` between 0 and 90) and (`khang_moc` between 0 and 90) and (`khang_thuy` between 0 and 90) and (`khang_hoa` between 0 and 90) and (`khang_tho` between 0 and 90) and (`khang_loi` between 0 and 90) and (`khang_bang` between 0 and 90) and (`khang_phong` between 0 and 90) and (`khang_duong` between 0 and 90) and (`khang_am` between 0 and 90))),
  CONSTRAINT `chk_kich_hoat` CHECK ((`ti_le_kich_hoat_hoi_hp` between 0 and 100)),
  CONSTRAINT `chk_ne` CHECK ((`ti_le_ne` between 0 and 75)),
  CONSTRAINT `chk_phan_tram_hoi` CHECK ((`phan_tram_hoi_hp_moi_luot` between 0 and 50))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Wide table. is_dirty=1 → cần recompute';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `player_tran_cu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_tran_cu` (
  `player_id` bigint unsigned NOT NULL,
  `tran_cu_id` smallint unsigned NOT NULL,
  `so_luong` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`player_id`,`tran_cu_id`),
  KEY `fk_ptc_tran_cu` (`tran_cu_id`),
  CONSTRAINT `fk_ptc_player` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ptc_tran_cu` FOREIGN KEY (`tran_cu_id`) REFERENCES `tmpl_tran_cu` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_bua_chu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_bua_chu` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('TanCong','PhongThu','HoTro','KhongChe') COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') COLLATE utf8mb4_unicode_ci NOT NULL,
  `yeu_cau_nghe_cap` tinyint unsigned NOT NULL DEFAULT '1',
  `effect` json NOT NULL,
  `mp_cost` int unsigned NOT NULL DEFAULT '50',
  `khoang_thach_id` smallint unsigned DEFAULT NULL,
  `so_luong_khoang_thach` smallint unsigned NOT NULL DEFAULT '1',
  `mau_yeu_thu_id` smallint unsigned DEFAULT NULL,
  `mau_yeu_thu_so_luong` smallint unsigned NOT NULL DEFAULT '0',
  `linh_dich_id` smallint unsigned DEFAULT NULL,
  `linh_dich_so_luong` smallint unsigned NOT NULL DEFAULT '0',
  `exp_base` int unsigned NOT NULL DEFAULT '100',
  `mo_ta` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bua_chu_code` (`code`),
  KEY `fk_bc_khoang_thach` (`khoang_thach_id`),
  KEY `fk_bc_mau` (`mau_yeu_thu_id`),
  KEY `fk_bc_linh_dich` (`linh_dich_id`),
  CONSTRAINT `fk_bc_khoang_thach` FOREIGN KEY (`khoang_thach_id`) REFERENCES `tmpl_khoang_thach` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_bc_linh_dich` FOREIGN KEY (`linh_dich_id`) REFERENCES `tmpl_linh_dich` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_bc_mau` FOREIGN KEY (`mau_yeu_thu_id`) REFERENCES `tmpl_mau_yeu_thu` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_bxh`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_bxh` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'VD: canh_gioi, linh_thach, exp_tuan',
  `ten` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `emoji` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `loai` enum('snapshot','seasonal') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'snapshot = không reset, seasonal = reset hàng tuần',
  `query_sql` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'SQL lấy top, dùng {limit}',
  `order_column` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Cột dùng để sort (cho seasonal)',
  `table_nguon` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Bảng nguồn (cho seasonal)',
  `is_active` tinyint NOT NULL DEFAULT '1',
  `thu_tu` smallint unsigned DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bxh_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Metadata các loại BXH. Thêm row mới = thêm BXH mới';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_cong_phap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_cong_phap` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `ten` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('NguHanh','DiHe','LuyenThe','LuyenHon') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` json DEFAULT NULL,
  `giai_cap` enum('Hoang','Huyen','Dia','Thien') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Ha','Trung','Thuong','Cuc','HoanMy') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `so_tang` tinyint unsigned NOT NULL DEFAULT '9',
  `effect_moi_tang` json NOT NULL,
  `yeu_cau_canh_gioi_id` tinyint unsigned DEFAULT NULL,
  `bonus_dac_biet` json DEFAULT NULL COMMENT '{"dieu_kien": "Duong", "he_so": 1.5} cho LuyenThe',
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cong_phap` (`ten`,`giai_cap`,`pham_cap`),
  KEY `idx_loai_giai` (`loai`,`giai_cap`),
  KEY `fk_cp_canh_gioi` (`yeu_cau_canh_gioi_id`),
  CONSTRAINT `fk_cp_canh_gioi` FOREIGN KEY (`yeu_cau_canh_gioi_id`) REFERENCES `canh_gioi` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_dan_duoc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_dan_duoc` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `ten` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('HoiPhuc','DotPha','TangTuVi','Buff','Doc','Ho Tro Dot Pha') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `effect` json NOT NULL,
  `yeu_cau_nghe_cap` tinyint unsigned NOT NULL DEFAULT '1',
  `ti_le_dot_pha_bonus` decimal(5,2) NOT NULL DEFAULT '0.00',
  `exp_bonus` bigint unsigned NOT NULL DEFAULT '0',
  `tu_vi_bonus` bigint unsigned NOT NULL DEFAULT '0',
  `thoi_gian_hieu_luc` int unsigned NOT NULL DEFAULT '0',
  `gioi_han_moi_canh_gioi` tinyint NOT NULL DEFAULT '0',
  `ap_dung_canh_gioi_id` tinyint unsigned DEFAULT NULL,
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dan_duoc_ten` (`ten`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_dan_phuong`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_dan_phuong` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `dan_duoc_id` int unsigned NOT NULL,
  `linh_thao_id` int unsigned NOT NULL,
  `so_luong` smallint unsigned NOT NULL,
  `ti_le_thanh_cong_max` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dan_phuong` (`dan_duoc_id`,`linh_thao_id`),
  KEY `fk_dp_linh_thao` (`linh_thao_id`),
  CONSTRAINT `fk_dp_dan_duoc` FOREIGN KEY (`dan_duoc_id`) REFERENCES `tmpl_dan_duoc` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_dp_linh_thao` FOREIGN KEY (`linh_thao_id`) REFERENCES `tmpl_linh_thao` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=139 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_dao_cu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_dao_cu` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('DotPhaLinhCan','TangTinhKhiet','TangTiLeDotPha','Khac') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Hệ của đạo cụ (NULL = dùng cho mọi hệ)',
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `effect` json NOT NULL COMMENT 'VD: {"ti_le_bonus":25} hoặc {"tinh_khiet":10}',
  `co_the_mua_premium` tinyint NOT NULL DEFAULT '0' COMMENT '1 = có bán trong shop tiên ngọc',
  `gia_tien_ngoc` int unsigned NOT NULL DEFAULT '0' COMMENT 'Giá mua bằng tiên ngọc',
  `is_active` tinyint NOT NULL DEFAULT '1',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dao_cu_code` (`code`),
  KEY `idx_dao_cu_loai` (`loai`,`pham_cap`),
  CONSTRAINT `chk_dao_cu_active` CHECK ((`is_active` in (0,1))),
  CONSTRAINT `chk_dao_cu_premium` CHECK ((`co_the_mua_premium` in (0,1)))
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Đạo cụ đặc biệt: đột phá linh căn, tăng tinh khiết, buff...';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_dia_diem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_dia_diem` (
  `id` tinyint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `he_so_linh_thach` decimal(4,2) NOT NULL DEFAULT '1.00',
  `he_so_exp` decimal(4,2) NOT NULL DEFAULT '1.00',
  `he_so_linh_thao` decimal(4,2) NOT NULL DEFAULT '1.00',
  `he_so_khoang_thach` decimal(4,2) NOT NULL DEFAULT '1.00',
  `he_so_dan_phuong` decimal(4,2) NOT NULL DEFAULT '1.00',
  `is_active` tinyint NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dia_diem_code` (`code`),
  UNIQUE KEY `uk_dia_diem_ten` (`ten`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_dia_diem_su_kien`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_dia_diem_su_kien` (
  `dia_diem_id` tinyint unsigned NOT NULL,
  `su_kien_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `trong_so` smallint unsigned NOT NULL DEFAULT '100',
  PRIMARY KEY (`dia_diem_id`,`su_kien_code`),
  CONSTRAINT `fk_ddsk_dia_diem` FOREIGN KEY (`dia_diem_id`) REFERENCES `tmpl_dia_diem` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_he_quan_he`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_he_quan_he` (
  `he_nguon` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci NOT NULL,
  `he_dich` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci NOT NULL,
  `quan_he` enum('TuongSinh','TuongKhac','TrungTinh') COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`he_nguon`,`he_dich`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_khoang_thach`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_khoang_thach` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('LuyenKhi','VePhu','CaHai') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gia_ban` int unsigned NOT NULL DEFAULT '0' COMMENT 'Giá bán cho hệ thống (linh thạch)',
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_khoang_thach_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_linh_can`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_linh_can` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `ten` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Ha','Trung','Thuong','Cuc','Tien') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `he_so_bonus` decimal(5,2) NOT NULL DEFAULT '1.00',
  `ti_le_dot_pha_bonus` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '% cộng vào tỉ lệ đột phá khi linh căn active',
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_linh_can` (`ten`,`pham_cap`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_linh_can_stat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_linh_can_stat` (
  `linh_can_id` smallint unsigned NOT NULL,
  `stat_id` smallint unsigned NOT NULL,
  `gia_tri_bonus` decimal(10,4) NOT NULL,
  PRIMARY KEY (`linh_can_id`,`stat_id`),
  KEY `fk_lcs_stat` (`stat_id`),
  CONSTRAINT `fk_lcs_linh_can` FOREIGN KEY (`linh_can_id`) REFERENCES `tmpl_linh_can` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_lcs_stat` FOREIGN KEY (`stat_id`) REFERENCES `tmpl_stat_type` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mapping linh căn → stat bonus. Có thể âm (debuff).';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_linh_dich`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_linh_dich` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci NOT NULL,
  `bonus_ti_le` decimal(5,2) NOT NULL DEFAULT '0.00',
  `mo_ta` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ld_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_linh_thao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_linh_thao` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `ten` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `thoi_gian_sinh_truong` int unsigned NOT NULL,
  `ti_le_dot_pha_bonus` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '% cộng vào tỉ lệ đột phá khi dùng',
  `exp_bonus` bigint unsigned NOT NULL DEFAULT '0' COMMENT 'Exp cộng thêm khi dùng',
  `tu_vi_bonus` bigint unsigned NOT NULL DEFAULT '0' COMMENT 'Tu vi cộng thêm khi dùng',
  `thoi_gian_hieu_luc` int unsigned NOT NULL DEFAULT '0' COMMENT 'Thời gian hiệu lực (giây)',
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_linh_thao_ten` (`ten`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_mau_yeu_thu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_mau_yeu_thu` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mo_ta` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_mau_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_nghe_nghiep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_nghe_nghiep` (
  `id` tinyint unsigned NOT NULL AUTO_INCREMENT,
  `ten` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('LuyenDan','LuyenKhi','TranPhap','PhuLuc') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `cap_toi_da` tinyint unsigned NOT NULL,
  `exp_moi_cap` json NOT NULL,
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_nghe_nghiep_ten` (`ten`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_nghe_nghiep_bonus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_nghe_nghiep_bonus` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nghe_nghiep_id` tinyint unsigned NOT NULL,
  `stat_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `gia_tri_bonus` decimal(10,4) NOT NULL,
  `mo_ta` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_nghe_stat` (`nghe_nghiep_id`,`stat_code`),
  CONSTRAINT `fk_nnb_nghe` FOREIGN KEY (`nghe_nghiep_id`) REFERENCES `tmpl_nghe_nghiep` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bonus stat cho từng nghề nghiệp';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_phap_khi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_phap_khi` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('VuKhi','Ao','Non','Giay','Nhan') COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') COLLATE utf8mb4_unicode_ci NOT NULL,
  `yeu_cau_canh_gioi_id` tinyint unsigned DEFAULT NULL,
  `yeu_cau_nghe_cap` tinyint unsigned NOT NULL DEFAULT '1',
  `cap_toi_da` tinyint unsigned NOT NULL DEFAULT '5',
  `effect_moi_cap` json NOT NULL,
  `khoang_thach_id` smallint unsigned DEFAULT NULL,
  `mo_ta` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_phap_khi_code` (`code`),
  KEY `idx_loai_pham` (`loai`,`pham_cap`),
  KEY `fk_pk_canh_gioi` (`yeu_cau_canh_gioi_id`),
  KEY `fk_pk_khoang_thach` (`khoang_thach_id`),
  CONSTRAINT `fk_pk_canh_gioi` FOREIGN KEY (`yeu_cau_canh_gioi_id`) REFERENCES `canh_gioi` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_pk_khoang_thach` FOREIGN KEY (`khoang_thach_id`) REFERENCES `tmpl_khoang_thach` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_phap_khi_cong_thuc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_phap_khi_cong_thuc` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `phap_khi_id` int unsigned NOT NULL,
  `khoang_thach_id` smallint unsigned NOT NULL,
  `so_luong` smallint unsigned NOT NULL,
  `ti_le_thanh_cong_max` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pkct` (`phap_khi_id`,`khoang_thach_id`),
  KEY `fk_pkct_khoang_thach` (`khoang_thach_id`),
  CONSTRAINT `fk_pkct_khoang_thach` FOREIGN KEY (`khoang_thach_id`) REFERENCES `tmpl_khoang_thach` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pkct_phap_khi` FOREIGN KEY (`phap_khi_id`) REFERENCES `tmpl_phap_khi` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_shop_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_shop_item` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `item_type` enum('DanDuoc','DaoCu','LinhThao','KhoangThach','DacBiet','CongPhap','TranCu','MauYeuThu','LinhDich') COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_id` int unsigned NOT NULL COMMENT 'ID tham chiếu tới bảng tương ứng',
  `gia_linh_thach` int unsigned NOT NULL DEFAULT '0',
  `gia_tien_ngoc` int unsigned NOT NULL DEFAULT '0',
  `so_luong_ton` int unsigned NOT NULL DEFAULT '0' COMMENT '0 = hết hàng, > 0 = còn hàng',
  `is_active` tinyint NOT NULL DEFAULT '1',
  `thu_tu_hien_thi` smallint unsigned DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_shop_item` (`item_type`,`item_id`),
  KEY `idx_shop_type` (`item_type`,`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=239 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_stat_khoi_dau`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_stat_khoi_dau` (
  `stat_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `gia_tri` int unsigned NOT NULL,
  `mo_ta` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`stat_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stat khởi đầu của mọi nhân vật (trước khi cộng bonus)';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_stat_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_stat_type` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten_hien_thi` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `nhom` enum('CoBan','ChienDau','KhangNguyenTo','TuLuyen','Utility','HieuUng','HoiPhuc') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `don_vi` enum('flat','percent','multiplier') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'flat',
  `gia_tri_mac_dinh` decimal(10,4) NOT NULL DEFAULT '0.0000',
  `gia_tri_toi_da` decimal(10,4) DEFAULT NULL,
  `gia_tri_toi_thieu` decimal(10,4) NOT NULL DEFAULT '0.0000',
  `cong_thuc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mo_ta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `thu_tu_hien_thi` smallint unsigned DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stat_code` (`code`),
  KEY `idx_nhom` (`nhom`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Định nghĩa metadata các loại stat. code dùng trong bot.';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_tran_cu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_tran_cu` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('TranCo','TranBan','TranNhan') COLLATE utf8mb4_unicode_ci NOT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gia_linh_thach` int unsigned NOT NULL DEFAULT '0',
  `gia_tien_ngoc` int unsigned NOT NULL DEFAULT '0',
  `mo_ta` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tran_cu_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tmpl_tran_phap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tmpl_tran_phap` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ten` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `loai` enum('Buff','Debuff','HonHop') COLLATE utf8mb4_unicode_ci NOT NULL,
  `he` enum('Kim','Moc','Thuy','Hoa','Tho','Loi','Bang','Phong','Duong','Am') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pham_cap` enum('Pham','Linh','Bao','Tien','Than') COLLATE utf8mb4_unicode_ci NOT NULL,
  `yeu_cau_nghe_cap` tinyint unsigned NOT NULL DEFAULT '1',
  `effect` json NOT NULL,
  `thoi_gian_hieu_luc` int unsigned NOT NULL,
  `ban_kinh` int unsigned NOT NULL DEFAULT '0',
  `khoang_thach_id` smallint unsigned DEFAULT NULL,
  `so_luong_khoang_thach` smallint unsigned NOT NULL DEFAULT '1',
  `mo_ta` text COLLATE utf8mb4_unicode_ci,
  `tran_co_id` smallint unsigned DEFAULT NULL,
  `tran_co_so_luong` smallint unsigned NOT NULL DEFAULT '1',
  `tran_ban_id` smallint unsigned DEFAULT NULL,
  `tran_ban_so_luong` smallint unsigned NOT NULL DEFAULT '1',
  `tran_nhan_id` smallint unsigned DEFAULT NULL,
  `tran_nhan_so_luong` smallint unsigned NOT NULL DEFAULT '1',
  `do_kho_quiz` tinyint unsigned NOT NULL DEFAULT '3',
  `bonus_moi_cau_dung` decimal(5,2) NOT NULL DEFAULT '5.00',
  `bonus_thoi_gian_moi_cau` decimal(5,2) NOT NULL DEFAULT '10.00',
  `exp_base` int unsigned NOT NULL DEFAULT '200',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tran_phap_code` (`code`),
  KEY `fk_tp_khoang_thach` (`khoang_thach_id`),
  KEY `fk_tp_tran_co` (`tran_co_id`),
  KEY `fk_tp_tran_ban` (`tran_ban_id`),
  KEY `fk_tp_tran_nhan` (`tran_nhan_id`),
  CONSTRAINT `fk_tp_khoang_thach` FOREIGN KEY (`khoang_thach_id`) REFERENCES `tmpl_khoang_thach` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_tp_tran_ban` FOREIGN KEY (`tran_ban_id`) REFERENCES `tmpl_tran_cu` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_tp_tran_co` FOREIGN KEY (`tran_co_id`) REFERENCES `tmpl_tran_cu` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_tp_tran_nhan` FOREIGN KEY (`tran_nhan_id`) REFERENCES `tmpl_tran_cu` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

