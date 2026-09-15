import discord
from discord import app_commands
from discord.ext import commands

from database.player_repo import (
    get_player_full_info,
    get_player_linh_can_full,
    get_linh_can_stats,
)


# ============================================================
# MAPPING HIỂN THỊ
# ============================================================
HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}

HE_TEN = {
    'Kim': 'Kim', 'Moc': 'Mộc', 'Thuy': 'Thủy', 'Hoa': 'Hỏa', 'Tho': 'Thổ',
    'Loi': 'Lôi', 'Bang': 'Băng', 'Phong': 'Phong', 'Duong': 'Dương', 'Am': 'Âm',
}

PHAM_CAP_TEN = {
    'Ha': 'Hạ phẩm', 'Trung': 'Trung phẩm', 'Thuong': 'Thượng phẩm',
    'Cuc': 'Cực phẩm', 'Tien': 'Tiên phẩm',
}

PHAM_CAP_EMOJI = {
    'Ha': '🟤', 'Trung': '🟢', 'Thuong': '🔵', 'Cuc': '🟣', 'Tien': '🟡',
}

PHAM_CAP_COLOR = {
    'Ha': 0x95a5a6,        # Xám
    'Trung': 0x3498db,     # Xanh dương
    'Thuong': 0x9b59b6,    # Tím
    'Cuc': 0xe67e22,       # Cam
    'Tien': 0xf1c40f,      # Vàng
}


def tao_progress_bar(hien_tai: float, toi_da: float = 100, do_dai: int = 15) -> str:
    """Tạo thanh progress bar."""
    if toi_da <= 0:
        return '█' * do_dai
    ti_le = min(hien_tai / toi_da, 1.0)
    so_o_day = int(ti_le * do_dai)
    return '█' * so_o_day + '░' * (do_dai - so_o_day)


def format_gia_tri(gia_tri: float, don_vi: str) -> str:
    """Format giá trị stat."""
    # Làm tròn
    if don_vi == 'flat':
        return f'+{gia_tri:.0f}' if gia_tri >= 0 else f'{gia_tri:.0f}'
    elif don_vi == 'percent':
        return f'+{gia_tri:.2f}%' if gia_tri >= 0 else f'{gia_tri:.2f}%'
    else:
        return f'{gia_tri}'


