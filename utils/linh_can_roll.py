"""Roll linh căn cho player."""

import random
import json
from database.connection import get_connection


# Nhóm hệ
NGU_HANH = ['Kim', 'Moc', 'Thuy', 'Hoa', 'Tho']
DI_HE = ['Loi', 'Bang', 'Phong', 'Duong', 'Am']


def lay_config(key_name: str):
    """Lấy config từ DB."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT value FROM he_thong_config WHERE key_name = %s
        """, (key_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f'Config `{key_name}` không tồn tại!')
        return json.loads(row['value'])
    finally:
        cursor.close()
        conn.close()


def roll_so_luong_linh_can() -> int:
    """Roll số lượng linh căn (1-5)."""
    ti_le_dict = lay_config('linh_can_roll_so_luong')
    so_luong_list = [int(k) for k in ti_le_dict.keys()]
    ti_le_list = [float(v) for v in ti_le_dict.values()]
    return random.choices(so_luong_list, weights=ti_le_list, k=1)[0]


def roll_nhom_he() -> str:
    """Roll nhóm hệ: NguHanh hoặc DiHe."""
    ti_le_dict = lay_config('linh_can_roll_nhom_he')
    nhom_list = list(ti_le_dict.keys())
    ti_le_list = [float(v) for v in ti_le_dict.values()]
    return random.choices(nhom_list, weights=ti_le_list, k=1)[0]


def roll_pham_cap() -> str:
    """Roll phẩm cấp: Ha/Trung/Thuong/Cuc/Tien."""
    ti_le_dict = lay_config('linh_can_roll_pham_cap')
    pham_list = list(ti_le_dict.keys())
    ti_le_list = [float(v) for v in ti_le_dict.values()]
    return random.choices(pham_list, weights=ti_le_list, k=1)[0]


def roll_1_linh_can(exclude_hes: list = None) -> int:
    """
    Roll 1 linh căn duy nhất, KHÔNG TRÙNG HỆ với các linh căn đã có.

    Flow:
        1. Roll nhóm hệ (85% ngũ hành / 15% dị hệ)
        2. Loại bỏ các hệ đã có trong exclude_hes
        3. Roll hệ cụ thể trong nhóm (sau khi loại)
        4. Roll phẩm cấp
        5. Tìm linh_can_id tương ứng trong DB
        6. Nếu trùng hệ (đã loại ở bước 2) → không cần check nữa

    Args:
        exclude_hes: Danh sách hệ đã có (VD: ['Kim', 'Moc'])

    Returns:
        (linh_can_id, he) — trả về cả hệ để caller track
    """
    if exclude_hes is None:
        exclude_hes = []

    for attempt in range(30):  # Tăng lên 30 vì có thể trùng hệ nhiều
        # 1. Roll nhóm hệ
        nhom = roll_nhom_he()
        ds_he = NGU_HANH if nhom == 'NguHanh' else DI_HE

        # 2. Loại bỏ hệ đã có
        ds_he_con_lai = [h for h in ds_he if h not in exclude_hes]

        # Nếu nhóm này hết hệ → thử nhóm khác
        if not ds_he_con_lai:
            nhom_khac = 'DiHe' if nhom == 'NguHanh' else 'NguHanh'
            ds_he_khac = NGU_HANH if nhom_khac == 'NguHanh' else DI_HE
            ds_he_con_lai = [h for h in ds_he_khac if h not in exclude_hes]

        # Nếu cả 2 nhóm đều hết hệ → raise
        if not ds_he_con_lai:
            raise ValueError(
                f'Đã roll hết tất cả hệ! Không thể roll thêm. '
                f'Đã có: {exclude_hes}'
            )

        # 3. Roll hệ cụ thể trong nhóm còn lại
        he = random.choice(ds_he_con_lai)

        # 4. Roll phẩm cấp
        pham_cap = roll_pham_cap()

        # 5. Tìm linh_can_id trong DB
        lc_id = tim_linh_can_id(he, pham_cap)

        if lc_id:
            return lc_id, he

    # Fallback (hiếm khi xảy ra)
    raise ValueError(f'Không roll được linh căn sau 30 lần thử!')


def tim_linh_can_id(he: str, pham_cap: str) -> int:
    """Tìm linh_can_id từ (he, pham_cap)."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id FROM tmpl_linh_can
            WHERE he = %s AND pham_cap = %s
            LIMIT 1
        """, (he, pham_cap))
        row = cursor.fetchone()
        return row['id'] if row else None
    finally:
        cursor.close()
        conn.close()


def roll_nhieu_linh_can(so_luong: int) -> list:
    """
    Roll nhiều linh căn, KHÔNG TRÙNG HỆ.

    Returns:
        List các linh_can_id (giữ nguyên interface cũ)
    """
    result_ids = []
    result_hes = []

    for _ in range(so_luong):
        lc_id, he = roll_1_linh_can(exclude_hes=result_hes)
        result_ids.append(lc_id)
        result_hes.append(he)

    return result_ids