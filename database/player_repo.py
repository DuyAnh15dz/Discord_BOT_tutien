from database.connection import get_connection


class Player:
    def __init__(self, row):
        self.player_id = row['player_id']
        self.discord_id = row['discord_id']
        self.ten_nhan_vat = row['ten_nhan_vat']
        self.canh_gioi_id = row['canh_gioi_id']
        self.tang_canh_gioi = row['tang_canh_gioi']
        self.tang_tich_luy = row.get('tang_tich_luy', 1)
        self.exp = row['exp']
        self.tu_vi = row['tu_vi']
        self.linh_thach = row['linh_thach']
        self.tien_ngoc = row['tien_ngoc']
        self.tam_canh = row['tam_canh']
        self.khi_van = row['khi_van']
        self.canh_gioi_ten = row.get('canh_gioi_ten')
        self.so_tang = row.get('so_tang', 9)
        self.exp_tang_1 = row.get('exp_tang_1', 100)
        self.he_so_tang = row.get('he_so_tang', 1.1)
        self.linh_can_list = row.get('linh_can_list', [])
        self.nghe_nghiep = row.get('nghe_nghiep')


# ============================================================
# HÀM CŨ — GIỮ NGUYÊN
# ============================================================

def get_player_full_info(discord_id: int):
    """
    Lấy TẤT CẢ thông tin player trong 1 query duy nhất.
    Trả về Player object (có thêm .linh_can_list và .nghe_nghiep).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Player + cảnh giới
        cursor.execute("""
            SELECT p.*, cg.ten AS canh_gioi_ten, cg.so_tang,
                   cg.exp_tang_1, cg.he_so_tang
            FROM player p
            JOIN canh_gioi cg ON cg.id = p.canh_gioi_id
            WHERE p.discord_id = %s
        """, (discord_id,))
        player_row = cursor.fetchone()
        if not player_row:
            return None
        
        player_id = player_row['player_id']
        
        # 2. Linh căn
        cursor.execute("""
            SELECT lc.ten, lc.he, lc.pham_cap,
                   plc.do_tinh_khiet, plc.is_active
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s
        """, (player_id,))
        player_row['linh_can_list'] = cursor.fetchall()
        
        # 3. Nghề nghiệp
        cursor.execute("""
            SELECT nn.ten, nn.cap_toi_da, nn.exp_moi_cap,
                   pnn.cap_do, pnn.kinh_nghiem, pnn.danh_vong
            FROM player_nghe_nghiep pnn
            JOIN tmpl_nghe_nghiep nn ON nn.id = pnn.nghe_nghiep_id
            WHERE pnn.player_id = %s
            LIMIT 1
        """, (player_id,))
        player_row['nghe_nghiep'] = cursor.fetchone()
        
        # ⭐ QUAN TRỌNG: Wrap dict vào Player object
        return Player(player_row)
    finally:
        cursor.close()
        conn.close()


def create_player(discord_id: int, ten_nhan_vat: str):
    """Tạo player + player_stat + roll linh căn."""
    from utils.linh_can_roll import roll_so_luong_linh_can, roll_nhieu_linh_can
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        # 1. Tạo player
        cursor.execute("""
            INSERT INTO player (discord_id, ten_nhan_vat, canh_gioi_id)
            VALUES (%s, %s, 1)
        """, (discord_id, ten_nhan_vat))
        player_id = cursor.lastrowid

        # 2. Tạo player_stat
        cursor.execute("""
            INSERT INTO player_stat (
                player_id, hp_max, mp_max, atk, def, matk, mdef,
                hp_hien_tai, mp_hien_tai
            ) VALUES (%s, 100, 50, 10, 5, 8, 5, 100, 50)
        """, (player_id,))

        # 3. Roll linh căn
        so_luong = roll_so_luong_linh_can()
        linh_can_ids = roll_nhieu_linh_can(so_luong)
        
        for lc_id in linh_can_ids:
            cursor.execute("""
                INSERT INTO player_linh_can 
                (player_id, linh_can_id, do_tinh_khiet, is_active)
                VALUES (%s, %s, 0, 1)
            """, (player_id, lc_id))
        
        print(f'[DB] Player {ten_nhan_vat} rolled {so_luong} linh căn: {linh_can_ids}')

        conn.commit()
        return get_player_full_info(discord_id), linh_can_ids
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def add_exp_and_tuvi(player_id: int, exp: int, tu_vi: int):
    """Cộng exp và tu vi trong 1 transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE player 
            SET exp = exp + %s, tu_vi = tu_vi + %s 
            WHERE player_id = %s
        """, (exp, tu_vi, player_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_canh_gioi(canh_gioi_id: int):
    """Lấy cảnh giới theo ID."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM canh_gioi WHERE id = %s", (canh_gioi_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_cooldown(player_id: int, action_code: str):
    """Lấy thời điểm sẵn sàng của cooldown."""
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT san_sang_luc FROM player_cooldown
            WHERE player_id = %s AND action_code = %s
        """, (player_id, action_code))
        row = cursor.fetchone()
        if not row:
            return None
        return row['san_sang_luc']
    finally:
        cursor.close()
        conn.close()


def set_cooldown(player_id: int, action_code: str, seconds: int):
    """Set cooldown."""
    from datetime import datetime, timedelta
    conn = get_connection()
    cursor = conn.cursor()
    try:
        san_sang = datetime.now() + timedelta(seconds=seconds)
        cursor.execute("""
            INSERT INTO player_cooldown (player_id, action_code, san_sang_luc)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE san_sang_luc = VALUES(san_sang_luc)
        """, (player_id, action_code, san_sang))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def delete_player(player_id: int) -> bool:
    """
    Xóa player và toàn bộ dữ liệu liên quan.
    Nhờ ON DELETE CASCADE trong schema.
    
    Returns:
        True nếu xóa thành công, False nếu không tìm thấy player
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM player WHERE player_id = %s", (player_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    finally:
        cursor.close()
        conn.close()


def get_player_linh_can_summary(player_id: int):
    """
    Lấy danh sách linh căn gọn cho profile.
    
    Returns:
        [{'ten': 'Kim Linh Căn - Trung', 'do_tinh_khiet': 45.5}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                lc.ten,
                lc.he,
                lc.pham_cap,
                plc.do_tinh_khiet,
                plc.is_active
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s
            ORDER BY lc.he,
                FIELD(lc.pham_cap, 'Ha', 'Trung', 'Thuong', 'Cuc', 'Tien')
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_player_nghe_nghiep(player_id: int):
    """
    Lấy thông tin nghề nghiệp của player.
    
    Returns:
        dict hoặc None nếu chưa chọn
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                nn.id AS nghe_id,
                nn.ten,
                nn.loai,
                nn.cap_toi_da,
                nn.exp_moi_cap,
                pnn.cap_do,
                pnn.kinh_nghiem,
                pnn.danh_vong
            FROM player_nghe_nghiep pnn
            JOIN tmpl_nghe_nghiep nn ON nn.id = pnn.nghe_nghiep_id
            WHERE pnn.player_id = %s
            LIMIT 1
        """, (player_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        # Tính exp cần cho cấp tiếp theo
        import json
        cap_do = row['cap_do']
        cap_tiep = cap_do + 1
        
        exp_moi_cap = row['exp_moi_cap']
        if isinstance(exp_moi_cap, str):
            exp_moi_cap = json.loads(exp_moi_cap)
        
        if cap_do >= row['cap_toi_da']:
            # Đã max
            row['exp_can_tang'] = None
            row['la_max'] = True
        else:
            row['exp_can_tang'] = int(exp_moi_cap.get(str(cap_tiep), 0))
            row['la_max'] = False
        
        return row
    finally:
        cursor.close()
        conn.close()


def get_player_linh_can_active(player_id: int):
    """Lấy tất cả linh căn active của player."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                plc.linh_can_id,
                plc.do_tinh_khiet,
                lc.ten,
                lc.he,
                lc.pham_cap
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s AND plc.is_active = 1
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def tang_tinh_khiet(player_id: int, linh_can_id: int, amount: float):
    """Tăng độ tinh khiết cho 1 linh căn."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE player_linh_can
            SET do_tinh_khiet = LEAST(do_tinh_khiet + %s, 100),
                san_sang_dot_pha = IF(do_tinh_khiet + %s >= 100, 1, 0)
            WHERE player_id = %s AND linh_can_id = %s
        """, (amount, amount, player_id, linh_can_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_player_linh_can_full(player_id: int):
    """
    Lấy tất cả linh căn của player kèm thông tin đầy đủ.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                plc.linh_can_id,
                plc.do_tinh_khiet,
                plc.is_active,
                plc.san_sang_dot_pha,
                plc.so_lan_dot_pha_that_bai,
                lc.ten,
                lc.he,
                lc.pham_cap,
                lc.he_so_bonus,
                lc.ti_le_dot_pha_bonus
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s
            ORDER BY 
                FIELD(lc.he, 'Kim', 'Moc', 'Thuy', 'Hoa', 'Tho', 'Loi', 'Bang', 'Phong', 'Duong', 'Am'),
                FIELD(lc.pham_cap, 'Tien', 'Cuc', 'Thuong', 'Trung', 'Ha')
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_linh_can_stats(linh_can_id: int, he_so_bonus: float = 1.0):
    """
    Lấy stat bonus của linh căn.
    ⚠️ DB đã nhân hệ số sẵn cho từng phẩm cấp.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                st.code,
                st.ten_hien_thi,
                st.don_vi,
                lcs.gia_tri_bonus
            FROM tmpl_linh_can_stat lcs
            JOIN tmpl_stat_type st ON st.id = lcs.stat_id
            WHERE lcs.linh_can_id = %s
            ORDER BY st.thu_tu_hien_thi
        """, (linh_can_id,))
        rows = cursor.fetchall()
        
        for row in rows:
            row['gia_tri_thuc_te'] = row['gia_tri_bonus']
        
        return rows
    finally:
        cursor.close()
        conn.close()


def xu_ly_tang_tu_dong(player_id: int) -> dict:
    """
    Xử lý tự động lên tầng.
    - tang_canh_gioi: tầng trong cảnh giới (1-9)
    - tang_tich_luy: tầng tích lũy (1-90)
    """
    from utils.stat_calc import tinh_exp_can_tang
    import json
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # ===== 1. Lấy thông tin =====
        cursor.execute("""
            SELECT p.*, cg.so_tang, cg.ten AS canh_gioi_ten, cg.he_so_suc_manh
            FROM player p
            JOIN canh_gioi cg ON cg.id = p.canh_gioi_id
            WHERE p.player_id = %s
            FOR UPDATE
        """, (player_id,))
        p = cursor.fetchone()
        if not p:
            conn.rollback()
            return None
        
        tang_cu = p['tang_canh_gioi']
        tang_tich_luy_cu = p['tang_tich_luy']
        exp_hien_tai = p['exp']
        canh_gioi_id = p['canh_gioi_id']
        so_tang = p['so_tang']
        canh_gioi_ten = p['canh_gioi_ten']
        he_so_suc_manh = float(p['he_so_suc_manh'])
        
        # ===== 2. Kiểm tra max tầng trong cảnh giới =====
        if tang_cu >= so_tang:
            conn.commit()
            return {
                'so_tang_len': 0,
                'tang_cu': tang_cu,
                'tang_moi': tang_cu,
                'tang_tich_luy_cu': tang_tich_luy_cu,
                'tang_tich_luy_moi': tang_tich_luy_cu,
                'exp_con_lai': exp_hien_tai,
                'canh_gioi_ten': canh_gioi_ten,
                'so_tang_toi_da': so_tang,
                'da_max_tang': True,
                'stat_tang_len': {},
            }
        
        # ===== 3. Vòng lặp lên tầng =====
        tang_moi = tang_cu
        tang_tich_luy_moi = tang_tich_luy_cu
        exp_con = exp_hien_tai
        
        while tang_moi < so_tang:
            exp_can = tinh_exp_can_tang(canh_gioi_id, tang_moi)
            
            if exp_con >= exp_can:
                exp_con -= exp_can
                tang_moi += 1
                tang_tich_luy_moi += 1
            else:
                break
        
        so_tang_len = tang_moi - tang_cu
        
        # ===== 4. Update DB =====
        stat_tang_len = {}
        
        if so_tang_len > 0:
            # 4a. Update player
            cursor.execute("""
                UPDATE player
                SET tang_canh_gioi = %s,
                    tang_tich_luy = %s,
                    exp = %s
                WHERE player_id = %s
            """, (tang_moi, tang_tich_luy_moi, exp_con, player_id))
            
            # 4b. Recompute stat
            cursor.execute("""
                SELECT value FROM he_thong_config
                WHERE key_name = 'stat_tang_moi_tang_pct'
            """)
            row = cursor.fetchone()
            pct = json.loads(row['value']) if row else 5.0
            
            cursor.execute("SELECT stat_code, gia_tri FROM tmpl_stat_khoi_dau")
            stat_khoi_dau = {r['stat_code']: float(r['gia_tri']) for r in cursor.fetchall()}
            
            if stat_khoi_dau:
                cursor.execute("""
                    SELECT hp_max, mp_max, atk, def, matk, mdef
                    FROM player_stat WHERE player_id = %s
                """, (player_id,))
                stat_cu = cursor.fetchone()
                
                # Công thức dùng tang_tich_luy
                he_so_cu = he_so_suc_manh * (1.0 + (tang_tich_luy_cu - 1) * (pct / 100.0))
                he_so_moi = he_so_suc_manh * (1.0 + (tang_tich_luy_moi - 1) * (pct / 100.0))
                
                # Lấy bonus percent từ linh căn
                cursor.execute("""
                    SELECT st.code, lcs.gia_tri_bonus
                    FROM player_linh_can plc
                    JOIN tmpl_linh_can_stat lcs ON lcs.linh_can_id = plc.linh_can_id
                    JOIN tmpl_stat_type st ON st.id = lcs.stat_id
                    WHERE plc.player_id = %s AND plc.is_active = 1
                """, (player_id,))
                bonus_pct = {}
                for r in cursor.fetchall():
                    code = r['code']
                    bonus_pct[code] = bonus_pct.get(code, 0.0) + float(r['gia_tri_bonus'])
                
                # Bonus từ nghề
                cursor.execute("""
                    SELECT nb.stat_code, nb.gia_tri_bonus
                    FROM player_nghe_nghiep pnn
                    JOIN tmpl_nghe_nghiep_bonus nb 
                        ON nb.nghe_nghiep_id = pnn.nghe_nghiep_id
                    WHERE pnn.player_id = %s
                """, (player_id,))
                for r in cursor.fetchall():
                    code = r['stat_code']
                    if code.endswith('_pct'):
                        bonus_pct[code] = bonus_pct.get(code, 0.0) + float(r['gia_tri_bonus'])
                
                # Bonus từ buff
                cursor.execute("""
                    SELECT effect FROM player_buff
                    WHERE player_id = %s AND het_han_luc > NOW()
                """, (player_id,))
                for r in cursor.fetchall():
                    effect = r['effect']
                    if isinstance(effect, str):
                        effect = json.loads(effect)
                    if not isinstance(effect, dict):
                        continue
                    for code, gia_tri in effect.items():
                        if code.endswith('_pct'):
                            try:
                                bonus_pct[code] = bonus_pct.get(code, 0.0) + float(gia_tri)
                            except (ValueError, TypeError):
                                pass
                
                # Tính stat mới
                updates = []
                params = []
                for code, gia_tri_goc in stat_khoi_dau.items():
                    gia_tri_base = gia_tri_goc * he_so_moi
                    pct_bonus = bonus_pct.get(f'{code}_pct', 0.0)
                    gia_tri_moi = int(gia_tri_base * (1 + pct_bonus / 100))
                    
                    gia_tri_cu = int(stat_cu.get(code, 0)) if stat_cu else 0
                    
                    updates.append(f"{code} = %s")
                    params.append(gia_tri_moi)
                    
                    stat_tang_len[code] = {
                        'cu': gia_tri_cu,
                        'moi': gia_tri_moi,
                        'chenh_lech': gia_tri_moi - gia_tri_cu,
                    }
                
                params.append(player_id)
                
                cursor.execute(f"""
                    UPDATE player_stat
                    SET {', '.join(updates)}
                    WHERE player_id = %s
                """, params)
            
            conn.commit()
        
        return {
            'so_tang_len': so_tang_len,
            'tang_cu': tang_cu,
            'tang_moi': tang_moi,
            'tang_tich_luy_cu': tang_tich_luy_cu,
            'tang_tich_luy_moi': tang_tich_luy_moi,
            'exp_con_lai': exp_con,
            'canh_gioi_ten': canh_gioi_ten,
            'so_tang_toi_da': so_tang,
            'da_max_tang': tang_moi >= so_tang, 
            'stat_tang_len': stat_tang_len,
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def recompute_player_stat(cursor, player_id: int) -> dict:
    """
    Recompute stat cơ bản của player.
    Dùng cursor có sẵn. KHÔNG commit — caller commit.
    
    Công thức:
        he_so_tang = he_so_suc_manh(canh_gioi) × (1 + (tang_tich_luy - 1) × pct/100)
        stat = stat_goc × he_so_tang × (1 + bonus_pct/100)
    
    Returns:
        dict {stat_code: gia_tri_moi}
    """
    import json
    
    # ===== 1. Lấy thông tin player =====
    cursor.execute("""
        SELECT p.tang_tich_luy, cg.he_so_suc_manh
        FROM player p
        JOIN canh_gioi cg ON cg.id = p.canh_gioi_id
        WHERE p.player_id = %s
    """, (player_id,))
    p = cursor.fetchone()
    if not p:
        return {}
    
    tang_tich_luy = p['tang_tich_luy']
    he_so_suc_manh = float(p['he_so_suc_manh'])
    
    # ===== 2. Lấy config pct =====
    cursor.execute("""
        SELECT value FROM he_thong_config
        WHERE key_name = 'stat_tang_moi_tang_pct'
    """)
    row = cursor.fetchone()
    pct = json.loads(row['value']) if row else 5.0
    
    # Công thức hệ số tầng
    he_so_tang = he_so_suc_manh * (1.0 + (tang_tich_luy - 1) * (pct / 100.0))
    
    # ===== 3. Lấy stat khởi đầu =====
    cursor.execute("SELECT stat_code, gia_tri FROM tmpl_stat_khoi_dau")
    stat_khoi_dau = {r['stat_code']: float(r['gia_tri']) for r in cursor.fetchall()}
    
    if not stat_khoi_dau:
        return {}
    
    # ===== 4. Lấy bonus percent =====
    bonus_pct = {}
    
    # 4a. Từ linh căn active
    cursor.execute("""
        SELECT st.code, lcs.gia_tri_bonus
        FROM player_linh_can plc
        JOIN tmpl_linh_can_stat lcs ON lcs.linh_can_id = plc.linh_can_id
        JOIN tmpl_stat_type st ON st.id = lcs.stat_id
        WHERE plc.player_id = %s AND plc.is_active = 1
    """, (player_id,))
    for r in cursor.fetchall():
        code = r['code']
        bonus_pct[code] = bonus_pct.get(code, 0.0) + float(r['gia_tri_bonus'])
    
    # 4b. Từ nghề nghiệp
    cursor.execute("""
        SELECT nb.stat_code, nb.gia_tri_bonus
        FROM player_nghe_nghiep pnn
        JOIN tmpl_nghe_nghiep_bonus nb 
            ON nb.nghe_nghiep_id = pnn.nghe_nghiep_id
        WHERE pnn.player_id = %s
    """, (player_id,))
    for r in cursor.fetchall():
        code = r['stat_code']
        if code.endswith('_pct'):
            bonus_pct[code] = bonus_pct.get(code, 0.0) + float(r['gia_tri_bonus'])
    
    # 4c. Từ buff
    cursor.execute("""
        SELECT effect FROM player_buff
        WHERE player_id = %s AND het_han_luc > NOW()
    """, (player_id,))
    for r in cursor.fetchall():
        effect = r['effect']
        if isinstance(effect, str):
            effect = json.loads(effect)
        if not isinstance(effect, dict):
            continue
        for code, gia_tri in effect.items():
            if code.endswith('_pct'):
                try:
                    bonus_pct[code] = bonus_pct.get(code, 0.0) + float(gia_tri)
                except (ValueError, TypeError):
                    pass
    
    # ===== 5. Tính stat mới =====
    updates = []
    params = []
    ket_qua = {}
    
    for code, gia_tri_goc in stat_khoi_dau.items():
        # Stat base = gốc × hệ số tầng
        gia_tri_base = gia_tri_goc * he_so_tang
        
        # Áp dụng percent bonus (VD: hp_max + hp_max_pct)
        pct_bonus = bonus_pct.get(f'{code}_pct', 0.0)
        gia_tri_moi = int(gia_tri_base * (1 + pct_bonus / 100))
        
        updates.append(f"{code} = %s")
        params.append(gia_tri_moi)
        ket_qua[code] = gia_tri_moi
    
    params.append(player_id)
    
    cursor.execute(f"""
        UPDATE player_stat
        SET {', '.join(updates)}
        WHERE player_id = %s
    """, params)
    
    # ===== 6. Điều chỉnh HP/MP không vượt max =====
    cursor.execute("""
        UPDATE player_stat
        SET hp_hien_tai = LEAST(hp_hien_tai, hp_max),
            mp_hien_tai = LEAST(mp_hien_tai, mp_max)
        WHERE player_id = %s
    """, (player_id,))
    
    return ket_qua

def xu_ly_dot_pha(player_id: int, thanh_cong: bool) -> dict:
    """
    Xử lý đột phá cảnh giới.
    
    Khi thành công:
        - canh_gioi_id += 1
        - tang_canh_gioi = 1 (reset về tầng 1)
        - tang_tich_luy += 1
        - exp = 0
        - Recompute stat với cảnh giới mới
    
    Khi thất bại:
        - so_du_lan_dot_pha += 1
        - Set cooldown theo config
    
    Returns:
        {
            'thanh_cong': bool,
            'canh_gioi_cu': str,
            'canh_gioi_moi': str,       # Chỉ khi thành công
            'tang_tich_luy_moi': int,    # Chỉ khi thành công
            'cooldown_giay': int,        # Chỉ khi thất bại
        }
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # ===== 1. Lấy thông tin hiện tại =====
        cursor.execute("""
            SELECT p.*, cg.ten AS canh_gioi_ten, cg.cap_bac
            FROM player p
            JOIN canh_gioi cg ON cg.id = p.canh_gioi_id
            WHERE p.player_id = %s
            FOR UPDATE
        """, (player_id,))
        p = cursor.fetchone()
        
        if not p:
            conn.rollback()
            return {
                'thanh_cong': False,
                'canh_gioi_cu': None,
                'canh_gioi_moi': None,
                'loi': 'Không tìm thấy player!',
                'cooldown_giay': 0,
            }
        
        canh_gioi_cu = p['canh_gioi_ten']
        cap_bac_cu = p['cap_bac']
        canh_gioi_id_cu = p['canh_gioi_id']
        tang_tich_luy_cu = p['tang_tich_luy']
        
        # ===== 2. Xử lý thành công =====
        if thanh_cong:
            # 2a. Lấy thông tin cảnh giới mới
            cursor.execute("""
                SELECT ten, so_tang, he_so_suc_manh
                FROM canh_gioi
                WHERE id = %s
            """, (canh_gioi_id_cu + 1,))
            cg_moi = cursor.fetchone()
            
            if not cg_moi:
                conn.rollback()
                return {
                    'thanh_cong': False,
                    'canh_gioi_cu': canh_gioi_cu,
                    'canh_gioi_moi': None,
                    'loi': 'Đã đạt cảnh giới tối đa!',
                    'cooldown_giay': 0,
                }
            
            # 2b. Update player: reset tầng, tăng tích lũy
            cursor.execute("""
                UPDATE player
                SET canh_gioi_id = canh_gioi_id + 1,
                    tang_canh_gioi = 1,
                    tang_tich_luy = tang_tich_luy + 1,
                    exp = 0,
                    so_du_lan_dot_pha = 0,
                    last_dot_pha = NOW()
                WHERE player_id = %s
            """, (player_id,))
            
            # 2c. Recompute stat với cảnh giới mới
            recompute_player_stat(cursor, player_id)
            
            conn.commit()
            
            return {
                'thanh_cong': True,
                'canh_gioi_cu': canh_gioi_cu,
                'canh_gioi_moi': cg_moi['ten'],
                'tang_tich_luy_moi': tang_tich_luy_cu + 1,
                'cooldown_giay': 0,
            }
        
        # ===== 3. Xử lý thất bại =====
        else:
            # 3a. Tăng counter thất bại
            cursor.execute("""
                UPDATE player
                SET so_du_lan_dot_pha = so_du_lan_dot_pha + 1,
                    last_dot_pha = NOW()
                WHERE player_id = %s
            """, (player_id,))
            
            # 3b. Lấy cooldown từ config
            cursor.execute("""
                SELECT value FROM he_thong_config 
                WHERE key_name = 'dotpha_cooldown_that_bai'
            """)
            row = cursor.fetchone()
            
            import json
            cd_dict = json.loads(row['value']) if row else {}
            cooldown_giay = int(cd_dict.get(str(cap_bac_cu), 7200))
            
            # 3c. Set cooldown
            from datetime import datetime, timedelta
            san_sang = datetime.now() + timedelta(seconds=cooldown_giay)
            
            cursor.execute("""
                INSERT INTO player_cooldown (player_id, action_code, san_sang_luc)
                VALUES (%s, 'dotpha', %s)
                ON DUPLICATE KEY UPDATE san_sang_luc = VALUES(san_sang_luc)
            """, (player_id, san_sang))
            
            conn.commit()
            
            return {
                'thanh_cong': False,
                'canh_gioi_cu': canh_gioi_cu,
                'canh_gioi_moi': None,
                'cooldown_giay': cooldown_giay,
            }
    
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] xu_ly_dot_pha: {e}')
        import traceback
        traceback.print_exc()
        raise e
    finally:
        cursor.close()
        conn.close()


def ghi_log_dot_pha(player_id: int, tu_cg_id: int, tu_tang: int,
                     den_cg_id: int, den_tang: int,
                     ti_le_data: dict, thanh_cong: bool):
    """Ghi log đột phá."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO log_dot_pha (
                player_id, tu_canh_gioi_id, tu_tang,
                den_canh_gioi_id, den_tang,
                ti_le_cuoi, ti_le_co_ban,
                bonus_linh_can, bonus_dan_duoc, bonus_khac,
                thanh_cong
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            player_id, tu_cg_id, tu_tang,
            den_cg_id if thanh_cong else None,
            den_tang if thanh_cong else None,
            ti_le_data['ti_le_cuoi'],
            ti_le_data['nguon'][0]['gia_tri'],
            next((n['gia_tri'] for n in ti_le_data['nguon'] if 'Linh căn' in n['ten']), 0),
            next((n['gia_tri'] for n in ti_le_data['nguon'] if 'Đan' in n['ten']), 0),
            sum(n['gia_tri'] for n in ti_le_data['nguon'][1:] 
                if 'Linh căn' not in n['ten'] and 'Đan' not in n['ten']),
            1 if thanh_cong else 0
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def tinh_hp_regen(player_id: int) -> dict:
    """
    Tính HP hiện tại dựa vào thời gian trôi qua (lazy regen).
    ⭐ Dùng hp_max từ stat_runtime (đúng), không từ player_stat.
    """
    import json
    from datetime import datetime
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Lấy HP hiện tại + metadata (KHÔNG lấy hp_max từ đây)
        cursor.execute("""
            SELECT hp_hien_tai, last_hp_update, in_combat
            FROM player_stat
            WHERE player_id = %s
        """, (player_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        hp_cu = row['hp_hien_tai']
        last_update = row['last_hp_update']
        in_combat = row['in_combat']
        
        # ⭐ 2. Lấy hp_max từ stat runtime (đúng)
        stat_runtime = tinh_stat_runtime(player_id)
        hp_max = int(stat_runtime.get('hp_max', 100))
        
        # 3. Nếu đang combat → không hồi
        if in_combat:
            return {
                'hp_cu': hp_cu,
                'hp_moi': hp_cu,
                'hp_max': hp_max,
                'hp_hoi': 0,
                'thoi_gian_giay': 0,
                'in_combat': True,
            }
        
        # 4. Nếu HP đầy → không cần hồi
        if hp_cu >= hp_max:
            return {
                'hp_cu': hp_cu,
                'hp_moi': hp_cu,
                'hp_max': hp_max,
                'hp_hoi': 0,
                'thoi_gian_giay': 0,
                'in_combat': False,
            }
        
        # 5. Tính thời gian trôi qua
        now = datetime.now()
        elapsed = (now - last_update).total_seconds()
        
        # 6. Lấy config
        cursor.execute("""
            SELECT key_name, value FROM he_thong_config
            WHERE key_name IN ('hp_regen_pct_per_sec', 'hp_regen_delay_sec')
        """)
        configs = {r['key_name']: json.loads(r['value']) for r in cursor.fetchall()}
        
        pct_per_sec = configs.get('hp_regen_pct_per_sec', 1.0)
        delay_sec = configs.get('hp_regen_delay_sec', 5)
        
        # 7. Trừ delay
        if elapsed <= delay_sec:
            return {
                'hp_cu': hp_cu,
                'hp_moi': hp_cu,
                'hp_max': hp_max,
                'hp_hoi': 0,
                'thoi_gian_giay': elapsed,
                'in_combat': False,
            }
        
        # 8. Tính HP hồi
        thoi_gian_hoi = elapsed - delay_sec
        hp_hoi = int(hp_max * pct_per_sec / 100 * thoi_gian_hoi)
        hp_moi = min(hp_cu + hp_hoi, hp_max)
        hp_hoi_thuc = hp_moi - hp_cu
        
        return {
            'hp_cu': hp_cu,
            'hp_moi': hp_moi,
            'hp_max': hp_max,
            'hp_hoi': hp_hoi_thuc,
            'thoi_gian_giay': elapsed,
            'in_combat': False,
        }
    finally:
        cursor.close()
        conn.close()


def update_hp_regen(player_id: int) -> int:
    """
    Update HP sau khi tính regen.
    Returns: HP mới
    """
    ket_qua = tinh_hp_regen(player_id)
    if not ket_qua:
        return 0
    
    # Nếu không có gì thay đổi → không update
    if ket_qua['hp_hoi'] == 0:
        return ket_qua['hp_cu']
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE player_stat
            SET hp_hien_tai = %s,
                last_hp_update = NOW()
            WHERE player_id = %s
        """, (ket_qua['hp_moi'], player_id))
        conn.commit()
        return ket_qua['hp_moi']
    finally:
        cursor.close()
        conn.close()


