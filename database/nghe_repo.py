"""Repository cho hệ thống nghề: Pháp khí, Trận pháp, Bùa chú."""

import json
import random
from datetime import datetime, timedelta
from database.connection import get_connection

import time

# ============================================================
# CACHE — giảm query DB cho dữ liệu tĩnh
# ============================================================
_CACHE = {}
_CACHE_TTL = 300  # 5 phút


def _get_cache(key):
    """Lấy cache nếu còn hiệu lực."""
    if key in _CACHE:
        data, timestamp = _CACHE[key]
        if time.time() - timestamp < _CACHE_TTL:
            return data
    return None


def _set_cache(key, data):
    """Lưu cache."""
    _CACHE[key] = (data, time.time())


def _clear_cache(key=None):
    """Xóa cache (dùng khi update DB)."""
    if key:
        _CACHE.pop(key, None)
    else:
        _CACHE.clear()
# ============================================================
# PHÁP KHÍ
# ============================================================

def get_ds_phap_khi_template() -> list:
    """Lấy template pháp khí. Cache 5 phút."""
    cached = _get_cache('ds_phap_khi')
    if cached:
        return cached
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT pk.*, kt.ten AS khoang_thach_ten
            FROM tmpl_phap_khi pk
            LEFT JOIN tmpl_khoang_thach kt ON kt.id = pk.khoang_thach_id
            ORDER BY 
                FIELD(pk.loai, 'VuKhi','Ao','Non','Giay','Nhan'),
                FIELD(pk.pham_cap, 'Pham','Linh','Bao','Tien','Than')
        """)
        items = cursor.fetchall()
        for item in items:
            if isinstance(item.get('effect_moi_cap'), str):
                item['effect_moi_cap'] = json.loads(item['effect_moi_cap'])
        
        _set_cache('ds_phap_khi', items)
        return items
    finally:
        cursor.close()
        conn.close()
        

def get_phap_khi_cong_thuc(phap_khi_id: int) -> dict:
    """Lấy công thức luyện pháp khí."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT pk.id, pk.ten, pk.loai, pk.he, pk.pham_cap,
                   pk.yeu_cau_nghe_cap, pk.cap_toi_da,
                   pk.effect_moi_cap, pk.mo_ta
            FROM tmpl_phap_khi pk
            WHERE pk.id = %s
        """, (phap_khi_id,))
        pk = cursor.fetchone()
        if not pk:
            return None
        
        cursor.execute("""
            SELECT ct.khoang_thach_id, ct.so_luong,
                   ct.ti_le_thanh_cong_max,
                   kt.ten, kt.pham_cap, kt.he
            FROM tmpl_phap_khi_cong_thuc ct
            JOIN tmpl_khoang_thach kt ON kt.id = ct.khoang_thach_id
            WHERE ct.phap_khi_id = %s
        """, (phap_khi_id,))
        nguyen_lieu = cursor.fetchall()
        
        if isinstance(pk.get('effect_moi_cap'), str):
            pk['effect_moi_cap'] = json.loads(pk['effect_moi_cap'])
        
        return {
            'phap_khi': pk,
            'nguyen_lieu': nguyen_lieu,
        }
    finally:
        cursor.close()
        conn.close()


def check_du_khoang_thach(player_id: int, nguyen_lieu: list) -> dict:
    """Check player có đủ khoáng thạch không."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT khoang_thach_id, so_luong FROM player_khoang_thach
            WHERE player_id = %s
        """, (player_id,))
        ds_co = {r['khoang_thach_id']: r['so_luong'] for r in cursor.fetchall()}
        
        thieu = []
        for nl in nguyen_lieu:
            co = ds_co.get(nl['khoang_thach_id'], 0)
            if co < nl['so_luong']:
                thieu.append({
                    'ten': nl['ten'],
                    'can': nl['so_luong'],
                    'co': co,
                    'thieu': nl['so_luong'] - co,
                })
        
        return {
            'du': len(thieu) == 0,
            'ds_co': ds_co,
            'thieu': thieu,
        }
    finally:
        cursor.close()
        conn.close()


def tinh_ti_le_luyen_khi(player_id: int, phap_khi_id: int) -> dict:
    """Tính tỉ lệ thành công luyện khí."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT pk.yeu_cau_nghe_cap,
                   ct.ti_le_thanh_cong_max,
                   p.tam_canh, p.khi_van
            FROM tmpl_phap_khi pk
            JOIN tmpl_phap_khi_cong_thuc ct ON ct.phap_khi_id = pk.id
            JOIN player p ON p.player_id = %s
            WHERE pk.id = %s
            LIMIT 1
        """, (player_id, phap_khi_id))
        info = cursor.fetchone()
        if not info:
            return None
        
        nguon = []
        ti_le_co_ban = 15.0
        nguon.append({'ten': 'Cơ bản', 'gia_tri': ti_le_co_ban, 'emoji': '🎯'})
        
        cursor.execute("""
            SELECT cap_do FROM player_nghe_nghiep
            WHERE player_id = %s AND nghe_nghiep_id = 2
        """, (player_id,))
        row = cursor.fetchone()
        cap_nghe = row['cap_do'] if row else 0
        yeu_cau = info['yeu_cau_nghe_cap'] or 1
        
        if cap_nghe >= yeu_cau:
            bonus_cap = 5.0 * (cap_nghe - yeu_cau)
        else:
            bonus_cap = -5.0 * (yeu_cau - cap_nghe)
        
        if bonus_cap != 0:
            nguon.append({
                'ten': f'Cấp nghề ({cap_nghe}/{yeu_cau})',
                'gia_tri': bonus_cap, 'emoji': '🔨'
            })
        
        bonus_tam_canh = (info['tam_canh'] or 0) * 0.1
        if bonus_tam_canh > 0:
            nguon.append({
                'ten': f'Tâm cảnh ({info["tam_canh"]})',
                'gia_tri': bonus_tam_canh, 'emoji': '🧘'
            })
        
        bonus_khi_van = (info['khi_van'] or 0) * 0.2
        if bonus_khi_van > 0:
            nguon.append({
                'ten': f'Khí vận ({info["khi_van"]})',
                'gia_tri': bonus_khi_van, 'emoji': '🍀'
            })
        
        ti_le_cuoi = sum(n['gia_tri'] for n in nguon)
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


def luyen_khi(player_id: int, phap_khi_id: int) -> dict:
    """Luyện pháp khí."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cong_thuc = get_phap_khi_cong_thuc(phap_khi_id)
        if not cong_thuc:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy công thức!'}
        
        check = check_du_khoang_thach(player_id, cong_thuc['nguyen_lieu'])
        if not check['du']:
            conn.rollback()
            thieu_lines = [f"{t['ten']}: thiếu {t['thieu']}" for t in check['thieu']]
            return {
                'thanh_cong': False,
                'loi': 'Thiếu khoáng thạch: ' + ', '.join(thieu_lines)
            }
        
        ti_le_data = tinh_ti_le_luyen_khi(player_id, phap_khi_id)
        ti_le = ti_le_data['ti_le_cuoi']
        
        # Trừ khoáng thạch
        for nl in cong_thuc['nguyen_lieu']:
            cursor.execute("""
                UPDATE player_khoang_thach
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND khoang_thach_id = %s
            """, (nl['so_luong'], player_id, nl['khoang_thach_id']))
            
            cursor.execute("""
                DELETE FROM player_khoang_thach
                WHERE player_id = %s AND khoang_thach_id = %s AND so_luong <= 0
            """, (player_id, nl['khoang_thach_id']))
        
        # Roll
        roll = random.uniform(0, 100)
        thanh_cong = roll <= ti_le
        
        # Exp nghề
        pham_cap = cong_thuc['phap_khi']['pham_cap']
        exp_range = {
            'Pham': (20, 50), 'Linh': (50, 100),
            'Bao': (150, 250), 'Tien': (500, 800),
            'Than': (2000, 3000),
        }
        exp_min, exp_max = exp_range.get(pham_cap, (20, 50))
        exp_nhan = random.randint(exp_min, exp_max)
        
        cursor.execute("""
            UPDATE player_nghe_nghiep
            SET kinh_nghiem = kinh_nghiem + %s
            WHERE player_id = %s AND nghe_nghiep_id = 2
        """, (exp_nhan, player_id))
        
        # Tạo pháp khí
        phap_khi_moi_id = None
        if thanh_cong:
            cursor.execute("""
                INSERT INTO player_phap_khi 
                (player_id, phap_khi_id, cap_do, dang_trang_bi)
                VALUES (%s, %s, 1, 0)
            """, (player_id, phap_khi_id))
            phap_khi_moi_id = cursor.lastrowid
        
        # Log
        cursor.execute("""
            INSERT INTO log_luyen_khi 
            (player_id, phap_khi_id, ket_qua, thanh_cong, exp_nhan)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            player_id, phap_khi_id,
            json.dumps({'roll': roll, 'ti_le': ti_le}, ensure_ascii=False),
            1 if thanh_cong else 0,
            exp_nhan
        ))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'luyen_thanh_cong': thanh_cong,
            'roll': roll,
            'ti_le': ti_le,
            'exp_nhan': exp_nhan,
            'ten_phap_khi': cong_thuc['phap_khi']['ten'],
            'phap_khi_moi_id': phap_khi_moi_id,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] luyen_khi: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


def get_ds_phap_khi_cua_player(player_id: int) -> list:
    """Lấy danh sách pháp khí player sở hữu."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ppk.id, ppk.phap_khi_id, ppk.cap_do,
                   ppk.dang_trang_bi, ppk.slot, ppk.ngay_tao,
                   pk.ten, pk.loai, pk.he, pk.pham_cap,
                   pk.cap_toi_da, pk.effect_moi_cap, pk.mo_ta
            FROM player_phap_khi ppk
            JOIN tmpl_phap_khi pk ON pk.id = ppk.phap_khi_id
            WHERE ppk.player_id = %s
            ORDER BY 
                ppk.dang_trang_bi DESC,
                FIELD(pk.loai, 'VuKhi','Ao','Non','Giay','Nhan'),
                FIELD(pk.pham_cap, 'Than','Tien','Bao','Linh','Pham')
        """, (player_id,))
        items = cursor.fetchall()
        for item in items:
            if isinstance(item.get('effect_moi_cap'), str):
                item['effect_moi_cap'] = json.loads(item['effect_moi_cap'])
        return items
    finally:
        cursor.close()
        conn.close()


def trang_bi_phap_khi(player_id: int, player_phap_khi_id: int) -> dict:
    """Trang bị pháp khí."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cursor.execute("""
            SELECT ppk.*, pk.loai, pk.ten
            FROM player_phap_khi ppk
            JOIN tmpl_phap_khi pk ON pk.id = ppk.phap_khi_id
            WHERE ppk.id = %s AND ppk.player_id = %s
            FOR UPDATE
        """, (player_phap_khi_id, player_id))
        pk = cursor.fetchone()
        
        if not pk:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy pháp khí!'}
        
        if pk['dang_trang_bi']:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Pháp khí đang được trang bị!'}
        
        slot = pk['loai']
        
        cursor.execute("""
            UPDATE player_phap_khi
            SET dang_trang_bi = 0, slot = NULL
            WHERE player_id = %s AND slot = %s
        """, (player_id, slot))
        
        cursor.execute("""
            UPDATE player_phap_khi
            SET dang_trang_bi = 1, slot = %s
            WHERE id = %s
        """, (slot, player_phap_khi_id))
        
        conn.commit()
        return {
            'thanh_cong': True,
            'loi': None,
            'ten': pk['ten'],
            'slot': slot,
        }
    except Exception as e:
        conn.rollback()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


def thao_phap_khi(player_id: int, player_phap_khi_id: int) -> dict:
    """Tháo pháp khí."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE player_phap_khi
            SET dang_trang_bi = 0, slot = NULL
            WHERE id = %s AND player_id = %s
        """, (player_phap_khi_id, player_id))
        conn.commit()
        return {'thanh_cong': cursor.rowcount > 0}
    finally:
        cursor.close()
        conn.close()


def get_bonus_phap_khi(player_id: int) -> dict:
    """Tính tổng bonus từ pháp khí đang trang bị."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT pk.effect_moi_cap, ppk.cap_do
            FROM player_phap_khi ppk
            JOIN tmpl_phap_khi pk ON pk.id = ppk.phap_khi_id
            WHERE ppk.player_id = %s AND ppk.dang_trang_bi = 1
        """, (player_id,))
        
        bonus = {}
        for row in cursor.fetchall():
            effect = row['effect_moi_cap']
            if isinstance(effect, str):
                effect = json.loads(effect)
            cap = row['cap_do']
            
            for stat_code, gia_tri in effect.items():
                try:
                    bonus[stat_code] = bonus.get(stat_code, 0.0) + float(gia_tri) * cap
                except (ValueError, TypeError):
                    pass
        
        return bonus
    finally:
        cursor.close()
        conn.close()


def nang_cap_phap_khi(player_id: int, player_phap_khi_id: int) -> dict:
    """Nâng cấp pháp khí."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cursor.execute("""
            SELECT ppk.*, pk.cap_toi_da, pk.ten, pk.khoang_thach_id
            FROM player_phap_khi ppk
            JOIN tmpl_phap_khi pk ON pk.id = ppk.phap_khi_id
            WHERE ppk.id = %s AND ppk.player_id = %s
            FOR UPDATE
        """, (player_phap_khi_id, player_id))
        pk = cursor.fetchone()
        
        if not pk:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy pháp khí!'}
        
        if pk['cap_do'] >= pk['cap_toi_da']:
            conn.rollback()
            return {'thanh_cong': False, 'loi': f'Pháp khí đã max cấp {pk["cap_toi_da"]}!'}
        
        so_luong_can = pk['cap_do'] * 5
        
        cursor.execute("""
            SELECT so_luong FROM player_khoang_thach
            WHERE player_id = %s AND khoang_thach_id = %s
            FOR UPDATE
        """, (player_id, pk['khoang_thach_id']))
        row = cursor.fetchone()
        
        if not row or row['so_luong'] < so_luong_can:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Cần {so_luong_can} khoáng thạch, có {row["so_luong"] if row else 0}'
            }
        
        cursor.execute("""
            UPDATE player_khoang_thach
            SET so_luong = so_luong - %s
            WHERE player_id = %s AND khoang_thach_id = %s
        """, (so_luong_can, player_id, pk['khoang_thach_id']))
        
        cursor.execute("""
            DELETE FROM player_khoang_thach
            WHERE player_id = %s AND khoang_thach_id = %s AND so_luong <= 0
        """, (player_id, pk['khoang_thach_id']))
        
        ti_le = max(30.0, 90.0 - pk['cap_do'] * 10)
        roll = random.uniform(0, 100)
        thanh_cong = roll <= ti_le
        
        if thanh_cong:
            cursor.execute("""
                UPDATE player_phap_khi
                SET cap_do = cap_do + 1
                WHERE id = %s
            """, (player_phap_khi_id,))
            cap_moi = pk['cap_do'] + 1
        else:
            cap_moi = pk['cap_do']
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'nang_cap_thanh_cong': thanh_cong,
            'ten': pk['ten'],
            'cap_cu': pk['cap_do'],
            'cap_moi': cap_moi,
            'ti_le': ti_le,
            'roll': roll,
            'khoang_thach_da_dung': so_luong_can,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] nang_cap_phap_khi: {e}')
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


# ============================================================
# QUAN HỆ HỆ
# ============================================================

def lay_quan_he_he(he_nguon: str, he_dich: str) -> str:
    """Lấy quan hệ giữa 2 hệ."""
    if not he_nguon or not he_dich:
        return 'TrungTinh'
    
    if he_nguon == he_dich:
        return 'CungHe'
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT quan_he FROM tmpl_he_quan_he
            WHERE he_nguon = %s AND he_dich = %s
        """, (he_nguon, he_dich))
        row = cursor.fetchone()
        return row['quan_he'] if row else 'TrungTinh'
    finally:
        cursor.close()
        conn.close()


