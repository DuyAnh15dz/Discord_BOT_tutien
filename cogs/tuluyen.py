import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import random
import json

from database.player_repo import (
    get_player_full_info,
    add_exp_and_tuvi,
    get_cooldown,
    set_cooldown,
    get_player_linh_can_active,
    tang_tinh_khiet,
    xu_ly_tang_tu_dong,
)
from database.connection import get_connection
from utils.stat_calc import tinh_exp_tuluyen


def lay_config(key_name: str, default=0):
    """Lấy config từ DB."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT value FROM he_thong_config WHERE key_name = %s
        """, (key_name,))
        row = cursor.fetchone()
        if not row:
            return default
        return json.loads(row['value'])
    finally:
        cursor.close()
        conn.close()


class TuLuyen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='tuluyen', description='Tu luyện để tăng exp và tu vi')
    async def tuluyen(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        # 1. Check player
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.')
            return

        # 2. Check cooldown
        san_sang = get_cooldown(player.player_id, 'tuluyen')
        if san_sang and san_sang > datetime.now():
            con_lai = int((san_sang - datetime.now()).total_seconds())
            phut = con_lai // 60
            giay = con_lai % 60
            await interaction.followup.send(
                f'⏳ Bạn đang mệt! Còn **{phut}p {giay}s** nữa mới tu luyện được.'
            )
            return

        # 3. Tính exp + tu vi
        exp_nhan, tu_vi_nhan = tinh_exp_tuluyen(
            player.canh_gioi_id,
            player.tang_canh_gioi
        )

        # 4. Cộng exp + tu vi
        add_exp_and_tuvi(player.player_id, exp_nhan, tu_vi_nhan)
        ket_qua_tang = xu_ly_tang_tu_dong(player.player_id)

        # ===== 5. CÀY ĐỘ TINH KHIẾT (Cơ chế lai) =====
        ds_linh_can = get_player_linh_can_active(player.player_id)
        tang_tinh_khiet_list = []

        chance = lay_config('linh_can_cay_tinh_khiet_chance', 0.02)
        amount_min = lay_config('linh_can_cay_tinh_khiet_amount_min', 0.05)
        amount_max = lay_config('linh_can_cay_tinh_khiet_amount_max', 0.2)

        for lc in ds_linh_can:
            # ⭐ BỎ QUA linh căn đã max 100%
            if lc['do_tinh_khiet'] >= 100:
                continue

            # Roll riêng cho từng linh căn
            if random.random() < chance:
                amount = random.uniform(amount_min, amount_max)
                do_tinh_khiet_moi = min(lc['do_tinh_khiet'] + amount, 100)

                tang_tinh_khiet(
                    player.player_id,
                    lc['linh_can_id'],
                    amount
                )

                tang_tinh_khiet_list.append({
                    'ten': lc['ten'],
                    'tang': amount,
                    'moi': do_tinh_khiet_moi,
                })

        # 6. Set cooldown
        set_cooldown(player.player_id, 'tuluyen', 120)

                # 7. Build embed
        embed = discord.Embed(
            title='✨ Tu Luyện',
            description=(
                f'**{player.ten_nhan_vat}** hấp thu linh khí trời đất...\n'
                f'Cảm giác linh lực tràn đầy cơ thể!'
            ),
            color=discord.Color.gold()
        )
        embed.add_field(
            name='📈 Exp nhận được',
            value=f'+{exp_nhan:,}',
            inline=True
        )
        embed.add_field(
            name='🔮 Tu vi nhận được',
            value=f'+{tu_vi_nhan:,}',
            inline=True
        )
        embed.add_field(
            name='⏱️ Cooldown',
            value='2 phút',
            inline=True
        )

        # ⭐ Hiện thông báo lên tầng
        if ket_qua_tang and ket_qua_tang['so_tang_len'] > 0:
            embed.add_field(
                name='⬆️ Lên tầng!',
                value=(
                    f'Tầng **{ket_qua_tang["tang_cu"]}** → **{ket_qua_tang["tang_moi"]}** '
                    f'(+{ket_qua_tang["so_tang_len"]} tầng)\n'
                    f'Exp còn lại: `{ket_qua_tang["exp_con_lai"]:,}`'
                ),
                inline=False
            )

            # Nếu max tầng
            if ket_qua_tang['da_max_tang']:
                embed.add_field(
                    name='🎯 Đã đạt tầng tối đa!',
                    value='Dùng `/dotpha` để đột phá lên cảnh giới mới!',
                    inline=False
                )

        # ⭐ Hiện thông báo tăng độ tinh khiết (chỉ khi có)
        if tang_tinh_khiet_list:
            lines = []
            for item in tang_tinh_khiet_list:
                lines.append(
                    f'• **{item["ten"]}**: +{item["tang"]:.3f}% → `{item["moi"]:.2f}%`'
                )
            embed.add_field(
                name='🌟 Độ tinh khiết tăng!',
                value='\n'.join(lines),
                inline=False
            )

        embed.set_footer(
            text=f'Cảnh giới: {player.canh_gioi_ten} tầng {player.tang_canh_gioi}'
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TuLuyen(bot))