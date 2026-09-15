import discord
from discord import app_commands
from discord.ext import commands

from database.connection import get_connection
from database.player_repo import (
    get_player_full_info,
    get_ti_gia_tien_ngoc,
    exchange_linh_thach_sang_tien_ngoc,
    get_shop_items,
    ban_item,
    ban_cong_phap,
    mua_item,
    get_player_linh_thao,
    get_player_khoang_thach,
    get_player_cong_phap_trong_tui,
)


# ============================================================
# MAPPING HIỂN THỊ
# ============================================================
PHAM_CAP_EMOJI = {
    'Pham': '🟤', 'Linh': '🟢', 'Bao': '🔵', 'Tien': '🟣', 'Than': '🟡',
}

PHAM_CAP_TEN = {
    'Pham': 'Phàm phẩm', 'Linh': 'Linh phẩm', 'Bao': 'Bảo phẩm',
    'Tien': 'Tiên phẩm', 'Than': 'Thần phẩm',
}

HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}

HE_TEN = {
    'Kim': 'Kim', 'Moc': 'Mộc', 'Thuy': 'Thủy', 'Hoa': 'Hỏa', 'Tho': 'Thổ',
    'Loi': 'Lôi', 'Bang': 'Băng', 'Phong': 'Phong', 'Duong': 'Dương', 'Am': 'Âm',
}

LOAI_SHOP = {
    'DanDuoc': '💊 Đan dược',
    'DaoCu': '🎁 Đạo cụ',
    'LinhThao': '🌿 Linh thảo',
    'KhoangThach': '⛰ Khoáng thạch',
    'CongPhap': '📖 Công pháp',   # ⭐ MỚI
}

GIAI_CAP_CONG_PHAP = {
    'Hoang': '📗 Hoàng giai',
    'Huyen': '📘 Huyền giai',
    'Dia': '📙 Địa giai',
    'Thien': '📕 Thiên giai',
}

LOAI_CONG_PHAP = {
    'NguHanh': 'Ngũ Hành',
    'DiHe': 'Dị Hệ',
    'LuyenThe': 'Luyện Thể',
    'LuyenHon': 'Luyện Hồn',
}

LOAI_DAN = {
    'HoiPhuc': 'Hồi phục', 'DotPha': 'Đột phá',
    'TangTuVi': 'Tăng tu vi', 'Buff': 'Buff', 'Doc': 'Độc',
}

LOAI_DAO_CU = {
    'DotPhaLinhCan': 'Đột phá linh căn',
    'TangTinhKhiet': 'Tăng tinh khiết',
    'Khac': 'Khác',
}

LOAI_KHOANG_THACH = {
    'LuyenKhi': 'Luyện khí', 'VePhu': 'Vẽ phù', 'CaHai': 'Cả hai',
}

ITEMS_PER_PAGE = 5


# ============================================================
# HELPER: FORMAT EFFECT CHI TIẾT
# ============================================================
def format_effect(item: dict) -> str:
    """Format effect chi tiết của item."""
    effect = item.get('dan_effect') or item.get('dao_cu_effect') or {}
    
    if not effect:
        # Đan đột phá
        if item.get('ti_le_dot_pha_bonus') and item['ti_le_dot_pha_bonus'] > 0:
            thoi_gian = item.get('thoi_gian_hieu_luc') or 0
            gio = thoi_gian // 3600
            phut = (thoi_gian % 3600) // 60
            thoi_gian_str = f'{gio}h' if gio > 0 else f'{phut}p'
            return f'   `📊 +{item["ti_le_dot_pha_bonus"]}% tỉ lệ đột phá / {thoi_gian_str}`'
        return ''
    
    key_map = {
        'hp': '❤️ HP', 'mp': '💙 MP',
        'hp_per_turn': '❤️ HP/lượt', 'mp_per_turn': '💙 MP/lượt',
        'turns': '🔄 Số lượt',
        'atk': '🗡️ ATK', 'def': '🛡️ DEF',
        'matk': '✨ MATK', 'mdef': '🔮 MDEF',
        'atk_pct': '🗡️ ATK %', 'def_pct': '🛡️ DEF %',
        'matk_pct': '✨ MATK %', 'mdef_pct': '🔮 MDEF %',
        'hp_max': '❤️ HP Max', 'hp_max_pct': '❤️ HP Max %',
        'mp_max_pct': '💙 MP Max %',
        'tu_vi': '🔮 Tu vi',
        'tinh_khiet': '💧 Tinh khiết',
        'poison_dmg': '☠️ Sát thương độc',
        'ignore_def': '🚫 Bỏ qua phòng ngự',
    }
    
    lines = []
    for key, value in effect.items():
        label = key_map.get(key, key)
        if isinstance(value, (int, float)):
            if 'pct' in key:
                value_str = f'{value}%'
            else:
                value_str = f'{value:,}'
        elif isinstance(value, dict):
            continue  # Bỏ nested dict
        else:
            value_str = str(value)
        lines.append(f'   `{label}: {value_str}`')
    
    return '\n'.join(lines)