def set_in_combat(player_id: int, in_combat: bool):
    """Bật/tắt flag combat."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE player_stat
            SET in_combat = %s, last_hp_update = NOW()
            WHERE player_id = %s
        """, (1 if in_combat else 0, player_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def tru_hp(player_id: int, hp_mat: int) -> dict:
    """Trừ HP (khi sập bẫy, thua combat)."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cursor.execute("""
            SELECT hp_hien_tai FROM player_stat
            WHERE player_id = %s FOR UPDATE
        """, (player_id,))
        row = cursor.fetchone()
        if not row:
            conn.rollback()
            return None
        
        hp_cu = row['hp_hien_tai']
        hp_moi = max(0, hp_cu - hp_mat)
        hp_mat_thuc = hp_cu - hp_moi
        
        cursor.execute("""
            UPDATE player_stat
            SET hp_hien_tai = %s, last_hp_update = NOW()
            WHERE player_id = %s
        """, (hp_moi, player_id))
        
        conn.commit()
        
        return {
            'hp_cu': hp_cu,
            'hp_moi': hp_moi,
            'hp_mat_thuc': hp_mat_thuc,
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def random_dia_diem():
    """Random 1 trong 6 địa điểm. Convert Decimal → float."""
    import random
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM tmpl_dia_diem WHERE is_active = 1")
        ds = cursor.fetchall()
        if not ds:
            return None
        
        dia_diem = random.choice(ds)
        
        # ⭐ Convert Decimal → float cho 5 cột hệ số
        for key in ['he_so_linh_thach', 'he_so_exp', 'he_so_linh_thao', 
                    'he_so_khoang_thach', 'he_so_dan_phuong']:
            if key in dia_diem and dia_diem[key] is not None:
                dia_diem[key] = float(dia_diem[key])
        
        return dia_diem
    finally:
        cursor.close()
        conn.close()


def get_xac_suat_su_kien(dia_diem_id: int):
    """Lấy danh sách sự kiện + trọng số theo địa điểm."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT su_kien_code, trong_so
            FROM tmpl_dia_diem_su_kien
            WHERE dia_diem_id = %s
        """, (dia_diem_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_random_linh_thao(pham_cap_list: list = None):
    """
    Random 1 linh thảo + số lượng.
    Tối ưu: Lấy tất cả ID của phẩm cấp về Python rồi random.
    """
    import random
    import json
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'lichluyen_linh_thao_ti_le'
        """)
        row = cursor.fetchone()
        ti_le_dict = json.loads(row['value']) if row else {
            'Pham': 50, 'Linh': 30, 'Bao': 15, 'Tien': 4, 'Than': 1
        }
        
        if pham_cap_list:
            ti_le_dict = {k: v for k, v in ti_le_dict.items() if k in pham_cap_list}
        if not ti_le_dict:
            return None, 0
        
        pham_list = list(ti_le_dict.keys())
        weights = list(ti_le_dict.values())
        pham_cap = random.choices(pham_list, weights=weights, k=1)[0]
        
        cursor.execute("SELECT id FROM tmpl_linh_thao WHERE pham_cap = %s", (pham_cap,))
        ids = [r['id'] for r in cursor.fetchall()]
        if not ids:
            return None, 0
        
        chosen_id = random.choice(ids)
        cursor.execute("SELECT * FROM tmpl_linh_thao WHERE id = %s", (chosen_id,))
        lt = cursor.fetchone()
        
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'lichluyen_linh_thao_so_luong'
        """)
        row = cursor.fetchone()
        config = json.loads(row['value']) if row else {"min": 1, "max": 2}
        so_luong = random.randint(config['min'], config['max'])
        
        return lt, so_luong
    finally:
        cursor.close()
        conn.close()


def get_random_dan_phuong():
    """
    Random 1 đan dược.
    Tối ưu: Lấy tất cả ID của phẩm cấp về Python rồi random.
    """
    import random
    import json
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'lichluyen_dan_phuong_ti_le'
        """)
        row = cursor.fetchone()
        ti_le_dict = json.loads(row['value']) if row else {
            'Pham': 50, 'Linh': 30, 'Bao': 15, 'Tien': 4, 'Than': 1
        }
        
        if not ti_le_dict:
            return None
        
        pham_list = list(ti_le_dict.keys())
        weights = list(ti_le_dict.values())
        pham_cap = random.choices(pham_list, weights=weights, k=1)[0]
        
        cursor.execute("""
            SELECT id FROM tmpl_dan_duoc
            WHERE loai IN ('HoiPhuc', 'Buff', 'TangTuVi')
              AND pham_cap = %s
        """, (pham_cap,))
        ids = [r['id'] for r in cursor.fetchall()]
        if not ids:
            return None
        
        chosen_id = random.choice(ids)
        cursor.execute("SELECT * FROM tmpl_dan_duoc WHERE id = %s", (chosen_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def ghi_log_lichluyen(player_id: int, dia_diem_id: int,
                       ket_qua: list, tong_lt: int, tong_tv: int):
    """Ghi log lịch luyện vào DB."""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO log_lichluyen 
            (player_id, dia_diem_id, ket_qua, tong_linh_thach, tong_tu_vi)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            player_id, 
            dia_diem_id,
            json.dumps(ket_qua, ensure_ascii=False),
            tong_lt, 
            tong_tv
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_linh_can_ky_ngo_range() -> tuple:
    """Lấy range độ tinh khiết tăng khi đốn ngộ."""
    import json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT key_name, value FROM he_thong_config
            WHERE key_name IN ('linh_can_ky_ngo_tinh_khiet_min', 
                               'linh_can_ky_ngo_tinh_khiet_max')
        """)
        rows = cursor.fetchall()
        configs = {r['key_name']: json.loads(r['value']) for r in rows}
        
        min_v = configs.get('linh_can_ky_ngo_tinh_khiet_min', 5)
        max_v = configs.get('linh_can_ky_ngo_tinh_khiet_max', 20)
        
        return int(min_v), int(max_v)
    finally:
        cursor.close()
        conn.close()


def update_player_sau_lichluyen(player_id: int,
                                  linh_thach: int = 0,
                                  tu_vi: int = 0,
                                  exp: int = 0,
                                  hp_mat: int = 0,
                                  linh_thach_mat: int = 0,
                                  linh_thao_list: list = None,
                                  tinh_khiet_list: list = None,
                                  khoang_thach_list: list = None):  # ⭐ MỚI
    """..."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        
        # 1. Cộng/trừ linh thạch
        if linh_thach != 0 or linh_thach_mat != 0:
            cursor.execute("""
                UPDATE player
                SET linh_thach = GREATEST(0, linh_thach + %s - %s)
                WHERE player_id = %s
            """, (linh_thach, linh_thach_mat, player_id))
        
        # 2. Cộng tu vi + exp
        if tu_vi != 0 or exp != 0:
            cursor.execute("""
                UPDATE player
                SET tu_vi = tu_vi + %s, exp = exp + %s
                WHERE player_id = %s
            """, (tu_vi, exp, player_id))
        
        # 3. Trừ HP
        if hp_mat > 0:
            cursor.execute("""
                UPDATE player_stat
                SET hp_hien_tai = GREATEST(0, hp_hien_tai - %s),
                    last_hp_update = NOW()
                WHERE player_id = %s
            """, (hp_mat, player_id))
        
        # 4. Cộng linh thảo
        if linh_thao_list:
            for lt_id, so_luong in linh_thao_list:
                cursor.execute("""
                    INSERT INTO player_linh_thao 
                    (player_id, linh_thao_id, so_luong)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        so_luong = so_luong + VALUES(so_luong)
                """, (player_id, lt_id, so_luong))
        
        # 5. Tăng độ tinh khiết
        if tinh_khiet_list:
            for lc_id, amount in tinh_khiet_list:
                cursor.execute("""
                    UPDATE player_linh_can
                    SET do_tinh_khiet = LEAST(do_tinh_khiet + %s, 100),
                        san_sang_dot_pha = IF(do_tinh_khiet + %s >= 100, 1, 0)
                    WHERE player_id = %s AND linh_can_id = %s
                """, (amount, amount, player_id, lc_id))
        
        # ⭐ 6. Cộng khoáng thạch (MỚI)
        if khoang_thach_list:
            for kt_id, so_luong in khoang_thach_list:
                cursor.execute("""
                    INSERT INTO player_khoang_thach 
                    (player_id, khoang_thach_id, so_luong)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        so_luong = so_luong + VALUES(so_luong)
                """, (player_id, kt_id, so_luong))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def lay_bonus_nghe(player_id: int, stat_code: str) -> float:
    """Lấy bonus của nghề nghiệp theo stat_code."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT nb.gia_tri_bonus
            FROM player_nghe_nghiep pnn
            JOIN tmpl_nghe_nghiep_bonus nb 
                ON nb.nghe_nghiep_id = pnn.nghe_nghiep_id
            WHERE pnn.player_id = %s AND nb.stat_code = %s
            LIMIT 1
        """, (player_id, stat_code))
        row = cursor.fetchone()
        return float(row['gia_tri_bonus']) if row else 0.0
    finally:
        cursor.close()
        conn.close()


def lay_nhieu_bonus_nghe(player_id: int, stat_codes: list) -> dict:
    """
    Lấy nhiều bonus cùng lúc, trả về dict {stat_code: value}.
    Tối ưu: 1 query thay vì N query.
    """
    if not stat_codes:
        return {}
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        format_strings = ','.join(['%s'] * len(stat_codes))
        cursor.execute(f"""
            SELECT nb.stat_code, nb.gia_tri_bonus
            FROM player_nghe_nghiep pnn
            JOIN tmpl_nghe_nghiep_bonus nb 
                ON nb.nghe_nghiep_id = pnn.nghe_nghiep_id
            WHERE pnn.player_id = %s AND nb.stat_code IN ({format_strings})
        """, [player_id] + stat_codes)
        return {row['stat_code']: float(row['gia_tri_bonus']) for row in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


# ============================================================
# CÁC HÀM *_with_cursor — MỚI THÊM
# Dùng cho các lệnh cần nhiều query (như /lichluyen)
# KHÔNG mở connection, nhận cursor từ bên ngoài.
# KHÔNG commit — để caller commit.
# ============================================================

def get_player_full_info_with_cursor(cursor, discord_id: int):
    """Lấy thông tin player, dùng cursor có sẵn."""
    cursor.execute("""
        SELECT p.*, cg.ten AS canh_gioi_ten, cg.so_tang,
               cg.exp_tang_1, cg.he_so_tang
        FROM player p
        JOIN canh_gioi cg ON cg.id = p.canh_gioi_id
        WHERE p.discord_id = %s
    """, (discord_id,))
    player_row = cursor.fetchone()
    if not player_row:
        return None
    
    player_id = player_row['player_id']
    
    cursor.execute("""
        SELECT lc.ten, lc.he, lc.pham_cap,
               plc.do_tinh_khiet, plc.is_active
        FROM player_linh_can plc
        JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
        WHERE plc.player_id = %s
    """, (player_id,))
    player_row['linh_can_list'] = cursor.fetchall()
    
    cursor.execute("""
        SELECT nn.ten, nn.cap_toi_da, nn.exp_moi_cap,
               pnn.cap_do, pnn.kinh_nghiem, pnn.danh_vong
        FROM player_nghe_nghiep pnn
        JOIN tmpl_nghe_nghiep nn ON nn.id = pnn.nghe_nghiep_id
        WHERE pnn.player_id = %s
        LIMIT 1
    """, (player_id,))
    player_row['nghe_nghiep'] = cursor.fetchone()
    
    return Player(player_row)


def get_cooldown_with_cursor(cursor, player_id: int, action_code: str):
    """Lấy cooldown, dùng cursor có sẵn."""
    cursor.execute("""
        SELECT san_sang_luc FROM player_cooldown
        WHERE player_id = %s AND action_code = %s
    """, (player_id, action_code))
    row = cursor.fetchone()
    return row['san_sang_luc'] if row else None


def set_cooldown_with_cursor(cursor, player_id: int, action_code: str, seconds: int):
    """Set cooldown, dùng cursor có sẵn. KHÔNG commit."""
    from datetime import datetime, timedelta
    san_sang = datetime.now() + timedelta(seconds=seconds)
    cursor.execute("""
        INSERT INTO player_cooldown (player_id, action_code, san_sang_luc)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE san_sang_luc = VALUES(san_sang_luc)
    """, (player_id, action_code, san_sang))


def get_random_dia_diem_with_cursor(cursor):
    """Random địa điểm, dùng cursor có sẵn. Convert Decimal → float."""
    import random
    cursor.execute("SELECT * FROM tmpl_dia_diem WHERE is_active = 1")
    ds = cursor.fetchall()
    if not ds:
        return None
    
    dia_diem = random.choice(ds)
    
    # ⭐ Convert Decimal → float cho 5 cột hệ số
    for key in ['he_so_linh_thach', 'he_so_exp', 'he_so_linh_thao', 
                'he_so_khoang_thach', 'he_so_dan_phuong']:
        if key in dia_diem and dia_diem[key] is not None:
            dia_diem[key] = float(dia_diem[key])
    
    return dia_diem


def get_xac_suat_su_kien_with_cursor(cursor, dia_diem_id: int):
    """Lấy xác suất sự kiện, dùng cursor có sẵn."""
    cursor.execute("""
        SELECT su_kien_code, trong_so
        FROM tmpl_dia_diem_su_kien
        WHERE dia_diem_id = %s
    """, (dia_diem_id,))
    return cursor.fetchall()


def lay_nhieu_config_with_cursor(cursor, key_names: list) -> dict:
    """Lấy nhiều config 1 lần, trả về dict."""
    if not key_names:
        return {}
    import json
    format_strings = ','.join(['%s'] * len(key_names))
    cursor.execute(f"""
        SELECT key_name, value FROM he_thong_config
        WHERE key_name IN ({format_strings})
    """, key_names)
    return {r['key_name']: json.loads(r['value']) for r in cursor.fetchall()}


def lay_nhieu_bonus_nghe_with_cursor(cursor, player_id: int, stat_codes: list) -> dict:
    """Lấy nhiều bonus nghề 1 lần, dùng cursor có sẵn."""
    if not stat_codes:
        return {}
    format_strings = ','.join(['%s'] * len(stat_codes))
    cursor.execute(f"""
        SELECT nb.stat_code, nb.gia_tri_bonus
        FROM player_nghe_nghiep pnn
        JOIN tmpl_nghe_nghiep_bonus nb 
            ON nb.nghe_nghiep_id = pnn.nghe_nghiep_id
        WHERE pnn.player_id = %s AND nb.stat_code IN ({format_strings})
    """, [player_id] + stat_codes)
    return {row['stat_code']: float(row['gia_tri_bonus']) for row in cursor.fetchall()}


def get_player_linh_can_active_with_cursor(cursor, player_id: int):
    """Lấy linh căn active, dùng cursor có sẵn."""
    cursor.execute("""
        SELECT 
            plc.linh_can_id,
            plc.do_tinh_khiet,
            lc.ten,
            lc.he,
            lc.pham_cap
        FROM player_linh_can plc
        JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
        WHERE plc.player_id = %s AND plc.is_active = 1
    """, (player_id,))
    return cursor.fetchall()


def get_random_linh_thao_with_cursor(cursor, pham_cap_list: list = None):
    """Random linh thảo, dùng cursor có sẵn. Bỏ ORDER BY RAND()."""
    import random
    import json
    
    cursor.execute("""
        SELECT value FROM he_thong_config
        WHERE key_name = 'lichluyen_linh_thao_ti_le'
    """)
    row = cursor.fetchone()
    ti_le_dict = json.loads(row['value']) if row else {
        'Pham': 50, 'Linh': 30, 'Bao': 15, 'Tien': 4, 'Than': 1
    }
    
    if pham_cap_list:
        ti_le_dict = {k: v for k, v in ti_le_dict.items() if k in pham_cap_list}
    if not ti_le_dict:
        return None, 0
    
    pham_list = list(ti_le_dict.keys())
    weights = list(ti_le_dict.values())
    pham_cap = random.choices(pham_list, weights=weights, k=1)[0]
    
    cursor.execute("SELECT id FROM tmpl_linh_thao WHERE pham_cap = %s", (pham_cap,))
    ids = [r['id'] for r in cursor.fetchall()]
    if not ids:
        return None, 0
    
    chosen_id = random.choice(ids)
    cursor.execute("SELECT * FROM tmpl_linh_thao WHERE id = %s", (chosen_id,))
    lt = cursor.fetchone()
    
    cursor.execute("""
        SELECT value FROM he_thong_config
        WHERE key_name = 'lichluyen_linh_thao_so_luong'
    """)
    row = cursor.fetchone()
    config = json.loads(row['value']) if row else {"min": 1, "max": 2}
    so_luong = random.randint(config['min'], config['max'])
    
    return lt, so_luong


def get_random_dan_phuong_with_cursor(cursor):
    """Random đan dược, dùng cursor có sẵn. Bỏ ORDER BY RAND()."""
    import random
    import json
    
    cursor.execute("""
        SELECT value FROM he_thong_config
        WHERE key_name = 'lichluyen_dan_phuong_ti_le'
    """)
    row = cursor.fetchone()
    ti_le_dict = json.loads(row['value']) if row else {
        'Pham': 50, 'Linh': 30, 'Bao': 15, 'Tien': 4, 'Than': 1
    }
    if not ti_le_dict:
        return None
    
    pham_list = list(ti_le_dict.keys())
    weights = list(ti_le_dict.values())
    pham_cap = random.choices(pham_list, weights=weights, k=1)[0]
    
    cursor.execute("""
        SELECT id FROM tmpl_dan_duoc
        WHERE loai IN ('HoiPhuc', 'Buff', 'TangTuVi')
          AND pham_cap = %s
    """, (pham_cap,))
    ids = [r['id'] for r in cursor.fetchall()]
    if not ids:
        return None
    
    chosen_id = random.choice(ids)
    cursor.execute("SELECT * FROM tmpl_dan_duoc WHERE id = %s", (chosen_id,))
    return cursor.fetchone()


def get_linh_can_ky_ngo_range_with_cursor(cursor) -> tuple:
    """Lấy range đốn ngộ, dùng cursor có sẵn."""
    import json
    cursor.execute("""
        SELECT key_name, value FROM he_thong_config
        WHERE key_name IN ('linh_can_ky_ngo_tinh_khiet_min', 
                           'linh_can_ky_ngo_tinh_khiet_max')
    """)
    rows = cursor.fetchall()
    configs = {r['key_name']: json.loads(r['value']) for r in rows}
    min_v = configs.get('linh_can_ky_ngo_tinh_khiet_min', 5)
    max_v = configs.get('linh_can_ky_ngo_tinh_khiet_max', 20)
    return int(min_v), int(max_v)


def update_player_sau_lichluyen_with_cursor(cursor, player_id: int,
                                              linh_thach: int = 0,
                                              tu_vi: int = 0,
                                              exp: int = 0,
                                              hp_mat: int = 0,
                                              linh_thach_mat: int = 0,
                                              linh_thao_list: list = None,
                                              tinh_khiet_list: list = None,
                                              khoang_thach_list: list = None):
    """Update player sau lịch luyện, dùng cursor có sẵn. KHÔNG commit."""
    if linh_thach != 0 or linh_thach_mat != 0:
        cursor.execute("""
            UPDATE player
            SET linh_thach = GREATEST(0, linh_thach + %s - %s)
            WHERE player_id = %s
        """, (linh_thach, linh_thach_mat, player_id))
    
    if tu_vi != 0 or exp != 0:
        cursor.execute("""
            UPDATE player
            SET tu_vi = tu_vi + %s, exp = exp + %s
            WHERE player_id = %s
        """, (tu_vi, exp, player_id))
    
    if hp_mat > 0:
        cursor.execute("""
            UPDATE player_stat
            SET hp_hien_tai = GREATEST(0, hp_hien_tai - %s),
                last_hp_update = NOW()
            WHERE player_id = %s
        """, (hp_mat, player_id))
    
    if linh_thao_list:
        for lt_id, so_luong in linh_thao_list:
            cursor.execute("""
                INSERT INTO player_linh_thao 
                (player_id, linh_thao_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    so_luong = so_luong + VALUES(so_luong)
            """, (player_id, lt_id, so_luong))
    
    if tinh_khiet_list:
        for lc_id, amount in tinh_khiet_list:
            cursor.execute("""
                UPDATE player_linh_can
                SET do_tinh_khiet = LEAST(do_tinh_khiet + %s, 100),
                    san_sang_dot_pha = IF(do_tinh_khiet + %s >= 100, 1, 0)
                WHERE player_id = %s AND linh_can_id = %s
            """, (amount, amount, player_id, lc_id))
    if khoang_thach_list:
            for kt_id, so_luong in khoang_thach_list:
                cursor.execute("""
                    INSERT INTO player_khoang_thach 
                    (player_id, khoang_thach_id, so_luong)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        so_luong = so_luong + VALUES(so_luong)
                """, (player_id, kt_id, so_luong))


def ghi_log_lichluyen_with_cursor(cursor, player_id: int, dia_diem_id: int,
                                    ket_qua: list, tong_lt: int, tong_tv: int):
    """Ghi log lịch luyện, dùng cursor có sẵn. KHÔNG commit."""
    import json
    cursor.execute("""
        INSERT INTO log_lichluyen 
        (player_id, dia_diem_id, ket_qua, tong_linh_thach, tong_tu_vi)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        player_id, 
        dia_diem_id,
        json.dumps(ket_qua, ensure_ascii=False),
        tong_lt, 
        tong_tv
    ))
    
        
def tinh_stat_runtime(player_id: int) -> dict:
    """
    Tính stat cuối cùng = stat_goc × he_so_tang + bonus_linh_can + bonus_nghe + bonus_buff + bonus_cong_phap.
    Sau đó áp dụng percent stat (hp_max_pct, mp_max_pct, atk_pct, ...).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Lấy thông tin player (cần tang_tich_luy + he_so_suc_manh)
        cursor.execute("""
            SELECT p.tang_tich_luy, p.canh_gioi_id, cg.he_so_suc_manh
            FROM player p
            JOIN canh_gioi cg ON cg.id = p.canh_gioi_id
            WHERE p.player_id = %s
        """, (player_id,))
        player = cursor.fetchone()
        if not player:
            return {}
        
        tang_tich_luy = player['tang_tich_luy']
        he_so_suc_manh = float(player['he_so_suc_manh'])
        
        # 2. Lấy config pct
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'stat_tang_moi_tang_pct'
        """)
        row = cursor.fetchone()
        import json
        pct = json.loads(row['value']) if row else 5.0
        
        # Công thức: he_so_suc_manh × (1 + (tang_tich_luy - 1) × pct/100)
        he_so_tang = he_so_suc_manh * (1.0 + (tang_tich_luy - 1) * (pct / 100.0))
        
        # 3. Lấy stat khởi đầu
        cursor.execute("SELECT stat_code, gia_tri FROM tmpl_stat_khoi_dau")
        stat_khoi_dau = {r['stat_code']: float(r['gia_tri']) for r in cursor.fetchall()}
        
        # 4. Lấy stat_type metadata
        cursor.execute("SELECT code, don_vi FROM tmpl_stat_type")
        stat_meta = {r['code']: r['don_vi'] for r in cursor.fetchall()}
        # ⭐ Danh sách stat percent
        stat_percent = {code for code, don_vi in stat_meta.items() if don_vi == 'percent'}
        # 5. Lấy stat runtime hiện tại từ player_stat
        cursor.execute("SELECT * FROM player_stat WHERE player_id = %s", (player_id,))
        stat_row = cursor.fetchone()
        if not stat_row:
            return {}
        
        # 6. Khởi tạo kết quả
        ket_qua = {}
        
        # 6a. Stat cơ bản (tăng theo tầng)
        for code, gia_tri_goc in stat_khoi_dau.items():
            ket_qua[code] = gia_tri_goc * he_so_tang
        
        # 6b. Stat khác (không tăng theo tầng)
        for code in stat_meta.keys():
            if code in stat_khoi_dau:
                continue
            if code in stat_row and stat_row[code] is not None:
                ket_qua[code] = float(stat_row[code])
        
        # 7. Cộng bonus từ linh căn active
        cursor.execute("""
            SELECT st.code, lcs.gia_tri_bonus
            FROM player_linh_can plc
            JOIN tmpl_linh_can_stat lcs ON lcs.linh_can_id = plc.linh_can_id
            JOIN tmpl_stat_type st ON st.id = lcs.stat_id
            WHERE plc.player_id = %s AND plc.is_active = 1
        """, (player_id,))
        for row in cursor.fetchall():
            code = row['code']
            ket_qua[code] = ket_qua.get(code, 0.0) + float(row['gia_tri_bonus'])
        
        # 8. Cộng bonus từ nghề
        cursor.execute("""
            SELECT nb.stat_code, nb.gia_tri_bonus
            FROM player_nghe_nghiep pnn
            JOIN tmpl_nghe_nghiep_bonus nb 
                ON nb.nghe_nghiep_id = pnn.nghe_nghiep_id
            WHERE pnn.player_id = %s
        """, (player_id,))
        for row in cursor.fetchall():
            code = row['stat_code']
            if code in stat_meta:
                ket_qua[code] = ket_qua.get(code, 0.0) + float(row['gia_tri_bonus'])
        
        # 9. Cộng bonus từ buff
        cursor.execute("""
            SELECT effect FROM player_buff
            WHERE player_id = %s AND het_han_luc > NOW()
        """, (player_id,))
        for row in cursor.fetchall():
            effect = row['effect']
            if isinstance(effect, str):
                effect = json.loads(effect)
            if not isinstance(effect, dict):
                continue
            for code, gia_tri in effect.items():
                if code in stat_meta:
                    try:
                        ket_qua[code] = ket_qua.get(code, 0.0) + float(gia_tri)
                    except (ValueError, TypeError):
                        pass
        # ⭐ 10. Cộng bonus từ công pháp đang tu luyện (CÓ THUẦN THỤC)
        cursor.execute("""
            SELECT 
                cp.ten,
                cp.effect_moi_tang,
                pcp.tang_hien_tai,
                pcp.do_thuan_thuc
            FROM player_cong_phap pcp
            JOIN tmpl_cong_phap cp ON cp.id = pcp.cong_phap_id
            WHERE pcp.player_id = %s AND pcp.dang_tu_luyen = 1
        """, (player_id,))
        for row in cursor.fetchall():
            effect = row['effect_moi_tang']
            if isinstance(effect, str):
                effect = json.loads(effect)
            if not isinstance(effect, dict):
                continue
            
            tang = row['tang_hien_tai']
            do_thuan_thuc = float(row.get('do_thuan_thuc', 0) or 0)
            
            # ⭐ Hệ số thuần thục
            he_so_flat = 1 + (do_thuan_thuc * 0.005)      # 1.0 → 1.5
            bonus_pct = do_thuan_thuc * 0.05               # 0% → +5%
            
            for stat_code, gia_tri_moi_tang in effect.items():
                try:
                    gia_tri_goc = float(gia_tri_moi_tang) * tang
                    
                    # ⭐ Phân biệt flat vs percent
                    if stat_code in stat_percent:
                        # Stat percent → cộng bonus
                        gia_tri_cuoi = gia_tri_goc + bonus_pct
                    else:
                        # Stat flat → nhân hệ số
                        gia_tri_cuoi = gia_tri_goc * he_so_flat
                    
                    ket_qua[stat_code] = ket_qua.get(stat_code, 0.0) + gia_tri_cuoi
                except (ValueError, TypeError):
                    pass
        # 10. Áp dụng percent stat
        for code in list(ket_qua.keys()):
            if code.endswith('_pct'):
                base_code = code[:-4]
                if base_code in ket_qua:
                    pct_value = ket_qua[code] / 100.0
                    ket_qua[base_code] = ket_qua[base_code] * (1 + pct_value)
        
        return ket_qua
    finally:
        cursor.close()
        conn.close()
        
# ============================================================
# ĐỘT PHÁ LINH CĂN
# ============================================================

PHAM_CAP_TIEP = {
    'Ha':     'Trung',
    'Trung':  'Thuong',
    'Thuong': 'Cuc',
    'Cuc':    'Tien',
    'Tien':   None,
}

DAO_CU_CODE = {
    'Ha':     'dot_pha_ha',
    'Trung':  'dot_pha_trung',
    'Thuong': 'dot_pha_thuong',
    'Cuc':    'dot_pha_cuc',
    'Tien':   None,
}


def get_linh_can_du_dieu_kien_dot_pha(player_id: int) -> list:
    """
    Lấy danh sách linh căn đủ điều kiện đột phá (bao gồm cả thiếu đạo cụ).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Lấy tất cả linh căn có 100% tinh khiết
        cursor.execute("""
            SELECT 
                plc.linh_can_id,
                plc.do_tinh_khiet,
                plc.so_lan_dung_dao_cu_dot_pha,
                lc.ten,
                lc.he,
                lc.pham_cap
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s
              AND plc.do_tinh_khiet >= 100
              AND lc.pham_cap != 'Tien'
            ORDER BY 
                FIELD(lc.pham_cap, 'Ha', 'Trung', 'Thuong', 'Cuc', 'Tien'),
                lc.he
        """, (player_id,))
        ds_linh_can = cursor.fetchall()
        
        if not ds_linh_can:
            return []
        
        # 2. Lấy TẤT CẢ đạo cụ đột phá (cả 2 loại)
        cursor.execute("""
            SELECT 
                dc.id AS dao_cu_id,
                dc.code AS dao_cu_code,
                dc.ten AS dao_cu_ten,
                dc.loai AS dao_cu_loai,
                dc.pham_cap AS dao_cu_pham_cap,
                dc.effect AS dao_cu_effect,
                COALESCE(pdc.so_luong, 0) AS so_luong
            FROM tmpl_dao_cu dc
            LEFT JOIN player_dao_cu pdc 
                ON pdc.dao_cu_id = dc.id AND pdc.player_id = %s
            WHERE dc.loai IN ('DotPhaLinhCan', 'TangTiLeDotPha')
        """, (player_id,))
        ds_dao_cu = cursor.fetchall()
        
        # 3. Map theo code
        dao_cu_100_map = {}     # {code: {...}} — đạo cụ 100%
        dao_cu_ti_le_list = []  # [danh sách] — đạo cụ tăng tỉ lệ
        
        import json
        for d in ds_dao_cu:
            if d['dao_cu_loai'] == 'DotPhaLinhCan':
                dao_cu_100_map[d['dao_cu_code']] = d
            elif d['dao_cu_loai'] == 'TangTiLeDotPha':
                effect = d['dao_cu_effect']
                if isinstance(effect, str):
                    try:
                        effect = json.loads(effect)
                    except:
                        effect = {}
                d['bonus_ti_le'] = float(effect.get('ti_le_bonus', 0))
                dao_cu_ti_le_list.append(d)
        
        # 4. Xây dựng kết quả
        ket_qua = []
        for lc in ds_linh_can:
            pham_cap = lc['pham_cap']
            pham_cap_moi = PHAM_CAP_TIEP.get(pham_cap)
            if not pham_cap_moi:
                continue
            
            # Đạo cụ 100% cần cho phẩm cấp này
            code_can = DAO_CU_CODE.get(pham_cap)
            dao_cu_100 = dao_cu_100_map.get(code_can) if code_can else None
            
            # Danh sách đạo cụ tăng tỉ lệ (chỉ hiển thị loại có sẵn)
            ds_ti_le = [
                {
                    'id': d['dao_cu_id'],
                    'code': d['dao_cu_code'],
                    'ten': d['dao_cu_ten'],
                    'bonus_ti_le': d['bonus_ti_le'],
                    'so_luong': d['so_luong'],
                }
                for d in dao_cu_ti_le_list if d['so_luong'] > 0
            ]
            
            ket_qua.append({
                'linh_can_id': lc['linh_can_id'],
                'ten': lc['ten'],
                'he': lc['he'],
                'pham_cap': pham_cap,
                'pham_cap_moi': pham_cap_moi,
                'do_tinh_khiet': float(lc['do_tinh_khiet']),
                'so_lan_da_dung': lc['so_lan_dung_dao_cu_dot_pha'],
                'dao_cu_100': {
                    'id': dao_cu_100['dao_cu_id'] if dao_cu_100 else None,
                    'code': dao_cu_100['dao_cu_code'] if dao_cu_100 else None,
                    'ten': dao_cu_100['dao_cu_ten'] if dao_cu_100 else None,
                    'so_luong': dao_cu_100['so_luong'] if dao_cu_100 else 0,
                },
                'ds_dao_cu_ti_le': ds_ti_le,
            })
        
        return ket_qua
    finally:
        cursor.close()
        conn.close()


def dot_pha_linh_can(player_id: int, linh_can_id_cu: int, ds_dao_cu: list = None) -> dict:
    """
    Đột phá linh căn.
    
    Args:
        ds_dao_cu: List các dict:
            - [{'id': int, 'loai': str, 'code': str, 'bonus_ti_le': float}, ...]
            - None hoặc [] → không dùng đạo cụ.
            - Có 1 đạo cụ 'DotPhaLinhCan' → 100% chắc chắn.
            - Có nhiều đạo cụ 'TangTiLeDotPha' → gộp bonus tỉ lệ.
    """
    import random
    import json
    
    if ds_dao_cu is None:
        ds_dao_cu = []
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 1. Lock linh căn
        cursor.execute("""
            SELECT 
                plc.linh_can_id,
                plc.do_tinh_khiet,
                plc.so_lan_dung_dao_cu_dot_pha,
                lc.ten,
                lc.he,
                lc.pham_cap
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s AND plc.linh_can_id = %s
            FOR UPDATE
        """, (player_id, linh_can_id_cu))
        lc_cu = cursor.fetchone()
        
        if not lc_cu:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy linh căn!'}
        
        lc_cu['do_tinh_khiet'] = float(lc_cu['do_tinh_khiet'])
        
        # 2. Verify
        if lc_cu['do_tinh_khiet'] < 100:
            conn.rollback()
            return {'thanh_cong': False, 'loi': f'Tinh khiết chỉ {lc_cu["do_tinh_khiet"]:.1f}%, cần 100%!'}
        
        if lc_cu['pham_cap'] == 'Tien':
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Linh căn Tiên đã max!'}
        
        # 3. Config
        cursor.execute("""
            SELECT key_name, value FROM he_thong_config
            WHERE key_name IN (
                'linh_can_dot_pha_ti_le_co_ban',
                'linh_can_dot_pha_mat_tinh_khiet_min',
                'linh_can_dot_pha_mat_tinh_khiet_max',
                'linh_can_dot_pha_max_lan_dung_dao_cu',
                'linh_can_dot_pha_ti_le_max'
            )
        """)
        configs = {r['key_name']: json.loads(r['value']) for r in cursor.fetchall()}
        
        ti_le_co_ban = float(configs.get('linh_can_dot_pha_ti_le_co_ban', 25.0))
        mat_min = int(configs.get('linh_can_dot_pha_mat_tinh_khiet_min', 15))
        mat_max = int(configs.get('linh_can_dot_pha_mat_tinh_khiet_max', 35))
        max_lan = int(configs.get('linh_can_dot_pha_max_lan_dung_dao_cu', 2))
        
        ti_le_max = float(configs.get('linh_can_dot_pha_ti_le_max', 95.0))
        if ti_le_max < 1:
            ti_le_max = ti_le_max * 100
        
        # 4. Phân tích đạo cụ
        loai_dot_pha = 'ti_le'
        tong_bonus = 0.0
        ds_dao_cu_dung = []       # List các đạo cụ dùng
        so_dao_cu_tang_ti_le = 0  # Đếm số đạo cụ tăng tỉ lệ
        
        for dc_info in ds_dao_cu:
            dao_cu_id = dc_info.get('id')
            if not dao_cu_id:
                continue
            
            cursor.execute("""
                SELECT dc.id, dc.code, dc.ten, dc.loai, dc.effect
                FROM tmpl_dao_cu dc
                WHERE dc.id = %s
            """, (dao_cu_id,))
            dao_cu = cursor.fetchone()
            
            if not dao_cu:
                conn.rollback()
                return {'thanh_cong': False, 'loi': f'Đạo cụ ID {dao_cu_id} không tồn tại!'}
            
            # Check player có đạo cụ
            cursor.execute("""
                SELECT so_luong FROM player_dao_cu
                WHERE player_id = %s AND dao_cu_id = %s
                FOR UPDATE
            """, (player_id, dao_cu_id))
            row = cursor.fetchone()
            
            if not row or row['so_luong'] < 1:
                conn.rollback()
                return {'thanh_cong': False, 'loi': f'Không có đạo cụ `{dao_cu["ten"]}`!'}
            
            if dao_cu['loai'] == 'DotPhaLinhCan':
                # 100% chắc chắn
                code_can = DAO_CU_CODE.get(lc_cu['pham_cap'])
                if dao_cu['code'] != code_can:
                    conn.rollback()
                    return {
                        'thanh_cong': False,
                        'loi': f'Đạo cụ `{dao_cu["ten"]}` không khớp linh căn {lc_cu["pham_cap"]}!'
                    }
                loai_dot_pha = 'chac_chan'
                ds_dao_cu_dung.append(dao_cu)
            
            elif dao_cu['loai'] == 'TangTiLeDotPha':
                effect = dao_cu['effect']
                if isinstance(effect, str):
                    effect = json.loads(effect)
                bonus = float(effect.get('ti_le_bonus', 0))
                tong_bonus += bonus
                so_dao_cu_tang_ti_le += 1
                ds_dao_cu_dung.append(dao_cu)
            
            else:
                conn.rollback()
                return {'thanh_cong': False, 'loi': f'Đạo cụ `{dao_cu["ten"]}` không dùng được!'}
        
        # 5. Verify số lượt dùng đạo cụ tăng tỉ lệ
        if so_dao_cu_tang_ti_le > 0:
            so_lan_cu = lc_cu['so_lan_dung_dao_cu_dot_pha']
            if so_lan_cu + so_dao_cu_tang_ti_le > max_lan:
                conn.rollback()
                return {
                    'thanh_cong': False,
                    'loi': f'Vượt quá {max_lan} lượt dùng! Còn `{max_lan - so_lan_cu}` lượt.'
                }
        
        # 6. Tính tỉ lệ cuối
        if loai_dot_pha == 'chac_chan':
            ti_le_cuoi = 100.0
            thanh_cong = True
            roll = 0.0
        else:
            ti_le_cuoi = min(ti_le_max, ti_le_co_ban + tong_bonus)
            roll = random.uniform(0, 100)
            thanh_cong = roll <= ti_le_cuoi
        
        # 7. Xử lý kết quả
        linh_can_moi = None
        mat_tinh_khiet = 0.0
        so_lan_moi = lc_cu['so_lan_dung_dao_cu_dot_pha']
        
        if thanh_cong:
            pham_cap_moi = PHAM_CAP_TIEP[lc_cu['pham_cap']]
            cursor.execute("""
                SELECT id, ten, pham_cap FROM tmpl_linh_can
                WHERE he = %s AND pham_cap = %s LIMIT 1
            """, (lc_cu['he'], pham_cap_moi))
            lc_moi = cursor.fetchone()
            
            if not lc_moi:
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Không tìm thấy linh căn mới!'}
            
            cursor.execute("""
                DELETE FROM player_linh_can
                WHERE player_id = %s AND linh_can_id = %s
            """, (player_id, linh_can_id_cu))
            
            cursor.execute("""
                INSERT INTO player_linh_can
                (player_id, linh_can_id, do_tinh_khiet, so_lan_dung_dao_cu_dot_pha, is_active)
                VALUES (%s, %s, 0, 0, 1)
            """, (player_id, lc_moi['id']))
            
            linh_can_moi = {'ten': lc_moi['ten'], 'pham_cap': lc_moi['pham_cap']}
        else:
            mat_tinh_khiet = random.uniform(mat_min, mat_max)
            tinh_khiet_moi = max(0, lc_cu['do_tinh_khiet'] - mat_tinh_khiet)
            
            # Tăng số lượt dùng
            so_lan_moi = lc_cu['so_lan_dung_dao_cu_dot_pha'] + so_dao_cu_tang_ti_le
            
            cursor.execute("""
                UPDATE player_linh_can
                SET do_tinh_khiet = %s,
                    so_lan_dung_dao_cu_dot_pha = %s,
                    san_sang_dot_pha = IF(%s >= 100, 1, 0)
                WHERE player_id = %s AND linh_can_id = %s
            """, (tinh_khiet_moi, so_lan_moi, tinh_khiet_moi, player_id, linh_can_id_cu))
        
        # 8. Trừ đạo cụ
        for dao_cu in ds_dao_cu_dung:
            cursor.execute("""
                UPDATE player_dao_cu
                SET so_luong = so_luong - 1
                WHERE player_id = %s AND dao_cu_id = %s
            """, (player_id, dao_cu['id']))
            
            cursor.execute("""
                DELETE FROM player_dao_cu
                WHERE player_id = %s AND dao_cu_id = %s AND so_luong <= 0
            """, (player_id, dao_cu['id']))
        
        # 9. Log (lấy đạo cụ đầu tiên làm đại diện)
        dao_cu_id_log = ds_dao_cu_dung[0]['id'] if ds_dao_cu_dung else None
        
        cursor.execute("""
            INSERT INTO log_dot_pha_linh_can (
                player_id, linh_can_id_cu, linh_can_id_moi,
                dao_cu_id, ti_le, ti_le_co_ban,
                bonus_dao_cu, bonus_that_bai, thanh_cong
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s)
        """, (
            player_id, linh_can_id_cu,
            lc_moi['id'] if thanh_cong else None,
            dao_cu_id_log, ti_le_cuoi, ti_le_co_ban,
            tong_bonus, 1 if thanh_cong else 0
        ))
        
        conn.commit()
        
        return {
            'thanh_cong': thanh_cong,
            'loi': None,
            'loai_dot_pha': loai_dot_pha,
            'roll': roll,
            'ti_le': ti_le_cuoi,
            'bonus_ti_le': tong_bonus,
            'linh_can_cu': {'ten': lc_cu['ten'], 'pham_cap': lc_cu['pham_cap']},
            'linh_can_moi': linh_can_moi,
            'mat_tinh_khiet': mat_tinh_khiet,
            'so_lan_da_dung': so_lan_moi,
            'so_dao_cu_dung': len(ds_dao_cu_dung),
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] dot_pha_linh_can: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()
        
def get_random_khoang_thach_with_cursor(cursor, pham_cap_list: list = None):
    """
    Random 1 khoáng thạch + số lượng, dùng cursor có sẵn.
    """
    import random
    import json
    
    # BƯỚC 1: Lấy config tỉ lệ phẩm cấp
    cursor.execute("""
        SELECT value FROM he_thong_config
        WHERE key_name = 'lichluyen_khoang_thach_ti_le'
    """)
    row = cursor.fetchone()
    ti_le_dict = json.loads(row['value']) if row else {
        'Pham': 50, 'Linh': 30, 'Bao': 15, 'Tien': 4, 'Than': 1
    }
    
    if pham_cap_list:
        ti_le_dict = {k: v for k, v in ti_le_dict.items() if k in pham_cap_list}
    if not ti_le_dict:
        return None, 0
    
    # BƯỚC 2: Roll phẩm cấp
    pham_list = list(ti_le_dict.keys())
    weights = list(ti_le_dict.values())
    pham_cap = random.choices(pham_list, weights=weights, k=1)[0]
    
    # BƯỚC 3: Lấy TẤT CẢ id khoáng thạch của phẩm cấp đó
    cursor.execute("SELECT id FROM tmpl_khoang_thach WHERE pham_cap = %s", (pham_cap,))
    ids = [r['id'] for r in cursor.fetchall()]
    if not ids:
        return None, 0
    
    chosen_id = random.choice(ids)
    cursor.execute("SELECT * FROM tmpl_khoang_thach WHERE id = %s", (chosen_id,))
    kt = cursor.fetchone()
    
    # BƯỚC 4: Lấy config số lượng
    cursor.execute("""
        SELECT value FROM he_thong_config
        WHERE key_name = 'lichluyen_khoang_thach_so_luong'
    """)
    row = cursor.fetchone()
    config = json.loads(row['value']) if row else {"min": 1, "max": 2}
    so_luong = random.randint(config['min'], config['max'])
    
    return kt, so_luong

# ============================================================
# TÚI ĐỒ
# ============================================================

def get_player_linh_thao(player_id: int) -> list:
    """
    Lấy danh sách linh thảo của player.
    
    Returns:
        [{'id': 1, 'ten': 'Nhân Sâm', 'pham_cap': 'Pham', 'so_luong': 5}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                lt.id,
                lt.ten,
                lt.pham_cap,
                lt.he,
                lt.mo_ta,
                plt.so_luong
            FROM player_linh_thao plt
            JOIN tmpl_linh_thao lt ON lt.id = plt.linh_thao_id
            WHERE plt.player_id = %s AND plt.so_luong > 0
            ORDER BY 
                FIELD(lt.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                lt.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_player_dan_duoc(player_id: int) -> list:
    """
    Lấy danh sách đan dược của player.
    
    Returns:
        [{'id': 1, 'ten': 'Hồi Khí Đan', 'pham_cap': 'Pham', 'so_luong': 3}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                dd.id,
                dd.ten,
                dd.pham_cap,
                dd.loai,
                dd.mo_ta,
                pdd.so_luong
            FROM player_dan_duoc pdd
            JOIN tmpl_dan_duoc dd ON dd.id = pdd.dan_duoc_id
            WHERE pdd.player_id = %s AND pdd.so_luong > 0
            ORDER BY 
                FIELD(dd.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                dd.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_player_dao_cu(player_id: int) -> list:
    """
    Lấy danh sách đạo cụ của player.
    
    Returns:
        [{'id': 1, 'ten': 'Đan Đột Phá - Hạ phẩm', 'loai': 'DotPhaLinhCan', 'so_luong': 2}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                dc.id,
                dc.code,
                dc.ten,
                dc.loai,
                dc.pham_cap,
                dc.he,
                dc.mo_ta,
                pdc.so_luong
            FROM player_dao_cu pdc
            JOIN tmpl_dao_cu dc ON dc.id = pdc.dao_cu_id
            WHERE pdc.player_id = %s AND pdc.so_luong > 0
            ORDER BY 
                FIELD(dc.loai, 'DotPhaLinhCan', 'TangTinhKhiet','TangTiLeDotPha', 'Khac'),
                FIELD(dc.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                dc.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_player_khoang_thach(player_id: int) -> list:
    """
    Lấy danh sách khoáng thạch của player.
    
    Returns:
        [{'id': 1, 'ten': 'Huyền Thiết', 'pham_cap': 'Pham', 'loai': 'LuyenKhi', 'so_luong': 3}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                kt.id,
                kt.code,
                kt.ten,
                kt.pham_cap,
                kt.loai,
                kt.he,
                kt.gia_ban,
                kt.mo_ta,
                pkt.so_luong
            FROM player_khoang_thach pkt
            JOIN tmpl_khoang_thach kt ON kt.id = pkt.khoang_thach_id
            WHERE pkt.player_id = %s AND pkt.so_luong > 0
            ORDER BY 
                FIELD(kt.loai, 'LuyenKhi', 'VePhu', 'CaHai'),
                FIELD(kt.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                kt.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        
# ============================================================
# SHOP
# ============================================================

def get_ti_gia_tien_ngoc() -> int:
    """Lấy tỉ lệ đổi tiên ngọc → linh thạch."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'ty_gia_tien_ngoc_linh_thach'
        """)
        row = cursor.fetchone()
        import json
        return int(json.loads(row['value'])) if row else 10000
    finally:
        cursor.close()
        conn.close()


def exchange_linh_thach_sang_tien_ngoc(player_id: int, so_tien_ngoc: int) -> dict:
    """
    Đổi linh thạch → tiên ngọc.
    
    Args:
        so_tien_ngoc: Số tiên ngọc muốn nhận
    
    Returns:
        {'thanh_cong': bool, 'loi': str, 'linh_thach_mat': int, 'tien_ngoc_nhan': int}
    """
    if so_tien_ngoc <= 0:
        return {'thanh_cong': False, 'loi': 'Số tiên ngọc phải > 0!'}
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 1. Lấy tỉ lệ
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'ty_gia_tien_ngoc_linh_thach'
        """)
        row = cursor.fetchone()
        import json
        ti_gia = int(json.loads(row['value'])) if row else 10000
        
        # 2. Tính linh thạch cần
        linh_thach_can = so_tien_ngoc * ti_gia
        
        # 3. Lock player
        cursor.execute("""
            SELECT linh_thach FROM player WHERE player_id = %s FOR UPDATE
        """, (player_id,))
        p = cursor.fetchone()
        
        if not p:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy player!'}
        
        if p['linh_thach'] < linh_thach_can:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Không đủ linh thạch! Cần `{linh_thach_can:,}`, có `{p["linh_thach"]:,}`'
            }
        
        # 4. Trừ linh thạch, cộng tiên ngọc
        cursor.execute("""
            UPDATE player
            SET linh_thach = linh_thach - %s,
                tien_ngoc = tien_ngoc + %s
            WHERE player_id = %s
        """, (linh_thach_can, so_tien_ngoc, player_id))
        
        # 5. Ghi log
        cursor.execute("""
            INSERT INTO log_giao_dich 
            (player_id, loai, item_type, item_id, so_luong, gia_linh_thach, gia_tien_ngoc)
            VALUES (%s, 'Mua', 'Exchange', 0, %s, %s, %s)
        """, (player_id, so_tien_ngoc, linh_thach_can, so_tien_ngoc))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'linh_thach_mat': linh_thach_can,
            'tien_ngoc_nhan': so_tien_ngoc,
            'ti_gia': ti_gia,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] exchange: {e}')
        return {'thanh_cong': False, 'loi': f'Lỗi hệ thống: {e}'}
    finally:
        cursor.close()
        conn.close()


def get_shop_items(item_type: str = None) -> list:
    """
    Lấy danh sách item trong shop kèm metadata đầy đủ.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        where = "WHERE si.is_active = 1"
        params = []
        if item_type:
            where += " AND si.item_type = %s"
            params.append(item_type)
        
        cursor.execute(f"""
            SELECT 
                si.id AS shop_id,
                si.item_type,
                si.item_id,
                si.gia_linh_thach,
                si.gia_tien_ngoc,
                si.so_luong_ton,
                si.thu_tu_hien_thi,
                -- Tên
                COALESCE(dd.ten, dc.ten, kt.ten, lt.ten, cp.ten) AS ten,
                -- Phẩm cấp
                COALESCE(dd.pham_cap, dc.pham_cap, kt.pham_cap, lt.pham_cap, cp.pham_cap) AS pham_cap,
                -- Hệ
                COALESCE(dc.he, kt.he, lt.he, cp.he) AS he,
                -- Loại
                COALESCE(dd.loai, dc.loai, kt.loai, cp.loai) AS loai,
                -- Mô tả
                COALESCE(dd.mo_ta, dc.mo_ta, kt.mo_ta, lt.mo_ta, cp.mo_ta) AS mo_ta,
                -- Effect
                dd.effect AS dan_effect,
                dc.effect AS dao_cu_effect,
                dd.ti_le_dot_pha_bonus,
                dd.thoi_gian_hieu_luc,
                -- Công pháp metadata
                cp.giai_cap,
                cp.so_tang,
                cp.effect_moi_tang
            FROM tmpl_shop_item si
            LEFT JOIN tmpl_dan_duoc dd ON si.item_type = 'DanDuoc' AND dd.id = si.item_id
            LEFT JOIN tmpl_dao_cu dc ON si.item_type = 'DaoCu' AND dc.id = si.item_id
            LEFT JOIN tmpl_khoang_thach kt ON si.item_type = 'KhoangThach' AND kt.id = si.item_id
            LEFT JOIN tmpl_linh_thao lt ON si.item_type = 'LinhThao' AND lt.id = si.item_id
            LEFT JOIN tmpl_cong_phap cp ON si.item_type = 'CongPhap' AND cp.id = si.item_id
            {where}
            ORDER BY si.thu_tu_hien_thi, si.id
        """, params)
        items = cursor.fetchall()
        
        import json
        for item in items:
            for key in ['dan_effect', 'dao_cu_effect', 'effect_moi_tang']:
                if item.get(key) and isinstance(item[key], str):
                    try:
                        item[key] = json.loads(item[key])
                    except:
                        pass
        
        return items
    finally:
        cursor.close()
        conn.close()


def get_shop_items_bao_gom_het_hang(item_type: str = None) -> list:
    """Lấy TẤT CẢ item (kể cả hết hàng) — dùng cho admin."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        where = "WHERE si.is_active = 1"
        params = []
        if item_type:
            where += " AND si.item_type = %s"
            params.append(item_type)
        
        cursor.execute(f"""
            SELECT 
                si.id AS shop_id,
                si.item_type,
                si.item_id,
                si.so_luong_ton,
                si.gia_linh_thach,
                si.gia_tien_ngoc,
                COALESCE(dd.ten, dc.ten, kt.ten, lt.ten) AS ten
            FROM tmpl_shop_item si
            LEFT JOIN tmpl_dan_duoc dd ON si.item_type = 'DanDuoc' AND dd.id = si.item_id
            LEFT JOIN tmpl_dao_cu dc ON si.item_type = 'DaoCu' AND dc.id = si.item_id
            LEFT JOIN tmpl_khoang_thach kt ON si.item_type = 'KhoangThach' AND kt.id = si.item_id
            LEFT JOIN tmpl_linh_thao lt ON si.item_type = 'LinhThao' AND lt.id = si.item_id
            {where}
            ORDER BY si.thu_tu_hien_thi, si.id
        """, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def mua_item(player_id: int, shop_id: int, so_luong: int, loai_tien: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # ===== 1. Lock shop item =====
        cursor.execute("""
            SELECT * FROM tmpl_shop_item 
            WHERE id = %s AND is_active = 1
            FOR UPDATE
        """, (shop_id,))
        shop_item = cursor.fetchone()
        
        if not shop_item:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Item không tồn tại!'}
        
        if so_luong <= 0:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Số lượng phải > 0!'}
        
        # ===== 2. Check tồn kho =====
        if shop_item['so_luong_ton'] < so_luong:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Hết hàng! Chỉ còn `{shop_item["so_luong_ton"]:,}` cái.'
            }
        
        # ===== 3. Lấy tỉ lệ đổi =====
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'ty_gia_tien_ngoc_linh_thach'
        """)
        row = cursor.fetchone()
        import json
        ti_gia = int(json.loads(row['value'])) if row else 10000
        
        # ===== 4. Lock player =====
        cursor.execute("""
            SELECT linh_thach, tien_ngoc FROM player
            WHERE player_id = %s FOR UPDATE
        """, (player_id,))
        p = cursor.fetchone()
        
        if not p:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy player!'}
        
        gia_lt = shop_item['gia_linh_thach'] * so_luong
        gia_tn = shop_item['gia_tien_ngoc'] * so_luong
        
        # ===== 5. Xử lý thanh toán =====
        lt_tru = 0
        tn_tru = 0
        
        if loai_tien == 'linh_thach':
            if shop_item['gia_linh_thach'] <= 0:
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Item này không bán bằng linh thạch!'}
            if p['linh_thach'] < gia_lt:
                conn.rollback()
                return {
                    'thanh_cong': False,
                    'loi': f'Không đủ linh thạch! Cần `{gia_lt:,}`, có `{p["linh_thach"]:,}`'
                }
            lt_tru = gia_lt
        
        elif loai_tien == 'tien_ngoc':
            if shop_item['gia_tien_ngoc'] <= 0:
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Item này không bán bằng tiên ngọc!'}
            
            if p['tien_ngoc'] >= gia_tn:
                tn_tru = gia_tn
            else:
                thieu_tn = gia_tn - p['tien_ngoc']
                lt_can_bu = thieu_tn * ti_gia
                
                if p['linh_thach'] < lt_can_bu:
                    conn.rollback()
                    return {
                        'thanh_cong': False,
                        'loi': (
                            f'Không đủ tiền!\n'
                            f'Cần `{gia_tn:,}` tiên ngọc, có `{p["tien_ngoc"]:,}`\n'
                            f'Thiếu `{thieu_tn:,}` tiên ngọc → cần bù `{lt_can_bu:,}` linh thạch, có `{p["linh_thach"]:,}`'
                        )
                    }
                
                tn_tru = p['tien_ngoc']
                lt_tru = lt_can_bu
        else:
            conn.rollback()
            return {'thanh_cong': False, 'loi': f'Loại tiền không hợp lệ: {loai_tien}'}
        
        # ===== 6. Trừ tiền =====
        cursor.execute("""
            UPDATE player
            SET linh_thach = linh_thach - %s,
                tien_ngoc = tien_ngoc - %s
            WHERE player_id = %s
        """, (lt_tru, tn_tru, player_id))
        
        # ===== 6b. Trừ tồn kho =====
        cursor.execute("""
            UPDATE tmpl_shop_item
            SET so_luong_ton = so_luong_ton - %s
            WHERE id = %s
        """, (so_luong, shop_id))
        
        # ===== 7. Cộng item =====
        item_type = shop_item['item_type']
        item_id = shop_item['item_id']
        
        if item_type == 'DanDuoc':
            cursor.execute("""
                INSERT INTO player_dan_duoc (player_id, dan_duoc_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
            """, (player_id, item_id, so_luong))
        
        elif item_type == 'DaoCu':
            cursor.execute("""
                INSERT INTO player_dao_cu (player_id, dao_cu_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
            """, (player_id, item_id, so_luong))
        
        elif item_type == 'LinhThao':
            cursor.execute("""
                INSERT INTO player_linh_thao (player_id, linh_thao_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
            """, (player_id, item_id, so_luong))
        
        elif item_type == 'KhoangThach':
            cursor.execute("""
                INSERT INTO player_khoang_thach (player_id, khoang_thach_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
            """, (player_id, item_id, so_luong))
        
        elif item_type == 'CongPhap':
            # ⭐ Lưu vào misc_tui_do dạng item
            cursor.execute(
                "SELECT ten FROM tmpl_cong_phap WHERE id = %s",
                (item_id,)
            )
            cp_row = cursor.fetchone()
            cp_ten = cp_row['ten'] if cp_row else '???'
            
            item_code = f'cong_phap_{item_id}'
            metadata = json.dumps(
                {'cong_phap_id': item_id, 'ten': cp_ten},
                ensure_ascii=False
            )
            
            # Check đã có trong túi chưa
            cursor.execute("""
                SELECT id FROM misc_tui_do
                WHERE player_id = %s AND item_code = %s
                LIMIT 1
            """, (player_id, item_code))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE misc_tui_do
                    SET so_luong = so_luong + %s
                    WHERE id = %s
                """, (so_luong, existing['id']))
            else:
                cursor.execute("""
                    INSERT INTO misc_tui_do (player_id, item_code, so_luong, metadata)
                    VALUES (%s, %s, %s, %s)
                """, (player_id, item_code, so_luong, metadata))
        
        else:
            conn.rollback()
            return {'thanh_cong': False, 'loi': f'Item type không hợp lệ: {item_type}'}
        
        # ===== 8. Log =====
        cursor.execute("""
            INSERT INTO log_giao_dich 
            (player_id, loai, item_type, item_id, so_luong, gia_linh_thach, gia_tien_ngoc)
            VALUES (%s, 'Mua', %s, %s, %s, %s, %s)
        """, (player_id, item_type, item_id, so_luong, lt_tru, tn_tru))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'item_type': item_type,
            'item_id': item_id,
            'ten': shop_item.get('ten'),
            'so_luong': so_luong,
            'linh_thach_tru': lt_tru,
            'tien_ngoc_tru': tn_tru,
            'so_luong_ton_con': shop_item['so_luong_ton'] - so_luong,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] mua_item: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi hệ thống: {e}'}
    finally:
        cursor.close()
        conn.close()

def ban_item(player_id: int, item_type: str, item_id: int, so_luong: int) -> dict:
    """Bán item lấy linh thạch."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        if so_luong <= 0:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Số lượng phải > 0!'}
        
        # 1. Lấy giá bán
        gia_ban = 0
        if item_type == 'KhoangThach':
            cursor.execute("SELECT gia_ban FROM tmpl_khoang_thach WHERE id = %s", (item_id,))
            row = cursor.fetchone()
            if row:
                gia_ban = row['gia_ban']
        elif item_type == 'LinhThao':
            cursor.execute("SELECT pham_cap FROM tmpl_linh_thao WHERE id = %s", (item_id,))
            row = cursor.fetchone()
            if row:
                # Giá bán linh thảo theo phẩm cấp (½ giá mua trong shop)
                gia_dict = {'Pham': 100, 'Linh': 1000, 'Bao': 10000, 'Tien': 500000, 'Than': 9000000}
                gia_ban = gia_dict.get(row['pham_cap'], 0)
        else:
            conn.rollback()
            return {'thanh_cong': False, 'loi': f'Không thể bán item type: {item_type}'}
        
        if gia_ban <= 0:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Item này không thể bán!'}
        
        # 2. Check player có item
        if item_type == 'KhoangThach':
            cursor.execute("""
                SELECT so_luong FROM player_khoang_thach
                WHERE player_id = %s AND khoang_thach_id = %s FOR UPDATE
            """, (player_id, item_id))
        elif item_type == 'LinhThao':
            cursor.execute("""
                SELECT so_luong FROM player_linh_thao
                WHERE player_id = %s AND linh_thao_id = %s FOR UPDATE
            """, (player_id, item_id))
        
        row = cursor.fetchone()
        if not row or row['so_luong'] < so_luong:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Bạn không có đủ item! (có {row["so_luong"] if row else 0})'
            }
        
        # 3. Trừ item
        if item_type == 'KhoangThach':
            cursor.execute("""
                UPDATE player_khoang_thach
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND khoang_thach_id = %s
            """, (so_luong, player_id, item_id))
            cursor.execute("""
                DELETE FROM player_khoang_thach
                WHERE player_id = %s AND khoang_thach_id = %s AND so_luong <= 0
            """, (player_id, item_id))
        elif item_type == 'LinhThao':
            cursor.execute("""
                UPDATE player_linh_thao
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND linh_thao_id = %s
            """, (so_luong, player_id, item_id))
            cursor.execute("""
                DELETE FROM player_linh_thao
                WHERE player_id = %s AND linh_thao_id = %s AND so_luong <= 0
            """, (player_id, item_id))
        
        # 4. Cộng linh thạch
        tong_tien = gia_ban * so_luong
        cursor.execute("""
            UPDATE player
            SET linh_thach = linh_thach + %s
            WHERE player_id = %s
        """, (tong_tien, player_id))
        
        # 5. Log
        cursor.execute("""
            INSERT INTO log_giao_dich 
            (player_id, loai, item_type, item_id, so_luong, gia_linh_thach, gia_tien_ngoc)
            VALUES (%s, 'Ban', %s, %s, %s, %s, 0)
        """, (player_id, item_type, item_id, so_luong, tong_tien))
        
        conn.commit()
        return {'thanh_cong': True, 'loi': None, 'tien_nhan': tong_tien}
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] ban_item: {e}')
        return {'thanh_cong': False, 'loi': f'Lỗi hệ thống: {e}'}
    finally:
        cursor.close()
        conn.close()
        
def restock_shop_item(shop_id: int, so_luong_them: int) -> dict:
    """
    Nhập thêm hàng cho 1 item trong shop.
    
    Args:
        shop_id: ID shop item
        so_luong_them: Số lượng nhập thêm (số dương)
    
    Returns:
        {'thanh_cong': bool, 'so_luong_moi': int, ...}
    """
    if so_luong_them <= 0:
        return {'thanh_cong': False, 'loi': 'Số lượng phải > 0!'}
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cursor.execute("""
            SELECT si.*, COALESCE(dd.ten, dc.ten, kt.ten, lt.ten) AS ten
            FROM tmpl_shop_item si
            LEFT JOIN tmpl_dan_duoc dd ON si.item_type = 'DanDuoc' AND dd.id = si.item_id
            LEFT JOIN tmpl_dao_cu dc ON si.item_type = 'DaoCu' AND dc.id = si.item_id
            LEFT JOIN tmpl_khoang_thach kt ON si.item_type = 'KhoangThach' AND kt.id = si.item_id
            LEFT JOIN tmpl_linh_thao lt ON si.item_type = 'LinhThao' AND lt.id = si.item_id
            WHERE si.id = %s
            FOR UPDATE
        """, (shop_id,))
        item = cursor.fetchone()
        
        if not item:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Item không tồn tại!'}
        
        so_luong_cu = item['so_luong_ton']
        so_luong_moi = so_luong_cu + so_luong_them
        
        cursor.execute("""
            UPDATE tmpl_shop_item
            SET so_luong_ton = %s
            WHERE id = %s
        """, (so_luong_moi, shop_id))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten': item['ten'],
            'so_luong_cu': so_luong_cu,
            'so_luong_them': so_luong_them,
            'so_luong_moi': so_luong_moi,
        }
    except Exception as e:
        conn.rollback()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


def restock_toan_bo(so_luong_them: int) -> dict:
    """Nhập hàng cho TẤT CẢ item trong shop."""
    if so_luong_them <= 0:
        return {'thanh_cong': False, 'loi': 'Số lượng phải > 0!'}
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        
        cursor.execute("""
            UPDATE tmpl_shop_item
            SET so_luong_ton = so_luong_ton + %s
            WHERE is_active = 1
        """, (so_luong_them,))
        
        so_item = cursor.rowcount
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'so_item': so_item,
            'so_luong_them': so_luong_them,
        }
    except Exception as e:
        conn.rollback()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()  
        
        
def them_dan_phuong_vao_tui(player_id: int, dan_duoc_id: int, so_luong: int = 1):
    """
    Thêm đan phương (dạng item) vào túi player.
    Lưu vào misc_tui_do với item_code = 'dan_phuong_<id>'.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # Lấy tên đan dược
        cursor.execute("SELECT ten FROM tmpl_dan_duoc WHERE id = %s", (dan_duoc_id,))
        dan = cursor.fetchone()
        if not dan:
            conn.rollback()
            return False
        
        import json
        item_code = f'dan_phuong_{dan_duoc_id}'
        metadata = json.dumps({'dan_duoc_id': dan_duoc_id, 'ten': dan['ten']}, ensure_ascii=False)
        
        # Check đã có item chưa
        cursor.execute("""
            SELECT id, so_luong FROM misc_tui_do
            WHERE player_id = %s AND item_code = %s
            LIMIT 1
        """, (player_id, item_code))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
                UPDATE misc_tui_do
                SET so_luong = so_luong + %s
                WHERE id = %s
            """, (so_luong, row['id']))
        else:
            cursor.execute("""
                INSERT INTO misc_tui_do (player_id, item_code, so_luong, metadata)
                VALUES (%s, %s, %s, %s)
            """, (player_id, item_code, so_luong, metadata))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] them_dan_phuong: {e}')
        return False
    finally:
        cursor.close()
        conn.close()

