import discord
from discord import app_commands
from discord.ext import commands

from database.player_repo import (
    get_player_full_info,
    get_daily_status,
    diem_danh_hang_ngay,
)


class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='daily',
        description='Điểm danh hàng ngày nhận linh thạch'
    )
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        # Check trạng thái
        status = get_daily_status(player.player_id)
        
        if not status['co_the_diem_danh']:
            # Đã điểm danh hôm nay
            embed = discord.Embed(
                title='⏰ Đã Điểm Danh Hôm Nay',
                description=(
                    f'Bạn đã điểm danh hôm nay rồi!\n'
                    f'🔥 Streak hiện tại: `{status["streak"]}` ngày\n\n'
                    f'Quay lại vào ngày mai nhé!'
                ),
                color=discord.Color.orange(),
            )
            embed.set_footer(text='Điểm danh reset theo ngày (UTC+7)')
            await interaction.followup.send(embed=embed)
            return
        
        # Điểm danh
        ket_qua = diem_danh_hang_ngay(player.player_id)
        
        if not ket_qua['thanh_cong']:
            await interaction.followup.send(f'❌ {ket_qua["loi"]}')
            return
        
        # Build embed kết quả
        embed = discord.Embed(
            title='🎁 Điểm Danh Thành Công!',
            color=discord.Color.green(),
        )
        
        # Streak
        if ket_qua['streak_tang']:
            streak_str = (
                f'🔥 Streak: `{ket_qua["streak_cu"]}` → `{ket_qua["streak_moi"]}` ngày\n'
                f'✨ **+1.5% linh thạch** từ streak!'
            )
        else:
            if ket_qua['streak_cu'] > 0:
                streak_str = (
                    f'💔 **Mất streak!** (Trước: `{ket_qua["streak_cu"]}` ngày)\n'
                    f'🔥 Streak mới: `1` ngày'
                )
            else:
                streak_str = '🔥 Streak: `1` ngày (bắt đầu chuỗi!)'
        
        embed.add_field(
            name='🔥 Chuỗi Điểm Danh',
            value=streak_str,
            inline=False,
        )
        
        # Linh thạch
        embed.add_field(
            name='💰 Linh Thạch Nhận Được',
            value=(
                f'• Cơ bản: `{ket_qua["linh_thach_base"]:,}`\n'
                f'• Bonus streak: `+{ket_qua["bonus_streak_pct"]:.1f}%`\n'
                f'• **Tổng: `+{ket_qua["linh_thach_cuoi"]:,}`**'
            ),
            inline=False,
        )
        
        # Số dư
        embed.add_field(
            name='💼 Số dư',
            value=f'💰 `{player.linh_thach + ket_qua["linh_thach_cuoi"]:,}` linh thạch',
            inline=True,
        )
        
        embed.set_footer(text='Điểm danh mỗi ngày để duy trì streak!')
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Daily(bot))