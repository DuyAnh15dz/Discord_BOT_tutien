import discord
from discord import app_commands
from discord.ext import commands
import json

from database.player_repo import get_player_full_info, get_player_nghe_nghiep
from database.nghe_repo import (
    get_ds_bua_chu_full,
    check_du_nguyen_lieu_ve_bua,
    ve_bua_10_la_v3,
    get_ds_bua_chu_cua_player,
    dung_bua_chu,
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

LOAI_BUA = {
    'TanCong': '⚔️ Tấn công', 'PhongThu': '🛡️ Phòng thủ',
    'HoTro': '💚 Hỗ trợ', 'KhongChe': '🌀 Khống chế',
}

HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}


# ============================================================
# HELPER
# ============================================================

def format_effect(effect: dict) -> str:
    """Format effect dict thành text hiển thị."""
    if not isinstance(effect, dict):
        return '*Không có*'
    
    key_map = {
        'dmg': '💥 Sát thương',
        'element': '🌟 Hệ',
        'shield': '🛡️ Khiên',
        'turns': '🔄 Số lượt',
        'hp_hoi': '❤️ HP hồi',
        'mp_hoi': '💙 MP hồi',
        'stun_turns': '💫 Choáng (lượt)',
        'ti_le': '🎲 Tỉ lệ',
        'ti_le_te_liet': '⚡ Tê liệt',
        'ti_le_dong_bang': '❄️ Đóng băng',
        'roi_loan_turns': '🌀 Rối loạn',
        'ignore_def': '🚫 Bỏ qua phòng ngự',
    }
    
    lines = []
    for code, val in effect.items():
        label = key_map.get(code, code)
        
        if code == 'element':
            label = f'{HE_EMOJI.get(val, "")} Hệ {val}'
            lines.append(f'• {label}')
        elif isinstance(val, (int, float)):
            if 'turns' in code or 'ti_le' in code:
                lines.append(f'• {label}: `{val}`')
            else:
                lines.append(f'• {label}: `{val:,}`')
        else:
            lines.append(f'• {label}: `{val}`')
    
    return '\n'.join(lines)


# ============================================================
# COG
# ============================================================

