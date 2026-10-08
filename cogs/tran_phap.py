import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio

from database.player_repo import get_player_full_info, get_player_nghe_nghiep
from database.nghe_repo import (
    get_ds_tran_phap_full,
    check_du_tran_cu,
    bay_tran_voi_quiz_v3,
    get_tran_dang_bay,
    thu_tran,
)
from utils.tran_phap_quiz import lay_cau_hoi_random


PHAM_CAP_EMOJI = {
    'Pham': '🟤', 'Linh': '🟢', 'Bao': '🔵', 'Tien': '🟣', 'Than': '🟡',
}

LOAI_TRAN = {
    'Buff': '✨ Buff', 'Debuff': '💀 Debuff', 'HonHop': '🌀 Hỗn hợp',
}


class TranPhap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='baytran',
        description='[Trận Pháp Sư] Bày trận (đạo cụ + quiz 3 câu)'
    )
    async def baytran(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        nghe = get_player_nghe_nghiep(player.player_id)
        if not nghe or nghe['loai'] != 'TranPhap':
            await interaction.followup.send('❌ Bạn không phải **Trận Pháp Sư**!')
            return
        
        tran_active = get_tran_dang_bay(player.player_id)
        if tran_active:
            con_lai = int((tran_active['het_han_luc'] - datetime.now()).total_seconds())
            await interaction.followup.send(
                f'⚠️ Bạn đang bày trận **{tran_active["ten"]}**.\n'
                f'Còn `{con_lai // 60}` phút. Dùng `/thutran` để thu.'
            )
            return
        
        ds_tp = get_ds_tran_phap_full()
        if not ds_tp:
            await interaction.followup.send('❌ Không có trận pháp nào!')
            return
        
        embed = discord.Embed(
            title='🔮 Bày Trận Pháp',
            description=(
                f'Cấp nghề: `{nghe["cap_do"]}/{nghe["cap_toi_da"]}`\n'
                f'Bạn sẽ trả lời **3 câu hỏi** trước khi bày trận.'
            ),
            color=discord.Color.purple(),
        )
        
        view = BayTranSelectView(player.player_id, ds_tp)
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name='thutran', description='Thu trận pháp')
    async def thutran(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        tran = get_tran_dang_bay(player.player_id)
        if not tran:
            await interaction.followup.send('❌ Bạn không có trận nào!')
            return
        
        ket_qua = thu_tran(player.player_id)
        
        if ket_qua['thanh_cong']:
            embed = discord.Embed(
                title='✅ Đã Thu Trận',
                description=f'Trận **{tran["ten"]}** đã thu hồi.',
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed)
            
            from database.player_repo import get_connection, recompute_player_stat
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                recompute_player_stat(cursor, player.player_id)
                conn.commit()
            finally:
                cursor.close()
                conn.close()


class BayTranSelect(discord.ui.Select):
    def __init__(self, player_id: int, ds_tp: list):
        self.player_id = player_id
        self.ds_tp = ds_tp
        
        options = []
        for i, tp in enumerate(ds_tp[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(tp['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=tp['ten'][:100],
                description=f"{LOAI_TRAN.get(tp['loai'], tp['loai'])} — Cấp {tp['yeu_cau_nghe_cap']}",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn trận pháp muốn bày...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        tp = self.ds_tp[idx]
        
        check = check_du_tran_cu(self.player_id, tp['id'])
        if not check:
            await interaction.response.send_message('❌ Lỗi!', ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f'🔮 Bày Trận: {tp["ten"]}',
            description=tp.get('mo_ta') or '*Không có mô tả*',
            color=discord.Color.purple(),
        )
        
        lines = []
        for it in check['items']:
            status = '✅' if it['du'] else '❌'
            lines.append(f'{status} {it["loai"]}: **{it["ten"]}** — `{it["co"]}/{it["can"]}`')
        
        embed.add_field(name='🎴 Đạo cụ cần', value='\n'.join(lines), inline=False)
        embed.add_field(
            name='📝 Quiz',
            value=f'`3` câu hỏi\nMỗi câu đúng: +5% tỉ lệ, +10% thời gian',
            inline=False,
        )
        
        if not check['du']:
            embed.add_field(
                name='❌ Không đủ đạo cụ',
                value='Mua tại `/shop` (tab Trận cụ).',
                inline=False,
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        view = XacNhanQuizView(self.player_id, tp['id'])
        await interaction.response.edit_message(embed=embed, view=view)


class BayTranSelectView(discord.ui.View):
    def __init__(self, player_id: int, ds_tp: list):
        super().__init__(timeout=180)
        self.add_item(BayTranSelect(player_id, ds_tp))


class XacNhanQuizView(discord.ui.View):
    def __init__(self, player_id: int, tran_phap_id: int):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.tran_phap_id = tran_phap_id
    
    @discord.ui.button(label='Bắt đầu Quiz', emoji='📝', style=discord.ButtonStyle.primary)
    async def bat_dau(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        ds_cau_hoi = lay_cau_hoi_random(3)
        
        state = QuizState(
            player_id=self.player_id,
            tran_phap_id=self.tran_phap_id,
            ds_cau_hoi=ds_cau_hoi,
            chi_so_cau=0,
            so_cau_dung=0,
            chi_tiet=[],
        )
        
        await hien_cau_hoi(interaction, state, edit=True)
    
    @discord.ui.button(label='Hủy', emoji='❌', style=discord.ButtonStyle.danger)
    async def huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message('❌ Đã hủy.', ephemeral=True)


class QuizState:
    def __init__(self, player_id, tran_phap_id, ds_cau_hoi, chi_so_cau, 
                 so_cau_dung, chi_tiet):
        self.player_id = player_id
        self.tran_phap_id = tran_phap_id
        self.ds_cau_hoi = ds_cau_hoi
        self.chi_so_cau = chi_so_cau
        self.so_cau_dung = so_cau_dung
        self.chi_tiet = chi_tiet


async def hien_cau_hoi(interaction: discord.Interaction, state: QuizState, edit: bool = True):
    if state.chi_so_cau >= len(state.ds_cau_hoi):
        await xu_ly_ket_qua_quiz(interaction, state)
        return
    
    cau = state.ds_cau_hoi[state.chi_so_cau]
    
    embed = discord.Embed(
        title=f'📝 Câu {state.chi_so_cau + 1}/{len(state.ds_cau_hoi)}',
        description=f'**{cau["cau_hoi"]}**',
        color=discord.Color.blue(),
    )
    embed.set_footer(text='Chọn đáp án — Không tiết lộ đáp án đúng')
    
    view = CauHoiView(state, cau)
    
    await interaction.response.edit_message(embed=embed, view=view)


class CauHoiView(discord.ui.View):
    def __init__(self, state: QuizState, cau_hoi: dict):
        super().__init__(timeout=120)
        self.state = state
        self.cau_hoi = cau_hoi
        
        for i, letter in enumerate(['A', 'B', 'C', 'D']):
            button = discord.ui.Button(
                label=f'{letter}. {cau_hoi["dap_an"][i]}',
                style=discord.ButtonStyle.secondary,
                custom_id=letter,
            )
            button.callback = self.make_callback(letter)
            self.add_item(button)
    
    def make_callback(self, letter: str):
        async def callback(interaction: discord.Interaction):
            dung = (letter == self.cau_hoi['dung'])
            
            self.state.chi_tiet.append({
                'id': self.cau_hoi.get('id', self.state.chi_so_cau + 1),
                'chon': letter,
                'dap_an': self.cau_hoi['dung'],
                'dung': dung,
            })
            
            if dung:
                self.state.so_cau_dung += 1
            
            # Disable buttons VÀ chuyển câu tiếp — gộp vào 1 response duy nhất
            self.state.chi_so_cau += 1
            
            if self.state.chi_so_cau >= len(self.state.ds_cau_hoi):
                # Hết câu → xử lý kết quả trực tiếp
                await interaction.response.defer()
                await xu_ly_ket_qua_quiz(interaction, self.state)
                return
            
            # Còn câu → hiện câu tiếp
            cau_tiep = self.state.ds_cau_hoi[self.state.chi_so_cau]
            
            embed = discord.Embed(
                title=f'📝 Câu {self.state.chi_so_cau + 1}/{len(self.state.ds_cau_hoi)}',
                description=f'**{cau_tiep["cau_hoi"]}**',
                color=discord.Color.blue(),
            )
            embed.set_footer(text='Chọn đáp án — Không tiết lộ đáp án đúng')
            
            view = CauHoiView(self.state, cau_tiep)
            await interaction.response.edit_message(embed=embed, view=view)
        
        return callback


async def xu_ly_ket_qua_quiz(interaction: discord.Interaction, state: QuizState):
    ket_qua = bay_tran_voi_quiz_v3(
        state.player_id,
        state.tran_phap_id,
        state.so_cau_dung,
        len(state.ds_cau_hoi),
        state.chi_tiet,
    )
    
    if not ket_qua['thanh_cong']:
        await interaction.edit_original_response(
            content=f'❌ {ket_qua["loi"]}', embed=None, view=None,
        )
        return
    
    if ket_qua['bay_thanh_cong']:
        embed = discord.Embed(
            title='🎉 Bày Trận Thành Công!',
            description=f'Trận **{ket_qua["ten"]}** đã kích hoạt!',
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title='💔 Bày Trận Thất Bại',
            description=f'Trận **{ket_qua["ten"]}** không kích hoạt được.',
            color=discord.Color.red(),
        )
    
    embed.add_field(
        name='📝 Quiz',
        value=f'Đúng **{ket_qua["so_cau_dung"]}/{ket_qua["tong_cau"]}** câu',
        inline=False,
    )
    
    if ket_qua['so_cau_dung'] > 0:
        embed.add_field(
            name='✨ Bonus từ Quiz',
            value=(
                f'• Tỉ lệ: `+{ket_qua["so_cau_dung"] * 5}%`\n'
                f'• Thời gian: `+{ket_qua["so_cau_dung"] * 10}%`'
            ),
            inline=False,
        )
    
    qh = ket_qua['quan_he_nhan']
    embed.add_field(
        name='🌟 Hệ nhãn',
        value=f'{qh["mo_ta"]}\nHệ số: `×{ket_qua["he_so_nhan"]}`',
        inline=False,
    )
    
    embed.add_field(
        name='📊 Roll',
        value=f'Tỉ lệ: `{ket_qua["ti_le_cuoi"]:.2f}%`\nRoll: `{ket_qua["roll"]:.2f}`',
        inline=True,
    )
    embed.add_field(
        name='⏱️ Thời gian',
        value=f'`{ket_qua["thoi_gian_cuoi"] // 60}` phút',
        inline=True,
    )
    embed.add_field(
        name='🔯 Exp nghề',
        value=f'`+{ket_qua["exp_nhan"]:,}`',
        inline=True,
    )
    
    if ket_qua['bay_thanh_cong']:
        from database.player_repo import get_connection, recompute_player_stat
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            recompute_player_stat(cursor, state.player_id)
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    await interaction.edit_original_response(embed=embed, view=None)
    
    
async def xu_ly_ket_qua_quiz(interaction: discord.Interaction, state: QuizState):
    ket_qua = bay_tran_voi_quiz_v3(
        state.player_id,
        state.tran_phap_id,
        state.so_cau_dung,
        len(state.ds_cau_hoi),
        state.chi_tiet,
    )
    
    if not ket_qua['thanh_cong']:
        # Dùng edit_original_response vì interaction đã defer
        await interaction.edit_original_response(
            content=f'❌ {ket_qua["loi"]}', embed=None, view=None,
        )
        return
    
    if ket_qua['bay_thanh_cong']:
        embed = discord.Embed(
            title='🎉 Bày Trận Thành Công!',
            description=f'Trận **{ket_qua["ten"]}** đã kích hoạt!',
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title='💔 Bày Trận Thất Bại',
            description=f'Trận **{ket_qua["ten"]}** không kích hoạt được.',
            color=discord.Color.red(),
        )
    
    embed.add_field(
        name='📝 Quiz',
        value=f'Đúng **{ket_qua["so_cau_dung"]}/{ket_qua["tong_cau"]}** câu',
        inline=False,
    )
    
    if ket_qua['so_cau_dung'] > 0:
        embed.add_field(
            name='✨ Bonus từ Quiz',
            value=(
                f'• Tỉ lệ: `+{ket_qua["so_cau_dung"] * 5}%`\n'
                f'• Thời gian: `+{ket_qua["so_cau_dung"] * 10}%`'
            ),
            inline=False,
        )
    
    qh = ket_qua['quan_he_nhan']
    embed.add_field(
        name='🌟 Hệ nhãn',
        value=f'{qh["mo_ta"]}\nHệ số: `×{ket_qua["he_so_nhan"]}`',
        inline=False,
    )
    
    embed.add_field(
        name='📊 Roll',
        value=f'Tỉ lệ: `{ket_qua["ti_le_cuoi"]:.2f}%`\nRoll: `{ket_qua["roll"]:.2f}`',
        inline=True,
    )
    embed.add_field(
        name='⏱️ Thời gian',
        value=f'`{ket_qua["thoi_gian_cuoi"] // 60}` phút',
        inline=True,
    )
    embed.add_field(
        name='🔯 Exp nghề',
        value=f'`+{ket_qua["exp_nhan"]:,}`',
        inline=True,
    )
    
    if ket_qua['bay_thanh_cong']:
        from database.player_repo import get_connection, recompute_player_stat
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            recompute_player_stat(cursor, state.player_id)
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    # Dùng edit_original_response vì interaction đã defer
    await interaction.edit_original_response(embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(TranPhap(bot))