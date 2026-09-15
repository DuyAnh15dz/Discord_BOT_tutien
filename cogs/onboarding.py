import discord
from discord import app_commands
from discord.ext import commands
from database.player_repo import update_hp_regen

from database.connection import get_connection
from database.player_repo import (
    get_player_full_info,
    create_player,
    get_player_linh_can_summary,
    get_player_nghe_nghiep,
    tinh_stat_runtime,
)
from utils.stat_calc import tinh_exp_can_tang, tinh_exp_can_dot_pha
from cogs.nghe import NgheView


def tao_progress_bar(hien_tai: int, toi_da: int, do_dai: int = 20) -> str:
    """Tạo thanh progress bar dạng text."""
    if toi_da <= 0:
        return '█' * do_dai
    ti_le = min(hien_tai / toi_da, 1.0)
    so_o_day = int(ti_le * do_dai)
    return '█' * so_o_day + '░' * (do_dai - so_o_day)


class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===== /nhapmon =====
    @app_commands.command(name='nhapmon', description='Đăng ký nhân vật tu tiên')
    @app_commands.describe(ten_nhan_vat='Tên nhân vật (2-50 ký tự)')
    async def dangky(self, interaction: discord.Interaction, ten_nhan_vat: str):
        await interaction.response.defer()

        ten_nhan_vat = ten_nhan_vat.strip()
        if len(ten_nhan_vat) < 2 or len(ten_nhan_vat) > 50:
            await interaction.followup.send('❌ Tên phải từ 2-50 ký tự!')
            return

        player = get_player_full_info(interaction.user.id)
        if player:
            await interaction.followup.send(
                f'❌ Bạn đã có nhân vật **{player.ten_nhan_vat}** rồi!'
            )
            return

        try:
            player, linh_can_ids = create_player(interaction.user.id, ten_nhan_vat)
        except Exception as e:
            print(f'[ERROR] create_player: {e}')
            await interaction.followup.send('❌ Có lỗi xảy ra!')
            return

        ten_lc_list = lay_ten_linh_can(linh_can_ids)
        linh_can_str = '\n'.join(f'• {ten}' for ten in ten_lc_list)

        embed = discord.Embed(
            title='🎉 Đăng ký thành công!',
            description=f'Chào mừng **{player.ten_nhan_vat}**!',
            color=discord.Color.green()
        )
        embed.add_field(
            name='🌟 Cảnh giới',
            value=f'{player.canh_gioi_ten} tầng {player.tang_canh_gioi}',
            inline=True
        )
        embed.add_field(
            name='💰 Linh thạch',
            value=f'{player.linh_thach:,}',
            inline=True
        )
        embed.add_field(
            name=f'✨ Linh căn ({len(linh_can_ids)})',
            value=linh_can_str or 'Không có',
            inline=False
        )
        embed.set_footer(text='Bước tiếp theo: Chọn nghề nghiệp')
        await interaction.followup.send(embed=embed)

        # Gửi dropdown chọn nghề
        view = NgheView(player_id=player.player_id)
        await interaction.followup.send(
            '👇 **Chọn nghề nghiệp của bạn** (chỉ chọn được 1 lần):',
            view=view,
        )

    # ===== /profile =====
    @app_commands.command(name='profile', description='Xem thông tin nhân vật')
    async def thongtin(self, interaction: discord.Interaction):
        await interaction.response.defer()

        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.')
            return

        # ⭐ Update HP regen trước khi hiển thị
        update_hp_regen(player.player_id)

        # ⭐ Tính stat runtime (đã cộng bonus từ linh căn + nghề + buff)
        stat_runtime = tinh_stat_runtime(player.player_id)

        # Lấy HP riêng (vì HP có logic regen)
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT hp_hien_tai, mp_hien_tai, in_combat
                FROM player_stat WHERE player_id = %s
            """, (player.player_id,))
            stat_hp = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        # ⭐ Dùng stat_runtime cho hp_max, mp_max
        hp_max = int(stat_runtime.get('hp_max', 100))
        mp_max = int(stat_runtime.get('mp_max', 50))
        hp_hien_tai = stat_hp['hp_hien_tai']
        mp_hien_tai = stat_hp['mp_hien_tai']

        # HP bar
        hp_pct = hp_hien_tai / hp_max * 100 if hp_max > 0 else 0
        hp_bar = tao_progress_bar(hp_hien_tai, hp_max, 15)
        # Tính exp cần
        if player.tang_canh_gioi < player.so_tang:
            exp_can = tinh_exp_can_tang(player.canh_gioi_id, player.tang_canh_gioi)
            ghi_chu = ''
        else:
            exp_can = tinh_exp_can_dot_pha(player.canh_gioi_id)
            ghi_chu = ' *(Đột phá)*'

        progress = tao_progress_bar(player.exp, exp_can)
        ti_le = min(player.exp / exp_can * 100, 100) if exp_can > 0 else 0

        # ⭐ Tạo embed (SAU KHI đã tính xong tất cả)
        embed = discord.Embed(
            title=f'📜 {player.ten_nhan_vat}',
            color=discord.Color.blue()
        )

        # 1. Cảnh giới
        embed.add_field(
            name='🌟 Cảnh giới',
            value=f'**{player.canh_gioi_ten}** — Tầng **{player.tang_canh_gioi}/{player.so_tang}**',
            inline=False
        )

        # 2. Exp
        embed.add_field(
            name='📈 Exp',
            value=(
                f'`{progress}` **{ti_le:.1f}%**\n'
                f'`{player.exp:,}` / `{exp_can:,}`{ghi_chu}'
            ),
            inline=False
        )

        # 3. HP + MP
        trang_thai = '⚔️ Combat' if stat_hp['in_combat'] else '💚 Hồi'
        embed.add_field(
            name=f'❤️ HP ({trang_thai})',
            value=(
                f'`{hp_bar}` **{hp_pct:.1f}%**\n'
                f'`{hp_hien_tai:,}` / `{hp_max:,}`'
            ),
            inline=False
        )

        # 4. Chỉ số cơ bản (dùng stat_runtime)
        embed.add_field(
            name='⚔️ Chỉ số cơ bản',
            value=(
                f'🗡️ ATK: `{stat_runtime.get("atk", 0):,.0f}` | '
                f'🛡️ DEF: `{stat_runtime.get("def", 0):,.0f}`\n'
                f'✨ MATK: `{stat_runtime.get("matk", 0):,.0f}` | '
                f'🔮 MDEF: `{stat_runtime.get("mdef", 0):,.0f}`'
            ),
            inline=False
        )

        # 5. Tu vi + Tài nguyên
        embed.add_field(name='🔮 Tu vi', value=f'`{player.tu_vi:,}`', inline=True)
        embed.add_field(name='💰 Linh thạch', value=f'`{player.linh_thach:,}`', inline=True)
        embed.add_field(name='💎 Tiên ngọc', value=f'`{player.tien_ngoc:,}`', inline=True)

        # 6. Linh căn
        ds_linh_can = get_player_linh_can_summary(player.player_id)
        if ds_linh_can:
            linh_can_lines = []
            for lc in ds_linh_can:
                active = '✅' if lc['is_active'] else '❌'
                tinh_khiet = lc['do_tinh_khiet']
                ten_ngan = lc['ten'].replace(' Linh Căn', '')
                linh_can_lines.append(f'{active} **{ten_ngan}** — `{tinh_khiet:.1f}%`')
            embed.add_field(
                name=f'🌟 Linh căn ({len(ds_linh_can)})',
                value='\n'.join(linh_can_lines),
                inline=False
            )
        else:
            embed.add_field(name='🌟 Linh căn', value='*Chưa có*', inline=False)

        # 7. Nghề nghiệp
        nghe = get_player_nghe_nghiep(player.player_id)
        if nghe:
            cap_do = nghe['cap_do']
            cap_max = nghe['cap_toi_da']

            if nghe['la_max']:
                exp_nghe_str = f'Cấp **{cap_do}/{cap_max}** — `MAX`'
            else:
                exp_hien = nghe['kinh_nghiem']
                exp_nghe_can = nghe['exp_can_tang']
                ti_le_nghe = (exp_hien / exp_nghe_can * 100) if exp_nghe_can > 0 else 0
                progress_nghe = tao_progress_bar(exp_hien, exp_nghe_can, 15)
                exp_nghe_str = (
                    f'Cấp **{cap_do}/{cap_max}**\n'
                    f'`{progress_nghe}` **{ti_le_nghe:.1f}%**\n'
                    f'`{exp_hien:,}` / `{exp_nghe_can:,}`'
                )

            embed.add_field(
                name=f'🛠️ Nghề: **{nghe["ten"]}**',
                value=exp_nghe_str,
                inline=False
            )
        else:
            embed.add_field(
                name='🛠️ Nghề nghiệp',
                value='*Chưa chọn*',
                inline=False
            )

        # 8. Footer
        embed.set_footer(
            text=f'🧘 Tâm cảnh: {player.tam_canh} | 🍀 Khí vận: {player.khi_van} | Dùng /stats để xem chi tiết'
        )

        await interaction.followup.send(embed=embed)


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def lay_ten_linh_can(linh_can_ids: list) -> list:
    """Lấy tên linh căn từ list id."""
    if not linh_can_ids:
        return []
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        format_strings = ','.join(['%s'] * len(linh_can_ids))
        cursor.execute(f"""
            SELECT ten FROM tmpl_linh_can 
            WHERE id IN ({format_strings})
        """, tuple(linh_can_ids))
        return [row['ten'] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


async def setup(bot):
    await bot.add_cog(Onboarding(bot))