def tinh_he_so_tran_nhan(he_tran: str, he_nhan: str) -> dict:
    """Tính hệ số thời gian dựa vào quan hệ hệ trận ↔ hệ nhãn."""
    if not he_tran or not he_nhan:
        return {
            'he_so': 1.0,
            'quan_he': 'TrungTinh',
            'mo_ta': 'Trận không có hệ hoặc nhãn vạn năng',
        }
    
    if he_tran == he_nhan:
        return {
            'he_so': 1.0,
            'quan_he': 'CungHe',
            'mo_ta': f'✅ Đúng hệ {he_tran} (+0%)',
        }
    
    quan_he = lay_quan_he_he(he_nhan, he_tran)
    
    if quan_he == 'TuongSinh':
        return {
            'he_so': 0.75,
            'quan_he': 'TuongSinh',
            'mo_ta': f'⚠️ Nhãn {he_nhan} tương sinh trận {he_tran} (-25%)',
        }
    elif quan_he == 'TuongKhac':
        return {
            'he_so': 0.80,
            'quan_he': 'TuongKhac',
            'mo_ta': f'❌ Nhãn {he_nhan} tương khắc trận {he_tran} (-20%)',
        }
    else:
        return {
            'he_so': 0.50,
            'quan_he': 'TrungTinh',
            'mo_ta': f'➖ Nhãn {he_nhan} trung tính với trận {he_tran} (-50%)',
        }


