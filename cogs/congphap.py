import discord
from discord import app_commands
from discord.ext import commands
import json

from database.connection import get_connection
from database.player_repo import get_player_full_info


# ============================================================
# MAPPING
# ============================================================
GIAI_CAP_EMOJI = {
    'Hoang': '📗', 'Huyen': '📘', 'Dia': '📙', 'Thien': '📕',
}

GIAI_CAP_TEN = {
    'Hoang': 'Hoàng giai',
    'Huyen': 'Huyền giai',
    'Dia': 'Địa giai',
    'Thien': 'Thiên giai',
}

PHAM_CAP_TEN = {
    'Ha': 'Hạ phẩm', 'Trung': 'Trung phẩm', 'Thuong': 'Thượng phẩm',
    'Cuc': 'Cực phẩm', 'HoanMy': 'Hoàn Mỹ',
}

HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}

HE_TEN = {
    'Kim': 'Kim', 'Moc': 'Mộc', 'Thuy': 'Thủy', 'Hoa': 'Hỏa', 'Tho': 'Thổ',
    'Loi': 'Lôi', 'Bang': 'Băng', 'Phong': 'Phong', 'Duong': 'Dương', 'Am': 'Âm',
}

LOAI_CONG_PHAP = {
    'NguHanh': 'Ngũ Hành',
    'DiHe': 'Dị Hệ',
    'LuyenThe': 'Luyện Thể',
    'LuyenHon': 'Luyện Hồn',
}


# ============================================================
# HÀM TÍNH TU VI CẦN
# ============================================================
# Hệ số tu vi theo giai cấp
GIAI_CAP_TU_VI_GOC = {
    'Hoang': 300,
    'Huyen': 600,
    'Dia': 900,
    'Thien': 1800,
}


def tinh_tu_vi_can_tang_cong_phap(tang_hien_tai: int, giai_cap: str) -> int:
    """
    Tính tu vi cần để tăng tầng công pháp.
    
    Args:
        tang_hien_tai: Tầng hiện tại (1-9)
        giai_cap: Giai cấp ('Hoang', 'Huyen', 'Dia', 'Thien')
    
    Returns:
        Số tu vi cần
    """
    he_so = GIAI_CAP_TU_VI_GOC.get(giai_cap, 300)
    return he_so * (tang_hien_tai ** 2)



# ============================================================
# HÀM HELPER
# ============================================================
def get_max_cong_phap_active(cursor) -> int:
    """Lấy số công pháp active tối đa từ config."""
    cursor.execute("""
        SELECT value FROM he_thong_config
        WHERE key_name = 'max_cong_phap_active'
    """)
    row = cursor.fetchone()
    if not row:
        return 2
    try:
        return int(json.loads(row['value']))
    except:
        return 2


def format_he(he_data) -> str:
    """Format hệ từ JSON array."""
    if not he_data:
        return ''
    try:
        if isinstance(he_data, str):
            he_list = json.loads(he_data)
        else:
            he_list = he_data
        if isinstance(he_list, list):
            return ' '.join(HE_EMOJI.get(h, '') for h in he_list)
    except:
        pass
    return ''


