import discord
from discord import app_commands
from discord.ext import commands
import json

from database.player_repo import (
    get_player_full_info,
    get_player_dan_phuong_da_hoc,
    check_du_nguyen_lieu,
    tinh_ti_le_luyen_dan,
    luyen_dan_theo_cong_thuc,
    luyen_dan_tu_do,
    get_player_linh_thao,
)


PHAM_CAP_EMOJI = {
    'Pham': '🟤', 'Linh': '🟢', 'Bao': '🔵', 'Tien': '🟣', 'Than': '🟡',
}

PHAM_CAP_TEN = {
    'Pham': 'Phàm phẩm', 'Linh': 'Linh phẩm', 'Bao': 'Bảo phẩm',
    'Tien': 'Tiên phẩm', 'Than': 'Thần phẩm',
}


# ============================================================
# MENU CHỌN CHẾ ĐỘ
# ============================================================
class MenuChonCheDo(discord.ui.View):
    def __init__(self, player_id: int):
        super().__init__(timeout=120)
        self.player_id = player_id
    
    @discord.ui.button(label='Theo công thức', emoji='📜', style=discord.ButtonStyle.primary)
    async def theo_cong_thuc(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Lấy danh sách đan phương đã học
        ds_dp = get_player_dan_phuong_da_hoc(self.player_id)
        
        if not ds_dp:
            await interaction.response.send_message(
                '❌ Bạn chưa học đan phương nào!',
                ephemeral=True,
            )
            return
        
        embed = discord.Embed(
            title='📜 Luyện Đan Theo Công Thức',
            description=f'Bạn có `{len(ds_dp)}` đan phương đã học.\nChọn đan muốn luyện bên dưới.',
            color=discord.Color.orange(),
        )
        
        view = ChonDanPhuongView(self.player_id, ds_dp)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='Tự do', emoji='🎨', style=discord.ButtonStyle.success)
    async def tu_do(self, interaction: discord.Interaction, button: discord.ui.Button):
        ds_lt = get_player_linh_thao(self.player_id)
        
        if not ds_lt:
            await interaction.response.send_message(
                '❌ Bạn không có linh thảo nào trong túi!',
                ephemeral=True,
            )
            return
        
        # ⭐ Tạo state với player_id và ds_lt
        state = TuDoState(self.player_id, ds_lt)
        
        embed = build_tu_do_embed(state)
        view = TuDoView(state)
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='Đóng', emoji='❌', style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content='Đã đóng.', embed=None, view=None)