def them_cong_phap_vao_tui(player_id: int, cong_phap_id: int, so_luong: int = 1):
    """Thêm công pháp (dạng item) vào túi player."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cursor.execute("SELECT ten FROM tmpl_cong_phap WHERE id = %s", (cong_phap_id,))
        cp = cursor.fetchone()
        if not cp:
            conn.rollback()
            return False
        
        import json
        item_code = f'cong_phap_{cong_phap_id}'
        metadata = json.dumps({'cong_phap_id': cong_phap_id, 'ten': cp['ten']}, ensure_ascii=False)
        
        cursor.execute("""
            SELECT id FROM misc_tui_do
            WHERE player_id = %s AND item_code = %s
            LIMIT 1
        """, (player_id, item_code))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
                UPDATE misc_tui_do
                SET so_luong = so_luong + %s
                WHERE id = %s
            """, (so_luong, row['id']))
        else:
            cursor.execute("""
                INSERT INTO misc_tui_do (player_id, item_code, so_luong, metadata)
                VALUES (%s, %s, %s, %s)
            """, (player_id, item_code, so_luong, metadata))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] them_cong_phap: {e}')
        return False
    finally:
        cursor.close()
        conn.close()
        
def get_dan_phuong_trong_tui(player_id: int) -> list:
    """Lấy danh sách đan phương (chưa học) trong túi."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                mtd.id,
                mtd.item_code,
                mtd.so_luong,
                mtd.metadata,
                dd.ten,
                dd.pham_cap,
                dd.loai,
                dd.mo_ta,
                COALESCE(pdph.so_lan_nghien_cuu, 0) AS so_lan_nghien_cuu
            FROM misc_tui_do mtd
            JOIN tmpl_dan_duoc dd 
                ON dd.id = CAST(JSON_EXTRACT(mtd.metadata, '$.dan_duoc_id') AS UNSIGNED)
            LEFT JOIN player_dan_phuong_hoc pdph
                ON pdph.player_id = mtd.player_id 
                AND pdph.dan_duoc_id = dd.id
            WHERE mtd.player_id = %s 
              AND mtd.item_code LIKE 'dan_phuong_%%'
              AND mtd.so_luong > 0
            ORDER BY 
                FIELD(dd.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                dd.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_cong_phap_trong_tui(player_id: int) -> list:
    """Lấy danh sách công pháp (chưa học) trong túi."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                mtd.id,
                mtd.item_code,
                mtd.so_luong,
                mtd.metadata,
                cp.ten,
                cp.loai,
                cp.he,
                cp.giai_cap,
                cp.pham_cap,
                cp.mo_ta
            FROM misc_tui_do mtd
            JOIN tmpl_cong_phap cp 
                ON cp.id = CAST(JSON_EXTRACT(mtd.metadata, '$.cong_phap_id') AS UNSIGNED)
            WHERE mtd.player_id = %s 
              AND mtd.item_code LIKE 'cong_phap_%%'
              AND mtd.so_luong > 0
            ORDER BY 
                FIELD(cp.giai_cap, 'Hoang', 'Huyen', 'Dia', 'Thien'),
                FIELD(cp.pham_cap, 'Ha', 'Trung', 'Thuong', 'Cuc', 'HoanMy'),
                cp.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        