# ============================================================
# /congphap — Xem danh sách công pháp đã học
# ============================================================
class CongPhap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='congphap',
        description='Xem danh sách công pháp đã học'
    )
    async def congphap(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    pcp.cong_phap_id,
                    pcp.tang_hien_tai,
                    pcp.dang_tu_luyen,
                    pcp.ngay_hoc,
                    cp.ten,
                    cp.loai,
                    cp.he,
                    cp.giai_cap,
                    cp.pham_cap,
                    cp.so_tang,
                    cp.effect_moi_tang,
                    cp.mo_ta
                FROM player_cong_phap pcp
                JOIN tmpl_cong_phap cp ON cp.id = pcp.cong_phap_id
                WHERE pcp.player_id = %s
                ORDER BY 
                    pcp.dang_tu_luyen DESC,
                    FIELD(cp.giai_cap, 'Thien', 'Dia', 'Huyen', 'Hoang'),
                    cp.ten
            """, (player.player_id,))
            ds_cp = cursor.fetchall()
            
            max_active = get_max_cong_phap_active(cursor)
        finally:
            cursor.close()
            conn.close()
        
        if not ds_cp:
            await interaction.followup.send(
                '📖 Bạn chưa học công pháp nào!\n'
                'Dùng `/hoc loai:Công pháp` để học.'
            )
            return
        
        # Đếm số đang active
        so_active = sum(1 for cp in ds_cp if cp['dang_tu_luyen'])
        
        embed = discord.Embed(
            title=f'📖 Công Pháp của {player.ten_nhan_vat}',
            description=(
                f'Tổng: `{len(ds_cp)}` công pháp\n'
                f'Đang tu luyện: `{so_active}/{max_active}`'
            ),
            color=discord.Color.purple(),
        )
        
        for cp in ds_cp[:15]:
            giai_emoji = GIAI_CAP_EMOJI.get(cp['giai_cap'], '📖')
            he_str = format_he(cp.get('he'))
            active_str = '🟢' if cp['dang_tu_luyen'] else '🔴'
            
            embed.add_field(
                name=f'{active_str} {giai_emoji} {cp["ten"]} {he_str}',
                value=(
                    f'Tầng `{cp["tang_hien_tai"]}/{cp["so_tang"]}` | '
                    f'{GIAI_CAP_TEN.get(cp["giai_cap"], cp["giai_cap"])} — '
                    f'{PHAM_CAP_TEN.get(cp["pham_cap"], cp["pham_cap"])}'
                ),
                inline=False,
            )
        
        if len(ds_cp) > 15:
            embed.set_footer(text=f'Hiển thị 15/{len(ds_cp)} công pháp')
        else:
            embed.set_footer(text='Dùng /congphap-chitiet để xem chi tiết')
        
        await interaction.followup.send(embed=embed)
    
    # ============================================================
    # /congphap-chitiet — Chi tiết 1 công pháp
    # ============================================================
    @app_commands.command(
        name='congphap-chitiet',
        description='Xem chi tiết 1 công pháp'
    )
    @app_commands.describe(ten='Tên công pháp')
    async def congphap_chitiet(
        self,
        interaction: discord.Interaction,
        ten: str,
    ):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    pcp.cong_phap_id,
                    pcp.tang_hien_tai,
                    pcp.dang_tu_luyen,
                    pcp.do_thuan_thuc,
                    pcp.ngay_hoc,
                    cp.ten,
                    cp.loai,
                    cp.he,
                    cp.giai_cap,
                    cp.pham_cap,
                    cp.so_tang,
                    cp.effect_moi_tang,
                    cp.bonus_dac_biet,
                    cp.mo_ta
                FROM player_cong_phap pcp
                JOIN tmpl_cong_phap cp ON cp.id = pcp.cong_phap_id
                WHERE pcp.player_id = %s AND LOWER(cp.ten) = LOWER(%s)
                LIMIT 1
            """, (player.player_id, ten))
            cp = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
        
        if not cp:
            await interaction.followup.send(f'❌ Không tìm thấy công pháp `{ten}` trong danh sách đã học!')
            return
        
        # Parse effect
        effect = cp['effect_moi_tang']
        if isinstance(effect, str):
            effect = json.loads(effect)
        # Lấy danh sách stat percent
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT code FROM tmpl_stat_type WHERE don_vi = 'percent'")
            stat_percent = {r['code'] for r in cursor.fetchall()}
        finally:
            cursor.close()
            conn.close()
        
        
        # Build embed
        giai_emoji = GIAI_CAP_EMOJI.get(cp['giai_cap'], '📖')
        he_str = format_he(cp.get('he'))
        active_str = '🟢 Đang tu luyện' if cp['dang_tu_luyen'] else '🔴 Chưa tu luyện'
        
        embed = discord.Embed(
            title=f'{giai_emoji} {cp["ten"]} {he_str}',
            description=cp.get('mo_ta') or '*Không có mô tả*',
            color=discord.Color.purple(),
        )
        
        embed.add_field(
            name='📊 Thông tin',
            value=(
                f'• Loại: `{LOAI_CONG_PHAP.get(cp["loai"], cp["loai"])}`\n'
                f'• Giai cấp: `{GIAI_CAP_TEN.get(cp["giai_cap"], cp["giai_cap"])}`\n'
                f'• Phẩm cấp: `{PHAM_CAP_TEN.get(cp["pham_cap"], cp["pham_cap"])}`\n'
                f'• Tầng: `{cp["tang_hien_tai"]}/{cp["so_tang"]}`\n'
                f'• Trạng thái: {active_str}'
            ),
            inline=False,
        )
        
        # ⭐ Hiển thị tu vi cần cho tầng tiếp theo
        if cp['tang_hien_tai'] < cp['so_tang']:
            tu_vi_can = tinh_tu_vi_can_tang_cong_phap(
                cp['tang_hien_tai'],
                cp['giai_cap']
            )
            
            # Lấy tu vi hiện tại
            conn2 = get_connection()
            cursor2 = conn2.cursor(dictionary=True)
            try:
                cursor2.execute(
                    "SELECT tu_vi FROM player WHERE player_id = %s",
                    (player.player_id,)
                )
                row = cursor2.fetchone()
                tu_vi_hien_tai = row['tu_vi'] if row else 0
            finally:
                cursor2.close()
                conn2.close()
            
            if tu_vi_hien_tai >= tu_vi_can:
                status = '✅ Đủ tu vi'
            else:
                thieu = tu_vi_can - tu_vi_hien_tai
                status = f'❌ Thiếu `{thieu:,}` tu vi'
            
            embed.add_field(
                name='⬆️ Tăng tầng tiếp theo',
                value=(
                    f'• Tầng: `{cp["tang_hien_tai"]}` → `{cp["tang_hien_tai"] + 1}`\n'
                    f'• Tu vi cần: `{tu_vi_can:,}`\n'
                    f'• Tu vi hiện có: `{tu_vi_hien_tai:,}`\n'
                    f'• Trạng thái: {status}'
                ),
                inline=False,
            )
        else:
            embed.add_field(
                name='⬆️ Tăng tầng',
                value='🎯 Đã đạt tầng tối đa!',
                inline=False,
            )
        
        # Hiển thị bonus
        if effect:
            do_thuan_thuc = float(cp.get('do_thuan_thuc', 0) or 0)
            he_so_flat = 1 + (do_thuan_thuc * 0.005)
            bonus_pct = do_thuan_thuc * 0.05
            
            lines = []
            for code, gia_tri in effect.items():
                gia_tri_goc = float(gia_tri) * cp['tang_hien_tai']
                
                # ⭐ Phân biệt flat vs percent
                if code in stat_percent:
                    gia_tri_cuoi = gia_tri_goc + bonus_pct
                    gia_tri_str = f'{gia_tri_cuoi:.2f}%'
                else:
                    gia_tri_cuoi = gia_tri_goc * he_so_flat
                    gia_tri_str = f'{gia_tri_cuoi:,.0f}'
                
                lines.append(f'• `{code}`: **{gia_tri_str}**')
            
            embed.add_field(
                name=f'✨ Bonus mỗi tầng (×{cp["tang_hien_tai"]} tầng)',
                value='\n'.join(lines) or '*Không có*',
                inline=False,
            )
            
            # ⭐ Hiển thị thuần thục
            embed.add_field(
                name=f'📖 Độ thuần thục',
                value=(
                    f'`{int(do_thuan_thuc)}/100`\n'
                    f'Flat: `×{he_so_flat:.2f}`\n'
                    f'Percent: `+{bonus_pct:.2f}%`'
                ),
                inline=True,
            )
        else:
            embed.add_field(
                name='✨ Bonus',
                value='*Không có*',
                inline=False,
            )
        
        if cp.get('bonus_dac_biet'):
            bd = cp['bonus_dac_biet']
            if isinstance(bd, str):
                bd = json.loads(bd)
            embed.add_field(
                name='⭐ Bonus đặc biệt',
                value=f'`{bd}`',
                inline=False,
            )
        
        embed.set_footer(text=f'Học ngày: {cp["ngay_hoc"].strftime("%d/%m/%Y")}')
        
        await interaction.followup.send(embed=embed)
    
    # ============================================================
    # /congphap-tuluyen — Active/deactive công pháp
    # ============================================================
    @app_commands.command(
        name='congphap-tuluyen',
        description='Bật/tắt tu luyện công pháp'
    )
    @app_commands.describe(ten='Tên công pháp muốn bật/tắt')
    async def congphap_tuluyen(
        self,
        interaction: discord.Interaction,
        ten: str,
    ):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            # 1. Tìm công pháp
            cursor.execute("""
                SELECT pcp.cong_phap_id, pcp.dang_tu_luyen, cp.ten
                FROM player_cong_phap pcp
                JOIN tmpl_cong_phap cp ON cp.id = pcp.cong_phap_id
                WHERE pcp.player_id = %s AND LOWER(cp.ten) = LOWER(%s)
                LIMIT 1
                FOR UPDATE
            """, (player.player_id, ten))
            cp = cursor.fetchone()
            
            if not cp:
                conn.rollback()
                await interaction.followup.send(f'❌ Bạn chưa học công pháp `{ten}`!')
                return
            
            # 2. Nếu đang active → tắt
            if cp['dang_tu_luyen']:
                cursor.execute("""
                    UPDATE player_cong_phap
                    SET dang_tu_luyen = 0
                    WHERE player_id = %s AND cong_phap_id = %s
                """, (player.player_id, cp['cong_phap_id']))
                conn.commit()
                
                embed = discord.Embed(
                    title='🔴 Đã tắt tu luyện',
                    description=f'Công pháp **{cp["ten"]}** đã ngừng tu luyện.',
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
                return
            
            # 3. Nếu chưa active → check slot
            cursor.execute("""
                SELECT COUNT(*) AS so_luong FROM player_cong_phap
                WHERE player_id = %s AND dang_tu_luyen = 1
            """, (player.player_id,))
            so_active = cursor.fetchone()['so_luong']
            
            max_active = get_max_cong_phap_active(cursor)
            
            # Khi bật (từ 0 → 1)
            if so_active >= max_active:
                await interaction.followup.send(f'❌ Đã đạt giới hạn {max_active}!')
                return
            
            # 4. Active
            cursor.execute("""
                UPDATE player_cong_phap
                SET dang_tu_luyen = 1
                WHERE player_id = %s AND cong_phap_id = %s
            """, (player.player_id, cp['cong_phap_id']))
            
            # Recompute stat
            from database.player_repo import recompute_player_stat
            recompute_player_stat(cursor, player.player_id)
            
            conn.commit()
            
            embed = discord.Embed(
                title='🟢 Đã bật tu luyện',
                description=f'Công pháp **{cp["ten"]}** bắt đầu được tu luyện.',
                color=discord.Color.green(),
            )
            embed.add_field(
                name='📊 Slot',
                value=f'`{so_active + 1}/{max_active}`',
                inline=False,
            )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            conn.rollback()
            print(f'[ERROR] congphap_tuluyen: {e}')
            await interaction.followup.send(f'❌ Lỗi: {e}')
        finally:
            cursor.close()
            conn.close()
    
    # ============================================================
    # /congphap-tangtang — Tăng tầng công pháp
    # ============================================================
    @app_commands.command(
        name='congphap-tangtang',
        description='Tăng tầng công pháp (dùng tu vi)'
    )
    @app_commands.describe(ten='Tên công pháp muốn tăng tầng')
    async def congphap_tangtang(
        self,
        interaction: discord.Interaction,
        ten: str,
    ):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            # 1. Lấy công pháp + tu vi player
            cursor.execute("""
                SELECT 
                    pcp.cong_phap_id, pcp.tang_hien_tai,
                    cp.ten, cp.so_tang, cp.giai_cap,
                    p.tu_vi
                FROM player_cong_phap pcp
                JOIN tmpl_cong_phap cp ON cp.id = pcp.cong_phap_id
                JOIN player p ON p.player_id = pcp.player_id
                WHERE pcp.player_id = %s AND LOWER(cp.ten) = LOWER(%s)
                LIMIT 1
                FOR UPDATE
            """, (player.player_id, ten))
            cp = cursor.fetchone()
            
            if not cp:
                conn.rollback()
                await interaction.followup.send(f'❌ Bạn chưa học công pháp `{ten}`!')
                return
            
            # 2. Check max tầng
            if cp['tang_hien_tai'] >= cp['so_tang']:
                conn.rollback()
                await interaction.followup.send(
                    f'❌ Công pháp **{cp["ten"]}** đã đạt tầng tối đa (`{cp["so_tang"]}`)!'
                )
                return
            
            # 3. Tính tu vi cần (dùng giai_cap)
            tu_vi_can = tinh_tu_vi_can_tang_cong_phap(
                cp['tang_hien_tai'],
                cp['giai_cap']
            )
            
            if cp['tu_vi'] < tu_vi_can:
                conn.rollback()
                await interaction.followup.send(
                    f'❌ Không đủ tu vi!\n'
                    f'• Cần: `{tu_vi_can:,}`\n'
                    f'• Có: `{cp["tu_vi"]:,}`\n'
                    f'• Thiếu: `{tu_vi_can - cp["tu_vi"]:,}`'
                )
                return
            
            # 4. Trừ tu vi, tăng tầng
            cursor.execute("""
                UPDATE player SET tu_vi = tu_vi - %s WHERE player_id = %s
            """, (tu_vi_can, player.player_id))
            
            cursor.execute("""
                UPDATE player_cong_phap
                SET tang_hien_tai = tang_hien_tai + 1
                WHERE player_id = %s AND cong_phap_id = %s
            """, (player.player_id, cp['cong_phap_id']))
            
            # Recompute stat
            from database.player_repo import recompute_player_stat
            recompute_player_stat(cursor, player.player_id)
            
            conn.commit()
            
            # 5. Build embed kết quả
            giai_cap_ten = GIAI_CAP_TEN.get(cp['giai_cap'], cp['giai_cap'])
            
            embed = discord.Embed(
                title='⬆️ Tăng Tầng Công Pháp',
                description=(
                    f'**{cp["ten"]}** tăng lên tầng '
                    f'**{cp["tang_hien_tai"] + 1}/{cp["so_tang"]}**!'
                ),
                color=discord.Color.gold(),
            )
            embed.add_field(
                name='📖 Giai cấp',
                value=giai_cap_ten,
                inline=True,
            )
            embed.add_field(
                name='💸 Tu vi đã dùng',
                value=f'`-{tu_vi_can:,}`',
                inline=True,
            )
            
            # Hiển thị tu vi cần cho tầng tiếp theo (nếu chưa max)
            if cp['tang_hien_tai'] + 1 < cp['so_tang']:
                tu_vi_tiep = tinh_tu_vi_can_tang_cong_phap(
                    cp['tang_hien_tai'] + 1,
                    cp['giai_cap']
                )
                embed.add_field(
                    name='📊 Tầng tiếp theo',
                    value=f'Cần `{tu_vi_tiep:,}` tu vi',
                    inline=False,
                )
            else:
                embed.add_field(
                    name='🎉 Chúc mừng',
                    value='Công pháp đã **MAX** tầng!',
                    inline=False,
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            conn.rollback()
            print(f'[ERROR] congphap_tangtang: {e}')
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f'❌ Lỗi: {e}')
        finally:
            cursor.close()
            conn.close()


async def setup(bot):
    await bot.add_cog(CongPhap(bot))