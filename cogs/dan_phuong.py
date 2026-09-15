import discord
from discord import app_commands
from discord.ext import commands
import json

from database.connection import get_connection
from database.player_repo import (
    get_player_full_info,
    get_player_dan_phuong_da_hoc,
    get_dan_phuong_chi_tiet,
    check_du_nguyen_lieu,
)


# ============================================================
# MAPPING
# ============================================================
PHAM_CAP_EMOJI = {
    'Pham': '🟤', 'Linh': '🟢', 'Bao': '🔵', 'Tien': '🟣', 'Than': '🟡',
}

PHAM_CAP_TEN = {
    'Pham': 'Phàm phẩm', 'Linh': 'Linh phẩm', 'Bao': 'Bảo phẩm',
    'Tien': 'Tiên phẩm', 'Than': 'Thần phẩm',
}

LOAI_DAN = {
    'HoiPhuc': '💊 Hồi phục',
    'DotPha': '⚡ Đột phá',
    'TangTuVi': '🔮 Tăng tu vi',
    'Buff': '✨ Buff',
    'Doc': '☠️ Độc',
}

HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}

HE_TEN = {
    'Kim': 'Kim', 'Moc': 'Mộc', 'Thuy': 'Thủy', 'Hoa': 'Hỏa', 'Tho': 'Thổ',
    'Loi': 'Lôi', 'Bang': 'Băng', 'Phong': 'Phong', 'Duong': 'Dương', 'Am': 'Âm',
}


