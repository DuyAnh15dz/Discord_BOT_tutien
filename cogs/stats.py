import discord
from discord import app_commands
from discord.ext import commands

from database.connection import get_connection
from database.player_repo import get_player_full_info


# ============================================================
# MAPPING HIỂN THỊ NHÓM
# ============================================================
NHOM_STAT = {
    'CoBan': {'ten': '📊 Chỉ số cơ bản', 'thu_tu': 1},
    'ChienDau': {'ten': '⚔️ Chiến đấu', 'thu_tu': 2},
    'KhangNguyenTo': {'ten': '🛡️ Kháng nguyên tố', 'thu_tu': 3},
    'TuLuyen': {'ten': '🧘 Tu luyện', 'thu_tu': 4},
    'HieuUng': {'ten': '🌀 Hiệu ứng', 'thu_tu': 5},
    'HoiPhuc': {'ten': '💚 Hồi phục', 'thu_tu': 6},
    'Utility': {'ten': '🎒 Tiện ích', 'thu_tu': 7},
}


def format_stat(gia_tri, don_vi):
    if gia_tri is None:
        return '`0`'
    gia_tri = float(gia_tri)
    if don_vi == 'flat':
        return f'`{int(gia_tri):,}`'  # ← Dùng int
    elif don_vi == 'percent':
        return f'`{gia_tri:.2f}%`'
    else:
        return f'`{gia_tri}`'


def lay_stat_chi_tiet(player_id: int) -> dict:
    """Lấy stat runtime + metadata."""
    from database.player_repo import tinh_stat_runtime
    
    stat_runtime = tinh_stat_runtime(player_id)
    if not stat_runtime:
        return {}
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT code, ten_hien_thi, nhom, don_vi, thu_tu_hien_thi
            FROM tmpl_stat_type
            ORDER BY thu_tu_hien_thi
        """)
        stat_types = cursor.fetchall()
        
        result = {}
        for st in stat_types:
            code = st['code']
            nhom = st['nhom']
            gia_tri = stat_runtime.get(code, 0.0)
            
            if nhom not in result:
                result[nhom] = []
            
            result[nhom].append({
                'ten': st['ten_hien_thi'],
                'gia_tri': gia_tri,
                'don_vi': st['don_vi'],
            })
        
        return result
    finally:
        cursor.close()
        conn.close()



class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name='stats',
        description='Xem chi tiết tất cả chỉ số nhân vật'
    )
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        # 1. Check player
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.')
            return

        # 2. Lấy stat chi tiết
        stat_data = lay_stat_chi_tiet(player.player_id)
        if not stat_data:
            await interaction.followup.send('❌ Không tìm thấy stat!')
            return

        # 3. Build embed
        embed = discord.Embed(
            title=f'📊 Chỉ số của {player.ten_nhan_vat}',
            description=f'**{player.canh_gioi_ten}** — Tầng **{player.tang_canh_gioi}/{player.so_tang}**',
            color=discord.Color.blue()
        )

        # Sắp xếp nhóm theo thứ tự
        nhom_sorted = sorted(
            stat_data.keys(),
            key=lambda n: NHOM_STAT.get(n, {'thu_tu': 99})['thu_tu']
        )

        for nhom in nhom_sorted:
            info = NHOM_STAT.get(nhom, {'ten': nhom})
            lines = []

            for st in stat_data[nhom]:
                gia_tri_str = format_stat(st['gia_tri'], st['don_vi'])
                lines.append(f'• **{st["ten"]}:** {gia_tri_str}')

            text = '\n'.join(lines)

            # Nếu quá 1024 ký tự, chia thành 2 field
            if len(text) > 1024:
                mid = len(lines) // 2
                embed.add_field(
                    name=info['ten'],
                    value='\n'.join(lines[:mid]),
                    inline=False
                )
                embed.add_field(
                    name=f'{info["ten"]} (tiếp)',
                    value='\n'.join(lines[mid:]),
                    inline=False
                )
            else:
                embed.add_field(
                    name=info['ten'],
                    value=text,
                    inline=False
                )

        embed.set_footer(
            text=f'ID: {player.player_id} | Dùng /profile để xem tổng quan'
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))