def hoc_dan_phuong(player_id: int, dan_duoc_id: int) -> dict:
    """
    Học đan phương: 
    - Nếu chưa học → học bình thường.
    - Nếu đã học → nghiên cứu, +1% tỉ lệ cơ bản.
    
    Returns:
        {
            'thanh_cong': bool,
            'loi': str,
            'ten': str,
            'loai': 'hoc_moi' | 'nghien_cuu',
            'so_lan_nghien_cuu': int,      # Nếu là nghiên cứu
            'ti_le_tang': float,            # Nếu là nghiên cứu
        }
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        item_code = f'dan_phuong_{dan_duoc_id}'
        
        # 1. Check trong túi
        cursor.execute("""
            SELECT id FROM misc_tui_do
            WHERE player_id = %s AND item_code = %s AND so_luong > 0
            FOR UPDATE
        """, (player_id, item_code))
        row = cursor.fetchone()
        
        if not row:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Bạn không có đan phương này!'}
        
        # 2. Lấy tên đan
        cursor.execute("SELECT ten FROM tmpl_dan_duoc WHERE id = %s", (dan_duoc_id,))
        dan = cursor.fetchone()
        if not dan:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Đan dược không tồn tại!'}
        
        # 3. Trừ khỏi túi
        cursor.execute("""
            UPDATE misc_tui_do SET so_luong = so_luong - 1 WHERE id = %s
        """, (row['id'],))
        
        cursor.execute("""
            DELETE FROM misc_tui_do WHERE id = %s AND so_luong <= 0
        """, (row['id'],))
        
        # 4. Check đã học chưa
        cursor.execute("""
            SELECT so_lan_nghien_cuu FROM player_dan_phuong_hoc
            WHERE player_id = %s AND dan_duoc_id = %s
            FOR UPDATE
        """, (player_id, dan_duoc_id))
        existing = cursor.fetchone()
        
        if existing:
            # ⭐ ĐÃ HỌC → NGHIÊN CỨU
            so_lan_moi = existing['so_lan_nghien_cuu'] + 1
            
            cursor.execute("""
                UPDATE player_dan_phuong_hoc
                SET so_lan_nghien_cuu = %s
                WHERE player_id = %s AND dan_duoc_id = %s
            """, (so_lan_moi, player_id, dan_duoc_id))
            
            conn.commit()
            
            return {
                'thanh_cong': True,
                'loi': None,
                'ten': dan['ten'],
                'loai': 'nghien_cuu',
                'so_lan_nghien_cuu': so_lan_moi,
                'ti_le_tang': 1.0,
            }
        else:
            # ⭐ CHƯA HỌC → HỌC MỚI
            cursor.execute("""
                INSERT INTO player_dan_phuong_hoc 
                (player_id, dan_duoc_id, so_lan_nghien_cuu)
                VALUES (%s, %s, 0)
            """, (player_id, dan_duoc_id))
            
            conn.commit()
            
            return {
                'thanh_cong': True,
                'loi': None,
                'ten': dan['ten'],
                'loai': 'hoc_moi',
                'so_lan_nghien_cuu': 0,
                'ti_le_tang': 0.0,
            }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] hoc_dan_phuong: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()
        
def hoc_cong_phap(player_id: int, cong_phap_id: int) -> dict:
    """
    Học công pháp: 
    - Nếu chưa học → học bình thường.
    - Nếu đã học → nghiên cứu, +1% tỉ lệ cơ bản.
    - ⭐ Check hệ: công pháp phải có ít nhất 1 hệ khớp với linh căn player.
    """
    import json
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        item_code = f'cong_phap_{cong_phap_id}'
        
        # 1. Check trong túi
        cursor.execute("""
            SELECT id FROM misc_tui_do
            WHERE player_id = %s AND item_code = %s AND so_luong > 0
            FOR UPDATE
        """, (player_id, item_code))
        row = cursor.fetchone()
        
        if not row:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Bạn không có công pháp này!'}
        
        # 2. Lấy thông tin công pháp
        cursor.execute("""
            SELECT ten, loai, he, giai_cap, pham_cap
            FROM tmpl_cong_phap
            WHERE id = %s
        """, (cong_phap_id,))
        cp = cursor.fetchone()
        
        if not cp:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Công pháp không tồn tại!'}
        
        # ⭐ 3. Check hệ (chỉ với công pháp Ngũ Hành / Dị Hệ)
        if cp['loai'] in ('NguHanh', 'DiHe') and cp['he']:
            he_cp = cp['he']
            if isinstance(he_cp, str):
                try:
                    he_cp = json.loads(he_cp)
                except:
                    he_cp = []
            
            if not isinstance(he_cp, list):
                he_cp = []
            
            # Lấy hệ linh căn của player
            cursor.execute("""
                SELECT lc.he
                FROM player_linh_can plc
                JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
                WHERE plc.player_id = %s AND plc.is_active = 1
            """, (player_id,))
            he_linh_can = [r['he'] for r in cursor.fetchall()]
            
            # Check ít nhất 1 hệ khớp
            so_he_khop = sum(1 for h in he_cp if h in he_linh_can)
            
            if so_he_khop == 0:
                conn.rollback()
                he_cp_str = ', '.join(he_cp)
                he_lc_str = ', '.join(he_linh_can) if he_linh_can else 'không có'
                return {
                    'thanh_cong': False,
                    'loi': (
                        f'❌ Bạn không có hệ nào khớp!\n'
                        f'• Công pháp cần: **{he_cp_str}**\n'
                        f'• Linh căn của bạn: **{he_lc_str}**\n'
                        f'Cần ít nhất 1 hệ trùng để học.'
                    )
                }
        
        # 4. Trừ khỏi túi
        cursor.execute("""
            UPDATE misc_tui_do SET so_luong = so_luong - 1 WHERE id = %s
        """, (row['id'],))
        
        cursor.execute("""
            DELETE FROM misc_tui_do WHERE id = %s AND so_luong <= 0
        """, (row['id'],))
        
       # 5. Check đã học chưa
        cursor.execute("""
            SELECT tang_hien_tai, dang_tu_luyen, do_thuan_thuc 
            FROM player_cong_phap
            WHERE player_id = %s AND cong_phap_id = %s
            FOR UPDATE
        """, (player_id, cong_phap_id))
        existing = cursor.fetchone()
        
        if existing:
            # ⭐ NGHIÊN CỨU: tăng độ thuần thục
            thuan_thuc_cu = int(existing.get('do_thuan_thuc', 0) or 0)
            
            cursor.execute("""
                UPDATE player_cong_phap
                SET do_thuan_thuc = LEAST(do_thuan_thuc + 1, 100)
                WHERE player_id = %s AND cong_phap_id = %s
            """, (player_id, cong_phap_id))
            
            thuan_thuc_moi = min(thuan_thuc_cu + 1, 100)
            
            conn.commit()
            
            return {
                'thanh_cong': True,
                'loi': None,
                'ten': cp['ten'],
                'loai': 'nghien_cuu',
                'do_thuan_thuc_cu': thuan_thuc_cu,
                'do_thuan_thuc_moi': thuan_thuc_moi,
            }
        else:
            # ⭐ HỌC MỚI
            # Check số công pháp đang tu luyện
            cursor.execute("""
                SELECT COUNT(*) AS so_luong FROM player_cong_phap
                WHERE player_id = %s AND dang_tu_luyen = 1
                FOR UPDATE
            """, (player_id,))
            so_dang_tu_luyen = cursor.fetchone()['so_luong']
            
            # Lấy config max
            cursor.execute("""
                SELECT value FROM he_thong_config
                WHERE key_name = 'max_cong_phap_active'
            """)
            row_cfg = cursor.fetchone()
            max_active = int(json.loads(row_cfg['value'])) if row_cfg else 2
            
            # Auto active nếu chưa đủ slot
            dang_tu_luyen = 1 if so_dang_tu_luyen < max_active else 0
            
            cursor.execute("""
                INSERT INTO player_cong_phap 
                (player_id, cong_phap_id, tang_hien_tai, dang_tu_luyen)
                VALUES (%s, %s, 1, %s)
            """, (player_id, cong_phap_id, dang_tu_luyen))
            
            conn.commit()
            
            return {
                'thanh_cong': True,
                'loi': None,
                'ten': cp['ten'],
                'loai': 'hoc_moi',
                'dang_tu_luyen': bool(dang_tu_luyen),
            }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] hoc_cong_phap: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()
        
def get_bonus_cong_phap(player_id: int) -> dict:
    """
    Tính tổng bonus từ các công pháp đang tu luyện.
    
    Returns:
        {'atk': 100, 'def': 50, 'hp_max': 500, ...}
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                cp.effect_moi_tang,
                cp.so_tang,
                pcp.tang_hien_tai,
                cp.bonus_dac_biet,
                cp.he
            FROM player_cong_phap pcp
            JOIN tmpl_cong_phap cp ON cp.id = pcp.cong_phap_id
            WHERE pcp.player_id = %s AND pcp.dang_tu_luyen = 1
        """, (player_id,))
        rows = cursor.fetchall()
        
        import json
        bonus = {}
        
        for row in rows:
            effect = row['effect_moi_tang']
            if isinstance(effect, str):
                effect = json.loads(effect)
            if not isinstance(effect, dict):
                continue
            
            tang = row['tang_hien_tai']
            
            # Bonus = effect_moi_tang × tầng hiện tại
            for stat_code, gia_tri_moi_tang in effect.items():
                try:
                    gia_tri = float(gia_tri_moi_tang) * tang
                    bonus[stat_code] = bonus.get(stat_code, 0.0) + gia_tri
                except (ValueError, TypeError):
                    pass
        
        return bonus
    finally:
        cursor.close()
        conn.close()    
        
def ban_cong_phap(player_id: int, cong_phap_id: int, so_luong: int) -> dict:
    """
    Bán công pháp (chưa học) lấy linh thạch.
    
    Args:
        player_id: ID player
        cong_phap_id: ID công pháp (trong tmpl_cong_phap)
        so_luong: Số lượng bán
    
    Returns:
        {'thanh_cong': bool, 'loi': str, 'tien_nhan': int}
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        if so_luong <= 0:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Số lượng phải > 0!'}
        
        # 1. Lấy giá bán theo giai cấp
        cursor.execute("""
            SELECT ten, giai_cap
            FROM tmpl_cong_phap
            WHERE id = %s
        """, (cong_phap_id,))
        cp = cursor.fetchone()
        
        if not cp:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Công pháp không tồn tại!'}
        
        # ⭐ Giá bán = 50% giá mua trong shop
        gia_ban_dict = {
            'Hoang': 2500,      # 5000 × 50%
            'Huyen': 10000,     # 20000 × 50%
            'Dia': 50000,       # 100000 × 50%
            'Thien': 250000,    # 500000 × 50%
        }
        gia_ban = gia_ban_dict.get(cp['giai_cap'], 0)
        
        if gia_ban <= 0:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Công pháp này không thể bán!'}
        
        # 2. Check player có công pháp trong túi
        item_code = f'cong_phap_{cong_phap_id}'
        cursor.execute("""
            SELECT id, so_luong FROM misc_tui_do
            WHERE player_id = %s AND item_code = %s AND so_luong > 0
            FOR UPDATE
        """, (player_id, item_code))
        row = cursor.fetchone()
        
        if not row or row['so_luong'] < so_luong:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Bạn không có đủ công pháp! (có {row["so_luong"] if row else 0})'
            }
        
        # 3. Trừ công pháp khỏi túi
        cursor.execute("""
            UPDATE misc_tui_do
            SET so_luong = so_luong - %s
            WHERE id = %s
        """, (so_luong, row['id']))
        
        cursor.execute("""
            DELETE FROM misc_tui_do
            WHERE id = %s AND so_luong <= 0
        """, (row['id'],))
        
        # 4. Cộng linh thạch
        tong_tien = gia_ban * so_luong
        cursor.execute("""
            UPDATE player
            SET linh_thach = linh_thach + %s
            WHERE player_id = %s
        """, (tong_tien, player_id))
        
        # 5. Log
        cursor.execute("""
            INSERT INTO log_giao_dich 
            (player_id, loai, item_type, item_id, so_luong, gia_linh_thach, gia_tien_ngoc)
            VALUES (%s, 'Ban', 'CongPhap', %s, %s, %s, 0)
        """, (player_id, cong_phap_id, so_luong, tong_tien))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten': cp['ten'],
            'tien_nhan': tong_tien,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] ban_cong_phap: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi hệ thống: {e}'}
    finally:
        cursor.close()
        conn.close()