# ============================================================
# TRẬN PHÁP
# ============================================================

def get_ds_tran_phap_full() -> list:
    """Lấy danh sách trận pháp. Cache 5 phút."""
    cached = _get_cache('ds_tran_phap')
    if cached:
        return cached
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT tp.*,
                   co.ten AS co_ten, co.pham_cap AS co_pc,
                   ban.ten AS ban_ten, ban.pham_cap AS ban_pc,
                   nhan.ten AS nhan_ten, nhan.he AS nhan_he,
                   nhan.pham_cap AS nhan_pc
            FROM tmpl_tran_phap tp
            LEFT JOIN tmpl_tran_cu co ON co.id = tp.tran_co_id
            LEFT JOIN tmpl_tran_cu ban ON ban.id = tp.tran_ban_id
            LEFT JOIN tmpl_tran_cu nhan ON nhan.id = tp.tran_nhan_id
            ORDER BY FIELD(tp.pham_cap, 'Pham','Linh','Bao','Tien','Than')
        """)
        items = cursor.fetchall()
        for item in items:
            if isinstance(item.get('effect'), str):
                item['effect'] = json.loads(item['effect'])
        
        _set_cache('ds_tran_phap', items)
        return items
    finally:
        cursor.close()
        conn.close()


def check_du_tran_cu(player_id: int, tran_phap_id: int) -> dict:
    """Check đủ trận cờ/bàn/nhãn."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT tp.*,
                   co.ten AS co_ten,
                   ban.ten AS ban_ten,
                   nhan.ten AS nhan_ten
            FROM tmpl_tran_phap tp
            LEFT JOIN tmpl_tran_cu co ON co.id = tp.tran_co_id
            LEFT JOIN tmpl_tran_cu ban ON ban.id = tp.tran_ban_id
            LEFT JOIN tmpl_tran_cu nhan ON nhan.id = tp.tran_nhan_id
            WHERE tp.id = %s
        """, (tran_phap_id,))
        tp = cursor.fetchone()
        
        if not tp:
            return None
        
        items_can = []
        if tp['tran_co_id']:
            items_can.append({
                'loai': 'Trận cờ',
                'tran_cu_id': tp['tran_co_id'],
                'ten': tp['co_ten'],
                'can': tp['tran_co_so_luong'],
            })
        if tp['tran_ban_id']:
            items_can.append({
                'loai': 'Trận bàn',
                'tran_cu_id': tp['tran_ban_id'],
                'ten': tp['ban_ten'],
                'can': tp['tran_ban_so_luong'],
            })
        if tp['tran_nhan_id']:
            items_can.append({
                'loai': 'Trận nhãn',
                'tran_cu_id': tp['tran_nhan_id'],
                'ten': tp['nhan_ten'],
                'can': tp['tran_nhan_so_luong'],
            })
        
        ket_qua = []
        du_tat_ca = True
        for item in items_can:
            cursor.execute("""
                SELECT so_luong FROM player_tran_cu
                WHERE player_id = %s AND tran_cu_id = %s
            """, (player_id, item['tran_cu_id']))
            row = cursor.fetchone()
            co = row['so_luong'] if row else 0
            
            du = co >= item['can']
            if not du:
                du_tat_ca = False
            
            ket_qua.append({**item, 'co': co, 'du': du})
        
        return {
            'du': du_tat_ca,
            'tran_phap': tp,
            'items': ket_qua,
        }
    finally:
        cursor.close()
        conn.close()


def bay_tran_voi_quiz_v3(
    player_id: int,
    tran_phap_id: int,
    so_cau_dung: int,
    tong_cau: int,
    ket_qua_quiz: list,
) -> dict:
    """Bày trận sau quiz."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        check = check_du_tran_cu(player_id, tran_phap_id)
        if not check:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy trận pháp!'}
        
        if not check['du']:
            conn.rollback()
            lines = [f"{it['ten']}: {it['co']}/{it['can']}" 
                     for it in check['items'] if not it['du']]
            return {
                'thanh_cong': False,
                'loi': 'Thiếu đạo cụ: ' + ', '.join(lines),
            }
        
        tp = check['tran_phap']
        
        cursor.execute("""
            SELECT cap_do FROM player_nghe_nghiep
            WHERE player_id = %s AND nghe_nghiep_id = 3
        """, (player_id,))
        row = cursor.fetchone()
        cap_nghe = row['cap_do'] if row else 1
        
        if cap_nghe < tp['yeu_cau_nghe_cap']:
            conn.rollback()
            return {
                'thanh_cong': False,
                'loi': f'Cần cấp nghề {tp["yeu_cau_nghe_cap"]}, bạn có {cap_nghe}!',
            }
        
        he_tran = tp['he']
        he_nhan = None
        if tp['tran_nhan_id']:
            cursor.execute("SELECT he FROM tmpl_tran_cu WHERE id = %s", 
                           (tp['tran_nhan_id'],))
            row = cursor.fetchone()
            he_nhan = row['he'] if row else None
        
        he_so_nhan_data = tinh_he_so_tran_nhan(he_tran, he_nhan)
        he_so_nhan = he_so_nhan_data['he_so']
        
        ti_le_co_ban = 50.0 + (cap_nghe - tp['yeu_cau_nghe_cap']) * 3
        bonus_quiz = so_cau_dung * float(tp['bonus_moi_cau_dung'])
        ti_le_cuoi = min(95.0, ti_le_co_ban + bonus_quiz)
        
        thoi_gian_co_ban = tp['thoi_gian_hieu_luc']
        bonus_quiz_tg = so_cau_dung * float(tp['bonus_thoi_gian_moi_cau']) / 100.0
        thoi_gian_truoc_nhan = int(thoi_gian_co_ban * (1 + bonus_quiz_tg))
        thoi_gian_cuoi = int(thoi_gian_truoc_nhan * he_so_nhan)
        
        for it in check['items']:
            cursor.execute("""
                UPDATE player_tran_cu
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND tran_cu_id = %s
            """, (it['can'], player_id, it['tran_cu_id']))
            
            cursor.execute("""
                DELETE FROM player_tran_cu
                WHERE player_id = %s AND tran_cu_id = %s AND so_luong <= 0
            """, (player_id, it['tran_cu_id']))
        
        roll = random.uniform(0, 100)
        thanh_cong = roll <= ti_le_cuoi
        
        exp_nhan = tp['exp_base'] + so_cau_dung * 50
        
        cursor.execute("""
            UPDATE player_nghe_nghiep
            SET kinh_nghiem = kinh_nghiem + %s
            WHERE player_id = %s AND nghe_nghiep_id = 3
        """, (exp_nhan, player_id))
        
        if thanh_cong:
            effect = tp['effect']
            if isinstance(effect, str):
                effect = json.loads(effect)
            
            het_han = datetime.now() + timedelta(seconds=thoi_gian_cuoi)
            
            cursor.execute("""
                INSERT INTO player_tran_phap_active
                (player_id, tran_phap_id, effect, het_han_luc)
                VALUES (%s, %s, %s, %s)
            """, (player_id, tran_phap_id, 
                  json.dumps(effect, ensure_ascii=False), het_han))
        
        cursor.execute("""
            INSERT INTO log_tran_phap_quiz
            (player_id, tran_phap_id, so_cau_dung, tong_cau, ket_qua)
            VALUES (%s, %s, %s, %s, %s)
        """, (player_id, tran_phap_id, so_cau_dung, tong_cau,
              json.dumps(ket_qua_quiz, ensure_ascii=False)))
        
        cursor.execute("""
            INSERT INTO log_bay_tran 
            (player_id, tran_phap_id, thanh_cong)
            VALUES (%s, %s, %s)
        """, (player_id, tran_phap_id, 1 if thanh_cong else 0))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'bay_thanh_cong': thanh_cong,
            'ten': tp['ten'],
            'ti_le_cuoi': ti_le_cuoi,
            'thoi_gian_cuoi': thoi_gian_cuoi,
            'thoi_gian_truoc_nhan': thoi_gian_truoc_nhan,
            'he_so_nhan': he_so_nhan,
            'quan_he_nhan': he_so_nhan_data,
            'roll': roll,
            'exp_nhan': exp_nhan,
            'so_cau_dung': so_cau_dung,
            'tong_cau': tong_cau,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] bay_tran_voi_quiz_v3: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


