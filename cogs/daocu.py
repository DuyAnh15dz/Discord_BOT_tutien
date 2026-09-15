import discord
from discord import app_commands
from discord.ext import commands
import json

from database.player_repo import (
    get_player_full_info,
    get_dao_cu_tang_tinh_khiet_cua_player,
    get_player_linh_can_full,
    dung_dao_cu_tang_tinh_khiet,
    get_player_dao_cu_full,          # ⭐ MỚI
)


HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}

HE_TEN = {
    'Kim': 'Kim', 'Moc': 'Mộc', 'Thuy': 'Thủy', 'Hoa': 'Hỏa', 'Tho': 'Thổ',
    'Loi': 'Lôi', 'Bang': 'Băng', 'Phong': 'Phong', 'Duong': 'Dương', 'Am': 'Âm',
}

PHAM_CAP_EMOJI = {
    'Ha': '🟤', 'Trung': '🟢', 'Thuong': '🔵', 'Cuc': '🟣', 'Tien': '🟡',
}

PHAM_CAP_TEN = {
    'Pham': 'Phàm phẩm', 'Linh': 'Linh phẩm', 'Bao': 'Bảo phẩm',
    'Tien': 'Tiên phẩm', 'Than': 'Thần phẩm',
}

LOAI_DAO_CU = {
    'DotPhaLinhCan': '🔮 Đột phá linh căn',
    'TangTinhKhiet': '💧 Tăng tinh khiết',
    'Khac': '❓ Khác',
}

# Map effect key
EFFECT_KEY_MAP = {
    'ti_le_bonus': '⚡ Bonus tỉ lệ đột phá',
    'tinh_khiet': '💧 Tinh khiết',
}


# ============================================================
# HELPER
# ============================================================
def format_effect(effect) -> str:
    """Format effect thành text."""
    if isinstance(effect, str):
        try:
            effect = json.loads(effect)
        except:
            return '*Không có*'
    
    if not isinstance(effect, dict) or not effect:
        return '*Không có*'
    
    lines = []
    for key, val in effect.items():
        label = EFFECT_KEY_MAP.get(key, key)
        if isinstance(val, (int, float)):
            if 'pct' in key or 'ti_le' in key or 'tinh_khiet' in key:
                lines.append(f'• {label}: `+{val}%`')
            else:
                lines.append(f'• {label}: `+{val:,}`')
        else:
            lines.append(f'• {label}: `{val}`')
    
    return '\n'.join(lines) if lines else '*Không có*'


def build_dao_cu_chi_tiet_embed(dc: dict) -> discord.Embed:
    """Build embed chi tiết đạo cụ."""
    pc_emoji = PHAM_CAP_EMOJI.get(dc['pham_cap'], '⚪')
    pc_ten = PHAM_CAP_TEN.get(dc['pham_cap'], dc['pham_cap'])
    loai_str = LOAI_DAO_CU.get(dc['loai'], dc['loai'])
    
    he_str = ''
    if dc.get('he'):
        he_str = f' {HE_EMOJI.get(dc["he"], "")} {HE_TEN.get(dc["he"], dc["he"])}'
    
    embed = discord.Embed(
        title=f'{pc_emoji} {dc["ten"]}{he_str}',
        description=dc.get('mo_ta') or '*Không có mô tả*',
        color=discord.Color.purple(),
    )
    
    info_lines = [
        f'📌 **{pc_ten}**',
        f'🏷️ Loại: `{loai_str}`',
        f'🎒 Trong túi: `×{dc["so_luong"]}`',
    ]
    
    if dc.get('he'):
        info_lines.append(f'🌟 Hệ: {HE_EMOJI.get(dc["he"], "")} {HE_TEN.get(dc["he"], dc["he"])}')
    
    embed.add_field(
        name='📋 Thông tin',
        value='\n'.join(info_lines),
        inline=False,
    )
    
    effect_str = format_effect(dc.get('effect'))
    embed.add_field(
        name='✨ Hiệu ứng',
        value=effect_str,
        inline=False,
    )
    
    # Cách dùng
    if dc['loai'] == 'DotPhaLinhCan':
        embed.add_field(
            name='💡 Cách dùng',
            value='Dùng `/dotpha-linhcan` khi có linh căn 100% tinh khiết.',
            inline=False,
        )
    elif dc['loai'] == 'TangTinhKhiet':
        embed.add_field(
            name='💡 Cách dùng',
            value='Dùng `/dungdaocu` để tăng tinh khiết cho linh căn cùng hệ.',
            inline=False,
        )
    
    # Giá mua
    if dc.get('co_the_mua_premium') and dc.get('gia_tien_ngoc', 0) > 0:
        embed.set_footer(text=f'Có thể mua tại shop: {dc["gia_tien_ngoc"]:,} tiên ngọc')
    
    return embed