def get_player_cong_phap_trong_tui(player_id: int) -> list:
    """
    Lấy danh sách công pháp (chưa học) trong túi để bán.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                mtd.id,
                mtd.item_code,
                mtd.so_luong,
                mtd.metadata,
                cp.id AS cong_phap_id,
                cp.ten,
                cp.giai_cap,
                cp.pham_cap,
                cp.loai,
                cp.he
            FROM misc_tui_do mtd
            JOIN tmpl_cong_phap cp 
                ON cp.id = CAST(JSON_EXTRACT(mtd.metadata, '$.cong_phap_id') AS UNSIGNED)
            WHERE mtd.player_id = %s 
              AND mtd.item_code LIKE 'cong_phap_%%'
              AND mtd.so_luong > 0
            ORDER BY 
                FIELD(cp.giai_cap, 'Hoang', 'Huyen', 'Dia', 'Thien'),
                cp.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        
# ============================================================
# DÙNG ĐẠO CỤ TĂNG TINH KHIẾT
# ============================================================

def get_dao_cu_tang_tinh_khiet_cua_player(player_id: int) -> list:
    """Lấy danh sách đạo cụ tăng tinh khiết của player."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                dc.id,
                dc.code,
                dc.ten,
                dc.he,
                dc.pham_cap,
                dc.mo_ta,
                pdc.so_luong
            FROM player_dao_cu pdc
            JOIN tmpl_dao_cu dc ON dc.id = pdc.dao_cu_id
            WHERE pdc.player_id = %s 
              AND dc.loai = 'TangTinhKhiet'
              AND pdc.so_luong > 0
            ORDER BY dc.he, dc.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def dung_dao_cu_tang_tinh_khiet(player_id: int, dao_cu_id: int, linh_can_id: int) -> dict:
    """
    Dùng đạo cụ tăng tinh khiết cho 1 linh căn.
    
    ⭐ 2 loại đạo cụ:
    - Tiên Linh Thạch (he NOT NULL): phải khớp hệ, tăng theo phẩm cấp linh căn (config).
    - Linh Dịch (he NULL): mọi hệ, tăng cố định theo effect.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 1. Lấy đạo cụ
        cursor.execute("""
            SELECT dc.id, dc.code, dc.ten, dc.he, dc.loai, dc.effect
            FROM tmpl_dao_cu dc
            WHERE dc.id = %s
        """, (dao_cu_id,))
        dao_cu = cursor.fetchone()
        
        if not dao_cu:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Đạo cụ không tồn tại!'}
        
        if dao_cu['loai'] != 'TangTinhKhiet':
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Đạo cụ không phải loại tăng tinh khiết!'}
        
        # 2. Lấy linh căn
        cursor.execute("""
            SELECT 
                plc.linh_can_id,
                plc.do_tinh_khiet,
                lc.ten,
                lc.he,
                lc.pham_cap
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s AND plc.linh_can_id = %s
            FOR UPDATE
        """, (player_id, linh_can_id))
        lc = cursor.fetchone()
        
        if not lc:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy linh căn!'}
        
        # ⭐ Convert Decimal → float
        lc['do_tinh_khiet'] = float(lc['do_tinh_khiet'])
        
        # 3. Check hệ
        if dao_cu['he'] is not None and dao_cu['he'] != lc['he']:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Đạo cụ hệ **{dao_cu["he"]}** không dùng được cho linh căn hệ **{lc["he"]}**!'
            }
        
        # 4. Check max
        if lc['do_tinh_khiet'] >= 100:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Linh căn đã đạt 100% tinh khiết!'}
        
        # 5. Tính % tăng
        import json
        
        if dao_cu['he'] is None:
            # Linh Dịch
            effect = dao_cu.get('effect')
            if isinstance(effect, str):
                effect = json.loads(effect)
            
            if not isinstance(effect, dict):
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Đạo cụ không có effect!'}
            
            pct = float(effect.get('tinh_khiet', 0))
            
            if pct <= 0:
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Đạo cụ không có hiệu ứng tinh khiết!'}
        else:
            # Tiên Linh Thạch
            cursor.execute("""
                SELECT value FROM he_thong_config
                WHERE key_name = 'dao_cu_tang_tinh_khiet_pct'
            """)
            row = cursor.fetchone()
            
            config = json.loads(row['value']) if row else {
                'Ha': 30, 'Trung': 25, 'Thuong': 20, 'Cuc': 10, 'Tien': 5
            }
            
            pct = float(config.get(lc['pham_cap'], 0))
            
            if pct <= 0:
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Không có config cho phẩm cấp này!'}
        
        # 6. Check player có đạo cụ
        cursor.execute("""
            SELECT so_luong FROM player_dao_cu
            WHERE player_id = %s AND dao_cu_id = %s
            FOR UPDATE
        """, (player_id, dao_cu_id))
        row = cursor.fetchone()
        
        if not row or row['so_luong'] < 1:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Bạn không có đạo cụ này!'}
        
        # 7. Tính lượng tăng (cap ở 100%)
        amount = min(pct, 100 - lc['do_tinh_khiet'])
        tinh_khiet_moi = lc['do_tinh_khiet'] + amount
        
        # 8. Trừ đạo cụ
        cursor.execute("""
            UPDATE player_dao_cu
            SET so_luong = so_luong - 1
            WHERE player_id = %s AND dao_cu_id = %s
        """, (player_id, dao_cu_id))
        
        cursor.execute("""
            DELETE FROM player_dao_cu
            WHERE player_id = %s AND dao_cu_id = %s AND so_luong <= 0
        """, (player_id, dao_cu_id))
        
        # 9. Tăng tinh khiết
        cursor.execute("""
            UPDATE player_linh_can
            SET do_tinh_khiet = LEAST(do_tinh_khiet + %s, 100),
                san_sang_dot_pha = IF(do_tinh_khiet + %s >= 100, 1, 0)
            WHERE player_id = %s AND linh_can_id = %s
        """, (amount, amount, player_id, linh_can_id))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten_dao_cu': dao_cu['ten'],
            'ten_linh_can': lc['ten'],
            'amount': amount,
            'tinh_khiet_cu': lc['do_tinh_khiet'],
            'tinh_khiet_moi': tinh_khiet_moi,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] dung_dao_cu_tang_tinh_khiet: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()
        
# ============================================================
# DÙNG ĐAN DƯỢC
# ============================================================

def dung_dan_duoc(player_id: int, dan_duoc_id: int) -> dict:
    """
    Dùng đan dược.
    Hỗ trợ: HoiPhuc, TangTuVi, Buff.
    Chưa hỗ trợ: DotPha, Doc (sẽ làm sau).
    
    Returns:
        {'thanh_cong': bool, 'loi': str, 'ket_qua': dict}
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 1. Lấy đan dược
        cursor.execute("""
            SELECT id, ten, loai, effect, pham_cap
            FROM tmpl_dan_duoc
            WHERE id = %s
        """, (dan_duoc_id,))
        dan = cursor.fetchone()
        
        if not dan:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Đan dược không tồn tại!'}
        
        # 2. Check player có đan
        cursor.execute("""
            SELECT so_luong FROM player_dan_duoc
            WHERE player_id = %s AND dan_duoc_id = %s
            FOR UPDATE
        """, (player_id, dan_duoc_id))
        row = cursor.fetchone()
        
        if not row or row['so_luong'] < 1:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Bạn không có đan dược này!'}
        
        # 3. Parse effect
        effect = dan['effect']
        if isinstance(effect, str):
            import json
            effect = json.loads(effect)
        
        if not isinstance(effect, dict):
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Đan dược không có hiệu ứng!'}
        
        loai_dan = dan['loai']
        ket_qua = {}
        
        # ===== 4. Xử lý theo loại =====
        if loai_dan == 'HoiPhuc':
            # Hồi HP/MP
            hp_hoi = effect.get('hp', 0)
            mp_hoi = effect.get('mp', 0)
            
            if hp_hoi > 0 or mp_hoi > 0:
                cursor.execute("""
                    UPDATE player_stat
                    SET hp_hien_tai = LEAST(hp_max, hp_hien_tai + %s),
                        mp_hien_tai = LEAST(mp_max, mp_hien_tai + %s),
                        last_hp_update = NOW()
                    WHERE player_id = %s
                """, (hp_hoi, mp_hoi, player_id))
                
                ket_qua['hp_hoi'] = hp_hoi
                ket_qua['mp_hoi'] = mp_hoi
        
        elif loai_dan == 'TangTuVi':
            # Cộng tu vi
            tu_vi = effect.get('tu_vi', 0)
            
            if tu_vi > 0:
                cursor.execute("""
                    UPDATE player
                    SET tu_vi = tu_vi + %s
                    WHERE player_id = %s
                """, (tu_vi, player_id))
                
                ket_qua['tu_vi'] = tu_vi
        
        elif loai_dan == 'Buff':
            # Thêm buff tạm
            # Lấy thời gian hiệu lực
            thoi_gian = 3600  # Mặc định 1 giờ
            cursor.execute("""
                SELECT thoi_gian_hieu_luc FROM tmpl_dan_duoc WHERE id = %s
            """, (dan_duoc_id,))
            row = cursor.fetchone()
            if row and row['thoi_gian_hieu_luc'] > 0:
                thoi_gian = row['thoi_gian_hieu_luc']
            
            from datetime import datetime, timedelta
            het_han = datetime.now() + timedelta(seconds=thoi_gian)
            
            import json
            effect_json = json.dumps(effect, ensure_ascii=False)
            
            # Upsert buff (nếu trùng code → kéo dài)
            buff_code = f'dan_{dan_duoc_id}'
            cursor.execute("""
                INSERT INTO player_buff (player_id, buff_code, effect, het_han_luc, nguon_goc)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    het_han_luc = VALUES(het_han_luc),
                    effect = VALUES(effect)
            """, (player_id, buff_code, effect_json, het_han, dan['ten']))
            
            ket_qua['buff'] = effect
            ket_qua['thoi_gian'] = thoi_gian
        
        elif loai_dan == 'DotPha':
            # Thêm buff tỉ lệ đột phá
            ti_le = effect.get('ti_le_dot_pha', 0)
            # Hoặc lấy từ cột ti_le_dot_pha_bonus
            cursor.execute("""
                SELECT ti_le_dot_pha_bonus, thoi_gian_hieu_luc 
                FROM tmpl_dan_duoc WHERE id = %s
            """, (dan_duoc_id,))
            row = cursor.fetchone()
            
            ti_le_bonus = row['ti_le_dot_pha_bonus'] if row else 0
            thoi_gian = row['thoi_gian_hieu_luc'] if row else 1800
            
            if ti_le_bonus > 0:
                from datetime import datetime, timedelta
                het_han = datetime.now() + timedelta(seconds=thoi_gian)
                
                import json
                buff_effect = json.dumps({'ti_le_dot_pha': ti_le_bonus}, ensure_ascii=False)
                buff_code = f'dan_dotpha_{dan_duoc_id}'
                
                cursor.execute("""
                    INSERT INTO player_buff (player_id, buff_code, effect, het_han_luc, nguon_goc)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        het_han_luc = VALUES(het_han_luc),
                        effect = VALUES(effect)
                """, (player_id, buff_code, buff_effect, het_han, dan['ten']))
                
                ket_qua['ti_le_dot_pha'] = ti_le_bonus
                ket_qua['thoi_gian'] = thoi_gian
        
        else:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Loại đan **{loai_dan}** chưa được hỗ trợ!'
            }
        
        # ===== 5. Trừ đan =====
        cursor.execute("""
            UPDATE player_dan_duoc
            SET so_luong = so_luong - 1
            WHERE player_id = %s AND dan_duoc_id = %s
        """, (player_id, dan_duoc_id))
        
        cursor.execute("""
            DELETE FROM player_dan_duoc
            WHERE player_id = %s AND dan_duoc_id = %s AND so_luong <= 0
        """, (player_id, dan_duoc_id))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten': dan['ten'],
            'loai': loai_dan,
            'ket_qua': ket_qua,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] dung_dan_duoc: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()
        