class LinhCan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===== /linhcan =====
    @app_commands.command(name='linhcan', description='Xem linh căn sở hữu')
    async def linhcan(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        # 1. Check player
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.')
            return

        # 2. Lấy linh căn
        ds_linh_can = get_player_linh_can_full(player.player_id)
        if not ds_linh_can:
            await interaction.followup.send('❌ Bạn chưa có linh căn nào!')
            return

        # 3. Group theo hệ
        nhom_theo_he = {}
        for lc in ds_linh_can:
            he = lc['he']
            if he not in nhom_theo_he:
                nhom_theo_he[he] = []
            nhom_theo_he[he].append(lc)

        # 4. Build embed
        embed = discord.Embed(
            title=f'🌟 Linh căn của {player.ten_nhan_vat}',
            description=f'Tổng cộng: **{len(ds_linh_can)}** linh căn',
            color=discord.Color.gold()
        )

        for he, ds in nhom_theo_he.items():
            emoji = HE_EMOJI.get(he, '❓')
            ten_he = HE_TEN.get(he, he)

            lines = []
            for lc in ds:
                pham_emoji = PHAM_CAP_EMOJI.get(lc['pham_cap'], '⚪')
                ten_pham = PHAM_CAP_TEN.get(lc['pham_cap'], lc['pham_cap'])
                tinh_khiet = lc['do_tinh_khiet']

                # Icon trạng thái
                active = '✅' if lc['is_active'] else '❌'
                san_sang = ' 🎯' if lc['san_sang_dot_pha'] else ''

                # Progress bar tinh khiết
                progress = tao_progress_bar(tinh_khiet, 100, 10)

                lines.append(
                    f'{active} {pham_emoji} **{lc["ten"]}**{san_sang}\n'
                    f'   `{progress}` **{tinh_khiet:.1f}%**'
                )

            embed.add_field(
                name=f'{emoji} {ten_he} hệ ({len(ds)})',
                value='\n'.join(lines),
                inline=False
            )

        embed.set_footer(
            text='Dùng /linhcan-chitiet <tên> để xem chi tiết stat'
        )
        await interaction.followup.send(embed=embed)

    # ===== /linhcan-chitiet =====
    @app_commands.command(
        name='linhcan-chitiet',
        description='Xem chi tiết 1 linh căn (stat bonus, độ tinh khiết)'
    )
    @app_commands.describe(
        ten_linh_can='Tên hệ hoặc tên linh căn (VD: Kim, Hỏa, Âm)'
    )
    async def linhcan_chitiet(
        self,
        interaction: discord.Interaction,
        ten_linh_can: str
    ):
        await interaction.response.defer(thinking=False)

        # 1. Check player
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return

        # 2. Lấy danh sách linh căn
        ds_linh_can = get_player_linh_can_full(player.player_id)
        if not ds_linh_can:
            await interaction.followup.send('❌ Bạn chưa có linh căn nào!')
            return

        # 3. Tìm linh căn khớp
        keyword = ten_linh_can.lower().strip()
        match = None

        for lc in ds_linh_can:
            # Match theo tên đầy đủ (VD: "Kim Linh Căn - Trung")
            if keyword in lc['ten'].lower():
                match = lc
                break
            # Match theo hệ (VD: "Kim")
            if keyword == HE_TEN.get(lc['he'], '').lower():
                match = lc
                break
            # Match theo phẩm cấp (VD: "Tiên")
            if keyword == PHAM_CAP_TEN.get(lc['pham_cap'], '').lower().replace(' phẩm', ''):
                match = lc
                break

        if not match:
            await interaction.followup.send(
                f'❌ Không tìm thấy linh căn `{ten_linh_can}`!\n'
                f'Gợi ý: Kim, Mộc, Thủy, Hỏa, Thổ, Lôi, Băng, Phong, Dương, Âm'
            )
            return

        # 4. Lấy stat bonus
        stats = get_linh_can_stats(match['linh_can_id'])


        # 5. Build embed
        emoji = HE_EMOJI.get(match['he'], '❓')
        ten_pham = PHAM_CAP_TEN.get(match['pham_cap'], match['pham_cap'])
        pham_emoji = PHAM_CAP_EMOJI.get(match['pham_cap'], '⚪')
        color = PHAM_CAP_COLOR.get(match['pham_cap'], 0x3498db)

        embed = discord.Embed(
            title=f'{emoji} {match["ten"]}',
            description=f'{pham_emoji} **{ten_pham}** — Hệ {HE_TEN.get(match["he"], match["he"])}',
            color=color
        )

        # Thông số cơ bản
        tinh_khiet = match['do_tinh_khiet']
        progress = tao_progress_bar(tinh_khiet, 100, 20)

        thong_so = (
            f'**Độ tinh khiết:** `{progress}` **{tinh_khiet:.2f}%**\n'
            f'**Hệ số bonus:** `×{match["he_so_bonus"]}`\n'
            f'**Bonus đột phá:** `+{match["ti_le_dot_pha_bonus"]}%`\n'
            f'**Trạng thái:** {"✅ Đang kích hoạt" if match["is_active"] else "❌ Không dùng"}\n'
            f'**Sẵn sàng đột phá:** {"🎯 Có" if match["san_sang_dot_pha"] else "❌ Chưa"}'
        )
        embed.add_field(
            name='📊 Thông số',
            value=thong_so,
            inline=False
        )

       # Stat bonus
        if stats:
            lines = []
            for st in stats:
                don_vi = st['don_vi']
                gia_tri = st['gia_tri_bonus']              # ← Chỉ dùng giá trị DB

                # Format giá trị
                if don_vi == 'flat':
                    gia_tri_str = f'{gia_tri:+.2f}'.rstrip('0').rstrip('.')
                    if gia_tri_str.endswith('.'):
                        gia_tri_str = gia_tri_str[:-1]
                elif don_vi == 'percent':
                    gia_tri_str = f'{gia_tri:+.2f}%'
                else:
                    gia_tri_str = f'{gia_tri}'

                lines.append(f'• **{st["ten_hien_thi"]}:** `{gia_tri_str}`')

            embed.add_field(
                name='✨ Stat bonus',                       # ← Không ghi "(×...)"
                value='\n'.join(lines),
                inline=False
            )

        # Footer
        embed.set_footer(
            text='Độ tinh khiết 100% → có thể đột phá phẩm cấp (cần đạo cụ)'
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LinhCan(bot))