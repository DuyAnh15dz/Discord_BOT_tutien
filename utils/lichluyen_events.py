"""Định nghĩa các sự kiện lịch luyện."""

# Mapping code -> thông tin sự kiện
SU_KIEN = {
    'linh_thach': {
        'ten': 'Nhận Linh Thạch',
        'emoji': '💰',
        'loai': 'reward',
        'base_min': 30,
        'base_max': 200,
        'he_so_canh_gioi': 2.0,
    },
    'exp_tuvi': {
        'ten': 'Ngộ Đạo',
        'emoji': '🔮',
        'loai': 'reward',
        'base_min': 10,
        'base_max': 20,
        'he_so_canh_gioi': 2.0,
    },
    'linh_thao': {
        'ten': 'Nhặt Linh Thảo',
        'emoji': '🌿',
        'loai': 'reward',
    },
    'khoang_thach': {
        'ten': 'Khai Thác Khoáng Thạch',
        'emoji': '⛰',
        'loai': 'reward',
    },
    'dan_phuong': {
        'ten': 'Phát Hiện Đan Phương',
        'emoji': '📜',
        'loai': 'reward',
    },
    'ky_ngo': {
        'ten': 'Đốn Ngộ',
        'emoji': '✨',
        'loai': 'special',
        # Config sẽ lấy từ DB: linh_can_ky_ngo_tinh_khiet_min/max
    },
    'sap_bay': {
        'ten': 'Sập Bẫy',
        'emoji': '💥',
        'loai': 'debuff',
        'hp_mat_pct_min': 5,
        'hp_mat_pct_max': 15,
    },
    'yeu_thu': {
        'ten': 'Chiến Đấu Yêu Thú',
        'emoji': '🐺',
        'loai': 'combat',
        'hp_mat_pct_min': 3,
        'hp_mat_pct_max': 8,
    },
    'ta_tu': {
        'ten': 'Bị Tà Tu Chặn Cướp',
        'emoji': '💀',
        'loai': 'combat',
        'linh_thach_mat_pct_min': 5,
        'linh_thach_mat_pct_max': 15,
    },
    'thuong_nhan': {
        'ten': 'Gặp Thương Nhân Thần Bí',
        'emoji': '🧙',
        'loai': 'special',
    },
    'binh_yen': {
        'ten': 'Bình Yên',
        'emoji': '😌',
        'loai': 'nothing',
    },
}


def tinh_gia_tri_reward(su_kien_code: str, cap_bac: int) -> tuple:
    """
    Tính giá trị reward dựa vào cảnh giới.
    
    Args:
        su_kien_code: Mã sự kiện
        cap_bac: Cấp bậc cảnh giới (1 = Luyện Khí)
    
    Returns:
        (min, max)
    """
    sk = SU_KIEN.get(su_kien_code, {})
    base_min = sk.get('base_min', 0)
    base_max = sk.get('base_max', 0)
    he_so = sk.get('he_so_canh_gioi', 1.0)
    
    # cap_bac: 1 = Luyện Khí, 2 = Trúc Cơ, ...
    # multiplier = he_so^(cap_bac - 1)
    multiplier = he_so ** (cap_bac - 1)
    
    return int(base_min * multiplier), int(base_max * multiplier)