# ============================================================
# ĐAN PHƯƠNG ĐÃ HỌC
# ============================================================

def get_player_dan_phuong_da_hoc(player_id: int) -> list:
    """Lấy danh sách đan phương player đã học."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                pdph.dan_duoc_id,
                pdph.so_lan_nghien_cuu,      -- ⭐ MỚI
                pdph.ngay_hoc,
                dd.ten,
                dd.pham_cap,
                dd.loai,
                dd.mo_ta
            FROM player_dan_phuong_hoc pdph
            JOIN tmpl_dan_duoc dd ON dd.id = pdph.dan_duoc_id
            WHERE pdph.player_id = %s
            ORDER BY 
                FIELD(dd.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                dd.ten
        """, (player_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_dan_phuong_chi_tiet(player_id: int, dan_duoc_id: int) -> dict:
    """
    Lấy chi tiết 1 đan phương (bao gồm nguyên liệu).
    
    Returns:
        {
            'dan_duoc': {...},
            'nguyen_lieu': [
                {'linh_thao_id', 'ten', 'pham_cap', 'so_luong', 'ti_le_thanh_cong_max'}, ...
            ]
        }
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Check đã học chưa
        cursor.execute("""
            SELECT 1 FROM player_dan_phuong_hoc
            WHERE player_id = %s AND dan_duoc_id = %s
        """, (player_id, dan_duoc_id))
        if not cursor.fetchone():
            return None
        
        # 2. Lấy thông tin đan
        cursor.execute("""
            SELECT * FROM tmpl_dan_duoc WHERE id = %s
        """, (dan_duoc_id,))
        dan = cursor.fetchone()
        
        if not dan:
            return None
        
        # 3. Lấy nguyên liệu
        cursor.execute("""
            SELECT 
                dp.linh_thao_id,
                dp.so_luong,
                dp.ti_le_thanh_cong_max,
                lt.ten,
                lt.pham_cap,
                lt.he
            FROM tmpl_dan_phuong dp
            JOIN tmpl_linh_thao lt ON lt.id = dp.linh_thao_id
            WHERE dp.dan_duoc_id = %s
        """, (dan_duoc_id,))
        nguyen_lieu = cursor.fetchall()
        
        return {
            'dan_duoc': dan,
            'nguyen_lieu': nguyen_lieu,
        }
    finally:
        cursor.close()
        conn.close()


def check_du_nguyen_lieu(player_id: int, dan_duoc_id: int) -> dict:
    """
    Kiểm tra player có đủ nguyên liệu để luyện đan này không.
    
    Returns:
        {
            'du': bool,
            'ds_can': [...],  # Nguyên liệu cần
            'ds_co': {...},   # Số lượng player có
            'thieu': [...],   # Nguyên liệu thiếu
        }
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Lấy nguyên liệu cần
        cursor.execute("""
            SELECT 
                dp.linh_thao_id,
                dp.so_luong,
                lt.ten,
                lt.pham_cap
            FROM tmpl_dan_phuong dp
            JOIN tmpl_linh_thao lt ON lt.id = dp.linh_thao_id
            WHERE dp.dan_duoc_id = %s
        """, (dan_duoc_id,))
        ds_can = cursor.fetchall()
        
        # 2. Lấy số lượng player có
        cursor.execute("""
            SELECT linh_thao_id, so_luong
            FROM player_linh_thao
            WHERE player_id = %s
        """, (player_id,))
        ds_co = {r['linh_thao_id']: r['so_luong'] for r in cursor.fetchall()}
        
        # 3. Tính thiếu
        thieu = []
        for nl in ds_can:
            co = ds_co.get(nl['linh_thao_id'], 0)
            if co < nl['so_luong']:
                thieu.append({
                    'ten': nl['ten'],
                    'can': nl['so_luong'],
                    'co': co,
                    'thieu': nl['so_luong'] - co,
                })
        
        return {
            'du': len(thieu) == 0,
            'ds_can': ds_can,
            'ds_co': ds_co,
            'thieu': thieu,
        }
    finally:
        cursor.close()
        conn.close()  
        
        
# ============================================================
# ĐẠO CỤ (xem)
# ============================================================

def get_player_dao_cu_full(player_id: int) -> list:
    """
    Lấy danh sách đạo cụ player sở hữu (đầy đủ thông tin).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                dc.id,
                dc.code,
                dc.ten,
                dc.loai,
                dc.pham_cap,
                dc.he,
                dc.effect,
                dc.mo_ta,
                dc.co_the_mua_premium,
                dc.gia_tien_ngoc,
                pdc.so_luong
            FROM player_dao_cu pdc
            JOIN tmpl_dao_cu dc ON dc.id = pdc.dao_cu_id
            WHERE pdc.player_id = %s AND pdc.so_luong > 0
            ORDER BY 
                FIELD(dc.loai, 'DotPhaLinhCan', 'TangTinhKhiet', 'TangTiLeDotPha', 'Khac'),
                FIELD(dc.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                dc.ten
        """, (player_id,))
        items = cursor.fetchall()
        
        import json
        for item in items:
            if item.get('effect') and isinstance(item['effect'], str):
                try:
                    item['effect'] = json.loads(item['effect'])
                except:
                    pass
        
        return items
    finally:
        cursor.close()
        conn.close()
        
        
