import discord
from discord import app_commands
from discord.ext import commands

from database.player_repo import (
    get_player_full_info,
    get_player_linh_thao,
    get_player_dan_duoc,
    get_player_dao_cu,
    get_player_khoang_thach,
    get_dan_phuong_trong_tui,
    get_cong_phap_trong_tui,
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

LOAI_KHOANG_THACH = {
    'LuyenKhi': '⚒️ Luyện Khí',
    'VePhu': '📜 Vẽ Phù',
    'CaHai': '⚒️📜 Cả hai',
}

LOAI_DAO_CU = {
    'DotPhaLinhCan': '🔮 Đột phá linh căn',
    'TangTinhKhiet': '💧 Tăng tinh khiết',
    'Khac': '❓ Khác',
    'TangTiLeDotPha': '📜 Tăng tỉ lệ đột phá',
}

GIAI_CAP_CONG_PHAP = {
    'Hoang': '📗 Hoàng giai',
    'Huyen': '📘 Huyền giai',
    'Dia': '📙 Địa giai',
    'Thien': '📕 Thiên giai',
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
# HÀM BUILD EMBED CHO TỪNG TAB
# ============================================================
def build_tab_tong_quan(ds_lt, ds_dd, ds_dc, ds_kt, ds_dp, ds_cp) -> discord.Embed:
    embed = discord.Embed(
        title='🎒 Túi Đồ',
        description='Tổng quan các vật phẩm bạn sở hữu',
        color=discord.Color.blue(),
    )
    
    tong_lt = sum(x['so_luong'] for x in ds_lt)
    tong_dd = sum(x['so_luong'] for x in ds_dd)
    tong_dc = sum(x['so_luong'] for x in ds_dc)
    tong_kt = sum(x['so_luong'] for x in ds_kt)
    tong_dp = sum(x['so_luong'] for x in ds_dp)
    tong_cp = sum(x['so_luong'] for x in ds_cp)
    
    embed.add_field(
        name='🌿 Linh thảo',
        value=f'`{len(ds_lt)}` loại — `{tong_lt:,}` cái',
        inline=True,
    )
    embed.add_field(
        name='💊 Đan dược',
        value=f'`{len(ds_dd)}` loại — `{tong_dd:,}` cái',
        inline=True,
    )
    embed.add_field(
        name='🎁 Đạo cụ',
        value=f'`{len(ds_dc)}` loại — `{tong_dc:,}` cái',
        inline=True,
    )
    embed.add_field(
        name='⛰ Khoáng thạch',
        value=f'`{len(ds_kt)}` loại — `{tong_kt:,}` cái',
        inline=True,
    )
    embed.add_field(
        name='📜 Đan phương',
        value=f'`{len(ds_dp)}` loại — `{tong_dp:,}` cái',
        inline=True,
    )
    embed.add_field(
        name='📖 Công pháp',
        value=f'`{len(ds_cp)}` loại — `{tong_cp:,}` cái',
        inline=True,
    )
    
    embed.set_footer(text='Chọn tab bên dưới để xem chi tiết')
    return embed


def build_tab_linh_thao(ds_lt) -> discord.Embed:
    embed = discord.Embed(
        title='🌿 Linh Thảo',
        description=f'Tổng: `{len(ds_lt)}` loại',
        color=discord.Color.green(),
    )
    
    if not ds_lt:
        embed.description = 'Bạn chưa có linh thảo nào.'
        return embed
    
    nhom = {}
    for lt in ds_lt:
        pc = lt['pham_cap']
        if pc not in nhom:
            nhom[pc] = []
        nhom[pc].append(lt)
    
    for pc in ['Pham', 'Linh', 'Bao', 'Tien', 'Than']:
        if pc not in nhom:
            continue
        ds = nhom[pc]
        lines = []
        for lt in ds[:15]:
            emoji = PHAM_CAP_EMOJI.get(pc, '⚪')
            he = lt.get('he')
            he_str = f' ({HE_EMOJI.get(he, "")})' if he else ''
            lines.append(f'{emoji} **{lt["ten"]}**{he_str} — `×{lt["so_luong"]:,}`')
        if len(ds) > 15:
            lines.append(f'*... và {len(ds) - 15} loại khác*')
        embed.add_field(
            name=f'{PHAM_CAP_TEN[pc]} ({len(ds)})',
            value='\n'.join(lines),
            inline=False,
        )
    
    return embed


def build_tab_dan_duoc(ds_dd) -> discord.Embed:
    embed = discord.Embed(
        title='💊 Đan Dược',
        description=f'Tổng: `{len(ds_dd)}` loại',
        color=discord.Color.gold(),
    )
    
    if not ds_dd:
        embed.description = 'Bạn chưa có đan dược nào.'
        return embed
    
    nhom = {}
    for dd in ds_dd:
        pc = dd['pham_cap']
        if pc not in nhom:
            nhom[pc] = []
        nhom[pc].append(dd)
    
    for pc in ['Pham', 'Linh', 'Bao', 'Tien', 'Than']:
        if pc not in nhom:
            continue
        ds = nhom[pc]
        lines = []
        for dd in ds[:15]:
            emoji = PHAM_CAP_EMOJI.get(pc, '⚪')
            lines.append(f'{emoji} **{dd["ten"]}** — `×{dd["so_luong"]:,}`')
        if len(ds) > 15:
            lines.append(f'*... và {len(ds) - 15} loại khác*')
        embed.add_field(
            name=f'{PHAM_CAP_TEN[pc]} ({len(ds)})',
            value='\n'.join(lines),
            inline=False,
        )
    
    return embed


def build_tab_dao_cu(ds_dc) -> discord.Embed:
    embed = discord.Embed(
        title='🎁 Đạo Cụ',
        description=f'Tổng: `{len(ds_dc)}` loại',
        color=discord.Color.purple(),
    )
    
    if not ds_dc:
        embed.description = 'Bạn chưa có đạo cụ nào.'
        return embed
    
    nhom = {}
    for dc in ds_dc:
        loai = dc['loai']
        if loai not in nhom:
            nhom[loai] = []
        nhom[loai].append(dc)
    
    for loai in ['DotPhaLinhCan', 'TangTinhKhiet','TangTiLeDotPha', 'Khac']:
        if loai not in nhom:
            continue
        ds = nhom[loai]
        lines = []
        for dc in ds[:15]:
            pc_emoji = PHAM_CAP_EMOJI.get(dc['pham_cap'], '⚪')
            he = dc.get('he')
            he_str = f' {HE_EMOJI.get(he, "")}' if he else ''
            lines.append(f'{pc_emoji} **{dc["ten"]}**{he_str} — `×{dc["so_luong"]:,}`')
        if len(ds) > 15:
            lines.append(f'*... và {len(ds) - 15} loại khác*')
        embed.add_field(
            name=f'{LOAI_DAO_CU.get(loai, loai)} ({len(ds)})',
            value='\n'.join(lines),
            inline=False,
        )
    
    return embed


def build_tab_khoang_thach(ds_kt) -> discord.Embed:
    embed = discord.Embed(
        title='⛰ Khoáng Thạch',
        description=f'Tổng: `{len(ds_kt)}` loại',
        color=discord.Color.dark_gray(),
    )
    
    if not ds_kt:
        embed.description = 'Bạn chưa có khoáng thạch nào.'
        return embed
    
    nhom = {}
    for kt in ds_kt:
        loai = kt['loai']
        if loai not in nhom:
            nhom[loai] = []
        nhom[loai].append(kt)
    
    for loai in ['LuyenKhi', 'VePhu', 'CaHai']:
        if loai not in nhom:
            continue
        ds = nhom[loai]
        lines = []
        for kt in ds[:15]:
            pc_emoji = PHAM_CAP_EMOJI.get(kt['pham_cap'], '⚪')
            he = kt.get('he')
            he_str = f' {HE_EMOJI.get(he, "")}' if he else ''
            lines.append(
                f'{pc_emoji} **{kt["ten"]}**{he_str} — `×{kt["so_luong"]:,}` '
                f'(bán: `{kt["gia_ban"]:,}`)'
            )
        if len(ds) > 15:
            lines.append(f'*... và {len(ds) - 15} loại khác*')
        embed.add_field(
            name=f'{LOAI_KHOANG_THACH.get(loai, loai)} ({len(ds)})',
            value='\n'.join(lines),
            inline=False,
        )
    
    return embed


# ⭐ 2 HÀM MỚI
def build_tab_dan_phuong(ds_dp) -> discord.Embed:
    """Build tab Đan phương."""
    embed = discord.Embed(
        title='📜 Đan Phương',
        description=f'Tổng: `{len(ds_dp)}` loại',
        color=discord.Color.orange(),
    )
    
    if not ds_dp:
        embed.description = 'Bạn chưa có đan phương nào.'
        return embed
    
    nhom = {}
    for dp in ds_dp:
        pc = dp.get('pham_cap', 'Khac')
        if pc not in nhom:
            nhom[pc] = []
        nhom[pc].append(dp)
    
    for pc in ['Pham', 'Linh', 'Bao', 'Tien', 'Than']:
        if pc not in nhom:
            continue
        ds = nhom[pc]
        lines = []
        for dp in ds[:15]:
            emoji = PHAM_CAP_EMOJI.get(pc, '⚪')
            lines.append(f'{emoji} **{dp["ten"]}** — `×{dp["so_luong"]:,}`')
        if len(ds) > 15:
            lines.append(f'*... và {len(ds) - 15} loại khác*')
        embed.add_field(
            name=f'{PHAM_CAP_TEN.get(pc, pc)} ({len(ds)})',
            value='\n'.join(lines),
            inline=False,
        )
    
    embed.set_footer(text='Dùng /hoc để học đan phương')
    return embed


def build_tab_cong_phap(ds_cp) -> discord.Embed:
    """Build tab Công pháp."""
    embed = discord.Embed(
        title='📖 Công Pháp',
        description=f'Tổng: `{len(ds_cp)}` loại',
        color=discord.Color.purple(),
    )
    
    if not ds_cp:
        embed.description = 'Bạn chưa có công pháp nào.'
        return embed
    
    nhom = {}
    for cp in ds_cp:
        gc = cp.get('giai_cap', 'Khac')
        if gc not in nhom:
            nhom[gc] = []
        nhom[gc].append(cp)
    
    for gc in ['Hoang', 'Huyen', 'Dia', 'Thien']:
        if gc not in nhom:
            continue
        ds = nhom[gc]
        lines = []
        for cp in ds[:15]:
            he = cp.get('he')
            he_str = ''
            if he:
                try:
                    import json
                    he_list = json.loads(he) if isinstance(he, str) else he
                    if isinstance(he_list, list):
                        he_str = ' ' + ' '.join(HE_EMOJI.get(h, '') for h in he_list)
                except:
                    pass
            lines.append(f'📖 **{cp["ten"]}**{he_str} — `×{cp["so_luong"]:,}`')
        if len(ds) > 15:
            lines.append(f'*... và {len(ds) - 15} loại khác*')
        embed.add_field(
            name=f'{GIAI_CAP_CONG_PHAP.get(gc, gc)} ({len(ds)})',
            value='\n'.join(lines),
            inline=False,
        )
    
    embed.set_footer(text='Dùng /hoc để học công pháp')
    return embed


# ============================================================
# DROPDOWN CHỌN TAB
# ============================================================
class TuiDoSelect(discord.ui.Select):
    def __init__(self, ds_lt, ds_dd, ds_dc, ds_kt, ds_dp, ds_cp):
        self.ds_lt = ds_lt
        self.ds_dd = ds_dd
        self.ds_dc = ds_dc
        self.ds_kt = ds_kt
        self.ds_dp = ds_dp
        self.ds_cp = ds_cp
        
        options = [
            discord.SelectOption(label='Tổng quan', emoji='📊', value='tong_quan'),
            discord.SelectOption(
                label=f'Linh thảo ({len(ds_lt)})',
                emoji='🌿',
                value='linh_thao',
            ),
            discord.SelectOption(
                label=f'Đan dược ({len(ds_dd)})',
                emoji='💊',
                value='dan_duoc',
            ),
            discord.SelectOption(
                label=f'Đạo cụ ({len(ds_dc)})',
                emoji='🎁',
                value='dao_cu',
            ),
            discord.SelectOption(
                label=f'Khoáng thạch ({len(ds_kt)})',
                emoji='⛰',
                value='khoang_thach',
            ),
            discord.SelectOption(
                label=f'Đan phương ({len(ds_dp)})',
                emoji='📜',
                value='dan_phuong',
            ),
            discord.SelectOption(
                label=f'Công pháp ({len(ds_cp)})',
                emoji='📖',
                value='cong_phap',
            ),
        ]
        
        super().__init__(
            placeholder='Chọn tab muốn xem...',
            min_values=1,
            max_values=1,
            options=options,
        )
    
    async def callback(self, interaction: discord.Interaction):
        tab = self.values[0]
        
        if tab == 'tong_quan':
            embed = build_tab_tong_quan(
                self.ds_lt, self.ds_dd, self.ds_dc, 
                self.ds_kt, self.ds_dp, self.ds_cp
            )
        elif tab == 'linh_thao':
            embed = build_tab_linh_thao(self.ds_lt)
        elif tab == 'dan_duoc':
            embed = build_tab_dan_duoc(self.ds_dd)
        elif tab == 'dao_cu':
            embed = build_tab_dao_cu(self.ds_dc)
        elif tab == 'khoang_thach':
            embed = build_tab_khoang_thach(self.ds_kt)
        elif tab == 'dan_phuong':
            embed = build_tab_dan_phuong(self.ds_dp)
        elif tab == 'cong_phap':
            embed = build_tab_cong_phap(self.ds_cp)
        else:
            embed = build_tab_tong_quan(
                self.ds_lt, self.ds_dd, self.ds_dc, 
                self.ds_kt, self.ds_dp, self.ds_cp
            )
        
        await interaction.response.edit_message(embed=embed, view=self.view)


class TuiDoView(discord.ui.View):
    def __init__(self, ds_lt, ds_dd, ds_dc, ds_kt, ds_dp, ds_cp):
        super().__init__(timeout=180)
        self.add_item(TuiDoSelect(ds_lt, ds_dd, ds_dc, ds_kt, ds_dp, ds_cp))


# ============================================================
# COG
# ============================================================
class TuiDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='bag',
        description='Xem túi đồ (linh thảo, đan dược, đạo cụ, khoáng thạch, đan phương, công pháp)'
    )
    async def tui(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        # 1. Check player
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.')
            return
        
        # 2. Lấy tất cả item
        ds_lt = get_player_linh_thao(player.player_id)
        ds_dd = get_player_dan_duoc(player.player_id)
        ds_dc = get_player_dao_cu(player.player_id)
        ds_kt = get_player_khoang_thach(player.player_id)
        ds_dp = get_dan_phuong_trong_tui(player.player_id)
        ds_cp = get_cong_phap_trong_tui(player.player_id)
        
        # 3. Build embed tổng quan
        embed = build_tab_tong_quan(ds_lt, ds_dd, ds_dc, ds_kt, ds_dp, ds_cp)
        
        # 4. Gửi view
        view = TuiDoView(ds_lt, ds_dd, ds_dc, ds_kt, ds_dp, ds_cp)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(TuiDo(bot))