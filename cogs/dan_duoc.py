import discord
from discord import app_commands
from discord.ext import commands
import json

from database.connection import get_connection
from database.player_repo import (
    get_player_full_info,
    get_player_dan_duoc,
    dung_dan_duoc,
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

LOAI_DAN = {
    'HoiPhuc': '💊 Hồi phục',
    'DotPha': '⚡ Đột phá',
    'TangTuVi': '🔮 Tăng tu vi',
    'Buff': '✨ Buff',
    'Doc': '☠️ Độc',
}

EFFECT_KEY_MAP = {
    'hp': '❤️ HP hồi',
    'mp': '💙 MP hồi',
    'hp_per_turn': '❤️ HP hồi/lượt',
    'mp_per_turn': '💙 MP hồi/lượt',
    'turns': '🔄 Số lượt',
    'atk': '🗡️ ATK',
    'def': '🛡️ DEF',
    'matk': '✨ MATK',
    'mdef': '🔮 MDEF',
    'atk_pct': '🗡️ ATK %',
    'def_pct': '🛡️ DEF %',
    'matk_pct': '✨ MATK %',
    'mdef_pct': '🔮 MDEF %',
    'hp_max': '❤️ HP Max',
    'hp_max_pct': '❤️ HP Max %',
    'mp_max_pct': '💙 MP Max %',
    'tu_vi': '🔮 Tu vi',
    'tinh_khiet': '💧 Tinh khiết',
    'poison_dmg': '☠️ Sát thương độc',
    'ignore_def': '🚫 Bỏ qua phòng ngự',
    'target': '🎯 Mục tiêu',
    'exp_cost': '💔 Mất EXP',
    'stun_turns': '💫 Choáng (lượt)',
    'death_after_turns': '💀 Tự hủy sau (lượt)',
    'hp_cost_per_turn_pct_hien_tai': '💔 Mất HP/lượt (%)',
}


# ============================================================
# HELPER
# ============================================================
def format_effect(effect: dict) -> str:
    """Format effect thành text."""
    if not isinstance(effect, dict):
        return '*Không có*'
    
    lines = []
    for key, val in effect.items():
        label = EFFECT_KEY_MAP.get(key, key)
        
        if isinstance(val, dict):
            sub_lines = []
            for k2, v2 in val.items():
                label2 = EFFECT_KEY_MAP.get(k2, k2)
                if 'pct' in k2:
                    sub_lines.append(f'  • {label2}: `{v2}%`')
                else:
                    sub_lines.append(f'  • {label2}: `{v2:,}`')
            lines.append(f'• {label}:\n' + '\n'.join(sub_lines))
        elif isinstance(val, (int, float)):
            if 'pct' in key:
                lines.append(f'• {label}: `{val}%`')
            elif key == 'target':
                target_map = {
                    'enemy': 'Kẻ địch',
                    'enemy_pvp': 'Đối thủ PvP',
                    'self': 'Bản thân',
                }
                lines.append(f'• {label}: `{target_map.get(str(val), val)}`')
            elif key == 'ignore_def':
                lines.append(f'• {label}: `{"Có" if val else "Không"}`')
            else:
                lines.append(f'• {label}: `{val:,}`')
        else:
            lines.append(f'• {label}: `{val}`')
    
    return '\n'.join(lines) if lines else '*Không có*'


def build_chi_tiet_embed(dan: dict, so_luong_tui: int = None) -> discord.Embed:
    """Build embed chi tiết 1 đan dược."""
    pc_emoji = PHAM_CAP_EMOJI.get(dan['pham_cap'], '⚪')
    pc_ten = PHAM_CAP_TEN.get(dan['pham_cap'], dan['pham_cap'])
    loai_str = LOAI_DAN.get(dan['loai'], dan['loai'])
    
    embed = discord.Embed(
        title=f'{pc_emoji} {dan["ten"]}',
        description=dan.get('mo_ta') or '*Không có mô tả*',
        color=discord.Color.gold(),
    )
    
    info_lines = [
        f'📌 **{pc_ten}**',
        f'🏷️ Loại: `{loai_str}`',
    ]
    
    if dan.get('yeu_cau_nghe_cap'):
        info_lines.append(f'📊 Yêu cầu nghề: cấp `{dan["yeu_cau_nghe_cap"]}`')
    
    if so_luong_tui is not None:
        info_lines.append(f'🎒 Trong túi: `×{so_luong_tui}`')
    
    embed.add_field(
        name='📋 Thông tin',
        value='\n'.join(info_lines),
        inline=False,
    )
    
    # Effect
    effect = dan.get('effect')
    if isinstance(effect, str):
        try:
            effect = json.loads(effect)
        except:
            effect = {}
    
    effect_str = format_effect(effect)
    embed.add_field(
        name='✨ Hiệu ứng',
        value=effect_str,
        inline=False,
    )
    
    # Bonus
    bonus_lines = []
    if dan.get('ti_le_dot_pha_bonus') and float(dan['ti_le_dot_pha_bonus']) > 0:
        bonus_lines.append(f'⚡ +{dan["ti_le_dot_pha_bonus"]}% tỉ lệ đột phá')
    
    if dan.get('exp_bonus') and dan['exp_bonus'] > 0:
        bonus_lines.append(f'📈 +{dan["exp_bonus"]:,} EXP')
    
    if dan.get('tu_vi_bonus') and dan['tu_vi_bonus'] > 0:
        bonus_lines.append(f'🔮 +{dan["tu_vi_bonus"]:,} Tu vi')
    
    if dan.get('thoi_gian_hieu_luc') and dan['thoi_gian_hieu_luc'] > 0:
        gio = dan['thoi_gian_hieu_luc'] // 3600
        phut = (dan['thoi_gian_hieu_luc'] % 3600) // 60
        thoi_gian_str = f'{gio}h {phut}m' if gio > 0 else f'{phut}m'
        bonus_lines.append(f'⏱️ Hiệu lực: `{thoi_gian_str}`')
    
    if dan.get('gioi_han_moi_canh_gioi'):
        bonus_lines.append('⚠️ Chỉ dùng 1 lần/cảnh giới')
    
    if dan.get('ap_dung_canh_gioi_id'):
        bonus_lines.append(f'🎯 Chỉ dùng khi đột phá cảnh giới `{dan["ap_dung_canh_gioi_id"]}`')
    
    if bonus_lines:
        embed.add_field(
            name='⭐ Thông số',
            value='\n'.join(bonus_lines),
            inline=False,
        )
    
    return embed


# ============================================================
# DROPDOWN: DÙNG ĐAN
# ============================================================
class DungDanSelect(discord.ui.Select):
    def __init__(self, ds_dan: list):
        self.ds_dan = ds_dan
        
        options = []
        for i, dan in enumerate(ds_dan[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(dan['pham_cap'], '⚪')
            loai_str = LOAI_DAN.get(dan['loai'], dan['loai'])
            options.append(discord.SelectOption(
                label=dan['ten'][:100],
                description=f"{loai_str} — ×{dan['so_luong']}",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đan dược muốn dùng...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        dan = self.ds_dan[idx]
        
        player = get_player_full_info(interaction.user.id)
        ket_qua = dung_dan_duoc(player.player_id, dan['id'])
        
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        self.view.stop()
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                f'❌ {ket_qua["loi"]}',
                ephemeral=True,
            )
            return
        
        embed = discord.Embed(
            title='✅ Dùng Đan Thành Công',
            description=f'Bạn đã dùng **{ket_qua["ten"]}**',
            color=discord.Color.green(),
        )
        
        kq = ket_qua['ket_qua']
        loai_dan = ket_qua['loai']
        
        if loai_dan == 'HoiPhuc':
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
        
        elif loai_dan == 'TangTuVi':
            tu_vi = kq.get('tu_vi', 0)
            embed.add_field(
                name='🔮 Tu vi',
                value=f'`+{tu_vi:,}`',
                inline=False,
            )
        
        elif loai_dan == 'Buff':
            buff = kq.get('buff', {})
            thoi_gian = kq.get('thoi_gian', 0)
            gio = thoi_gian // 3600
            phut = (thoi_gian % 3600) // 60
            thoi_gian_str = f'{gio}h {phut}m' if gio > 0 else f'{phut}m'
            
            lines = []
            for code, val in buff.items():
                if 'pct' in code:
                    lines.append(f'• `{code}`: `+{val}%`')
                else:
                    lines.append(f'• `{code}`: `+{val:,}`')
            
            embed.add_field(
                name=f'✨ Buff ({thoi_gian_str})',
                value='\n'.join(lines) or '*Không có*',
                inline=False,
            )
        
        elif loai_dan == 'DotPha':
            ti_le = kq.get('ti_le_dot_pha', 0)
            thoi_gian = kq.get('thoi_gian', 0)
            gio = thoi_gian // 3600
            phut = (thoi_gian % 3600) // 60
            thoi_gian_str = f'{gio}h {phut}m' if gio > 0 else f'{phut}m'
            
            embed.add_field(
                name='⚡ Tỉ lệ đột phá',
                value=f'`+{ti_le}%` trong `{thoi_gian_str}`',
                inline=False,
            )
            embed.set_footer(text='Dùng /dotpha để đột phá cảnh giới')
        
        embed.set_footer(text=f'Còn lại: {dan["so_luong"] - 1} cái')
        await interaction.response.send_message(embed=embed)


class DungDanView(discord.ui.View):
    def __init__(self, ds_dan: list):
        super().__init__(timeout=120)
        self.add_item(DungDanSelect(ds_dan))


# ============================================================
# DROPDOWN: XEM CHI TIẾT ĐAN
# ============================================================
class XemChiTietSelect(discord.ui.Select):
    def __init__(self, ds_dan: list):
        self.ds_dan = ds_dan
        
        options = []
        for i, dan in enumerate(ds_dan[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(dan['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=dan['ten'][:100],
                description=f"×{dan['so_luong']} — {PHAM_CAP_TEN.get(dan['pham_cap'], dan['pham_cap'])}",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đan dược để xem chi tiết...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        dan = self.ds_dan[idx]
        
        embed = build_chi_tiet_embed(dan, so_luong_tui=dan['so_luong'])
        await interaction.response.send_message(embed=embed, ephemeral=True)


class XemChiTietView(discord.ui.View):
    def __init__(self, ds_dan: list):
        super().__init__(timeout=180)
        self.add_item(XemChiTietSelect(ds_dan))


# ============================================================
# COG
# ============================================================
class DanDuoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # ===== /drug — Dùng đan =====
    @app_commands.command(
        name='drug',
        description='Dùng đan dược từ túi'
    )
    async def drug(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_dan = get_player_dan_duoc(player.player_id)
        
        if not ds_dan:
            await interaction.followup.send(
                '❌ Bạn không có đan dược nào!\n'
                'Mua tại `/shop` (tab Đan dược).'
            )
            return
        
        embed = discord.Embed(
            title='💊 Dùng Đan Dược',
            description=(
                f'Bạn có `{len(ds_dan)}` loại đan dược.\n'
                f'Chọn đan muốn dùng bên dưới.'
            ),
            color=discord.Color.gold(),
        )
        embed.set_footer(text='Đan dược sẽ bị tiêu hao sau khi dùng')
        
        view = DungDanView(ds_dan)
        await interaction.followup.send(embed=embed, view=view)
    
    # ===== /danduoc — Xem chi tiết =====
    @app_commands.command(
        name='danduoc',
        description='Xem chi tiết đan dược (trong túi hoặc tra cứu)'
    )
    @app_commands.describe(ten='Tên đan dược (để trống để xem túi)')
    async def danduoc(
        self,
        interaction: discord.Interaction,
        ten: str = None,
    ):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # ===== Có tên → xem chi tiết =====
            if ten:
                cursor.execute("""
                    SELECT 
                        dd.*,
                        pdd.so_luong AS so_luong_tui
                    FROM player_dan_duoc pdd
                    JOIN tmpl_dan_duoc dd ON dd.id = pdd.dan_duoc_id
                    WHERE pdd.player_id = %s 
                      AND LOWER(dd.ten) = LOWER(%s)
                      AND pdd.so_luong > 0
                    LIMIT 1
                """, (player.player_id, ten))
                dan = cursor.fetchone()
                
                if not dan:
                    cursor.execute("""
                        SELECT * FROM tmpl_dan_duoc
                        WHERE LOWER(ten) = LOWER(%s)
                        LIMIT 1
                    """, (ten,))
                    dan = cursor.fetchone()
                    
                    if not dan:
                        await interaction.followup.send(
                            f'❌ Không tìm thấy đan dược `{ten}`!'
                        )
                        return
                    
                    embed = build_chi_tiet_embed(dan, so_luong_tui=None)
                    embed.set_footer(text='⚠️ Đan này không có trong túi bạn')
                    await interaction.followup.send(embed=embed)
                    return
                
                embed = build_chi_tiet_embed(dan, so_luong_tui=dan['so_luong_tui'])
                await interaction.followup.send(embed=embed)
                return
            
            # ===== Không có tên → xem túi =====
            cursor.execute("""
                SELECT 
                    dd.*,
                    pdd.so_luong
                FROM player_dan_duoc pdd
                JOIN tmpl_dan_duoc dd ON dd.id = pdd.dan_duoc_id
                WHERE pdd.player_id = %s AND pdd.so_luong > 0
                ORDER BY 
                    FIELD(dd.pham_cap, 'Pham', 'Linh', 'Bao', 'Tien', 'Than'),
                    dd.ten
            """, (player.player_id,))
            ds_dan = cursor.fetchall()
            
            if not ds_dan:
                await interaction.followup.send(
                    '💊 Bạn không có đan dược nào trong túi!\n'
                    'Mua tại `/shop` (tab Đan dược).'
                )
                return
            
            nhom = {}
            for dan in ds_dan:
                pc = dan['pham_cap']
                if pc not in nhom:
                    nhom[pc] = []
                nhom[pc].append(dan)
            
            embed = discord.Embed(
                title='💊 Đan Dược Trong Túi',
                description=(
                    f'Tổng: `{len(ds_dan)}` loại\n'
                    f'Chọn từ dropdown để xem chi tiết.'
                ),
                color=discord.Color.gold(),
            )
            
            for pc in ['Pham', 'Linh', 'Bao', 'Tien', 'Than']:
                if pc not in nhom:
                    continue
                ds = nhom[pc]
                lines = []
                for dan in ds[:15]:
                    pc_emoji = PHAM_CAP_EMOJI.get(pc, '⚪')
                    loai_str = LOAI_DAN.get(dan['loai'], dan['loai'])
                    lines.append(
                        f'{pc_emoji} **{dan["ten"]}** — `×{dan["so_luong"]:,}`\n'
                        f'   *{loai_str}*'
                    )
                if len(ds) > 15:
                    lines.append(f'*... và {len(ds) - 15} loại khác*')
                embed.add_field(
                    name=f'{PHAM_CAP_TEN.get(pc, pc)} ({len(ds)})',
                    value='\n'.join(lines),
                    inline=False,
                )
            
            embed.set_footer(text='Dùng /danduoc <tên> để xem chi tiết')
            
            view = XemChiTietView(ds_dan)
            await interaction.followup.send(embed=embed, view=view)
        
        except Exception as e:
            print(f'[ERROR] danduoc: {e}')
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f'❌ Lỗi: {e}')
        finally:
            cursor.close()
            conn.close()
    
    @danduoc.autocomplete('ten')
    async def danduoc_ten_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete tên đan dược.
        Ưu tiên đan trong túi của player, sau đó đến DB.
        """
        # Lấy player
        player = get_player_full_info(interaction.user.id)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # ⭐ Ưu tiên đan trong túi của player
            if player:
                if current:
                    cursor.execute("""
                        SELECT DISTINCT dd.ten
                        FROM player_dan_duoc pdd
                        JOIN tmpl_dan_duoc dd ON dd.id = pdd.dan_duoc_id
                        WHERE pdd.player_id = %s 
                          AND pdd.so_luong > 0
                          AND dd.ten LIKE %s
                        ORDER BY dd.ten
                        LIMIT 25
                    """, (player.player_id, f'%{current}%'))
                else:
                    cursor.execute("""
                        SELECT DISTINCT dd.ten
                        FROM player_dan_duoc pdd
                        JOIN tmpl_dan_duoc dd ON dd.id = pdd.dan_duoc_id
                        WHERE pdd.player_id = %s AND pdd.so_luong > 0
                        ORDER BY dd.ten
                        LIMIT 25
                    """, (player.player_id,))
                
                ds_tui = cursor.fetchall()
                
                if ds_tui:
                    return [
                        app_commands.Choice(name=r['ten'][:100], value=r['ten'][:100])
                        for r in ds_tui
                    ]
            
            # ⭐ Nếu không có đan trong túi → tìm tất cả trong DB
            if current:
                cursor.execute("""
                    SELECT ten FROM tmpl_dan_duoc
                    WHERE ten LIKE %s
                    ORDER BY ten
                    LIMIT 25
                """, (f'%{current}%',))
            else:
                cursor.execute("""
                    SELECT ten FROM tmpl_dan_duoc
                    ORDER BY ten
                    LIMIT 25
                """)
            
            return [
                app_commands.Choice(name=r['ten'][:100], value=r['ten'][:100])
                for r in cursor.fetchall()
            ]
        except Exception as e:
            print(f'[ERROR] autocomplete danduoc: {e}')
            return []
        finally:
            cursor.close()
            conn.close()

async def setup(bot):
    await bot.add_cog(DanDuoc(bot))