# ============================================================
# HELPER: BUILD FIELD CHO ITEM
# ============================================================
def build_item_field(item: dict) -> tuple:
    """Build 1 field cho item trong embed shop."""
    emoji = PHAM_CAP_EMOJI.get(item['pham_cap'], '⚪')
    shop_id = item['shop_id']
    ten = item['ten']
    
    he_str = ''
    if item.get('he'):
        he_str = f' {HE_EMOJI.get(item["he"], "")} {HE_TEN.get(item["he"], item["he"])}'
    
    field_name = f'{emoji} #{shop_id} — {ten}{he_str}'
    
    lines = []
    
    # Phẩm cấp + Loại
    pham_cap = PHAM_CAP_TEN.get(item['pham_cap'], item['pham_cap'])
    loai_str = ''
    loai_raw = item.get('loai')
    if item['item_type'] == 'DanDuoc' and loai_raw:
        loai_str = f' | {LOAI_DAN.get(loai_raw, loai_raw)}'
    elif item['item_type'] == 'DaoCu' and loai_raw:
        loai_str = f' | {LOAI_DAO_CU.get(loai_raw, loai_raw)}'
    elif item['item_type'] == 'KhoangThach' and loai_raw:
        loai_str = f' | {LOAI_KHOANG_THACH.get(loai_raw, loai_raw)}'
    elif item['item_type'] == 'CongPhap' and loai_raw:
        # ⭐ MỚI: hiển thị giai cấp + loại công pháp
        giai_cap = item.get('giai_cap', '')
        giai_str = GIAI_CAP_CONG_PHAP.get(giai_cap, giai_cap)
        loai_cp = LOAI_CONG_PHAP.get(loai_raw, loai_raw)
        loai_str = f' | {loai_cp}'
        lines.append(f'📌 **{giai_str}** — **{pham_cap}**')
    else:
        lines.append(f'📌 **{pham_cap}**{loai_str}')
    
    # Nếu không phải công pháp, thêm dòng phẩm cấp bình thường
    if item['item_type'] != 'CongPhap':
        lines.append(f'📌 **{pham_cap}**{loai_str}')
    
    # Mô tả
    if item.get('mo_ta'):
        lines.append(f'📝 {item["mo_ta"]}')
    
    # ⭐ Effect riêng cho công pháp
    if item['item_type'] == 'CongPhap':
        effect = item.get('effect_moi_tang')
        if effect and isinstance(effect, dict):
            effect_lines = []
            for code, val in list(effect.items())[:5]:  # Chỉ hiển thị 5 stat đầu
                if 'pct' in code or 'ti_le' in code:
                    effect_lines.append(f'   `{code}: {val}%/tầng`')
                else:
                    effect_lines.append(f'   `{code}: {val}/tầng`')
            if effect_lines:
                lines.append('✨ **Bonus mỗi tầng:**')
                lines.extend(effect_lines)
        
        so_tang = item.get('so_tang', 9)
        lines.append(f'📊 **Số tầng tối đa:** `{so_tang}`')
    else:
        # Effect chi tiết cho item khác
        effect_str = format_effect(item)
        if effect_str:
            lines.append(effect_str)
    
    # Giá
    gia_parts = []
    if item['gia_linh_thach'] > 0:
        gia_parts.append(f'💰 `{item["gia_linh_thach"]:,}` linh thạch')
    if item['gia_tien_ngoc'] > 0:
        gia_parts.append(f'💎 `{item["gia_tien_ngoc"]:,}` tiên ngọc')
    if gia_parts:
        lines.append(' • '.join(gia_parts))
    else:
        lines.append('💰 *Miễn phí*')
    
    # Tồn kho
    so_luong_ton = item.get('so_luong_ton', 0)
    if so_luong_ton > 0:
        lines.append(f'📦 Tồn kho: `{so_luong_ton:,}`')
    else:
        lines.append('📦 **HẾT HÀNG**')
    
    field_value = '\n'.join(lines)
    
    if len(field_value) > 1024:
        field_value = field_value[:1020] + '...'
    
    return field_name, field_value


