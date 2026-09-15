import discord
from discord import app_commands
from discord.ext import commands

from database.player_repo import (
    get_player_full_info,
    get_dan_phuong_trong_tui,
    get_cong_phap_trong_tui,
    hoc_dan_phuong,
    hoc_cong_phap,
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


# ============================================================
# DROPDOWN HỌC ĐAN PHƯƠNG
# ============================================================
class DanPhuongHocSelect(discord.ui.Select):
    def __init__(self, ds_dp: list):
        self.ds_dp = ds_dp
        
        options = []
        for i, dp in enumerate(ds_dp[:25]):
            emoji = PHAM_CAP_EMOJI.get(dp['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=dp['ten'][:100],
                description=f"{PHAM_CAP_TEN.get(dp['pham_cap'], dp['pham_cap'])} — ×{dp['so_luong']}",
                emoji=emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đan phương muốn học...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        dp = self.ds_dp[idx]
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.response.send_message('❌ Bạn chưa đăng ký!', ephemeral=True)
            return
        
        try:
            dan_duoc_id = int(dp['item_code'].replace('dan_phuong_', ''))
        except ValueError:
            await interaction.response.send_message('❌ Lỗi item code!', ephemeral=True)
            return
        
        ket_qua = hoc_dan_phuong(player.player_id, dan_duoc_id)
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                'ket_qua["loi"]', ephemeral=True
                )
            return
        
        # ⭐ Xử lý theo loại
        if ket_qua['loai'] == 'hoc_moi':
            embed = discord.Embed(
                title='📜 Học Đan Phương Thành Công',
                description=f'Bạn đã học **{ket_qua["ten"]}**!',
                color=discord.Color.green(),
            )
            embed.add_field(
                name='✨ Công dụng',
                value='Bây giờ bạn có thể luyện đan này (nếu có đủ linh thảo).',
                inline=False,
            )
            embed.set_footer(text='Dùng /luyendan để bắt đầu luyện đan')
        
        else:  # nghien_cuu
            embed = discord.Embed(
                title='📖 Nghiên Cứu Đan Phương',
                description=f'Bạn đã nghiên cứu thêm về **{ket_qua["ten"]}**!',
                color=discord.Color.blue(),
            )
            embed.add_field(
                name='📊 Kết quả',
                value=(
                    f'• Số lần nghiên cứu: `{ket_qua["so_lan_nghien_cuu"]}`\n'
                    f'• Tỉ lệ cơ bản: `+{ket_qua["so_lan_nghien_cuu"]}%`'
                ),
                inline=False,
            )
            embed.set_footer(text='Tỉ lệ luyện đan đã được tăng!')
        
        await interaction.response.send_message(embed=embed)
        
        # Disable dropdown
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        self.view.stop()


class DanPhuongHocView(discord.ui.View):
    def __init__(self, ds_dp: list):
        super().__init__(timeout=120)
        self.add_item(DanPhuongHocSelect(ds_dp))


# ============================================================
# DROPDOWN HỌC CÔNG PHÁP
# ============================================================
class CongPhapHocSelect(discord.ui.Select):
    def __init__(self, ds_cp: list):
        self.ds_cp = ds_cp
        
        options = []
        for i, cp in enumerate(ds_cp[:25]):
            giai_cap = cp.get('giai_cap', '')
            emoji = '📖'
            
            options.append(discord.SelectOption(
                label=cp['ten'][:100],
                description=f"{GIAI_CAP_CONG_PHAP.get(giai_cap, giai_cap)} — ×{cp['so_luong']}",
                emoji=emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn công pháp muốn học...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        cp = self.ds_cp[idx]
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.response.send_message('❌ Bạn chưa đăng ký!', ephemeral=True)
            return
        
        try:
            cong_phap_id = int(cp['item_code'].replace('cong_phap_', ''))
        except ValueError:
            await interaction.response.send_message('❌ Lỗi item code!', ephemeral=True)
            return
        
        ket_qua = hoc_cong_phap(player.player_id, cong_phap_id)
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                ket_qua['loi'], ephemeral=True
            )
            return
        
        # ⭐ Xử lý theo loại
        if ket_qua['loai'] == 'hoc_moi':
            embed = discord.Embed(
                title='📖 Học Công Pháp Thành Công',
                description=f'Bạn đã học **{ket_qua["ten"]}**!',
                color=discord.Color.purple(),
            )
            
            if ket_qua.get('dang_tu_luyen'):
                embed.add_field(
                    name='✨ Trạng thái',
                    value='🟢 **Đang tu luyện** — Bonus sẽ được cộng vào stat.',
                    inline=False,
                )
            else:
                embed.add_field(
                    name='✨ Trạng thái',
                    value='🔴 **Chưa tu luyện** — Đã đạt giới hạn 2 công pháp song song.',
                    inline=False,
                )
        
        else:  # nghien_cuu
            thuan_thuc_moi = ket_qua.get('do_thuan_thuc_moi', 0)
            he_so_flat = 1 + (thuan_thuc_moi * 0.005)
            bonus_pct = thuan_thuc_moi * 0.05
            
            embed = discord.Embed(
                title='📖 Nghiên Cứu Công Pháp',
                description=f'Bạn đã nghiên cứu thêm về **{ket_qua["ten"]}**!',
                color=discord.Color.blue(),
            )
            embed.add_field(
                name='📊 Độ thuần thục',
                value=(
                    f'`{ket_qua["do_thuan_thuc_cu"]}%` → `{thuan_thuc_moi}%`\n'
                    f'Bonus flat: `×{he_so_flat:.2f}`\n'
                    f'Bonus percent: `+{bonus_pct:.2f}%`'
                ),
                inline=False,
            )
            embed.set_footer(text='Nghiên cứu thêm để tăng (max 100%)')
                
        await interaction.response.send_message(embed=embed)
        
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        self.view.stop()


class CongPhapHocView(discord.ui.View):
    def __init__(self, ds_cp: list):
        super().__init__(timeout=120)
        self.add_item(CongPhapHocSelect(ds_cp))


# ============================================================
# COG /hoc
# ============================================================
class Hoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='hoc',
        description='Học đan phương hoặc công pháp từ túi'
    )
    @app_commands.choices(loai=[
        app_commands.Choice(name='Đan phương', value='dan_phuong'),
        app_commands.Choice(name='Công pháp', value='cong_phap'),
    ])
    async def hoc(self, interaction: discord.Interaction, loai: str):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        if loai == 'dan_phuong':
            ds_items = get_dan_phuong_trong_tui(player.player_id)
            tieu_de = '📜 Học Đan Phương'
            color = discord.Color.orange()
            view_class = DanPhuongHocView
        else:
            ds_items = get_cong_phap_trong_tui(player.player_id)
            tieu_de = '📖 Học Công Pháp'
            color = discord.Color.purple()
            view_class = CongPhapHocView
        
        if not ds_items:
            await interaction.followup.send(
                f'❌ Bạn không có {loai.replace("_", " ")} nào trong túi!'
            )
            return
        
        embed = discord.Embed(
            title=tieu_de,
            description=(
                f'Bạn có `{len(ds_items)}` loại trong túi.\n'
                f'Chọn item muốn học bên dưới.'
            ),
            color=color,
        )
        
        # Hiển thị trước 10 item
        for i, item in enumerate(ds_items[:10], 1):
            ten = item['ten']
            so_luong = item['so_luong']
            
            if loai == 'dan_phuong':
                pham_cap = item.get('pham_cap', '')
                pham_str = PHAM_CAP_TEN.get(pham_cap, pham_cap)
                embed.add_field(
                    name=f'{i}. 📜 {ten}',
                    value=f'{pham_str} — `×{so_luong}`',
                    inline=False,
                )
            else:
                giai_cap = item.get('giai_cap', '')
                giai_str = GIAI_CAP_CONG_PHAP.get(giai_cap, giai_cap)
                embed.add_field(
                    name=f'{i}. 📖 {ten}',
                    value=f'{giai_str} — `×{so_luong}`',
                    inline=False,
                )
        
        if len(ds_items) > 10:
            embed.set_footer(text=f'Hiển thị 10/{len(ds_items)} item. Chọn từ dropdown.')
        else:
            embed.set_footer(text='Chọn từ dropdown bên dưới')
        
        view = view_class(ds_items)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Hoc(bot))