# ============================================================
# CHẾ ĐỘ 1: THEO CÔNG THỨC
# ============================================================
class ChonDanPhuongSelect(discord.ui.Select):
    def __init__(self, player_id: int, ds_dp: list):
        self.player_id = player_id
        self.ds_dp = ds_dp
        
        options = []
        for i, dp in enumerate(ds_dp[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(dp['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=dp['ten'][:100],
                description=PHAM_CAP_TEN.get(dp['pham_cap'], dp['pham_cap']),
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn đan phương muốn luyện...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        dp = self.ds_dp[idx]
        
        # Kiểm tra nguyên liệu
        check = check_du_nguyen_lieu(self.player_id, dp['dan_duoc_id'])
        
        embed = discord.Embed(
            title=f'⚗️ Xác Nhận Luyện Đan',
            description=f'Bạn muốn luyện **{dp["ten"]}**?',
            color=discord.Color.gold(),
        )
        
        # Nguyên liệu
        lines = []
        for nl in check['ds_can']:
            co = check['ds_co'].get(nl['linh_thao_id'], 0)
            can = nl['so_luong']
            status = '✅' if co >= can else '❌'
            lines.append(f'{status} **{nl["ten"]}** — `{co}/{can}`')
        
        embed.add_field(
            name='🌿 Nguyên liệu',
            value='\n'.join(lines),
            inline=False,
        )
        
        # Tỉ lệ thành công
        ti_le_data = tinh_ti_le_luyen_dan(self.player_id, dp['dan_duoc_id'])
        if ti_le_data:
            nguon_lines = []
            for n in ti_le_data['nguon']:
                nguon_lines.append(f'{n["emoji"]} **{n["ten"]}**: `+{n["gia_tri"]:.2f}%`')
            
            embed.add_field(
                name=f'📊 Tỉ lệ thành công: `{ti_le_data["ti_le_cuoi"]:.2f}%`',
                value='\n'.join(nguon_lines),
                inline=False,
            )
        
        if not check['du']:
            embed.add_field(
                name='❌ Không đủ nguyên liệu',
                value='Bạn cần thêm linh thảo để luyện đan này.',
                inline=False,
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        embed.set_footer(text='Nhấn Xác nhận để luyện đan')
        
        view = XacNhanLuyenView(self.player_id, dp['dan_duoc_id'])
        await interaction.response.edit_message(embed=embed, view=view)


class ChonDanPhuongView(discord.ui.View):
    def __init__(self, player_id: int, ds_dp: list):
        super().__init__(timeout=120)
        self.add_item(ChonDanPhuongSelect(player_id, ds_dp))


class XacNhanLuyenView(discord.ui.View):
    def __init__(self, player_id: int, dan_duoc_id: int):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.dan_duoc_id = dan_duoc_id
    
    @discord.ui.button(label='Xác nhận', emoji='⚗️', style=discord.ButtonStyle.success)
    async def xac_nhan(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        # Luyện đan
        ket_qua = luyen_dan_theo_cong_thuc(self.player_id, self.dan_duoc_id)
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                f'❌ {ket_qua["loi"]}',
                ephemeral=True,
            )
            return
        
        # Build embed kết quả
        embed = build_ket_qua_embed(ket_qua)
        await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label='Hủy', emoji='❌', style=discord.ButtonStyle.danger)
    async def huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message('❌ Đã hủy.', ephemeral=True)

# ============================================================
# CHẾ ĐỘ 2: TỰ DO
# ============================================================
class TuDoState:
    """State cho chế độ tự do."""
    def __init__(self, player_id: int, ds_lt: list):
        self.player_id = player_id
        self.ds_lt = ds_lt
        self.ds_chon = {}  # {linh_thao_id: {'ten': str, 'so_luong': int, 'pham_cap': str}}


class ChonLinhThaoSelect(discord.ui.Select):
    def __init__(self, state: TuDoState):
        self.state = state
        
        options = []
        for lt in state.ds_lt[:25]:
            pc_emoji = PHAM_CAP_EMOJI.get(lt['pham_cap'], '⚪')
            da_chon = state.ds_chon.get(lt['id'], {}).get('so_luong', 0)
            con_lai = lt['so_luong'] - da_chon
            
            if con_lai <= 0:
                continue
            
            desc = f"Có: {con_lai}"
            if da_chon > 0:
                desc = f"Đã chọn: {da_chon} | Còn: {con_lai}"
            
            options.append(discord.SelectOption(
                label=lt['ten'][:100],
                description=desc,
                emoji=pc_emoji,
                value=str(lt['id']),
            ))
        
        if not options:
            options.append(discord.SelectOption(label='Không còn linh thảo', value='0'))
        
        super().__init__(
            placeholder='Chọn linh thảo để thêm...',
            options=options[:25],
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        lt_id = int(self.values[0])
        
        if lt_id == 0:
            await interaction.response.send_message('❌ Không còn linh thảo!', ephemeral=True)
            return
        
        lt = next((x for x in self.state.ds_lt if x['id'] == lt_id), None)
        if not lt:
            await interaction.response.send_message('❌ Không tìm thấy linh thảo!', ephemeral=True)
            return
        
        # Mở modal nhập số lượng
        await interaction.response.send_modal(
            NhapSoLuongModal(self.state, lt)
        )


class NhapSoLuongModal(discord.ui.Modal, title='Nhập Số Lượng'):
    def __init__(self, state: TuDoState, linh_thao: dict):
        super().__init__()
        self.state = state
        self.linh_thao = linh_thao
        
        da_chon = state.ds_chon.get(linh_thao['id'], {}).get('so_luong', 0)
        con_lai = linh_thao['so_luong'] - da_chon
        
        self.so_luong = discord.ui.TextInput(
            label=f'Số lượng (tối đa {con_lai})',
            placeholder='Nhập số lượng',
            default='1',
            min_length=1,
            max_length=5,
        )
        self.add_item(self.so_luong)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            so_luong = int(self.so_luong.value)
        except ValueError:
            await interaction.response.send_message('❌ Số lượng không hợp lệ!', ephemeral=True)
            return
        
        da_chon = self.state.ds_chon.get(self.linh_thao['id'], {}).get('so_luong', 0)
        con_lai = self.linh_thao['so_luong'] - da_chon
        
        if so_luong <= 0 or so_luong > con_lai:
            await interaction.response.send_message(
                f'❌ Số lượng phải từ 1 đến {con_lai}!',
                ephemeral=True,
            )
            return
        
        # Cập nhật state
        self.state.ds_chon[self.linh_thao['id']] = {
            'ten': self.linh_thao['ten'],
            'so_luong': da_chon + so_luong,
            'pham_cap': self.linh_thao['pham_cap'],
        }
        
        # ⭐ Rebuild toàn bộ message
        embed = build_tu_do_embed(self.state)
        view = TuDoView(self.state)
        
        await interaction.response.edit_message(embed=embed, view=view)


def build_tu_do_embed(state: TuDoState) -> discord.Embed:
    """Build embed cho chế độ tự do."""
    embed = discord.Embed(
        title='🎨 Luyện Đan Tự Do',
        description=(
            'Chọn linh thảo và số lượng để luyện.\n'
            'Nếu tổ hợp khớp công thức đan phương nào đó, bạn sẽ học được đan phương đó!'
        ),
        color=discord.Color.green(),
    )
    
    # Danh sách đã chọn
    if state.ds_chon:
        lines = []
        for lt_id, info in state.ds_chon.items():
            pc_emoji = PHAM_CAP_EMOJI.get(info['pham_cap'], '⚪')
            lines.append(f'{pc_emoji} **{info["ten"]}** — `×{info["so_luong"]}`')
        
        embed.add_field(
            name=f'📋 Đã chọn ({len(state.ds_chon)} loại)',
            value='\n'.join(lines),
            inline=False,
        )
    else:
        embed.add_field(
            name='📋 Đã chọn',
            value='*Chưa chọn linh thảo nào*',
            inline=False,
        )
    
    return embed


# ============================================================
# VIEW CHÍNH CHO CHẾ ĐỘ TỰ DO
# ============================================================
class TuDoView(discord.ui.View):
    def __init__(self, state: TuDoState):
        super().__init__(timeout=300)
        self.state = state
        
        # Dropdown chọn linh thảo
        self.add_item(ChonLinhThaoSelect(state))
        
        # Nút "Bỏ linh thảo" — chỉ hiện khi có ít nhất 1 linh thảo
        if state.ds_chon:
            self.add_item(XoaLinhThaoButton(state))
        
        # Nút "Xác nhận"
        self.add_item(XacNhanTuDoButton(state))
        
        # Nút "Hủy"
        self.add_item(HuyTuDoButton())


class XoaLinhThaoButton(discord.ui.Button):
    def __init__(self, state: TuDoState):
        super().__init__(
            label='Bỏ linh thảo',
            emoji='🗑️',
            style=discord.ButtonStyle.secondary,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        # Hiển thị view mới để chọn linh thảo muốn bỏ
        embed = discord.Embed(
            title='🗑️ Bỏ Linh Thảo',
            description='Chọn linh thảo muốn bỏ khỏi danh sách:',
            color=discord.Color.red(),
        )
        
        view = XoaLinhThaoView(self.state)
        await interaction.response.edit_message(embed=embed, view=view)


class XoaLinhThaoView(discord.ui.View):
    def __init__(self, state: TuDoState):
        super().__init__(timeout=120)
        self.state = state
        self.add_item(XoaSelect(state))
        self.add_item(QuayLaiButton(state))


class XoaSelect(discord.ui.Select):
    def __init__(self, state: TuDoState):
        self.state = state
        
        options = []
        for lt_id, info in state.ds_chon.items():
            pc_emoji = PHAM_CAP_EMOJI.get(info['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=info['ten'][:100],
                description=f"Đang chọn: {info['so_luong']}",
                emoji=pc_emoji,
                value=str(lt_id),
            ))
        
        if not options:
            options.append(discord.SelectOption(label='Không có gì để bỏ', value='0'))
        
        super().__init__(
            placeholder='Chọn linh thảo muốn bỏ...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        lt_id = int(self.values[0])
        
        if lt_id == 0:
            return
        
        # Xóa khỏi state
        if lt_id in self.state.ds_chon:
            ten = self.state.ds_chon[lt_id]['ten']
            del self.state.ds_chon[lt_id]
        
        # Rebuild message với view chính
        embed = build_tu_do_embed(self.state)
        view = TuDoView(self.state)
        
        await interaction.response.edit_message(embed=embed, view=view)


class QuayLaiButton(discord.ui.Button):
    def __init__(self, state: TuDoState):
        super().__init__(
            label='Quay lại',
            emoji='↩️',
            style=discord.ButtonStyle.primary,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        embed = build_tu_do_embed(self.state)
        view = TuDoView(self.state)
        await interaction.response.edit_message(embed=embed, view=view)


class XacNhanTuDoButton(discord.ui.Button):
    def __init__(self, state: TuDoState):
        super().__init__(
            label='Xác nhận luyện',
            emoji='⚗️',
            style=discord.ButtonStyle.success,
        )
        self.state = state
    
    async def callback(self, interaction: discord.Interaction):
        if not self.state.ds_chon:
            await interaction.response.send_message('❌ Chưa chọn linh thảo!', ephemeral=True)
            return
        
        # Chuyển dict
        nguyen_lieu_dict = {
            lt_id: info['so_luong']
            for lt_id, info in self.state.ds_chon.items()
        }
        
        # Disable view
        for child in self.view.children:
            child.disabled = True
        await interaction.message.edit(view=self.view)
        
        # Luyện
        ket_qua = luyen_dan_tu_do(self.state.player_id, nguyen_lieu_dict)
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                f'❌ {ket_qua["loi"]}',
                ephemeral=True,
            )
            return
        
        # Build embed kết quả
        embed = build_ket_qua_embed(ket_qua, hoc_moi=ket_qua.get('hoc_moi', False))
        await interaction.response.send_message(embed=embed)


class HuyTuDoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='Hủy',
            emoji='❌',
            style=discord.ButtonStyle.danger,
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content='❌ Đã hủy luyện đan.',
            embed=None,
            view=None,
        )
        


# ============================================================
# EMBED KẾT QUẢ
# ============================================================
def build_ket_qua_embed(ket_qua: dict, hoc_moi: bool = False) -> discord.Embed:
    """Build embed kết quả luyện đan."""
    thanh_cong_count = ket_qua['so_vien_thanh_cong']
    that_bai_count = ket_qua['so_vien_that_bai']
    max_vien = ket_qua['max_vien']
    
    if thanh_cong_count > 0:
        embed = discord.Embed(
            title='🎉 Luyện Đan Thành Công!',
            description=f'Bạn đã luyện **{ket_qua["ten_dan"]}**!',
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title='💔 Luyện Đan Thất Bại',
            description=f'Bạn đã thất bại khi luyện **{ket_qua["ten_dan"]}**.',
            color=discord.Color.red(),
        )
    
    # Thông tin chung
    embed.add_field(
        name='📦 Kết quả',
        value=(
            f'✅ Thành công: `{thanh_cong_count}/{max_vien}`\n'
            f'❌ Thất bại: `{that_bai_count}/{max_vien}`'
        ),
        inline=True,
    )
    embed.add_field(
        name='📊 Tỉ lệ',
        value=f'`{ket_qua["ti_le"]:.2f}%`',
        inline=True,
    )
    embed.add_field(
        name='⚒️ Exp nghề',
        value=f'`+{ket_qua["exp_nhan"]:,}`',
        inline=True,
    )
    
    # Chi tiết từng viên (nếu ít)
    if max_vien <= 9:
        lines = []
        for v in ket_qua['chi_tiet_vien']:
            emoji = '✅' if v['thanh_cong'] else '❌'
            lines.append(f'{emoji} Viên {v["stt"]}: `{v["roll"]:.2f}` (exp: `{v["exp"]:.2f}`)')
        
        embed.add_field(
            name='🔍 Chi tiết roll',
            value='\n'.join(lines),
            inline=False,
        )
    
    # Thông báo học đan phương mới
    if hoc_moi:
        embed.add_field(
            name='📜 Học được đan phương mới!',
            value=f'Bạn đã tự học được đan phương **{ket_qua["ten_dan"]}**!',
            inline=False,
        )
    
    return embed


# ============================================================
# COG
# ============================================================
class LuyenDan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
    name='luyendan',
    description='Luyện đan từ linh thảo'
)
    async def luyendan(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        try:
            player = get_player_full_info(interaction.user.id)
            if not player:
                await interaction.followup.send('❌ Bạn chưa đăng ký!')
                return
            
            # ⭐ CHECK NGHỀ LUYỆN ĐAN SƯ
            from database.player_repo import get_player_nghe_nghiep
            nghe = get_player_nghe_nghiep(player.player_id)
            if not nghe or nghe['loai'] != 'LuyenDan':
                await interaction.followup.send(
                    '❌ Bạn không phải **Luyện Đan Sư**!\n'
                    'Dùng `/chonnghe` để chọn nghề Luyện Đan Sư.'
                )
                return
            
            embed = discord.Embed(
                title='⚗️ Luyện Đan',
                description=(
                    'Chọn chế độ luyện đan:\n\n'
                    '📜 **Theo công thức** — Chọn đan phương đã học, hệ thống tự lấy nguyên liệu.\n'
                    '🎨 **Tự do** — Tự chọn linh thảo, nếu khớp công thức sẽ tự học đan phương.'
                ),
                color=discord.Color.orange(),
            )
            
            view = MenuChonCheDo(player.player_id)
            await interaction.followup.send(embed=embed, view=view)
        
        except Exception as e:
            print(f'[ERROR] luyendan: {e}')
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send(
                    f'❌ Có lỗi xảy ra: `{e}`'
                )
            except:
                pass


async def setup(bot):
    await bot.add_cog(LuyenDan(bot))