def get_tran_dang_bay(player_id: int) -> dict:
    """Lấy trận pháp đang active."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT pta.*,
                   tp.ten, tp.loai, tp.he, tp.pham_cap,
                   tp.thoi_gian_hieu_luc, tp.mo_ta
            FROM player_tran_phap_active pta
            JOIN tmpl_tran_phap tp ON tp.id = pta.tran_phap_id
            WHERE pta.player_id = %s AND pta.het_han_luc > NOW()
        """, (player_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        if isinstance(row.get('effect'), str):
            row['effect'] = json.loads(row['effect'])
        
        return row
    finally:
        cursor.close()
        conn.close()


def thu_tran(player_id: int) -> dict:
    """Thu trận pháp."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM player_tran_phap_active
            WHERE player_id = %s
        """, (player_id,))
        conn.commit()
        return {'thanh_cong': cursor.rowcount > 0}
    finally:
        cursor.close()
        conn.close()


def get_bonus_tran_phap(player_id: int) -> dict:
    """Bonus từ trận pháp active."""
    tran = get_tran_dang_bay(player_id)
    if not tran:
        return {}
    return tran.get('effect', {})


# ============================================================
# BÙA CHÚ
# ============================================================

def get_ds_bua_chu_full() -> list:
    """Lấy bùa chú. Cache 5 phút."""
    cached = _get_cache('ds_bua_chu')
    if cached:
        return cached
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT bc.*,
                   myt.ten AS mau_ten,
                   myt.he AS mau_he,
                   ld.ten AS linh_dich_ten,
                   ld.he AS linh_dich_he,
                   ld.bonus_ti_le AS linh_dich_bonus
            FROM tmpl_bua_chu bc
            LEFT JOIN tmpl_mau_yeu_thu myt ON myt.id = bc.mau_yeu_thu_id
            LEFT JOIN tmpl_linh_dich ld ON ld.id = bc.linh_dich_id
            ORDER BY 
                FIELD(bc.loai, 'TanCong','PhongThu','HoTro','KhongChe'),
                FIELD(bc.pham_cap, 'Pham','Linh','Bao','Tien','Than')
        """)
        items = cursor.fetchall()
        for item in items:
            if isinstance(item.get('effect'), str):
                item['effect'] = json.loads(item['effect'])
        
        _set_cache('ds_bua_chu', items)
        return items
    finally:
        cursor.close()
        conn.close()


def check_du_nguyen_lieu_ve_bua(player_id: int, bua_chu_id: int) -> dict:
    """Check đủ nguyên liệu vẽ bùa."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT bc.*, myt.ten AS mau_ten
            FROM tmpl_bua_chu bc
            LEFT JOIN tmpl_mau_yeu_thu myt ON myt.id = bc.mau_yeu_thu_id
            WHERE bc.id = %s
        """, (bua_chu_id,))
        bc = cursor.fetchone()
        
        if not bc:
            return None
        
        cursor.execute("""
            SELECT mp_hien_tai FROM player_stat WHERE player_id = %s
        """, (player_id,))
        row = cursor.fetchone()
        mp_co = row['mp_hien_tai'] if row else 0
        
        mau_info = None
        if bc['mau_yeu_thu_id']:
            cursor.execute("""
                SELECT so_luong FROM player_mau_yeu_thu
                WHERE player_id = %s AND mau_yeu_thu_id = %s
            """, (player_id, bc['mau_yeu_thu_id']))
            row = cursor.fetchone()
            mau_co = row['so_luong'] if row else 0
            
            mau_info = {
                'id': bc['mau_yeu_thu_id'],
                'ten': bc['mau_ten'],
                'can': bc['mau_yeu_thu_so_luong'],
                'co': mau_co,
            }
        
        linh_dich_info = None
        if bc['linh_dich_id']:
            cursor.execute("""
                SELECT so_luong FROM player_linh_dich
                WHERE player_id = %s AND linh_dich_id = %s
            """, (player_id, bc['linh_dich_id']))
            row = cursor.fetchone()
            ld_co = row['so_luong'] if row else 0
            
            cursor.execute("SELECT ten FROM tmpl_linh_dich WHERE id = %s",
                           (bc['linh_dich_id'],))
            ld_row = cursor.fetchone()
            
            linh_dich_info = {
                'id': bc['linh_dich_id'],
                'ten': ld_row['ten'] if ld_row else '?',
                'can': bc['linh_dich_so_luong'],
                'co': ld_co,
            }
        
        du_mp = mp_co >= bc['mp_cost']
        du_mau = mau_info is None or mau_info['co'] >= mau_info['can']
        du_ld = linh_dich_info is None or linh_dich_info['co'] >= linh_dich_info['can']
        
        return {
            'du': du_mp and du_mau and du_ld,
            'bua_chu': bc,
            'mp_can': bc['mp_cost'],
            'mp_co': mp_co,
            'mau': mau_info,
            'linh_dich': linh_dich_info,
        }
    finally:
        cursor.close()
        conn.close()


def ve_bua_10_la_v3(player_id: int, bua_chu_id: int) -> dict:
    """Vẽ 10 lá bùa cùng lúc."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        check = check_du_nguyen_lieu_ve_bua(player_id, bua_chu_id)
        if not check:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không tìm thấy bùa chú!'}
        
        if not check['du']:
            conn.rollback()
            errors = []
            if check['mp_co'] < check['mp_can']:
                errors.append(f'MP: {check["mp_co"]}/{check["mp_can"]}')
            if check['mau'] and check['mau']['co'] < check['mau']['can']:
                errors.append(f'{check["mau"]["ten"]}: {check["mau"]["co"]}/{check["mau"]["can"]}')
            if check['linh_dich'] and check['linh_dich']['co'] < check['linh_dich']['can']:
                errors.append(f'{check["linh_dich"]["ten"]}: {check["linh_dich"]["co"]}/{check["linh_dich"]["can"]}')
            
            return {
                'thanh_cong': False,
                'loi': 'Thiếu nguyên liệu: ' + ', '.join(errors),
            }
        
        bc = check['bua_chu']
        
        cursor.execute("""
            SELECT cap_do FROM player_nghe_nghiep
            WHERE player_id = %s AND nghe_nghiep_id = 4
        """, (player_id,))
        row = cursor.fetchone()
        cap_nghe = row['cap_do'] if row else 1
        
        yeu_cau = bc['yeu_cau_nghe_cap'] or 1
        ti_le_co_ban = 60.0 + (cap_nghe - yeu_cau) * 3
        
        cursor.execute("""
            SELECT do_thuan_thuc FROM player_bua_chu_thuan_thuc
            WHERE player_id = %s AND bua_chu_id = %s
        """, (player_id, bua_chu_id))
        row = cursor.fetchone()
        do_thuan_thuc = row['do_thuan_thuc'] if row else 0
        bonus_thuan_thuc = do_thuan_thuc * 0.2
        
        bonus_linh_dich = 0.0
        if check['linh_dich']:
            cursor.execute("""
                SELECT bonus_ti_le FROM tmpl_linh_dich WHERE id = %s
            """, (check['linh_dich']['id'],))
            ld = cursor.fetchone()
            if ld:
                bonus_linh_dich = float(ld['bonus_ti_le'])
        
        ti_le = min(95.0, ti_le_co_ban + bonus_linh_dich + bonus_thuan_thuc)
        
        cursor.execute("""
            UPDATE player_stat
            SET mp_hien_tai = mp_hien_tai - %s
            WHERE player_id = %s
        """, (bc['mp_cost'], player_id))
        
        if check['mau']:
            cursor.execute("""
                UPDATE player_mau_yeu_thu
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND mau_yeu_thu_id = %s
            """, (check['mau']['can'], player_id, check['mau']['id']))
            
            cursor.execute("""
                DELETE FROM player_mau_yeu_thu
                WHERE player_id = %s AND mau_yeu_thu_id = %s AND so_luong <= 0
            """, (player_id, check['mau']['id']))
        
        if check['linh_dich']:
            cursor.execute("""
                UPDATE player_linh_dich
                SET so_luong = so_luong - %s
                WHERE player_id = %s AND linh_dich_id = %s
            """, (check['linh_dich']['can'], player_id, check['linh_dich']['id']))
            
            cursor.execute("""
                DELETE FROM player_linh_dich
                WHERE player_id = %s AND linh_dich_id = %s AND so_luong <= 0
            """, (player_id, check['linh_dich']['id']))
        
        exp_range = {
            'Pham': (1, 10), 'Linh': (5, 20),
            'Bao': (20, 50), 'Tien': (100, 300),
            'Than': (500, 1000),
        }
        exp_min, exp_max = exp_range.get(bc['pham_cap'], (1, 10))
        
        SO_LA = 10
        chi_tiet_la = []
        so_thanh_cong = 0
        tong_exp = 0.0
        
        for i in range(SO_LA):
            roll = random.uniform(0, 100)
            thanh_cong = roll <= ti_le
            
            if thanh_cong:
                exp_la = random.randint(exp_min, exp_max)
                so_thanh_cong += 1
            else:
                exp_la = random.randint(exp_min, exp_max) * 0.1
            
            tong_exp += exp_la
            chi_tiet_la.append({
                'stt': i + 1,
                'roll': roll,
                'thanh_cong': thanh_cong,
                'exp': exp_la,
            })
        
        tong_exp = int(tong_exp)
        
        if so_thanh_cong > 0:
            cursor.execute("""
                INSERT INTO player_bua_chu (player_id, bua_chu_id, so_luong)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
            """, (player_id, bua_chu_id, so_thanh_cong))
        
        cursor.execute("""
            UPDATE player_nghe_nghiep
            SET kinh_nghiem = kinh_nghiem + %s
            WHERE player_id = %s AND nghe_nghiep_id = 4
        """, (tong_exp, player_id))
        
        cursor.execute("""
            INSERT INTO player_bua_chu_thuan_thuc 
            (player_id, bua_chu_id, so_lan_ve)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE 
                so_lan_ve = so_lan_ve + 1
        """, (player_id, bua_chu_id))
        
        cursor.execute("""
            INSERT INTO log_ve_bua 
            (player_id, bua_chu_id, so_luong_thanh_cong, exp_nhan)
            VALUES (%s, %s, %s, %s)
        """, (player_id, bua_chu_id, so_thanh_cong, tong_exp))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten': bc['ten'],
            'ti_le': ti_le,
            'so_thanh_cong': so_thanh_cong,
            'so_that_bai': SO_LA - so_thanh_cong,
            'chi_tiet_la': chi_tiet_la,
            'exp_nhan': tong_exp,
            'mp_da_dung': bc['mp_cost'],
            'do_thuan_thuc': do_thuan_thuc,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] ve_bua_10_la_v3: {e}')
        import traceback
        traceback.print_exc()
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()


