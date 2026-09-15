import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import random

from database.player_repo import (
    get_player_full_info,
    get_cooldown,
    xu_ly_dot_pha,
    ghi_log_dot_pha,
)
from utils.stat_calc import tinh_ti_le_dot_pha_chi_tiet


def format_thoi_gian(giay: int) -> str:
    """Format giây thành '1h 30m'."""
    gio = giay // 3600
    phut = (giay % 3600) // 60
    
    if gio > 0 and phut > 0:
        return f'{gio}h {phut}m'
    elif gio > 0:
        return f'{gio}h'
    else:
        return f'{phut}m'


# ============================================================
# VIEW XÁC NHẬN
# ============================================================
class XacNhanDotPhaView(discord.ui.View):
    def __init__(self, player, ti_le_data):
        super().__init__(timeout=60)
        self.player = player
        self.ti_le_data = ti_le_data

    @discord.ui.button(
        label='Xác nhận Độ Kiếp',
        style=discord.ButtonStyle.danger,
        emoji='⚡'
    )
    async def xac_nhan(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable tất cả button
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Roll đột phá
        ti_le = self.ti_le_data['ti_le_cuoi']
        roll = random.uniform(0, 100)
        thanh_cong = roll <= ti_le

        # Xử lý
        ket_qua = xu_ly_dot_pha(self.player.player_id, thanh_cong)

        # Ghi log
        ghi_log_dot_pha(
            self.player.player_id,
            self.player.canh_gioi_id,
            self.player.tang_canh_gioi,
            self.player.canh_gioi_id + 1 if thanh_cong else 0,
            1 if thanh_cong else 0,
            self.ti_le_data,
            thanh_cong
        )

        # Build response
        if thanh_cong:
            embed = discord.Embed(
                title='🎉 ĐỘ KIẾP THÀNH CÔNG!',
                description=(
                    f'**{self.player.ten_nhan_vat}** đã vượt qua thiên kiếp!\n'
                    f'Cảnh giới: **{ket_qua["canh_gioi_cu"]}** → **{ket_qua["canh_gioi_moi"]}**'
                ),
                color=discord.Color.gold()
            )
            embed.add_field(
                name='📊 Tỉ lệ',
                value=f'`{ti_le:.2f}%` — Roll: `{roll:.2f}`',
                inline=True
            )
            embed.set_footer(text='Chúc mừng đạo hữu!')
        else:
            cd_giay = ket_qua['cooldown_giay']
            cd_str = format_thoi_gian(cd_giay)
            embed = discord.Embed(
                title='💔 ĐỘ KIẾP THẤT BẠI!',
                description=(
                    f'**{self.player.ten_nhan_vat}** đã không vượt qua thiên kiếp...\n'
                    f'Cảnh giới giữ nguyên: **{ket_qua["canh_gioi_cu"]}**'
                ),
                color=discord.Color.red()
            )
            embed.add_field(
                name='📊 Tỉ lệ',
                value=f'`{ti_le:.2f}%` — Roll: `{roll:.2f}`',
                inline=True
            )
            embed.add_field(
                name='💪 Lần sau',
                value=f'Tỉ lệ +5% (tổng {self.player.so_du_lan_dot_pha + 1} lần thất bại)',
                inline=True
            )
            embed.add_field(
                name='⏳ Cooldown',
                value=f'**{cd_str}**',
                inline=False
            )
            embed.set_footer(text='Cố gắng luyện tập, đạo hữu!')

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(
        label='Hủy',
        style=discord.ButtonStyle.secondary,
        emoji='❌'
    )
    async def huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(
            '❌ Đã hủy độ kiếp.',
            ephemeral=True
        )


class DotPha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name='dotpha',
        description='Đột phá đại cảnh giới (cần ở tầng cuối)'
    )
    async def dotpha(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        # 1. Check player
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.')
            return

        # 2. Check ở tầng cuối
        if player.tang_canh_gioi < player.so_tang:
            await interaction.followup.send(
                f'❌ Bạn đang ở **tầng {player.tang_canh_gioi}/{player.so_tang}**. '
                f'Phải lên tầng cuối mới có thể đột phá!\n'
                f'Dùng `/tuluyen` để lên tầng.'
            )
            return

        # 3. Check cooldown độ kiếp
        san_sang = get_cooldown(player.player_id, 'dotpha')
        if san_sang and san_sang > datetime.now():
            con_lai = int((san_sang - datetime.now()).total_seconds())
            await interaction.followup.send(
                f'⏳ Bạn đang bị thương sau lần độ kiếp thất bại!\n'
                f'Còn **{format_thoi_gian(con_lai)}** nữa mới có thể thử lại.'
            )
            return

        # 4. Tính tỉ lệ đột phá
        ti_le_data = tinh_ti_le_dot_pha_chi_tiet(player.player_id)

        # 5. Build embed xác nhận
        embed = discord.Embed(
            title='⚡ ĐỘ KIẾP',
            description=(
                f'**{player.ten_nhan_vat}** đang chuẩn bị độ kiếp!\n'
                f'Cảnh giới: **{ti_le_data["canh_gioi_ten"]}** (tầng cuối)\n'
                f'Bạn có chắc chắn muốn độ kiếp?'
            ),
            color=discord.Color.orange()
        )

        # Hiển thị tỉ lệ với nguồn
        nguon_lines = []
        for n in ti_le_data['nguon']:
            nguon_lines.append(
                f'{n["emoji"]} **{n["ten"]}:** `+{n["gia_tri"]:.2f}%`'
            )
        
        embed.add_field(
            name=f'📊 Tỉ lệ độ kiếp: `{ti_le_data["ti_le_cuoi"]:.2f}%`',
            value='\n'.join(nguon_lines),
            inline=False
        )

        embed.add_field(
            name='⚠️ Lưu ý',
            value=(
                f'• Thành công: lên cảnh giới mới, reset tầng 1\n'
                f'• Thất bại: giữ nguyên cảnh giới, +5% tỉ lệ lần sau\n'
                f'• Thất bại: cooldown dài (vài giờ)\n'
                f'• Tỉ lệ tối đa: `{ti_le_data["ti_le_toi_da"]}%`'
            ),
            inline=False
        )

        embed.set_footer(text='Nhấn Xác nhận để bắt đầu độ kiếp (60s)')

        # 6. Gửi view xác nhận
        view = XacNhanDotPhaView(player, ti_le_data)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(DotPha(bot))