# ============================================================
# DROPDOWN 1: CHỌN ĐẠO CỤ (dùng cho /dungdaocu)
# ============================================================
class DaoCuSelect(discord.ui.Select):
    def __init__(self, ds_dao_cu: list):
        self.ds_dao_cu = ds_dao_cu
        
        options = []
        for i, dc in enumerate(ds_dao_cu[:25]):
            if dc.get('he'):
                he_emoji = HE_EMOJI.get(dc['he'], '❓')
                desc = f"{he_emoji} Hệ {dc['he']} — có {dc['so_luong']}"
            else:
                he_emoji = '🌀'
                desc = f"🌀 Mọi hệ — có {dc['so_luong']}"

            options.append(discord.SelectOption(
                label=dc['ten'][:100],
                description=desc,
                emoji=he_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đạo cụ tăng tinh khiết...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        dc = self.ds_dao_cu[idx]
        
        player = get_player_full_info(interaction.user.id)
        ds_linh_can = get_player_linh_can_full(player.player_id)
        
       # ⭐ Nếu đạo cụ không có hệ (he = None) → cho chọn MỌI linh căn chưa max
        if dc.get('he') is None:
            ds_linh_can_phu_hop = [
                lc for lc in ds_linh_can
                if lc['do_tinh_khiet'] < 100
            ]
        else:
            ds_linh_can_phu_hop = [
                lc for lc in ds_linh_can
                if lc['he'] == dc['he'] and lc['do_tinh_khiet'] < 100
            ]
        
        if not ds_linh_can_phu_hop:
            await interaction.response.send_message(
                f'❌ Bạn không có linh căn hệ **{dc["he"]}** nào chưa max tinh khiết!',
                ephemeral=True,
            )
            return
        if dc.get('he'):
            he_line = f'Hệ: {HE_EMOJI.get(dc["he"], "")} **{dc["he"]}**'
        else:
            he_line = '🌀 **Mọi hệ**'

        embed = discord.Embed(
            title='🌟 Chọn Linh Căn',
            description=(
                f'Đạo cụ: **{dc["ten"]}**\n'
                f'{he_line}\n\n'
                f'Chọn linh căn muốn tăng tinh khiết:'
            ),
            color=discord.Color.gold(),
        )

        
        view = LinhCanSelectView(dc, ds_linh_can_phu_hop)
        await interaction.response.edit_message(embed=embed, view=view)


# ============================================================
# DROPDOWN 2: CHỌN LINH CĂN
# ============================================================
class LinhCanSelect(discord.ui.Select):
    def __init__(self, dao_cu: dict, ds_linh_can: list):
        self.dao_cu = dao_cu
        self.ds_linh_can = ds_linh_can
        
        options = []
        for i, lc in enumerate(ds_linh_can[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(lc['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=lc['ten'][:100],
                description=f"Tinh khiết: {lc['do_tinh_khiet']:.1f}%",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn linh căn...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        lc = self.ds_linh_can[idx]
        
        player = get_player_full_info(interaction.user.id)
        
        ket_qua = dung_dao_cu_tang_tinh_khiet(
            player.player_id,
            self.dao_cu['id'],
            lc['linh_can_id'],
        )
        
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        self.view.stop()
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                f'❌ {ket_qua["loi"]}',
                ephemeral=True,
            )
            return
        
        embed = discord.Embed(
            title='✅ Tăng Tinh Khiết Thành Công',
            description=(
                f'Đã dùng **{ket_qua["ten_dao_cu"]}**\n'
                f'cho **{ket_qua["ten_linh_can"]}**'
            ),
            color=discord.Color.green(),
        )
        embed.add_field(
            name='💧 Độ tinh khiết',
            value=(
                f'`{ket_qua["tinh_khiet_cu"]:.2f}%` → `{ket_qua["tinh_khiet_moi"]:.2f}%`\n'
                f'(+{ket_qua["amount"]:.2f}%)'
            ),
            inline=False,
        )
        
        if ket_qua['tinh_khiet_moi'] >= 100:
            embed.add_field(
                name='🎯 Sẵn sàng đột phá!',
                value='Dùng `/dotpha-linhcan` để đột phá phẩm cấp.',
                inline=False,
            )
        
        await interaction.response.send_message(embed=embed)


class LinhCanSelectView(discord.ui.View):
    def __init__(self, dao_cu: dict, ds_linh_can: list):
        super().__init__(timeout=120)
        self.add_item(LinhCanSelect(dao_cu, ds_linh_can))


class DaoCuView(discord.ui.View):
    def __init__(self, ds_dao_cu: list):
        super().__init__(timeout=120)
        self.add_item(DaoCuSelect(ds_dao_cu))


# ============================================================
# DROPDOWN XEM CHI TIẾT ĐẠO CỤ
# ============================================================
class XemChiTietSelect(discord.ui.Select):
    def __init__(self, ds_dc: list):
        self.ds_dc = ds_dc
        
        options = []
        for i, dc in enumerate(ds_dc[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(dc['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=dc['ten'][:100],
                description=f"×{dc['so_luong']} — {PHAM_CAP_TEN.get(dc['pham_cap'], dc['pham_cap'])}",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đạo cụ để xem chi tiết...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        dc = self.ds_dc[idx]
        
        embed = build_dao_cu_chi_tiet_embed(dc)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class XemChiTietView(discord.ui.View):
    def __init__(self, ds_dc: list):
        super().__init__(timeout=180)
        self.add_item(XemChiTietSelect(ds_dc))


# ============================================================
# COG
# ============================================================
class DaoCu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # ===== /dungdaocu =====
    @app_commands.command(
        name='dungdaocu',
        description='Dùng đạo cụ tăng tinh khiết cho linh căn'
    )
    async def dungdaocu(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_dao_cu = get_dao_cu_tang_tinh_khiet_cua_player(player.player_id)
        
        if not ds_dao_cu:
            await interaction.followup.send(
                '❌ Bạn không có đạo cụ tăng tinh khiết nào!\n'
                'Mua tại `/shop` (tab Đạo cụ).'
            )
            return
        
        embed = discord.Embed(
            title='💧 Dùng Đạo Cụ Tăng Tinh Khiết',
            description=(
                f'Bạn có `{len(ds_dao_cu)}` loại đạo cụ.\n'
                f'Chọn đạo cụ muốn dùng bên dưới.'
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text='Lưu ý: Đạo cụ phải khớp hệ với linh căn')
        
        view = DaoCuView(ds_dao_cu)
        await interaction.followup.send(embed=embed, view=view)
    
    # ===== /daocu =====
    @app_commands.command(
        name='daocu',
        description='Xem danh sách đạo cụ sở hữu'
    )
    async def daocu(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_dc = get_player_dao_cu_full(player.player_id)
        
        if not ds_dc:
            await interaction.followup.send(
                '🎁 Bạn chưa có đạo cụ nào!\n'
                'Mua tại `/shop` (tab Đạo cụ).'
            )
            return
        
        # Group theo loại
        nhom = {}
        for dc in ds_dc:
            loai = dc['loai']
            if loai not in nhom:
                nhom[loai] = []
            nhom[loai].append(dc)
        
        embed = discord.Embed(
            title=f'🎁 Đạo Cụ của {player.ten_nhan_vat}',
            description=(
                f'Tổng: `{len(ds_dc)}` loại\n'
                f'Chọn từ dropdown để xem chi tiết.'
            ),
            color=discord.Color.purple(),
        )
        
        for loai in ['DotPhaLinhCan', 'TangTinhKhiet', 'Khac']:
            if loai not in nhom:
                continue
            ds = nhom[loai]
            lines = []
            for dc in ds[:15]:
                pc_emoji = PHAM_CAP_EMOJI.get(dc['pham_cap'], '⚪')
                he_str = ''
                if dc.get('he'):
                    he_str = f' {HE_EMOJI.get(dc["he"], "")}'
                lines.append(f'{pc_emoji} **{dc["ten"]}**{he_str} — `×{dc["so_luong"]:,}`')
            if len(ds) > 15:
                lines.append(f'*... và {len(ds) - 15} loại khác*')
            embed.add_field(
                name=f'{LOAI_DAO_CU.get(loai, loai)} ({len(ds)})',
                value='\n'.join(lines),
                inline=False,
            )
        
        embed.set_footer(text='Dùng /daocu-chitiet <tên> để xem chi tiết')
        
        view = XemChiTietView(ds_dc)
        await interaction.followup.send(embed=embed, view=view)
    
    # ===== /daocu-chitiet =====
    @app_commands.command(
        name='daocu-chitiet',
        description='Xem chi tiết đạo cụ'
    )
    @app_commands.describe(ten='Tên đạo cụ')
    async def daocu_chitiet(
        self,
        interaction: discord.Interaction,
        ten: str,
    ):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_dc = get_player_dao_cu_full(player.player_id)
        
        # Tìm đạo cụ
        match = None
        for dc in ds_dc:
            if dc['ten'].lower() == ten.lower():
                match = dc
                break
        
        if not match:
            await interaction.followup.send(
                f'❌ Bạn không có đạo cụ `{ten}`!'
            )
            return
        
        embed = build_dao_cu_chi_tiet_embed(match)
        await interaction.followup.send(embed=embed)
    
    # ===== Autocomplete cho /daocu-chitiet =====
    @daocu_chitiet.autocomplete('ten')
    async def daocu_chitiet_ten_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete tên đạo cụ."""
        player = get_player_full_info(interaction.user.id)
        if not player:
            return []
        
        ds_dc = get_player_dao_cu_full(player.player_id)
        
        if current:
            ds_dc = [dc for dc in ds_dc if current.lower() in dc['ten'].lower()]
        
        return [
            app_commands.Choice(name=dc['ten'][:100], value=dc['ten'][:100])
            for dc in ds_dc[:25]
        ]


async def setup(bot):
    await bot.add_cog(DaoCu(bot))