def build_shop_embed(items: list, item_type: str, page: int) -> discord.Embed:
    """Build embed cho 1 trang shop."""
    total_pages = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = items[start:end]
    
    embed = discord.Embed(
        title=f'🛒 Shop — {LOAI_SHOP[item_type]}',
        description=f'Tổng: `{len(items)}` item | Trang `{page}/{total_pages}`',
        color=discord.Color.blue(),
    )
    
    if not page_items:
        embed.description = 'Không có item nào.'
    else:
        for item in page_items:
            name, value = build_item_field(item)
            embed.add_field(name=name, value=value, inline=False)
    
    embed.set_footer(text='Dùng /mua <ID> <số_lượng> để mua')
    return embed


# ============================================================
# /exchange
# ============================================================
class Exchange(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='exchange',
        description='Đổi linh thạch sang tiên ngọc'
    )
    @app_commands.describe(so_tien_ngoc='Số tiên ngọc muốn nhận')
    async def exchange(self, interaction: discord.Interaction, so_tien_ngoc: int):
        await interaction.response.defer(thinking=False)
        
        if so_tien_ngoc <= 0:
            await interaction.followup.send('❌ Số tiên ngọc phải > 0!')
            return
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ti_gia = get_ti_gia_tien_ngoc()
        ket_qua = exchange_linh_thach_sang_tien_ngoc(player.player_id, so_tien_ngoc)
        
        if not ket_qua['thanh_cong']:
            await interaction.followup.send(f'❌ {ket_qua["loi"]}')
            return
        
        embed = discord.Embed(
            title='💎 Đổi Tiền Tệ Thành Công',
            color=discord.Color.gold(),
        )
        embed.add_field(
            name='💰 Đã trả',
            value=f'`{ket_qua["linh_thach_mat"]:,}` linh thạch',
            inline=True,
        )
        embed.add_field(
            name='💎 Đã nhận',
            value=f'`{ket_qua["tien_ngoc_nhan"]:,}` tiên ngọc',
            inline=True,
        )
        embed.set_footer(text=f'Tỉ lệ: 1 tiên ngọc = {ti_gia:,} linh thạch')
        
        await interaction.followup.send(embed=embed)


# ============================================================
# /shop — PHÂN TRANG
# ============================================================
class ShopPaginator(discord.ui.View):
    def __init__(self, items: list, item_type: str, page: int = 1):
        super().__init__(timeout=300)
        self.items = items
        self.item_type = item_type
        self.page = page
        self.total_pages = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        self._update_buttons()
    
    def _update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == 'prev':
                    child.disabled = (self.page <= 1)
                elif child.custom_id == 'next':
                    child.disabled = (self.page >= self.total_pages)
    
    @discord.ui.button(label='Trang trước', emoji='⬅️', style=discord.ButtonStyle.secondary, custom_id='prev')
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            self._update_buttons()
            embed = build_shop_embed(self.items, self.item_type, self.page)
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='Trang sau', emoji='➡️', style=discord.ButtonStyle.secondary, custom_id='next')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages:
            self.page += 1
            self._update_buttons()
            embed = build_shop_embed(self.items, self.item_type, self.page)
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='Đóng', emoji='❌', style=discord.ButtonStyle.danger, custom_id='close')
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(
            content='Đã đóng shop.',
            embed=None,
            view=None,
        )


class ShopSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Đan dược', emoji='💊', value='DanDuoc'),
            discord.SelectOption(label='Đạo cụ', emoji='🎁', value='DaoCu'),
            discord.SelectOption(label='Linh thảo', emoji='🌿', value='LinhThao'),
            discord.SelectOption(label='Khoáng thạch', emoji='⛰', value='KhoangThach'),
            discord.SelectOption(label='Công pháp', emoji='📖', value='CongPhap'), 
        ]
        super().__init__(
            placeholder='Chọn loại muốn xem...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        item_type = self.values[0]
        items = get_shop_items(item_type)
        
        embed = build_shop_embed(items, item_type, page=1)
        view = ShopPaginator(items, item_type, page=1)
        
        await interaction.response.edit_message(embed=embed, view=view)


class ShopInitialView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(ShopSelect())


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='shop', description='Xem cửa hàng')
    async def shop(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        embed = discord.Embed(
            title='🛒 Cửa Hàng',
            description=(
                'Chọn loại vật phẩm muốn xem bên dưới.\n\n'
                '**Hướng dẫn:**\n'
                '• Ghi nhớ **ID** (VD: `#1`, `#25`)\n'
                '• Dùng `/mua <ID> <số_lượng>` để mua'
            ),
            color=discord.Color.blue(),
        )
        
        view = ShopInitialView()
        await interaction.followup.send(embed=embed, view=view)


# ============================================================
# /mua — HÓA ĐƠN XÁC NHẬN
# ============================================================
class MuaConfirmView(discord.ui.View):
    def __init__(self, player_id: int, shop_id: int, so_luong: int,
                 item_info: dict, gia_lt: int, gia_tn: int):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.shop_id = shop_id
        self.so_luong = so_luong
        self.item_info = item_info
        self.gia_lt = gia_lt
        self.gia_tn = gia_tn
        
        # Tắt nút nếu không có giá tương ứng
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == 'tra_lt' and gia_lt <= 0:
                    child.disabled = True
                elif child.custom_id == 'tra_tn' and gia_tn <= 0:
                    child.disabled = True
    
    async def _xu_ly_mua(self, interaction: discord.Interaction, loai_tien: str):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        ket_qua = mua_item(self.player_id, self.shop_id, self.so_luong, loai_tien)
        
        if not ket_qua['thanh_cong']:
            embed = discord.Embed(
                title='❌ Mua Thất Bại',
                description=ket_qua['loi'],
                color=discord.Color.red(),
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        embed = discord.Embed(
            title='✅ Mua Thành Công',
            color=discord.Color.green(),
        )
        embed.add_field(
            name='📦 Vật phẩm',
            value=f'**{self.item_info["ten"]}** × `{self.so_luong}`',
            inline=False,
        )
        
        payment_lines = []
        if ket_qua['linh_thach_tru'] > 0:
            payment_lines.append(f'💰 `-{ket_qua["linh_thach_tru"]:,}` linh thạch')
        if ket_qua['tien_ngoc_tru'] > 0:
            payment_lines.append(f'💎 `-{ket_qua["tien_ngoc_tru"]:,}` tiên ngọc')
        
        embed.add_field(
            name='💵 Đã trả',
            value='\n'.join(payment_lines) or '*Miễn phí*',
            inline=False,
        )
        
        embed.add_field(
            name='📦 Tồn kho còn lại',
            value=f'`{ket_qua["so_luong_ton_con"]:,}`',
            inline=True,
        )
        
        embed.set_footer(text=f'Shop ID: #{self.shop_id}')
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label='Trả linh thạch', emoji='💰', style=discord.ButtonStyle.success, custom_id='tra_lt')
    async def tra_linh_thach(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._xu_ly_mua(interaction, 'linh_thach')
    
    @discord.ui.button(label='Trả tiên ngọc', emoji='💎', style=discord.ButtonStyle.primary, custom_id='tra_tn')
    async def tra_tien_ngoc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._xu_ly_mua(interaction, 'tien_ngoc')
    
    @discord.ui.button(label='Hủy', emoji='❌', style=discord.ButtonStyle.danger, custom_id='huy')
    async def huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message('❌ Đã hủy đơn hàng.', ephemeral=True)


class MuaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='mua', description='Mua item từ shop')
    @app_commands.describe(
        shop_id='ID item trong shop',
        so_luong='Số lượng muốn mua (mặc định 1)',
    )
    async def mua(
        self,
        interaction: discord.Interaction,
        shop_id: int,
        so_luong: int = 1,
    ):
        await interaction.response.defer(thinking=False)
        
        if so_luong <= 0:
            await interaction.followup.send('❌ Số lượng phải > 0!')
            return
        if so_luong > 10000:
            await interaction.followup.send('❌ Số lượng tối đa 10,000!')
            return
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        # Lấy thông tin item
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
            SELECT 
                si.*,
                COALESCE(dd.ten, dc.ten, kt.ten, lt.ten, cp.ten) AS ten,
                COALESCE(dd.pham_cap, dc.pham_cap, kt.pham_cap, lt.pham_cap, cp.pham_cap) AS pham_cap,
                COALESCE(dc.he, kt.he, lt.he, cp.he) AS he,
                cp.giai_cap,
                cp.so_tang,
                cp.effect_moi_tang
            FROM tmpl_shop_item si
            LEFT JOIN tmpl_dan_duoc dd ON si.item_type = 'DanDuoc' AND dd.id = si.item_id
            LEFT JOIN tmpl_dao_cu dc ON si.item_type = 'DaoCu' AND dc.id = si.item_id
            LEFT JOIN tmpl_khoang_thach kt ON si.item_type = 'KhoangThach' AND kt.id = si.item_id
            LEFT JOIN tmpl_linh_thao lt ON si.item_type = 'LinhThao' AND lt.id = si.item_id
            LEFT JOIN tmpl_cong_phap cp ON si.item_type = 'CongPhap' AND cp.id = si.item_id
            WHERE si.id = %s AND si.is_active = 1
            """, (shop_id,))    
            item_info = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
        
        if not item_info:
            await interaction.followup.send(f'❌ Không tìm thấy item ID `#{shop_id}`!')
            return
        
        # Check tồn kho
        if item_info['so_luong_ton'] < so_luong:
            await interaction.followup.send(
                f'❌ **Hết hàng!** Chỉ còn `{item_info["so_luong_ton"]:,}` cái.'
            )
            return
        
        if item_info['gia_linh_thach'] <= 0 and item_info['gia_tien_ngoc'] <= 0:
            await interaction.followup.send('❌ Item không có giá!')
            return
        
        # Tính tổng
        gia_lt = item_info['gia_linh_thach'] * so_luong
        gia_tn = item_info['gia_tien_ngoc'] * so_luong
        
        # Build hóa đơn
        embed = discord.Embed(
            title='🧾 HÓA ĐƠN MUA HÀNG',
            color=discord.Color.gold(),
        )
        
        emoji = PHAM_CAP_EMOJI.get(item_info['pham_cap'], '⚪')
        he_str = ''
        if item_info.get('he'):
            he_str = f' {HE_EMOJI.get(item_info["he"], "")} {HE_TEN.get(item_info["he"], item_info["he"])}'
        
        embed.add_field(
            name='📦 Vật phẩm',
            value=f'{emoji} **{item_info["ten"]}**{he_str}',
            inline=False,
        )
        
        chi_tiet_lines = [
            f'🆔 Shop ID: `#{shop_id}`',
            f'📊 Số lượng: `{so_luong:,}`',
        ]
        if item_info['gia_linh_thach'] > 0:
            chi_tiet_lines.append(f'💰 Đơn giá linh thạch: `{item_info["gia_linh_thach"]:,}`')
        if item_info['gia_tien_ngoc'] > 0:
            chi_tiet_lines.append(f'💎 Đơn giá tiên ngọc: `{item_info["gia_tien_ngoc"]:,}`')
        
        embed.add_field(
            name='📋 Chi tiết',
            value='\n'.join(chi_tiet_lines),
            inline=False,
        )
        
        # Tổng cộng
        tong_parts = []
        if gia_lt > 0:
            tong_parts.append(f'💰 `{gia_lt:,}` linh thạch')
        if gia_tn > 0:
            tong_parts.append(f'💎 `{gia_tn:,}` tiên ngọc')
        
        if len(tong_parts) > 1:
            tong_value = '**Hoặc**\n' + '\n'.join(tong_parts)
        else:
            tong_value = tong_parts[0] if tong_parts else '*Miễn phí*'
        
        embed.add_field(
            name='💵 TỔNG CỘNG',
            value=tong_value,
            inline=False,
        )
        
        embed.add_field(
            name='💼 Số dư của bạn',
            value=(
                f'💰 Linh thạch: `{player.linh_thach:,}`\n'
                f'💎 Tiên ngọc: `{player.tien_ngoc:,}`'
            ),
            inline=False,
        )
        
        embed.add_field(
            name='📦 Tồn kho',
            value=f'Còn `{item_info["so_luong_ton"]:,}` → Sau khi mua: `{item_info["so_luong_ton"] - so_luong:,}`',
            inline=False,
        )
        
        embed.set_footer(text='Nhấn nút bên dưới để xác nhận thanh toán (60s)')
        
        view = MuaConfirmView(
            player_id=player.player_id,
            shop_id=shop_id,
            so_luong=so_luong,
            item_info=item_info,
            gia_lt=gia_lt,
            gia_tn=gia_tn,
        )
        
        await interaction.followup.send(embed=embed, view=view)


# ============================================================
# /ban — BÁN ITEM
# ============================================================
class BanSelect(discord.ui.Select):
    def __init__(self, ds_items: list, loai: str):
        self.ds_items = ds_items
        self.loai = loai
        
        options = []
        for i, item in enumerate(ds_items[:25]):
            emoji = PHAM_CAP_EMOJI.get(item['pham_cap'], '⚪')
            if loai == 'cong_phap':
                giai_cap = item.get('giai_cap', '')
                giai_str = GIAI_CAP_CONG_PHAP.get(giai_cap, giai_cap)
                label = f"{item['ten']} ({giai_str}) ×{item['so_luong']}"
            else:
                label = f"{item['ten']} (×{item['so_luong']})"
            
            options.append(discord.SelectOption(
                label=label[:100],
                emoji=emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn item muốn bán...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        item = self.ds_items[idx]
        
        # Hỏi số lượng
        await interaction.response.send_modal(
            BanSoLuongModal(self.loai, item)
        )


class BanSoLuongModal(discord.ui.Modal, title='Bán Item'):
    def __init__(self, loai: str, item: dict):
        super().__init__()
        self.loai = loai
        self.item = item
        
        self.so_luong = discord.ui.TextInput(
            label=f'Số lượng (tối đa {item["so_luong"]})',
            placeholder='Nhập số lượng muốn bán',
            min_length=1,
            max_length=6,
        )
        self.add_item(self.so_luong)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            so_luong = int(self.so_luong.value)
        except ValueError:
            await interaction.response.send_message('❌ Số lượng không hợp lệ!', ephemeral=True)
            return
        
        if so_luong <= 0:
            await interaction.response.send_message('❌ Số lượng phải > 0!', ephemeral=True)
            return
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.response.send_message('❌ Bạn chưa đăng ký!', ephemeral=True)
            return
        
        if self.loai == 'khoang_thach':
            item_type = 'KhoangThach'
            ket_qua = ban_item(player.player_id, item_type, self.item['id'], so_luong)
        elif self.loai == 'linh_thao':
            item_type = 'LinhThao'
            ket_qua = ban_item(player.player_id, item_type, self.item['id'], so_luong)
        else:  # cong_phap
            ket_qua = ban_cong_phap(
                player.player_id,
                self.item['cong_phap_id'],
                so_luong,
            )
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(f'❌ {ket_qua["loi"]}', ephemeral=True)
            return
        
        embed = discord.Embed(
            title='✅ Bán Thành Công',
            color=discord.Color.green(),
        )
        embed.add_field(
            name='📦 Đã bán',
            value=f'**{self.item["ten"]}** × `{so_luong}`',
            inline=False,
        )
        embed.add_field(
            name='💰 Nhận được',
            value=f'`+{ket_qua["tien_nhan"]:,}` linh thạch',
            inline=False,
        )
        
        await interaction.response.send_message(embed=embed)


class BanView(discord.ui.View):
    def __init__(self, ds_items: list, loai: str):
        super().__init__(timeout=120)
        self.add_item(BanSelect(ds_items, loai))


class BanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='sell', description='Bán khoáng thạch hoặc linh thảo')
    @app_commands.choices(loai=[
        app_commands.Choice(name='Khoáng thạch', value='khoang_thach'),
        app_commands.Choice(name='Linh thảo', value='linh_thao'),
        app_commands.Choice(name='Công pháp', value='cong_phap'),
    ])
    async def ban(self, interaction: discord.Interaction, loai: str):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        if loai == 'khoang_thach':
            ds_items = get_player_khoang_thach(player.player_id)
            tieu_de = '⛰ Bán Khoáng Thạch'
        elif loai == 'linh_thao':
            ds_items = get_player_linh_thao(player.player_id)
            tieu_de = '🌿 Bán Linh Thảo'
        else:  # cong_phap
            ds_items = get_player_cong_phap_trong_tui(player.player_id)
            tieu_de = '📖 Bán Công Pháp'
        
        if not ds_items:
            await interaction.followup.send(f'❌ Bạn không có {loai.replace("_", " ")} nào!')
            return
        
        embed = discord.Embed(
            title=tieu_de,
            description=f'Bạn có `{len(ds_items)}` loại. Chọn item muốn bán.',
            color=discord.Color.green(),
        )
        
        view = BanView(ds_items, loai)
        await interaction.followup.send(embed=embed, view=view)


# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(Exchange(bot))
    await bot.add_cog(Shop(bot))
    await bot.add_cog(MuaCog(bot))
    await bot.add_cog(BanCog(bot))