class BuaChu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # ===== /vebua =====
    @app_commands.command(
        name='vebua',
        description='[Phù Lục Sư] Vẽ bùa chú (10 lá/lần)'
    )
    async def vebua(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        nghe = get_player_nghe_nghiep(player.player_id)
        if not nghe or nghe['loai'] != 'PhuLuc':
            await interaction.followup.send('❌ Bạn không phải **Phù Lục Sư**!')
            return
        
        ds_bc = get_ds_bua_chu_full()
        if not ds_bc:
            await interaction.followup.send('❌ Không có bùa chú nào!')
            return
        
        embed = discord.Embed(
            title='📜 Vẽ Bùa Chú',
            description=(
                f'Cấp nghề: `{nghe["cap_do"]}/{nghe["cap_toi_da"]}`\n'
                f'Mỗi lần vẽ: **10 lá**'
            ),
            color=discord.Color.orange(),
        )
        
        view = VeBuaSelectView(player.player_id, ds_bc)
        await interaction.followup.send(embed=embed, view=view)
    
    # ===== /buachu =====
    @app_commands.command(name='buachu', description='Xem bùa chú sở hữu')
    async def buachu(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_bc = get_ds_bua_chu_cua_player(player.player_id)
        if not ds_bc:
            await interaction.followup.send('📜 Bạn chưa có bùa chú nào!')
            return
        
        embed = discord.Embed(
            title=f'📜 Bùa Chú của {player.ten_nhan_vat}',
            description=f'Tổng: `{len(ds_bc)}` loại',
            color=discord.Color.orange(),
        )
        
        nhom = {}
        for bc in ds_bc:
            nhom.setdefault(bc['loai'], []).append(bc)
        
        for loai in ['TanCong', 'PhongThu', 'HoTro', 'KhongChe']:
            if loai not in nhom:
                continue
            ds = nhom[loai]
            lines = []
            for bc in ds[:10]:
                pc_emoji = PHAM_CAP_EMOJI.get(bc['pham_cap'], '⚪')
                he_emoji = HE_EMOJI.get(bc['he'], '') if bc['he'] else ''
                lines.append(f'{pc_emoji} {he_emoji} **{bc["ten"]}** — `×{bc["so_luong"]}`')
            embed.add_field(
                name=f'{LOAI_BUA.get(loai, loai)} ({len(ds)})',
                value='\n'.join(lines),
                inline=False,
            )
        
        embed.set_footer(text='Dùng /dungbua để sử dụng')
        await interaction.followup.send(embed=embed)
    
    # ===== /dungbua =====
    @app_commands.command(name='dungbua', description='Dùng bùa chú')
    async def dungbua(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_bc = get_ds_bua_chu_cua_player(player.player_id)
        if not ds_bc:
            await interaction.followup.send('❌ Bạn chưa có bùa chú nào!')
            return
        
        embed = discord.Embed(
            title='🎴 Dùng Bùa Chú',
            description='Chọn bùa chú muốn dùng.',
            color=discord.Color.orange(),
        )
        view = DungBuaSelectView(player.player_id, ds_bc)
        await interaction.followup.send(embed=embed, view=view)


# ============================================================
# SELECTS & VIEWS — VẼ BÙA
# ============================================================

class VeBuaSelect(discord.ui.Select):
    def __init__(self, player_id: int, ds_bc: list):
        self.player_id = player_id
        self.ds_bc = ds_bc
        
        options = []
        for i, bc in enumerate(ds_bc[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(bc['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=bc['ten'][:100],
                description=f"{LOAI_BUA.get(bc['loai'], bc['loai'])} — {PHAM_CAP_TEN.get(bc['pham_cap'], '')}",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn bùa chú muốn vẽ...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        bc = self.ds_bc[idx]
        
        check = check_du_nguyen_lieu_ve_bua(self.player_id, bc['id'])
        if not check:
            await interaction.response.send_message('❌ Lỗi!', ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f'📜 Vẽ {bc["ten"]} × 10 lá',
            description=bc.get('mo_ta') or '*Không có mô tả*',
            color=discord.Color.orange(),
        )
        
        effect = bc['effect']
        if isinstance(effect, str):
            effect = json.loads(effect)
        
        embed.add_field(
            name='✨ Hiệu ứng (mỗi lá)',
            value=format_effect(effect),
            inline=False,
        )
        
        lines = []
        mp_status = '✅' if check['mp_co'] >= check['mp_can'] else '❌'
        lines.append(f'{mp_status} 💙 MP: `{check["mp_co"]:,}/{check["mp_can"]:,}`')
        
        if check['mau']:
            mau_status = '✅' if check['mau']['co'] >= check['mau']['can'] else '❌'
            lines.append(
                f'{mau_status} 🩸 {check["mau"]["ten"]}: '
                f'`{check["mau"]["co"]:,}/{check["mau"]["can"]:,}`'
            )
        
        if check['linh_dich']:
            ld_status = '✅' if check['linh_dich']['co'] >= check['linh_dich']['can'] else '❌'
            lines.append(
                f'{ld_status} 💧 {check["linh_dich"]["ten"]}: '
                f'`{check["linh_dich"]["co"]:,}/{check["linh_dich"]["can"]:,}`'
            )
        
        embed.add_field(
            name='🧪 Nguyên liệu (cho 10 lá)',
            value='\n'.join(lines),
            inline=False,
        )
        
        if not check['du']:
            embed.add_field(
                name='❌ Không đủ nguyên liệu',
                value='Hãy cày thêm trước khi vẽ.',
                inline=False,
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        view = XacNhanVeBuaView(self.player_id, bc['id'])
        await interaction.response.edit_message(embed=embed, view=view)


class VeBuaSelectView(discord.ui.View):
    def __init__(self, player_id: int, ds_bc: list):
        super().__init__(timeout=180)
        self.add_item(VeBuaSelect(player_id, ds_bc))


class XacNhanVeBuaView(discord.ui.View):
    def __init__(self, player_id: int, bua_chu_id: int):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.bua_chu_id = bua_chu_id
    
    @discord.ui.button(label='Vẽ 10 lá', emoji='🖌️', style=discord.ButtonStyle.success)
    async def xac_nhan(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        ket_qua = ve_bua_10_la_v3(self.player_id, self.bua_chu_id)
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                f'❌ {ket_qua["loi"]}', ephemeral=True
            )
            return
        
        thanh_cong_count = ket_qua['so_thanh_cong']
        
        if thanh_cong_count > 0:
            embed = discord.Embed(
                title='🎉 Vẽ Bùa Hoàn Tất!',
                description=f'**{ket_qua["ten"]}** — `{thanh_cong_count}/10` lá thành công',
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title='💔 Vẽ Bùa Thất Bại',
                description=f'Không lá **{ket_qua["ten"]}** nào thành công...',
                color=discord.Color.red(),
            )
        
        embed.add_field(name='📊 Tỉ lệ', value=f'`{ket_qua["ti_le"]:.2f}%`', inline=True)
        embed.add_field(name='✍️ Exp nghề', value=f'`+{ket_qua["exp_nhan"]:,}`', inline=True)
        embed.add_field(name='💙 MP dùng', value=f'`-{ket_qua["mp_da_dung"]:,}`', inline=True)
        
        chi_tiet_lines = []
        for la in ket_qua['chi_tiet_la']:
            if la['thanh_cong']:
                chi_tiet_lines.append(f'✅ Lá {la["stt"]}: `{la["roll"]:.1f}`')
            else:
                chi_tiet_lines.append(f'❌ Lá {la["stt"]}: `{la["roll"]:.1f}`')
        
        embed.add_field(
            name='🔍 Chi tiết 10 lá',
            value='\n'.join(chi_tiet_lines),
            inline=False,
        )
        
        await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label='Hủy', emoji='❌', style=discord.ButtonStyle.danger)
    async def huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message('❌ Đã hủy.', ephemeral=True)


# ============================================================
# SELECTS & VIEWS — DÙNG BÙA
# ============================================================

class DungBuaSelect(discord.ui.Select):
    def __init__(self, player_id: int, ds_bc: list):
        self.player_id = player_id
        self.ds_bc = ds_bc
        
        options = []
        for i, bc in enumerate(ds_bc[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(bc['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=f"{bc['ten']} (×{bc['so_luong']})",
                description=LOAI_BUA.get(bc['loai'], bc['loai']),
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn bùa chú muốn dùng...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        bc = self.ds_bc[idx]
        
        embed = discord.Embed(
            title=f'🎴 Dùng {bc["ten"]}',
            description=bc.get('mo_ta') or '*Không có mô tả*',
            color=discord.Color.orange(),
        )
        
        effect = bc['effect']
        if isinstance(effect, str):
            effect = json.loads(effect)
        
        embed.add_field(name='✨ Effect', value=format_effect(effect), inline=False)
        embed.add_field(name='📦 Số lượng', value=f'`×{bc["so_luong"]}`', inline=True)
        
        view = XacNhanDungBuaView(self.player_id, bc['id'])
        await interaction.response.edit_message(embed=embed, view=view)


class DungBuaSelectView(discord.ui.View):
    def __init__(self, player_id: int, ds_bc: list):
        super().__init__(timeout=180)
        self.add_item(DungBuaSelect(player_id, ds_bc))


class XacNhanDungBuaView(discord.ui.View):
    def __init__(self, player_id: int, bua_chu_id: int):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.bua_chu_id = bua_chu_id
    
    @discord.ui.button(label='Dùng', emoji='🎴', style=discord.ButtonStyle.success)
    async def dung(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        ket_qua = dung_bua_chu(self.player_id, self.bua_chu_id)
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                f'❌ {ket_qua["loi"]}', ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title='✅ Dùng Bùa Thành Công',
            description=f'Bạn đã dùng **{ket_qua["ten"]}**.',
            color=discord.Color.green(),
        )
        
        kq = ket_qua['ket_qua']
        loai = ket_qua['loai']
        
        if loai == 'HoTro':
            lines = []
            if kq.get('hp_hoi', 0) > 0:
                lines.append(f'❤️ Hồi `+{kq["hp_hoi"]:,}` HP')
            if kq.get('mp_hoi', 0) > 0:
                lines.append(f'💙 Hồi `+{kq["mp_hoi"]:,}` MP')
            embed.add_field(
                name='💊 Hiệu ứng',
                value='\n'.join(lines) or '*Không có*',
                inline=False,
            )
        
        elif loai == 'PhongThu':
            embed.add_field(
                name='🛡️ Khiên',
                value=(
                    f'• Sát thương hấp thụ: `{kq.get("shield", 0):,}`\n'
                    f'• Số lượt: `{kq.get("turns", 0)}`'
                ),
                inline=False,
            )
        
        elif loai in ('TanCong', 'KhongChe'):
            embed.add_field(
                name='⚔️ Combat',
                value='Bùa sẽ được kích hoạt trong combat tiếp theo!',
                inline=False,
            )
        
        await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label='Hủy', emoji='❌', style=discord.ButtonStyle.danger)
    async def huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message('❌ Đã hủy.', ephemeral=True)


# ============================================================
# SETUP
# ============================================================

async def setup(bot):
    await bot.add_cog(BuaChu(bot))