# ============================================================
# DROPDOWN CHỌN ĐAN PHƯƠNG
# ============================================================
class DanPhuongSelect(discord.ui.Select):
    def __init__(self, ds_dp: list):
        self.ds_dp = ds_dp
        
        options = []
        for i, dp in enumerate(ds_dp[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(dp['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=dp['ten'][:100],
                description=PHAM_CAP_TEN.get(dp['pham_cap'], dp['pham_cap']),
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đan phương để xem chi tiết...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        dp = self.ds_dp[idx]
        
        player = get_player_full_info(interaction.user.id)
        
        # Build embed chi tiết
        embed = build_chi_tiet_dan_phuong_embed(player.player_id, dp['dan_duoc_id'])
        
        # Thêm field nghiên cứu
        nghien_cuu = dp.get('so_lan_nghien_cuu', 0)
        if nghien_cuu > 0:
            embed.add_field(
                name='📖 Nghiên cứu',
                value=(
                    f'• Số lần: `{nghien_cuu}`\n'
                    f'• Bonus tỉ lệ cơ bản: `+{nghien_cuu}%`'
                ),
                inline=False,
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DanPhuongView(discord.ui.View):
    def __init__(self, ds_dp: list):
        super().__init__(timeout=180)
        self.add_item(DanPhuongSelect(ds_dp))


# ============================================================
# BUILD EMBED
# ============================================================
def build_chi_tiet_dan_phuong_embed(player_id: int, dan_duoc_id: int) -> discord.Embed:
    """Build embed chi tiết đan phương."""
    chi_tiet = get_dan_phuong_chi_tiet(player_id, dan_duoc_id)
    
    if not chi_tiet:
        embed = discord.Embed(
            title='❌ Không tìm thấy',
            description='Bạn chưa học đan phương này!',
            color=discord.Color.red(),
        )
        return embed
    
    dan = chi_tiet['dan_duoc']
    nguyen_lieu = chi_tiet['nguyen_lieu']
    
    pc_emoji = PHAM_CAP_EMOJI.get(dan['pham_cap'], '⚪')
    pc_ten = PHAM_CAP_TEN.get(dan['pham_cap'], dan['pham_cap'])
    loai_str = LOAI_DAN.get(dan['loai'], dan['loai'])
    
    embed = discord.Embed(
        title=f'📜 {dan["ten"]}',
        description=dan.get('mo_ta') or '*Không có mô tả*',
        color=discord.Color.orange(),
    )
    
    # Thông tin
    embed.add_field(
        name='📋 Thông tin',
        value=(
            f'📌 **{pc_ten}**\n'
            f'🏷️ Loại: `{loai_str}`'
        ),
        inline=False,
    )
    
    # Nguyên liệu
    if nguyen_lieu:
        check = check_du_nguyen_lieu(player_id, dan_duoc_id)
        ds_co = check['ds_co']
        
        lines = []
        for nl in nguyen_lieu:
            he_emoji = HE_EMOJI.get(nl['he'], '') if nl.get('he') else ''
            co = ds_co.get(nl['linh_thao_id'], 0)
            can = nl['so_luong']
            
            if co >= can:
                status = '✅'
            elif co > 0:
                status = '⚠️'
            else:
                status = '❌'
            
            lines.append(
                f'{status} {he_emoji} **{nl["ten"]}** — `{co}/{can}`'
            )
        
        embed.add_field(
            name=f'🌿 Nguyên liệu ({len(nguyen_lieu)})',
            value='\n'.join(lines),
            inline=False,
        )
        
        # Tỉ lệ thành công
        ti_le_max = nguyen_lieu[0].get('ti_le_thanh_cong_max', 0)
        if ti_le_max > 0:
            embed.add_field(
                name='⚗️ Tỉ lệ thành công tối đa',
                value=f'`{ti_le_max}%`',
                inline=True,
            )
    
    # Trạng thái đủ nguyên liệu
    check = check_du_nguyen_lieu(player_id, dan_duoc_id)
    if check['du']:
        embed.add_field(
            name='✅ Trạng thái',
            value='**Đủ nguyên liệu!** Dùng `/luyendan` để luyện.',
            inline=False,
        )
    else:
        thieu_lines = []
        for t in check['thieu']:
            thieu_lines.append(f'• **{t["ten"]}**: thiếu `{t["thieu"]}`')
        embed.add_field(
            name='❌ Trạng thái',
            value='**Thiếu nguyên liệu:**\n' + '\n'.join(thieu_lines),
            inline=False,
        )
    
    return embed


# ============================================================
# COG
# ============================================================
class DanPhuong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='danphuong',
        description='Xem danh sách đan phương đã học'
    )
    async def danphuong(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_dp = get_player_dan_phuong_da_hoc(player.player_id)
        
        if not ds_dp:
            await interaction.followup.send(
                '📜 Bạn chưa học đan phương nào!\n'
                'Dùng `/hoc loai:Đan phương` để học.'
            )
            return
        
        # Group theo phẩm cấp
        nhom = {}
        for dp in ds_dp:
            pc = dp['pham_cap']
            if pc not in nhom:
                nhom[pc] = []
            nhom[pc].append(dp)
        
        embed = discord.Embed(
            title=f'📜 Đan Phương của {player.ten_nhan_vat}',
            description=(
                f'Tổng: `{len(ds_dp)}` đan phương\n'
                f'Chọn từ dropdown để xem chi tiết.'
            ),
            color=discord.Color.orange(),
        )
        
        for pc in ['Pham', 'Linh', 'Bao', 'Tien', 'Than']:
            if pc not in nhom:
                continue
            ds = nhom[pc]
            lines = []
            for dp in ds[:15]:
                pc_emoji = PHAM_CAP_EMOJI.get(pc, '⚪')
                loai_str = LOAI_DAN.get(dp['loai'], dp['loai'])
                nghien_cuu = dp.get('so_lan_nghien_cuu', 0)
                nghien_cuu_str = f' `(+{nghien_cuu}%)`' if nghien_cuu > 0 else ''
                lines.append(f'{pc_emoji} **{dp["ten"]}** — *{loai_str}*{nghien_cuu_str}')
            if len(ds) > 15:
                lines.append(f'*... và {len(ds) - 15} loại khác*')
            embed.add_field(
                name=f'{PHAM_CAP_TEN.get(pc, pc)} ({len(ds)})',
                value='\n'.join(lines),
                inline=False,
            )
        
        embed.set_footer(text='Dùng /danphuong-chitiet <tên> để xem chi tiết')
        
        view = DanPhuongView(ds_dp)
        await interaction.followup.send(embed=embed, view=view)
    
    # ============================================================
    # /danphuong-chitiet
    # ============================================================
    @app_commands.command(
        name='danphuong-chitiet',
        description='Xem chi tiết đan phương đã học'
    )
    @app_commands.describe(ten='Tên đan phương')
    async def danphuong_chitiet(
        self,
        interaction: discord.Interaction,
        ten: str,
    ):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        # Tìm đan phương theo tên
        ds_dp = get_player_dan_phuong_da_hoc(player.player_id)
        
        match = None
        for dp in ds_dp:
            if dp['ten'].lower() == ten.lower():
                match = dp
                break
        
        if not match:
            await interaction.followup.send(
                f'❌ Bạn chưa học đan phương `{ten}`!'
            )
            return
        
        # Build embed chi tiết
        embed = build_chi_tiet_dan_phuong_embed(player.player_id, match['dan_duoc_id'])
        
        # Thêm field nghiên cứu
        nghien_cuu = match.get('so_lan_nghien_cuu', 0)
        if nghien_cuu > 0:
            embed.add_field(
                name='📖 Nghiên cứu',
                value=(
                    f'• Số lần: `{nghien_cuu}`\n'
                    f'• Bonus tỉ lệ cơ bản: `+{nghien_cuu}%`'
                ),
                inline=False,
            )
        
        await interaction.followup.send(embed=embed)
    
    # ============================================================
    # Autocomplete cho /danphuong-chitiet
    # ============================================================
    @danphuong_chitiet.autocomplete('ten')
    async def danphuong_chitiet_ten_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete tên đan phương đã học."""
        player = get_player_full_info(interaction.user.id)
        if not player:
            return []
        
        ds_dp = get_player_dan_phuong_da_hoc(player.player_id)
        
        if current:
            ds_dp = [dp for dp in ds_dp if current.lower() in dp['ten'].lower()]
        
        return [
            app_commands.Choice(name=dp['ten'][:100], value=dp['ten'][:100])
            for dp in ds_dp[:25]
        ]


async def setup(bot):
    await bot.add_cog(DanPhuong(bot))