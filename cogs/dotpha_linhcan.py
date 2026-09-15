import discord
from discord import app_commands
from discord.ext import commands

from database.player_repo import (
    get_player_full_info,
    get_linh_can_du_dieu_kien_dot_pha,
    dot_pha_linh_can,
)


HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}

PHAM_CAP_TEN = {
    'Ha': 'Hạ phẩm', 'Trung': 'Trung phẩm', 'Thuong': 'Thượng phẩm',
    'Cuc': 'Cực phẩm', 'Tien': 'Tiên phẩm',
}


# ============================================================
# DROPDOWN CHỌN LINH CĂN
# ============================================================
class LinhCanSelect(discord.ui.Select):
    def __init__(self, ds_linh_can: list, player_id: int):
        self.ds_linh_can = ds_linh_can
        self.player_id = player_id
        
        options = []
        for i, lc in enumerate(ds_linh_can[:25]):
            emoji = HE_EMOJI.get(lc['he'], '❓')
            
            # Đếm số cách đột phá
            so_cach = 0
            if lc['dao_cu_100']['so_luong'] > 0:
                so_cach += 1
            if lc['so_lan_da_dung'] < 2:
                so_cach += 1
            
            options.append(discord.SelectOption(
                label=f"{lc['ten']}",
                description=f"Tinh khiết: {lc['do_tinh_khiet']:.1f}% | {so_cach} cách",
                emoji=emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn linh căn muốn đột phá...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        lc = self.ds_linh_can[idx]
        
        # Hiển thị view chọn cách đột phá
        embed = build_chon_cach_embed(lc)
        view = ChonCachView(lc, self.player_id)
        
        await interaction.response.edit_message(embed=embed, view=view)


class LinhCanView(discord.ui.View):
    def __init__(self, ds_linh_can: list, player_id: int):
        super().__init__(timeout=180)
        self.add_item(LinhCanSelect(ds_linh_can, player_id))


# ============================================================
# DROPDOWN CHỌN CÁCH ĐỘT PHÁ
# ============================================================
class ChonCachView(discord.ui.View):
    def __init__(self, lc: dict, player_id: int):
        super().__init__(timeout=120)
        self.lc = lc
        self.player_id = player_id
        
        # Nút "Đột phá 100%" (chỉ hiện nếu có đạo cụ)
        if lc['dao_cu_100']['so_luong'] > 0:
            self.add_item(DotPhaChacChanButton(lc, player_id))
        
        # Nút "Đột phá tỉ lệ" (chỉ hiện nếu còn lượt)
        if lc['so_lan_da_dung'] < 2:
            self.add_item(DotPhaTiLeButton(lc, player_id))
        
        # Nút "Đóng"
        self.add_item(HuyButton())


# ============================================================
# NÚT ĐỘT PHÁ 100%
# ============================================================
class DotPhaChacChanButton(discord.ui.Button):
    def __init__(self, lc: dict, player_id: int):
        super().__init__(
            label=f"Đột phá 100% ({lc['dao_cu_100']['so_luong']})",
            emoji='🎯',
            style=discord.ButtonStyle.success,
        )
        self.lc = lc
        self.player_id = player_id
    
    async def callback(self, interaction: discord.Interaction):
        # Disable tất cả
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        
        # Thực hiện đột phá
        ket_qua = dot_pha_linh_can(
        self.player_id,
        self.lc['linh_can_id'],
        [{'id': self.lc['dao_cu_100']['id']}],
    )
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(f'❌ {ket_qua["loi"]}', ephemeral=True)
            return
        
        embed = build_ket_qua_embed(ket_qua)
        await interaction.response.send_message(embed=embed)


# ============================================================
# NÚT ĐỘT PHÁ TỈ LỆ
# ============================================================
class DotPhaTiLeButton(discord.ui.Button):
    def __init__(self, lc: dict, player_id: int):
        super().__init__(
            label='Đột phá theo tỉ lệ',
            emoji='🎲',
            style=discord.ButtonStyle.primary,
        )
        self.lc = lc
        self.player_id = player_id
    
    async def callback(self, interaction: discord.Interaction):
        # State mới: danh sách đạo cụ đã chọn
        state = TiLeState(
            lc=self.lc,
            player_id=self.player_id,
            ds_da_chon=[],  # List các dict đạo cụ đã chọn
        )
        
        embed = build_quan_ly_dao_cu_embed(state)
        view = QuanLyDaoCuView(state)
        await interaction.response.edit_message(embed=embed, view=view)

class TiLeState:
    """State quản lý đạo cụ tăng tỉ lệ đã chọn."""
    def __init__(self, lc: dict, player_id: int, ds_da_chon: list):
        self.lc = lc
        self.player_id = player_id
        self.ds_da_chon = ds_da_chon  # List[dict]
    
    def tinh_tong_bonus(self) -> float:
        return sum(dc['bonus_ti_le'] for dc in self.ds_da_chon)
    
    def so_luot_con(self) -> int:
        max_lan = 2
        return max_lan - self.lc['so_lan_da_dung'] - len(self.ds_da_chon)


class QuanLyDaoCuView(discord.ui.View):
    def __init__(self, state: TiLeState):
        super().__init__(timeout=300)
        self.state = state
        
        # Nút "Thêm đạo cụ" (chỉ hiện nếu còn lượt và còn đạo cụ)
        if state.so_luot_con() > 0 and state.lc['ds_dao_cu_ti_le']:
            self.add_item(ThemDaoCuButton(state))
        
        # Nút "Xóa đạo cụ" (chỉ hiện nếu có ít nhất 1 đạo cụ đã chọn)
        if state.ds_da_chon:
            self.add_item(XoaDaoCuButton(state))
        
        # Nút "Xác nhận đột phá" (luôn hiện)
        self.add_item(XacNhanDotPhaButton(state))
        
        # Nút "Quay lại"
        self.add_item(QuayLaiTiLeButton(state))


# ============================================================
# NÚT THÊM ĐẠO CỤ (mở dropdown)
# ============================================================
class ThemDaoCuButton(discord.ui.Button):
    def __init__(self, state: TiLeState):
        super().__init__(
            label='Thêm đạo cụ',
            emoji='➕',
            style=discord.ButtonStyle.success,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        # Chuyển sang view chọn đạo cụ
        embed = build_chon_them_dao_cu_embed(self.state)
        view = ChonThemDaoCuView(self.state)
        await interaction.response.edit_message(embed=embed, view=view)


# ============================================================
# VIEW CHỌN ĐẠO CỤ ĐỂ THÊM
# ============================================================
class ChonThemDaoCuView(discord.ui.View):
    def __init__(self, state: TiLeState):
        super().__init__(timeout=120)
        self.state = state
        self.add_item(ChonDaoCuThemSelect(state))
        self.add_item(QuayLaiQuanLyButton(state))


class ChonDaoCuThemSelect(discord.ui.Select):
    def __init__(self, state: TiLeState):
        self.state = state
        
        # Lọc các đạo cụ chưa chọn
        da_chon_ids = [dc['id'] for dc in state.ds_da_chon]
        
        options = []
        for dc in state.lc['ds_dao_cu_ti_le']:
            if dc['id'] in da_chon_ids:
                continue
            
            options.append(discord.SelectOption(
                label=dc['ten'][:100],
                description=f"+{dc['bonus_ti_le']}% | Có: {dc['so_luong']}",
                emoji='📜',
                value=str(dc['id']),
            ))
        
        if not options:
            options.append(discord.SelectOption(label='Không còn đạo cụ', value='0'))
        
        super().__init__(
            placeholder='Chọn đạo cụ để thêm...',
            options=options[:25],
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        dao_cu_id = int(self.values[0])
        
        if dao_cu_id == 0:
            await interaction.response.send_message('❌ Không có đạo cụ!', ephemeral=True)
            return
        
        # Tìm đạo cụ trong danh sách
        dc = next((d for d in self.state.lc['ds_dao_cu_ti_le'] if d['id'] == dao_cu_id), None)
        if not dc:
            await interaction.response.send_message('❌ Không tìm thấy đạo cụ!', ephemeral=True)
            return
        
        # Thêm vào state
        self.state.ds_da_chon.append(dc)
        
        # Quay lại view quản lý
        embed = build_quan_ly_dao_cu_embed(self.state)
        view = QuanLyDaoCuView(self.state)
        await interaction.response.edit_message(embed=embed, view=view)


class QuayLaiQuanLyButton(discord.ui.Button):
    def __init__(self, state: TiLeState):
        super().__init__(
            label='Quay lại',
            emoji='↩️',
            style=discord.ButtonStyle.secondary,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        embed = build_quan_ly_dao_cu_embed(self.state)
        view = QuanLyDaoCuView(self.state)
        await interaction.response.edit_message(embed=embed, view=view)


# ============================================================
# NÚT XÓA ĐẠO CỤ
# ============================================================
class XoaDaoCuButton(discord.ui.Button):
    def __init__(self, state: TiLeState):
        super().__init__(
            label='Xóa đạo cụ',
            emoji='🗑️',
            style=discord.ButtonStyle.secondary,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        embed = build_xoa_dao_cu_embed(self.state)
        view = XoaDaoCuView(self.state)
        await interaction.response.edit_message(embed=embed, view=view)


class XoaDaoCuView(discord.ui.View):
    def __init__(self, state: TiLeState):
        super().__init__(timeout=120)
        self.state = state
        self.add_item(XoaDaoCuSelect(state))
        self.add_item(QuayLaiQuanLyButton(state))


class XoaDaoCuSelect(discord.ui.Select):
    def __init__(self, state: TiLeState):
        self.state = state
        
        options = []
        for i, dc in enumerate(state.ds_da_chon):
            options.append(discord.SelectOption(
                label=dc['ten'][:100],
                description=f"Đang chọn: +{dc['bonus_ti_le']}%",
                emoji='📜',
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đạo cụ muốn xóa...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        
        # Xóa khỏi state
        if 0 <= idx < len(self.state.ds_da_chon):
            del self.state.ds_da_chon[idx]
        
        embed = build_quan_ly_dao_cu_embed(self.state)
        view = QuanLyDaoCuView(self.state)
        await interaction.response.edit_message(embed=embed, view=view)


# ============================================================
# NÚT XÁC NHẬN ĐỘT PHÁ (ROLL)
# ============================================================
class XacNhanDotPhaButton(discord.ui.Button):
    def __init__(self, state: TiLeState):
        super().__init__(
            label='Xác nhận đột phá',
            emoji='⚗️',
            style=discord.ButtonStyle.danger,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        
        # Chuẩn bị ds_dao_cu từ state
        ds_dao_cu = [{'id': dc['id']} for dc in self.state.ds_da_chon]
        
        ket_qua = dot_pha_linh_can(
            self.state.player_id,
            self.state.lc['linh_can_id'],
            ds_dao_cu,
        )
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(f'❌ {ket_qua["loi"]}', ephemeral=True)
            return
        
        embed = build_ket_qua_embed(ket_qua)
        await interaction.response.send_message(embed=embed)


class QuayLaiTiLeButton(discord.ui.Button):
    def __init__(self, state: TiLeState):
        super().__init__(
            label='Quay lại',
            emoji='↩️',
            style=discord.ButtonStyle.secondary,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        embed = build_chon_cach_embed(self.state.lc)
        view = ChonCachView(self.state.lc, self.state.player_id)
        await interaction.response.edit_message(embed=embed, view=view)
        
        
# ============================================================
# CHỌN ĐẠO CỤ TĂNG TỈ LỆ
# ============================================================
class DotPhaKhongDaoCuButton(discord.ui.Button):
    def __init__(self, lc: dict, player_id: int):
        super().__init__(
            label='Không dùng đạo cụ',
            emoji='🎲',
            style=discord.ButtonStyle.secondary,
        )
        self.lc = lc
        self.player_id = player_id
    
    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        
        ket_qua = dot_pha_linh_can(
            self.player_id,
            self.lc['linh_can_id'],
            [],
        )
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(f'❌ {ket_qua["loi"]}', ephemeral=True)
            return
        
        embed = build_ket_qua_embed(ket_qua)
        await interaction.response.send_message(embed=embed)


class QuayLaiButton(discord.ui.Button):
    def __init__(self, lc: dict, player_id: int):
        super().__init__(
            label='Quay lại',
            emoji='↩️',
            style=discord.ButtonStyle.secondary,
        )
        self.lc = lc
        self.player_id = player_id
    
    async def callback(self, interaction: discord.Interaction):
        embed = build_chon_cach_embed(self.lc)
        view = ChonCachView(self.lc, self.player_id)
        await interaction.response.edit_message(embed=embed, view=view)


class HuyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='Đóng',
            emoji='❌',
            style=discord.ButtonStyle.danger,
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content='Đã đóng.',
            embed=None,
            view=None,
        )


# ============================================================
# BUILD EMBED
# ============================================================
def build_chon_cach_embed(lc: dict) -> discord.Embed:
    """Embed chọn cách đột phá."""
    emoji = HE_EMOJI.get(lc['he'], '❓')
    
    embed = discord.Embed(
        title=f'🌟 Đột Phá {lc["ten"]}',
        description=(
            f'{emoji} Hệ **{lc["he"]}** — **{PHAM_CAP_TEN[lc["pham_cap"]]}**\n'
            f'Tinh khiết: `{lc["do_tinh_khiet"]:.2f}%`\n'
            f'Đột phá: **{PHAM_CAP_TEN[lc["pham_cap"]]}** → **{PHAM_CAP_TEN[lc["pham_cap_moi"]]}**\n\n'
            f'Chọn cách đột phá:'
        ),
        color=discord.Color.gold(),
    )
    
    # Cách 1: 100%
    if lc['dao_cu_100']['so_luong'] > 0:
        embed.add_field(
            name='🎯 Cách 1: Chắc chắn 100%',
            value=(
                f'Dùng: **{lc["dao_cu_100"]["ten"]}**\n'
                f'Số lượng: `×{lc["dao_cu_100"]["so_luong"]}`\n'
                f'Kết quả: **Luôn thành công**'
            ),
            inline=False,
        )
    else:
        embed.add_field(
            name='🎯 Cách 1: Chắc chắn 100%',
            value=f'❌ Thiếu **{lc["dao_cu_100"]["ten"] or "đạo cụ đột phá"}**',
            inline=False,
        )
    
    # Cách 2: Tỉ lệ
    luot_con = 2 - lc['so_lan_da_dung']
    if luot_con > 0:
        embed.add_field(
            name=f'🎲 Cách 2: Đột phá theo tỉ lệ',
            value=(
                f'Tỉ lệ cơ bản: `25%`\n'
                f'Lượt dùng đạo cụ còn: `{luot_con}/2`\n'
                f'Có thể dùng đạo cụ tăng tỉ lệ (+10-100%)'
            ),
            inline=False,
        )
    else:
        embed.add_field(
            name='🎲 Cách 2: Đột phá theo tỉ lệ',
            value=f'❌ Đã dùng tối đa 2 lần đạo cụ tăng tỉ lệ!',
            inline=False,
        )
    
    embed.set_footer(text='Chọn cách đột phá bên dưới')
    return embed


def build_chon_dao_cu_ti_le_embed(lc: dict) -> discord.Embed:
    """Embed chọn đạo cụ tăng tỉ lệ."""
    embed = discord.Embed(
        title=f'🎲 Đột Phá Theo Tỉ Lệ — {lc["ten"]}',
        description=(
            f'Tỉ lệ cơ bản: `25%`\n'
            f'Lượt dùng đạo cụ còn: `{2 - lc["so_lan_da_dung"]}/2`\n\n'
            f'Chọn đạo cụ tăng tỉ lệ hoặc đột phá không đạo cụ:'
        ),
        color=discord.Color.blue(),
    )
    
    for dc in lc['ds_dao_cu_ti_le'][:10]:
        embed.add_field(
            name=f'📜 {dc["ten"]}',
            value=f'• Bonus: `+{dc["bonus_ti_le"]}%`\n• Có: `×{dc["so_luong"]}`',
            inline=True,
        )
    
    return embed


def build_ket_qua_embed(ket_qua: dict) -> discord.Embed:
    """Embed kết quả đột phá."""
    if ket_qua['thanh_cong']:
        embed = discord.Embed(
            title='🎉 ĐỘT PHÁ THÀNH CÔNG!',
            color=discord.Color.green(),
        )
        embed.add_field(
            name='📊 Kết quả',
            value=(
                f'{HE_EMOJI.get("", "")} **{ket_qua["linh_can_cu"]["ten"]}**\n'
                f'→ **{ket_qua["linh_can_moi"]["ten"]}**'
            ),
            inline=False,
        )
    else:
        embed = discord.Embed(
            title='💔 ĐỘT PHÁ THẤT BẠI',
            color=discord.Color.red(),
        )
        embed.add_field(
            name='📊 Kết quả',
            value=(
                f'**{ket_qua["linh_can_cu"]["ten"]}** giữ nguyên\n'
                f'Mất `{ket_qua["mat_tinh_khiet"]:.2f}%` tinh khiết'
            ),
            inline=False,
        )
    
    # Chi tiết
    if ket_qua['loai_dot_pha'] == 'chac_chan':
        embed.add_field(
            name='🎯 Loại',
            value='Chắc chắn 100%',
            inline=True,
        )
    else:
        embed.add_field(
            name='🎲 Loại',
            value=(
                f'Tỉ lệ: `{ket_qua["ti_le"]:.2f}%`\n'
                f'Roll: `{ket_qua["roll"]:.2f}`\n'
                f'Bonus đạo cụ: `+{ket_qua["bonus_ti_le"]:.0f}%`'
            ),
            inline=True,
        )
    
    if not ket_qua['thanh_cong']:
        embed.add_field(
            name='📊 Lượt dùng',
            value=f'`{ket_qua["so_lan_da_dung"]}/2`',
            inline=True,
        )
    
    embed.set_footer(text='Dùng /lichluyen để cày lại tinh khiết')
    return embed

def build_quan_ly_dao_cu_embed(state: TiLeState) -> discord.Embed:
    """Embed quản lý đạo cụ tăng tỉ lệ."""
    lc = state.lc
    
    embed = discord.Embed(
        title=f'🎲 Đột Phá Theo Tỉ Lệ — {lc["ten"]}',
        description=(
            f'Tỉ lệ cơ bản: `25%`\n'
            f'Lượt dùng đạo cụ còn: `{state.so_luot_con() + len(state.ds_da_chon)}/2`\n'
            f'Đạo cụ đã chọn: `{len(state.ds_da_chon)}/2`\n'
        ),
        color=discord.Color.blue(),
    )
    
    # Bonus
    tong_bonus = state.tinh_tong_bonus()
    ti_le_cuoi = min(95, 25 + tong_bonus)
    
    embed.add_field(
        name='📊 Tỉ lệ hiện tại',
        value=(
            f'Cơ bản: `25%`\n'
            f'Bonus đạo cụ: `+{tong_bonus}%`\n'
            f'**Tổng: `{ti_le_cuoi}%`**'
        ),
        inline=False,
    )
    
    # Danh sách đã chọn
    if state.ds_da_chon:
        lines = []
        for dc in state.ds_da_chon:
            lines.append(f'📜 **{dc["ten"]}** — `+{dc["bonus_ti_le"]}%`')
        embed.add_field(
            name=f'✅ Đã chọn ({len(state.ds_da_chon)}/2)',
            value='\n'.join(lines),
            inline=False,
        )
    else:
        embed.add_field(
            name='✅ Đã chọn',
            value='*Chưa chọn đạo cụ nào*',
            inline=False,
        )
    
    embed.set_footer(text='Thêm đạo cụ hoặc bấm Xác nhận để roll')
    return embed


def build_chon_them_dao_cu_embed(state: TiLeState) -> discord.Embed:
    """Embed chọn đạo cụ để thêm."""
    embed = discord.Embed(
        title='📜 Chọn Đạo Cụ Tăng Tỉ Lệ',
        description=(
            f'Chọn đạo cụ để thêm vào danh sách (tối đa 2).\n'
            f'Đã chọn: `{len(state.ds_da_chon)}/2`'
        ),
        color=discord.Color.green(),
    )
    
    for dc in state.lc['ds_dao_cu_ti_le'][:10]:
        da_chon = any(d['id'] == dc['id'] for d in state.ds_da_chon)
        status = '✅' if da_chon else ''
        embed.add_field(
            name=f'{status} 📜 {dc["ten"]}',
            value=f'• Bonus: `+{dc["bonus_ti_le"]}%`\n• Có: `×{dc["so_luong"]}`',
            inline=True,
        )
    
    return embed


def build_xoa_dao_cu_embed(state: TiLeState) -> discord.Embed:
    """Embed xóa đạo cụ."""
    embed = discord.Embed(
        title='🗑️ Xóa Đạo Cụ',
        description='Chọn đạo cụ muốn xóa khỏi danh sách:',
        color=discord.Color.red(),
    )
    return embed
# ============================================================
# COG
# ============================================================
class DotPhaLinhCan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='dotpha-linhcan',
        description='Đột phá linh căn (100% hoặc theo tỉ lệ)'
    )
    async def dotpha_linhcan(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_linh_can = get_linh_can_du_dieu_kien_dot_pha(player.player_id)
        
        if not ds_linh_can:
            await interaction.followup.send(
                '❌ **Không có linh căn nào đủ điều kiện đột phá!**\n\n'
                '**Điều kiện:**\n'
                '• Độ tinh khiết đạt 100%\n'
                '• Chưa max phẩm cấp\n\n'
                'Dùng `/lichluyen` để cày độ tinh khiết.'
            )
            return
        
        embed = discord.Embed(
            title='✨ Đột Phá Linh Căn',
            description=(
                f'Bạn có **{len(ds_linh_can)}** linh căn đủ điều kiện.\n'
                f'Chọn linh căn muốn đột phá bên dưới.'
            ),
            color=discord.Color.gold(),
        )
        
        for i, lc in enumerate(ds_linh_can[:10], 1):
            emoji = HE_EMOJI.get(lc['he'], '❓')
            embed.add_field(
                name=f'{i}. {emoji} {lc["ten"]}',
                value=(
                    f'• Tinh khiết: `100%`\n'
                    f'• Đột phá: **{PHAM_CAP_TEN[lc["pham_cap"]]}** → **{PHAM_CAP_TEN[lc["pham_cap_moi"]]}**\n'
                    f'• Đạo cụ 100%: `×{lc["dao_cu_100"]["so_luong"]}`\n'
                    f'• Lượt tỉ lệ: `{2 - lc["so_lan_da_dung"]}/2`'
                ),
                inline=False,
            )
        
        view = LinhCanView(ds_linh_can, player.player_id)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(DotPhaLinhCan(bot))