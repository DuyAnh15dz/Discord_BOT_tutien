"""Bộ câu hỏi trắc nghiệm cho Trận Pháp Sư."""

import random


# ============================================================
# CÂU HỎI THEO CHỦ ĐỀ
# ============================================================

NGU_HANH_CAU_HOI = [
    {
        'cau_hoi': 'Trong Ngũ Hành, hệ nào khắc hệ Thủy?',
        'dap_an': ['Kim', 'Mộc', 'Thổ', 'Hỏa'],
        'dung': 'C',
        'chu_de': 'NguHanh',
    },
    {
        'cau_hoi': 'Ngũ Hành tương sinh: Hỏa sinh ra hệ nào?',
        'dap_an': ['Kim', 'Thủy', 'Mộc', 'Thổ'],
        'dung': 'D',
        'chu_de': 'NguHanh',
    },
    {
        'cau_hoi': 'Hệ nào được sinh bởi Kim?',
        'dap_an': ['Mộc', 'Thủy', 'Hỏa', 'Thổ'],
        'dung': 'B',
        'chu_de': 'NguHanh',
    },
    {
        'cau_hoi': 'Trong Ngũ Hành, hệ nào khắc hệ Kim?',
        'dap_an': ['Mộc', 'Thủy', 'Hỏa', 'Thổ'],
        'dung': 'C',
        'chu_de': 'NguHanh',
    },
    {
        'cau_hoi': 'Mộc sinh ra hệ nào?',
        'dap_an': ['Kim', 'Hỏa', 'Thủy', 'Thổ'],
        'dung': 'B',
        'chu_de': 'NguHanh',
    },
    {
        'cau_hoi': 'Hệ nào tương sinh với Thổ?',
        'dap_an': ['Kim', 'Mộc', 'Thủy', 'Hỏa'],
        'dung': 'A',
        'chu_de': 'NguHanh',
    },
    {
        'cau_hoi': 'Trong Ngũ Hành, hướng nào thuộc hành Mộc?',
        'dap_an': ['Đông', 'Tây', 'Nam', 'Bắc'],
        'dung': 'A',
        'chu_de': 'NguHanh',
    },
    {
        'cau_hoi': 'Hướng Bắc thuộc hành nào trong Ngũ Hành?',
        'dap_an': ['Kim', 'Mộc', 'Thủy', 'Hỏa'],
        'dung': 'C',
        'chu_de': 'NguHanh',
    },
]

AM_DUONG_CAU_HOI = [
    {
        'cau_hoi': 'Âm Dương trong tự nhiên, Dương tượng trưng cho gì?',
        'dap_an': ['Mặt Trăng', 'Mặt Trời', 'Ban đêm', 'Mùa đông'],
        'dung': 'B',
        'chu_de': 'AmDuong',
    },
    {
        'cau_hoi': 'Số nào được coi là số cực Dương trong Kinh Dịch?',
        'dap_an': ['2', '4', '6', '9'],
        'dung': 'D',
        'chu_de': 'AmDuong',
    },
    {
        'cau_hoi': 'Theo Âm Dương, ban đêm thuộc về?',
        'dap_an': ['Dương', 'Âm', 'Cả hai', 'Không thuộc'],
        'dung': 'B',
        'chu_de': 'AmDuong',
    },
    {
        'cau_hoi': 'Trong cơ thể người, phần nào thuộc Dương?',
        'dap_an': ['Lưng', 'Bụng', 'Ngực', 'Chân'],
        'dung': 'A',
        'chu_de': 'AmDuong',
    },
    {
        'cau_hoi': 'Thái Cực sinh ra gì?',
        'dap_an': ['Tam Tài', 'Tứ Tượng', 'Lưỡng Nghi', 'Bát Quái'],
        'dung': 'C',
        'chu_de': 'AmDuong',
    },
    {
        'cau_hoi': 'Trong Âm Dương, mùa hạ thuộc về?',
        'dap_an': ['Âm', 'Dương', 'Chuyển tiếp', 'Trung tính'],
        'dung': 'B',
        'chu_de': 'AmDuong',
    },
]