# ============================================================
# LUYỆN ĐAN
# ============================================================

# ============================================================
# LUYỆN ĐAN (nâng cao)
# ============================================================

def get_dan_phuong_cong_thuc(dan_duoc_id: int) -> dict:
    """
    Lấy công thức luyện đan (nguyên liệu cần).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Thông tin đan
        cursor.execute("""
            SELECT 
                dd.id, dd.ten, dd.pham_cap, dd.loai, dd.mo_ta,
                dd.yeu_cau_nghe_cap
            FROM tmpl_dan_duoc dd
            WHERE dd.id = %s
        """, (dan_duoc_id,))
        dan = cursor.fetchone()
        
        if not dan:
            return None
        
        # Nguyên liệu
        cursor.execute("""
            SELECT 
                dp.linh_thao_id,
                dp.so_luong,
                dp.ti_le_thanh_cong_max,
                lt.ten,
                lt.pham_cap,
                lt.he
            FROM tmpl_dan_phuong dp
            JOIN tmpl_linh_thao lt ON lt.id = dp.linh_thao_id
            WHERE dp.dan_duoc_id = %s
        """, (dan_duoc_id,))
        nguyen_lieu = cursor.fetchall()
        
        return {
            'dan_duoc': dan,
            'nguyen_lieu': nguyen_lieu,
        }
    finally:
        cursor.close()
        conn.close()


def find_dan_phuong_by_nguyen_lieu(nguyen_lieu_dict: dict) -> list:
    """
    Tìm đan phương khớp với tổ hợp nguyên liệu.
    
    Args:
        nguyen_lieu_dict: {linh_thao_id: so_luong, ...}
    
    Returns:
        [{'dan_duoc_id', 'ten', 'pham_cap', ...}, ...]
    """
    if not nguyen_lieu_dict:
        return []
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Lấy tất cả đan phương có công thức
        cursor.execute("""
            SELECT 
                dd.id AS dan_duoc_id,
                dd.ten,
                dd.pham_cap,
                dd.loai,
                dd.yeu_cau_nghe_cap,
                dp.linh_thao_id,
                dp.so_luong,
                dp.ti_le_thanh_cong_max
            FROM tmpl_dan_duoc dd
            JOIN tmpl_dan_phuong dp ON dp.dan_duoc_id = dd.id
        """)
        rows = cursor.fetchall()
        
        # Group theo dan_duoc_id
        cong_thuc_map = {}
        for r in rows:
            did = r['dan_duoc_id']
            if did not in cong_thuc_map:
                cong_thuc_map[did] = {
                    'dan_duoc_id': did,
                    'ten': r['ten'],
                    'pham_cap': r['pham_cap'],
                    'loai': r['loai'],
                    'yeu_cau_nghe_cap': r['yeu_cau_nghe_cap'],
                    'ti_le_thanh_cong_max': float(r['ti_le_thanh_cong_max']),
                    'nguyen_lieu': {},
                }
            cong_thuc_map[did]['nguyen_lieu'][r['linh_thao_id']] = r['so_luong']
        
        # So sánh
        ket_qua = []
        for did, info in cong_thuc_map.items():
            if info['nguyen_lieu'] == nguyen_lieu_dict:
                ket_qua.append(info)
        
        return ket_qua
    finally:
        cursor.close()
        conn.close()


def tinh_ti_le_luyen_dan(player_id: int, dan_duoc_id: int) -> dict:
    """
    Tính tỉ lệ thành công luyện đan.
    
    Returns:
        {
            'ti_le_cuoi': float,
            'ti_le_toi_da': float,
            'nguon': [
                {'ten': str, 'gia_tri': float, 'emoji': str}, ...
            ]
        }
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Lấy thông tin cần thiết
        cursor.execute("""
            SELECT 
                dd.yeu_cau_nghe_cap,
                dd.pham_cap,
                dp.ti_le_thanh_cong_max,
                p.tam_canh,
                p.khi_van
            FROM tmpl_dan_duoc dd
            JOIN tmpl_dan_phuong dp ON dp.dan_duoc_id = dd.id
            JOIN player p ON p.player_id = %s
            WHERE dd.id = %s
            LIMIT 1
        """, (player_id, dan_duoc_id))
        info = cursor.fetchone()
        
        if not info:
            return None
        
        nguon = []
        
        # 2. Tỉ lệ cơ bản
        ti_le_co_ban = 10.0  # Cơ bản 50%
        nguon.append({
            'ten': 'Cơ bản',
            'gia_tri': ti_le_co_ban,
            'emoji': '🎯'
        })
        
        # 3. Bonus cấp nghề Luyện Đan Sư
        cursor.execute("""
            SELECT cap_do FROM player_nghe_nghiep
            WHERE player_id = %s AND nghe_nghiep_id = 1
        """, (player_id,))
        row = cursor.fetchone()
        cap_nghe = row['cap_do'] if row else 0
        
        yeu_cau = info['yeu_cau_nghe_cap'] or 1
        
        if cap_nghe >= yeu_cau:
            bonus_cap = 5.0 * (cap_nghe - yeu_cau)
        else:
            # Dưới cấp yêu cầu → phạt
            bonus_cap = -5.0 * (yeu_cau - cap_nghe)
        
        if bonus_cap != 0:
            nguon.append({
                'ten': f'Cấp nghề ({cap_nghe}/{yeu_cau})',
                'gia_tri': bonus_cap,
                'emoji': '🔨'
            })
        
        # ⭐ Bonus từ nghiên cứu đan phương
        cursor.execute("""
            SELECT so_lan_nghien_cuu FROM player_dan_phuong_hoc
            WHERE player_id = %s AND dan_duoc_id = %s
        """, (player_id, dan_duoc_id))
        row_nc = cursor.fetchone()

        if row_nc and row_nc['so_lan_nghien_cuu'] > 0:
            so_lan = row_nc['so_lan_nghien_cuu']
            bonus_nghien_cuu = so_lan * 1.0  # +1% mỗi lần
            nguon.append({
                'ten': f'Nghiên cứu ({so_lan} lần)',
                'gia_tri': bonus_nghien_cuu,
                'emoji': '📖'
            })
        
        # 4. Bonus tâm cảnh (0.1%/điểm)
        tam_canh = info['tam_canh'] or 0
        bonus_tam_canh = tam_canh * 0.1
        if bonus_tam_canh > 0:
            nguon.append({
                'ten': f'Tâm cảnh ({tam_canh})',
                'gia_tri': bonus_tam_canh,
                'emoji': '🧘'
            })
        
        # 5. Bonus khí vận (0.2%/điểm)
        khi_van = info['khi_van'] or 0
        bonus_khi_van = khi_van * 0.2
        if bonus_khi_van > 0:
            nguon.append({
                'ten': f'Khí vận ({khi_van})',
                'gia_tri': bonus_khi_van,
                'emoji': '🍀'
            })
        
        # 6. Tổng
        ti_le_cuoi = sum(n['gia_tri'] for n in nguon)
        
        # 7. Clamp
        ti_le_toi_da = float(info['ti_le_thanh_cong_max'])
        ti_le_cuoi = max(1.0, min(ti_le_cuoi, ti_le_toi_da))
        
        return {
            'ti_le_cuoi': ti_le_cuoi,
            'ti_le_toi_da': ti_le_toi_da,
            'nguon': nguon,
        }
    finally:
        cursor.close()
        conn.close()


