"""Tính toán stat cho player."""

import random
from database.connection import get_connection


def tinh_exp_can_tang(canh_gioi_id: int, tang: int) -> int:
    """Exp cần để lên tầng tiếp theo."""
    cg = _get_canh_gioi(canh_gioi_id)
    exp = cg['exp_tang_1'] * (cg['he_so_tang'] ** (tang - 1))
    return int(exp)


def tinh_exp_can_dot_pha(canh_gioi_id: int) -> int:
    """Exp cần để đột phá cảnh giới."""
    cg = _get_canh_gioi(canh_gioi_id)
    exp_tang_cuoi = cg['exp_tang_1'] * (cg['he_so_tang'] ** (cg['so_tang'] - 1))
    return int(exp_tang_cuoi * cg['he_so_dot_pha'])


def tinh_exp_tuluyen(canh_gioi_id: int, tang: int) -> tuple:
    """Tính exp + tu vi nhận được khi tu luyện."""
    exp_can = tinh_exp_can_tang(canh_gioi_id, tang)
    ti_le = random.uniform(0.01, 0.03)
    exp_nhan = max(1, int(exp_can * ti_le))
    return exp_nhan, exp_nhan


def format_exp(player) -> str:
    """
    Format exp hiển thị.
    
    Examples:
        '3/100'       -- tầng thường
        '1500/5000'   -- gần đầy
        '500/1929 (Đột phá)' -- tầng cuối
    """
    if player.tang_canh_gioi < player.so_tang:
        # Tầng thường
        exp_can = tinh_exp_can_tang(player.canh_gioi_id, player.tang_canh_gioi)
        return f'{player.exp:,}/{exp_can:,}'
    else:
        # Tầng cuối → cần đột phá
        exp_can = tinh_exp_can_dot_pha(player.canh_gioi_id)
        return f'{player.exp:,}/{exp_can:,} *(Đột phá)*'


def _get_canh_gioi(canh_gioi_id: int):
    """Lấy thông tin cảnh giới từ DB."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM canh_gioi WHERE id = %s", (canh_gioi_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
        
def tinh_ti_le_dot_pha_chi_tiet(player_id: int) -> dict:
    """
    Tính tỉ lệ đột phá cảnh giới với chi tiết nguồn bonus.
    
    Returns:
        {
            'ti_le_cuoi': float,
            'nguon': [
                {'ten': 'Cơ bản', 'gia_tri': 50.0, 'emoji': '🎯'},
                {'ten': 'Linh căn (3 active)', 'gia_tri': 5.0, 'emoji': '🌟'},
                ...
            ],
            'ti_le_toi_da': float,
        }
    """
    from database.connection import get_connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Lấy thông tin player + cảnh giới
        cursor.execute("""
            SELECT p.*, cg.ti_le_dot_pha_co_ban, cg.ti_le_dot_pha_toi_da,
                   cg.ten AS canh_gioi_ten, cg.cap_bac
            FROM player p
            JOIN canh_gioi cg ON cg.id = p.canh_gioi_id
            WHERE p.player_id = %s
        """, (player_id,))
        p = cursor.fetchone()
        
        nguon = []
        
        # 2. Cơ bản từ cảnh giới
        ti_le_co_ban = float(p['ti_le_dot_pha_co_ban'])
        nguon.append({
            'ten': 'Cơ bản',
            'gia_tri': ti_le_co_ban,
            'emoji': '🎯'
        })
        
        # 3. Bonus từ linh căn active
        cursor.execute("""
            SELECT 
                COUNT(*) AS so_lc,
                COALESCE(SUM(lc.ti_le_dot_pha_bonus), 0) AS tong_bonus
            FROM player_linh_can plc
            JOIN tmpl_linh_can lc ON lc.id = plc.linh_can_id
            WHERE plc.player_id = %s AND plc.is_active = 1
        """, (player_id,))
        lc = cursor.fetchone()
        bonus_linh_can = float(lc['tong_bonus'] or 0)
        if bonus_linh_can > 0:
            nguon.append({
                'ten': f'Linh căn ({lc["so_lc"]} active)',
                'gia_tri': bonus_linh_can,
                'emoji': '🌟'
            })
        
        # 4. Bonus từ tâm cảnh (1 điểm = 0.1%)
        bonus_tam_canh = float(p['tam_canh']) * 0.1
        if bonus_tam_canh != 0:
            nguon.append({
                'ten': f'Tâm cảnh ({p["tam_canh"]})',
                'gia_tri': bonus_tam_canh,
                'emoji': '🧘'
            })
        
        # 5. Bonus từ khí vận (1 điểm = 0.05%)
        bonus_khi_van = float(p['khi_van']) * 0.05
        if bonus_khi_van != 0:
            nguon.append({
                'ten': f'Khí vận ({p["khi_van"]})',
                'gia_tri': bonus_khi_van,
                'emoji': '🍀'
            })
        
        # 6. Bonus từ thất bại liên tiếp
        bonus_that_bai = float(p['so_du_lan_dot_pha']) * 5.0
        if bonus_that_bai > 0:
            nguon.append({
                'ten': f'Thất bại {p["so_du_lan_dot_pha"]} lần',
                'gia_tri': bonus_that_bai,
                'emoji': '💪'
            })
        
        # 7. Bonus từ đan dược/buff (từ player_buff)
        cursor.execute("""
            SELECT COALESCE(SUM(
                CAST(JSON_EXTRACT(effect, '$.ti_le_dot_pha') AS DECIMAL(10,2))
            ), 0) AS bonus
            FROM player_buff
            WHERE player_id = %s AND het_han_luc > NOW()
        """, (player_id,))
        r = cursor.fetchone()
        bonus_dan = float(r['bonus'] or 0)
        if bonus_dan > 0:
            nguon.append({
                'ten': 'Đan dược/Buff',
                'gia_tri': bonus_dan,
                'emoji': '💊'
            })
        
        # 8. Tổng
        ti_le_cuoi = sum(n['gia_tri'] for n in nguon)
        ti_le_toi_da = float(p['ti_le_dot_pha_toi_da'])
        
        # Clamp
        ti_le_cuoi = max(1.0, min(ti_le_cuoi, ti_le_toi_da))
        
        return {
            'ti_le_cuoi': ti_le_cuoi,
            'nguon': nguon,
            'ti_le_toi_da': ti_le_toi_da,
            'canh_gioi_ten': p['canh_gioi_ten'],
            'cap_bac': p['cap_bac'],
        }
    finally:
        cursor.close()
        conn.close()