THIEN_DIA_CAU_HOI = [
    {
        'cau_hoi': 'Bát Quái gồm bao nhiêu quẻ?',
        'dap_an': ['4', '6', '8', '64'],
        'dung': 'C',
        'chu_de': 'ThienDia',
    },
    {
        'cau_hoi': 'Bát Quái được tạo ra từ ai trong truyền thuyết?',
        'dap_an': ['Phục Hy', 'Thần Nông', 'Hoàng Đế', 'Lão Tử'],
        'dung': 'A',
        'chu_de': 'ThienDia',
    },
    {
        'cau_hoi': 'Quẻ Càn trong Bát Quái tượng trưng cho gì?',
        'dap_an': ['Đất', 'Trời', 'Nước', 'Lửa'],
        'dung': 'B',
        'chu_de': 'ThienDia',
    },
    {
        'cau_hoi': 'Quẻ Khôn trong Bát Quái tượng trưng cho gì?',
        'dap_an': ['Trời', 'Đất', 'Gió', 'Sấm'],
        'dung': 'B',
        'chu_de': 'ThienDia',
    },
    {
        'cau_hoi': 'Tam Tài trong triết học phương Đông gồm?',
        'dap_an': ['Thiên - Địa - Nhân', 'Âm - Dương - Khí', 
                   'Kim - Mộc - Thủy', 'Đông - Tây - Nam'],
        'dung': 'A',
        'chu_de': 'ThienDia',
    },
    {
        'cau_hoi': 'Tứ Tượng được sinh ra từ?',
        'dap_an': ['Thái Cực', 'Bát Quái', 'Lưỡng Nghi', 'Ngũ Hành'],
        'dung': 'C',
        'chu_de': 'ThienDia',
    },
    {
        'cau_hoi': '64 quẻ trong Kinh Dịch được tạo từ?',
        'dap_an': ['Bát Quái', 'Lục Thập Tứ', 'Tam Tài', 'Ngũ Hành'],
        'dung': 'A',
        'chu_de': 'ThienDia',
    },
]

TRAN_PHAP_CAU_HOI = [
    {
        'cau_hoi': 'Trận nhãn trong trận pháp có tác dụng gì?',
        'dap_an': ['Trang trí', 'Tập trung năng lượng', 'Ghi chép', 'Chống đỡ'],
        'dung': 'B',
        'chu_de': 'TranPhap',
    },
    {
        'cau_hoi': 'Trận pháp cần tối thiểu bao nhiêu yếu tố để vận hành?',
        'dap_an': ['1', '2', '3', '4'],
        'dung': 'C',
        'chu_de': 'TranPhap',
    },
    {
        'cau_hoi': 'Trận pháp bị phá khi nào?',
        'dap_an': ['Trận nhãn vỡ', 'Trận cờ gãy', 'Hết thời gian', 'Cả 3 đáp án'],
        'dung': 'D',
        'chu_de': 'TranPhap',
    },
    {
        'cau_hoi': 'Loại trận pháp nào dùng để phòng thủ?',
        'dap_an': ['Công kích trận', 'Phòng ngự trận', 'Mê huyễn trận', 'Cấm chế trận'],
        'dung': 'B',
        'chu_de': 'TranPhap',
    },
]


ALL_CAU_HOI = (
    NGU_HANH_CAU_HOI
    + AM_DUONG_CAU_HOI
    + THIEN_DIA_CAU_HOI
    + TRAN_PHAP_CAU_HOI
)


# ============================================================
# HÀM HELPER
# ============================================================

def lay_cau_hoi_random(so_luong: int = 3) -> list:
    """
    Lấy N câu hỏi ngẫu nhiên.
    
    Args:
        so_luong: Số câu hỏi cần lấy
    
    Returns:
        List các dict câu hỏi (đã đánh id)
    """
    if so_luong > len(ALL_CAU_HOI):
        so_luong = len(ALL_CAU_HOI)
    
    ds_chon = random.sample(ALL_CAU_HOI, so_luong)
    
    # Đánh id
    for i, cau in enumerate(ds_chon):
        cau['id'] = i + 1
    
    return ds_chon


def kiem_tra_dap_an(cau_hoi: dict, dap_an_chon: str) -> bool:
    """
    Kiểm tra đáp án.
    
    Args:
        cau_hoi: dict câu hỏi có key 'dung'
        dap_an_chon: 'A' | 'B' | 'C' | 'D'
    
    Returns:
        True nếu đúng
    """
    return dap_an_chon.upper() == cau_hoi['dung'].upper()