def luyen_dan_theo_cong_thuc(player_id: int, dan_duoc_id: int) -> dict:
    """
    Luyện đan theo công thức đã học.
    
    Returns:
        {
            'thanh_cong': bool,
            'loi': str,
            'ten_dan': str,
            'so_vien_thanh_cong': int,
            'so_vien_that_bai': int,
            'max_vien': int,
            'exp_nhan': int,
            'ti_le': float,
            'chi_tiet_vien': [...],
        }
    """
    import random
    import json
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 1. Check đã học đan phương chưa
        cursor.execute("""
            SELECT 1 FROM player_dan_phuong_hoc
            WHERE player_id = %s AND dan_duoc_id = %s
        """, (player_id, dan_duoc_id))
        if not cursor.fetchone():
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Bạn chưa học đan phương này!'}
        
        # 2. Lấy công thức
        cursor.execute("""
            SELECT dp.linh_thao_id, dp.so_luong
            FROM tmpl_dan_phuong dp
            WHERE dp.dan_duoc_id = %s
        """, (dan_duoc_id,))
        nguyen_lieu = cursor.fetchall()
        
        if not nguyen_lieu:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Đan này chưa có công thức!'}
        
        # 3. Check nguyên liệu
        cursor.execute("""
            SELECT linh_thao_id, so_luong FROM player_linh_thao
            WHERE player_id = %s FOR UPDATE
        """, (player_id,))
        ds_co = {r['linh_thao_id']: r['so_luong'] for r in cursor.fetchall()}
        
        for nl in nguyen_lieu:
            co = ds_co.get(nl['linh_thao_id'], 0)
            if co < nl['so_luong']:
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Không đủ nguyên liệu!'}
        
        # 4. Lấy thông tin đan + phẩm cấp
        cursor.execute("""
            SELECT ten, pham_cap FROM tmpl_dan_duoc WHERE id = %s
        """, (dan_duoc_id,))
        dan = cursor.fetchone()
        
        # 5. Tính tỉ lệ
        ti_le_data = tinh_ti_le_luyen_dan(player_id, dan_duoc_id)
        if not ti_le_data:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tính được tỉ lệ!'}
        
        ti_le = ti_le_data['ti_le_cuoi']
        
        # 6. Lấy max viên theo phẩm cấp
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'luyen_dan_so_vien_max'
        """)
        row = cursor.fetchone()
        config = json.loads(row['value']) if row else {
            "1": 9, "2": 7, "3": 5, "4": 3, "5": 3
        }
        
        pham_to_num = {'Pham': '1', 'Linh': '2', 'Bao': '3', 'Tien': '4', 'Than': '5'}
        max_vien = config.get(pham_to_num.get(dan['pham_cap'], '1'), 3)
        
        # 7. Trừ nguyên liệu
        for nl in nguyen_lieu:
            cursor.execute("""
                UPDATE player_linh_thao
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND linh_thao_id = %s
            """, (nl['so_luong'], player_id, nl['linh_thao_id']))
            
            cursor.execute("""
                DELETE FROM player_linh_thao
                WHERE player_id = %s AND linh_thao_id = %s AND so_luong <= 0
            """, (player_id, nl['linh_thao_id']))
        
        # 8. Roll từng viên
        chi_tiet_vien = []
        so_thanh_cong = 0
        so_that_bai = 0
        exp_tong = 0.0
        
        # Exp range theo phẩm cấp
        exp_range = {
            'Pham': (1, 10),
            'Linh': (10, 20),
            'Bao': (30, 50),
            'Tien': (100, 300),
            'Than': (500, 1000),
        }
        exp_min, exp_max = exp_range.get(dan['pham_cap'], (1, 10))
        
        for i in range(max_vien):
            roll = random.uniform(0, 100)
            thanh_cong = roll <= ti_le
            
            if thanh_cong:
                so_thanh_cong += 1
                exp_vien = random.randint(exp_min, exp_max)
                exp_tong += exp_vien
                chi_tiet_vien.append({
                    'stt': i + 1,
                    'roll': roll,
                    'thanh_cong': True,
                    'exp': exp_vien,
                })
            else:
                so_that_bai += 1
                exp_vien = random.randint(exp_min, exp_max) * 0.05
                exp_tong += exp_vien
                chi_tiet_vien.append({
                    'stt': i + 1,
                    'roll': roll,
                    'thanh_cong': False,
                    'exp': exp_vien,
                })
        
        # 9. Cộng đan thành công
        if so_thanh_cong > 0:
            cursor.execute("""
                INSERT INTO player_dan_duoc (player_id, dan_duoc_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
            """, (player_id, dan_duoc_id, so_thanh_cong))
        
        # 10. Cộng exp nghề
        exp_tong = int(exp_tong)
        if exp_tong > 0:
            cursor.execute("""
                UPDATE player_nghe_nghiep
                SET kinh_nghiem = kinh_nghiem + %s
                WHERE player_id = %s AND nghe_nghiep_id = 1
            """, (exp_tong, player_id))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten_dan': dan['ten'],
            'pham_cap': dan['pham_cap'],
            'so_vien_thanh_cong': so_thanh_cong,
            'so_vien_that_bai': so_that_bai,
            'max_vien': max_vien,
            'exp_nhan': exp_tong,
            'ti_le': ti_le,
            'chi_tiet_vien': chi_tiet_vien,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] luyen_dan_theo_cong_thuc: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


def luyen_dan_tu_do(player_id: int, nguyen_lieu_dict: dict) -> dict:
    """
    Luyện đan tự do (tự chọn linh thảo).
    
    Args:
        nguyen_lieu_dict: {linh_thao_id: so_luong, ...}
    
    Returns:
        Như luyen_dan_theo_cong_thuc + 'hoc_dan_phuong' (bool), 'dan_phuong_moi' (list)
    """
    import random
    import json
    
    if not nguyen_lieu_dict:
        return {'thanh_cong': False, 'loi': 'Chưa chọn nguyên liệu!'}
    
    # 1. Tìm đan phương khớp
    ds_khop = find_dan_phuong_by_nguyen_lieu(nguyen_lieu_dict)
    
    if not ds_khop:
        return {
            'thanh_cong': False,
            'loi': 'Không có đan phương nào khớp với tổ hợp nguyên liệu này!'
        }
    
    # 2. Lấy đan phương đầu tiên
    dan_phuong = ds_khop[0]
    dan_duoc_id = dan_phuong['dan_duoc_id']
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 3. Check nguyên liệu
        cursor.execute("""
            SELECT linh_thao_id, so_luong FROM player_linh_thao
            WHERE player_id = %s FOR UPDATE
        """, (player_id,))
        ds_co = {r['linh_thao_id']: r['so_luong'] for r in cursor.fetchall()}
        
        for lt_id, so_luong in nguyen_lieu_dict.items():
            co = ds_co.get(lt_id, 0)
            if co < so_luong:
                conn.rollback()
                return {'thanh_cong': False, 'loi': 'Không đủ nguyên liệu!'}
        
        # 4. Tự động học đan phương (nếu chưa học)
        hoc_moi = False
        cursor.execute("""
            SELECT 1 FROM player_dan_phuong_hoc
            WHERE player_id = %s AND dan_duoc_id = %s
        """, (player_id, dan_duoc_id))
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO player_dan_phuong_hoc (player_id, dan_duoc_id)
                VALUES (%s, %s)
            """, (player_id, dan_duoc_id))
            hoc_moi = True
        
        # 5. Tính tỉ lệ
        ti_le_data = tinh_ti_le_luyen_dan(player_id, dan_duoc_id)
        ti_le = ti_le_data['ti_le_cuoi'] if ti_le_data else 50.0
        
        # 6. Max viên
        cursor.execute("""
            SELECT value FROM he_thong_config
            WHERE key_name = 'luyen_dan_so_vien_max'
        """)
        row = cursor.fetchone()
        config = json.loads(row['value']) if row else {
            "1": 9, "2": 7, "3": 5, "4": 3, "5": 3
        }
        
        pham_to_num = {'Pham': '1', 'Linh': '2', 'Bao': '3', 'Tien': '4', 'Than': '5'}
        max_vien = config.get(pham_to_num.get(dan_phuong['pham_cap'], '1'), 3)
        
        # 7. Trừ nguyên liệu
        for lt_id, so_luong in nguyen_lieu_dict.items():
            cursor.execute("""
                UPDATE player_linh_thao
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND linh_thao_id = %s
            """, (so_luong, player_id, lt_id))
            
            cursor.execute("""
                DELETE FROM player_linh_thao
                WHERE player_id = %s AND linh_thao_id = %s AND so_luong <= 0
            """, (player_id, lt_id))
        
        # 8. Roll
        chi_tiet_vien = []
        so_thanh_cong = 0
        so_that_bai = 0
        exp_tong = 0.0
        
        exp_range = {
            'Pham': (1, 10),
            'Linh': (10, 20),
            'Bao': (30, 50),
            'Tien': (100, 300),
            'Than': (500, 1000),
        }
        exp_min, exp_max = exp_range.get(dan_phuong['pham_cap'], (1, 10))
        
        for i in range(max_vien):
            roll = random.uniform(0, 100)
            thanh_cong = roll <= ti_le
            
            if thanh_cong:
                so_thanh_cong += 1
                exp_vien = random.randint(exp_min, exp_max)
                exp_tong += exp_vien
                chi_tiet_vien.append({
                    'stt': i + 1,
                    'roll': roll,
                    'thanh_cong': True,
                    'exp': exp_vien,
                })
            else:
                so_that_bai += 1
                exp_vien = random.randint(exp_min, exp_max) * 0.05
                exp_tong += exp_vien
                chi_tiet_vien.append({
                    'stt': i + 1,
                    'roll': roll,
                    'thanh_cong': False,
                    'exp': exp_vien,
                })
        
        # 9. Cộng đan
        if so_thanh_cong > 0:
            cursor.execute("""
                INSERT INTO player_dan_duoc (player_id, dan_duoc_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
            """, (player_id, dan_duoc_id, so_thanh_cong))
        
        # 10. Cộng exp nghề
        exp_tong = int(exp_tong)
        if exp_tong > 0:
            cursor.execute("""
                UPDATE player_nghe_nghiep
                SET kinh_nghiem = kinh_nghiem + %s
                WHERE player_id = %s AND nghe_nghiep_id = 1
            """, (exp_tong, player_id))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten_dan': dan_phuong['ten'],
            'pham_cap': dan_phuong['pham_cap'],
            'so_vien_thanh_cong': so_thanh_cong,
            'so_vien_that_bai': so_that_bai,
            'max_vien': max_vien,
            'exp_nhan': exp_tong,
            'ti_le': ti_le,
            'chi_tiet_vien': chi_tiet_vien,
            'hoc_moi': hoc_moi,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] luyen_dan_tu_do: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()
        
# ============================================================
# ĐIỂM DANH HÀNG NGÀY
# ============================================================

def _get_ngay_hom_nay_vn() -> str:
    """
    Lấy ngày hôm nay theo múi giờ VN (UTC+7).
    """
    from datetime import datetime, timezone, timedelta
    tz_vn = timezone(timedelta(hours=7))
    return datetime.now(tz_vn).strftime('%Y-%m-%d')


def get_daily_status(player_id: int) -> dict:
    """
    Lấy trạng thái điểm danh của player.
    
    Returns:
        {
            'da_diem_danh_hom_nay': bool,
            'ngay_cuoi': str | None,
            'streak': int,
            'co_the_diem_danh': bool,
        }
    """
    ngay_hom_nay = _get_ngay_hom_nay_vn()
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ngay_cuoi, streak
            FROM player_daily
            WHERE player_id = %s
        """, (player_id,))
        row = cursor.fetchone()
        
        if not row:
            return {
                'da_diem_danh_hom_nay': False,
                'ngay_cuoi': None,
                'streak': 0,
                'co_the_diem_danh': True,
            }
        
        ngay_cuoi_str = row['ngay_cuoi'].strftime('%Y-%m-%d') if row['ngay_cuoi'] else None
        
        return {
            'da_diem_danh_hom_nay': ngay_cuoi_str == ngay_hom_nay,
            'ngay_cuoi': ngay_cuoi_str,
            'streak': row['streak'],
            'co_the_diem_danh': ngay_cuoi_str != ngay_hom_nay,
        }
    finally:
        cursor.close()
        conn.close()


def diem_danh_hang_ngay(player_id: int) -> dict:
    """
    Điểm danh hàng ngày.
    
    Returns:
        {
            'thanh_cong': bool,
            'loi': str,
            'linh_thach_base': int,
            'bonus_streak_pct': float,
            'linh_thach_cuoi': int,
            'streak_cu': int,
            'streak_moi': int,
            'streak_tang': bool,
        }
    """
    import random
    from datetime import datetime, timedelta, timezone
    
    ngay_hom_nay = _get_ngay_hom_nay_vn()
    ngay_hom_qua = (datetime.strptime(ngay_hom_nay, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 1. Lấy trạng thái hiện tại
        cursor.execute("""
            SELECT ngay_cuoi, streak
            FROM player_daily
            WHERE player_id = %s
            FOR UPDATE
        """, (player_id,))
        row = cursor.fetchone()
        
        streak_cu = row['streak'] if row else 0
        ngay_cuoi_str = row['ngay_cuoi'].strftime('%Y-%m-%d') if row and row['ngay_cuoi'] else None
        
        # 2. Check đã điểm danh hôm nay chưa
        if ngay_cuoi_str == ngay_hom_nay:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Bạn đã điểm danh hôm nay rồi!'}
        
        # 3. Xác định streak mới
        if ngay_cuoi_str == ngay_hom_qua:
            # Điểm danh liên tiếp
            streak_moi = streak_cu + 1
            streak_tang = True
        else:
            # Mất streak (hoặc lần đầu)
            streak_moi = 1
            streak_tang = False
        
        # 4. Tính linh thạch
        base = random.randint(10, 200)
        bonus_pct = streak_moi * 1.5  # Mỗi streak +1.5%
        linh_thach_cuoi = int(base * (1 + bonus_pct / 100))
        
        # 5. Update player
        cursor.execute("""
            UPDATE player
            SET linh_thach = linh_thach + %s
            WHERE player_id = %s
        """, (linh_thach_cuoi, player_id))
        
        # 6. Update daily
        if row:
            cursor.execute("""
                UPDATE player_daily
                SET ngay_cuoi = %s,
                    streak = %s,
                    tong_linh_thach = tong_linh_thach + %s,
                    so_lan_diem_danh = so_lan_diem_danh + 1
                WHERE player_id = %s
            """, (ngay_hom_nay, streak_moi, linh_thach_cuoi, player_id))
        else:
            cursor.execute("""
                INSERT INTO player_daily
                (player_id, ngay_cuoi, streak, tong_linh_thach, so_lan_diem_danh)
                VALUES (%s, %s, %s, %s, 1)
            """, (player_id, ngay_hom_nay, streak_moi, linh_thach_cuoi))
        
        # 7. Log
        cursor.execute("""
            INSERT INTO log_daily (player_id, ngay, streak, linh_thach_nhan)
            VALUES (%s, %s, %s, %s)
        """, (player_id, ngay_hom_nay, streak_moi, linh_thach_cuoi))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'linh_thach_base': base,
            'bonus_streak_pct': bonus_pct,
            'linh_thach_cuoi': linh_thach_cuoi,
            'streak_cu': streak_cu,
            'streak_moi': streak_moi,
            'streak_tang': streak_tang,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] diem_danh_hang_ngay: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()
        
# ============================================================
# BẢNG XẾP HẠNG
# ============================================================

def _get_tuan_hien_tai() -> str:
    """
    Lấy ngày thứ 2 đầu tuần (VN).
    Returns: 'YYYY-MM-DD'
    """
    from datetime import datetime, timezone, timedelta
    tz_vn = timezone(timedelta(hours=7))
    now = datetime.now(tz_vn)
    thu_2 = now - timedelta(days=now.weekday())
    return thu_2.strftime('%Y-%m-%d')


def get_ds_bxh_active() -> list:
    """Lấy danh sách BXH đang active."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, code, ten, emoji, loai, query_sql, order_column, table_nguon, thu_tu
            FROM tmpl_bxh
            WHERE is_active = 1
            ORDER BY thu_tu, id
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_bxh_by_code(code: str) -> dict:
    """Lấy metadata BXH theo code."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM tmpl_bxh WHERE code = %s
        """, (code,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_top_bxh(loai_bxh: str, limit: int = 10) -> list:
    """
    Lấy top player theo loại BXH.
    
    - 'snapshot': chạy query_sql từ tmpl_bxh.
    - 'seasonal': query từ player_bxh_tuan.
    """
    meta = get_bxh_by_code(loai_bxh)
    if not meta:
        return []
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if meta['loai'] == 'snapshot':
            sql = meta['query_sql'].replace('{limit}', str(limit))
            cursor.execute(sql)
            return cursor.fetchall()
        
        elif meta['loai'] == 'seasonal':
            tuan = _get_tuan_hien_tai()
            table = meta['table_nguon']
            
            cursor.execute(f"""
                SELECT 
                    p.player_id, p.discord_id, p.ten_nhan_vat,
                    t.gia_tri AS gia_tri_sort,
                    FORMAT(t.gia_tri, 0) AS gia_tri_hien_thi
                FROM {table} t
                JOIN player p ON p.player_id = t.player_id
                WHERE t.loai_bxh = %s AND t.tuan = %s
                ORDER BY t.gia_tri DESC
                LIMIT %s
            """, (loai_bxh, tuan, limit))
            return cursor.fetchall()
        
        return []
    finally:
        cursor.close()
        conn.close()


def check_top1_lien_tiep(player_id: int, loai_bxh: str, tuan: str) -> bool:
    """Check player có phải top 1 tuần trước không."""
    from datetime import datetime, timedelta
    tuan_truoc = (datetime.strptime(tuan, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 1 FROM log_bxh_thuong
            WHERE player_id = %s 
              AND loai_bxh = %s 
              AND tuan = %s
              AND hang = 1
            LIMIT 1
        """, (player_id, loai_bxh, tuan_truoc))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


def tinh_phan_thuong_bxh(hang: int) -> dict:
    """Tính phần thưởng dựa vào hạng."""
    import random
    import json
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT key_name, value FROM he_thong_config
            WHERE key_name LIKE 'bxh_thuong_%'
        """)
        configs = {r['key_name']: json.loads(r['value']) for r in cursor.fetchall()}
        
        lt_min = configs.get('bxh_thuong_linh_thach_min', 2000)
        lt_max = configs.get('bxh_thuong_linh_thach_max', 5000)
        exp_min = configs.get('bxh_thuong_exp_min', 1000)
        exp_max = configs.get('bxh_thuong_exp_max', 1500)
        tv_min = configs.get('bxh_thuong_tu_vi_min', 1000)
        tv_max = configs.get('bxh_thuong_tu_vi_max', 1500)
        
        he_so_h3 = float(configs.get('bxh_thuong_hang3_he_so', 1.5))
        he_so_h2 = float(configs.get('bxh_thuong_hang2_he_so', 2.0))
        he_so_h1 = float(configs.get('bxh_thuong_hang1_he_so', 3.0))
        
        if hang == 1:
            he_so = he_so_h1
            dan_phuong_count = 0
            linh_dich = True
        elif hang == 2:
            he_so = he_so_h2
            dan_phuong_count = 3
            linh_dich = False
        elif hang == 3:
            he_so = he_so_h3
            dan_phuong_count = 1
            linh_dich = False
        else:
            he_so = 1.0
            dan_phuong_count = 0
            linh_dich = False
        
        return {
            'linh_thach': int(random.randint(lt_min, lt_max) * he_so),
            'exp': int(random.randint(exp_min, exp_max) * he_so),
            'tu_vi': int(random.randint(tv_min, tv_max) * he_so),
            'he_so': he_so,
            'dan_phuong_count': dan_phuong_count,
            'linh_dich': linh_dich,
        }
    finally:
        cursor.close()
        conn.close()


def trao_thuong_bxh(player_id: int, loai_bxh: str, hang: int, tuan: str,
                     la_top1_lien_tiep: bool = False) -> dict:
    """Trao thưởng cho 1 player."""
    import random
    import json
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        thuong = tinh_phan_thuong_bxh(hang)
        
        if hang == 1 and la_top1_lien_tiep:
            thuong['linh_dich'] = False
        
        # Cộng linh thạch + exp + tu vi
        cursor.execute("""
            UPDATE player
            SET linh_thach = linh_thach + %s,
                exp = exp + %s,
                tu_vi = tu_vi + %s
            WHERE player_id = %s
        """, (thuong['linh_thach'], thuong['exp'], thuong['tu_vi'], player_id))
        
        # Đan phương
        dan_phuong_nhan = []
        if thuong['dan_phuong_count'] > 0:
            for _ in range(thuong['dan_phuong_count']):
                cursor.execute("""
                    SELECT id, ten FROM tmpl_dan_duoc
                    WHERE pham_cap IN ('Pham', 'Linh', 'Bao')
                    ORDER BY RAND()
                    LIMIT 1
                """)
                dan = cursor.fetchone()
                if dan:
                    item_code = f'dan_phuong_{dan["id"]}'
                    metadata = json.dumps(
                        {'dan_duoc_id': dan['id'], 'ten': dan['ten']},
                        ensure_ascii=False
                    )
                    cursor.execute("""
                        SELECT id FROM misc_tui_do
                        WHERE player_id = %s AND item_code = %s LIMIT 1
                    """, (player_id, item_code))
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute("""
                            UPDATE misc_tui_do SET so_luong = so_luong + 1 WHERE id = %s
                        """, (existing['id'],))
                    else:
                        cursor.execute("""
                            INSERT INTO misc_tui_do (player_id, item_code, so_luong, metadata)
                            VALUES (%s, %s, 1, %s)
                        """, (player_id, item_code, metadata))
                    
                    dan_phuong_nhan.append({'dan_duoc_id': dan['id'], 'ten': dan['ten']})
        
        # Linh Dịch
        dao_cu_nhan = None
        if thuong['linh_dich']:
            cursor.execute("""
                SELECT id FROM tmpl_dao_cu WHERE code = 'tang_tinh_khiet_nho' LIMIT 1
            """)
            dc = cursor.fetchone()
            if dc:
                cursor.execute("""
                    INSERT INTO player_dao_cu (player_id, dao_cu_id, so_luong)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE so_luong = so_luong + 1
                """, (player_id, dc['id']))
                dao_cu_nhan = dc['id']
        
        # Log
        cursor.execute("""
            INSERT INTO log_bxh_thuong 
            (player_id, loai_bxh, hang, linh_thach, exp, tu_vi,
             dan_phuong_nhan, dao_cu_nhan, tuan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            player_id, loai_bxh, hang,
            thuong['linh_thach'], thuong['exp'], thuong['tu_vi'],
            json.dumps(dan_phuong_nhan, ensure_ascii=False) if dan_phuong_nhan else None,
            dao_cu_nhan, tuan
        ))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'thuong': thuong,
            'dan_phuong_nhan': dan_phuong_nhan,
            'dao_cu_nhan': dao_cu_nhan,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] trao_thuong_bxh: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


def trao_thuong_tat_ca_bxh() -> dict:
    """Trao thưởng cho tất cả BXH đang active."""
    tuan = _get_tuan_hien_tai()
    ds_bxh = get_ds_bxh_active()
    
    chi_tiet = {}
    for bxh in ds_bxh:
        code = bxh['code']
        chi_tiet[code] = []
        
        top = get_top_bxh(code, limit=10)
        
        for i, player in enumerate(top):
            hang = i + 1
            player_id = player['player_id']
            
            la_lien_tiep = False
            if hang == 1:
                la_lien_tiep = check_top1_lien_tiep(player_id, code, tuan)
            
            ket_qua = trao_thuong_bxh(player_id, code, hang, tuan, la_lien_tiep)
            
            if ket_qua['thanh_cong']:
                chi_tiet[code].append({
                    'player_id': player_id,
                    'discord_id': player['discord_id'],
                    'ten': player['ten_nhan_vat'],
                    'hang': hang,
                    'thuong': ket_qua['thuong'],
                    'dan_phuong_nhan': ket_qua['dan_phuong_nhan'],
                    'la_lien_tiep': la_lien_tiep,
                })
    
    return {
        'thanh_cong': True,
        'loi': None,
        'tuan': tuan,
        'chi_tiet': chi_tiet,
    }


def tang_stat_bxh_tuan(player_id: int, loai_bxh: str, gia_tri: int):
    """
    Tăng stat cho seasonal BXH (dùng khi player làm hành động).
    """
    tuan = _get_tuan_hien_tai()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO player_bxh_tuan (player_id, loai_bxh, tuan, gia_tri)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE gia_tri = gia_tri + VALUES(gia_tri)
        """, (player_id, loai_bxh, tuan, gia_tri))
        conn.commit()
    finally:
        cursor.close()
        conn.close()