def get_ds_bua_chu_cua_player(player_id: int) -> list:
    """Lấy danh sách bùa chú player sở hữu."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT bc.id, bc.code, bc.ten, bc.loai,
                   bc.he, bc.pham_cap, bc.effect, bc.mo_ta,
                   pbc.so_luong
            FROM player_bua_chu pbc
            JOIN tmpl_bua_chu bc ON bc.id = pbc.bua_chu_id
            WHERE pbc.player_id = %s AND pbc.so_luong > 0
            ORDER BY 
                FIELD(bc.loai, 'TanCong','PhongThu','HoTro','KhongChe'),
                FIELD(bc.pham_cap, 'Pham','Linh','Bao','Tien','Than')
        """, (player_id,))
        items = cursor.fetchall()
        for item in items:
            if isinstance(item.get('effect'), str):
                item['effect'] = json.loads(item['effect'])
        return items
    finally:
        cursor.close()
        conn.close()


def dung_bua_chu(player_id: int, bua_chu_id: int) -> dict:
    """Dùng bùa chú (ngoài combat)."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cursor.execute("""
            SELECT so_luong FROM player_bua_chu
            WHERE player_id = %s AND bua_chu_id = %s
            FOR UPDATE
        """, (player_id, bua_chu_id))
        row = cursor.fetchone()
        
        if not row or row['so_luong'] < 1:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Không có bùa chú này!'}
        
        cursor.execute("SELECT * FROM tmpl_bua_chu WHERE id = %s", (bua_chu_id,))
        bc = cursor.fetchone()
        
        if not bc:
            conn.rollback()
            return {'thanh_cong': False, 'loi': 'Bùa chú không tồn tại!'}
        
        effect = bc['effect']
        if isinstance(effect, str):
            effect = json.loads(effect)
        
        loai = bc['loai']
        ket_qua = {}
        
        if loai == 'HoTro':
            hp_hoi = effect.get('hp_hoi', 0)
            mp_hoi = effect.get('mp_hoi', 0)
            
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
        
        elif loai == 'PhongThu':
            shield = effect.get('shield', 0)
            turns = effect.get('turns', 3)
            
            if shield > 0:
                buff_code = f'bua_shield_{bua_chu_id}'
                het_han = datetime.now() + timedelta(minutes=turns * 5)
                buff_effect = json.dumps({'shield': shield}, ensure_ascii=False)
                
                cursor.execute("""
                    INSERT INTO player_buff 
                    (player_id, buff_code, effect, het_han_luc, nguon_goc)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        het_han_luc = VALUES(het_han_luc),
                        effect = VALUES(effect)
                """, (player_id, buff_code, buff_effect, het_han, bc['ten']))
                ket_qua['shield'] = shield
                ket_qua['turns'] = turns
        
        elif loai in ('TanCong', 'KhongChe'):
            ket_qua['combat_effect'] = effect
            ket_qua['loai'] = loai
        
        cursor.execute("""
            UPDATE player_bua_chu
            SET so_luong = so_luong - 1
            WHERE player_id = %s AND bua_chu_id = %s
        """, (player_id, bua_chu_id))
        
        cursor.execute("""
            DELETE FROM player_bua_chu
            WHERE player_id = %s AND bua_chu_id = %s AND so_luong <= 0
        """, (player_id, bua_chu_id))
        
        conn.commit()
        
        return {
            'thanh_cong': True,
            'loi': None,
            'ten': bc['ten'],
            'loai': loai,
            'ket_qua': ket_qua,
        }
    except Exception as e:
        conn.rollback()
        print(f'[ERROR] dung_bua_chu: {e}')
        return {'thanh_cong': False, 'loi': f'Lỗi: {e}'}
    finally:
        cursor.close()
        conn.close()