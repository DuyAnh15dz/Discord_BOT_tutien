import discord
from discord import app_commands
from discord.ext import commands

from database.player_repo import get_player_full_info, get_player_nghe_nghiep
from database.nghe_repo import (
    get_ds_phap_khi_template,
    get_phap_khi_cong_thuc,
    check_du_khoang_thach,
    tinh_ti_le_luyen_khi,
    luyen_khi,
    get_ds_phap_khi_cua_player,
    trang_bi_phap_khi,
    thao_phap_khi,
    nang_cap_phap_khi,
)


PHAM_CAP_EMOJI = {
    'Pham': '🟤', 'Linh': '🟢', 'Bao': '🔵', 'Tien': '🟣', 'Than': '🟡',
}

LOAI_PHAP_KHI = {
    'VuKhi': '⚔️ Vũ khí', 'Ao': '👕 Áo', 'Non': '🎩 Nón',
    'Giay': '👢 Giày', 'Nhan': '💍 Nhẫn',
}

HE_EMOJI = {
    'Kim': '⚔️', 'Moc': '🌳', 'Thuy': '💧', 'Hoa': '🔥', 'Tho': '⛰',
    'Loi': '⚡', 'Bang': '❄️', 'Phong': '🌪️', 'Duong': '☀️', 'Am': '🌑',
}


class LuyenKhi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='luyenkhi',
        description='[Luyện Khí Sư] Luyện pháp khí từ khoáng thạch'
    )
    async def luyenkhi(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        nghe = get_player_nghe_nghiep(player.player_id)
        if not nghe or nghe['loai'] != 'LuyenKhi':
            await interaction.followup.send('❌ Bạn không phải **Luyện Khí Sư**!')
            return
        
        ds_pk = get_ds_phap_khi_template()
        if not ds_pk:
            await interaction.followup.send('❌ Không có pháp khí nào!')
            return
        
        embed = discord.Embed(
            title='⚒️ Luyện Khí',
            description=(
                f'Cấp nghề: `{nghe["cap_do"]}/{nghe["cap_toi_da"]}`\n'
                f'Chọn pháp khí muốn luyện bên dưới.'
            ),
            color=discord.Color.dark_gold(),
        )
        
        view = LuyenKhiSelectView(player.player_id, ds_pk)
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name='phapkhi', description='Xem pháp khí sở hữu')
    async def phapkhi(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_pk = get_ds_phap_khi_cua_player(player.player_id)
        if not ds_pk:
            await interaction.followup.send(
                '⚔️ Bạn chưa có pháp khí nào!\nDùng `/luyenkhi` để luyện.'
            )
            return
        
        embed = discord.Embed(
            title=f'⚔️ Pháp Khí của {player.ten_nhan_vat}',
            description=f'Tổng: `{len(ds_pk)}`',
            color=discord.Color.dark_gold(),
        )
        
        nhom = {}
        for pk in ds_pk:
            nhom.setdefault(pk['loai'], []).append(pk)
        
        for loai in ['VuKhi', 'Ao', 'Non', 'Giay', 'Nhan']:
            if loai not in nhom:
                continue
            ds = nhom[loai]
            lines = []
            for pk in ds[:10]:
                pc_emoji = PHAM_CAP_EMOJI.get(pk['pham_cap'], '⚪')
                he_emoji = HE_EMOJI.get(pk['he'], '') if pk['he'] else ''
                status = '🟢' if pk['dang_trang_bi'] else '⚪'
                lines.append(f'{status} {pc_emoji} {he_emoji} **{pk["ten"]}** `+{pk["cap_do"]}`')
            embed.add_field(
                name=f'{LOAI_PHAP_KHI.get(loai, loai)} ({len(ds)})',
                value='\n'.join(lines),
                inline=False,
            )
        
        embed.set_footer(text='Dùng /trangbi để trang bị pháp khí')
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name='trangbi', description='Trang bị pháp khí')
    async def trangbi(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_pk = get_ds_phap_khi_cua_player(player.player_id)
        if not ds_pk:
            await interaction.followup.send('❌ Bạn chưa có pháp khí nào!')
            return
        
        embed = discord.Embed(
            title='🎽 Trang Bị Pháp Khí',
            description='Chọn pháp khí muốn trang bị.',
            color=discord.Color.blue(),
        )
        view = TrangBiSelectView(player.player_id, ds_pk)
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(
        name='nangcap-phapkhi',
        description='Nâng cấp pháp khí (dùng khoáng thạch)'
    )
    async def nangcap_phapkhi(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký!')
            return
        
        ds_pk = get_ds_phap_khi_cua_player(player.player_id)
        if not ds_pk:
            await interaction.followup.send('❌ Bạn chưa có pháp khí nào!')
            return
        
        embed = discord.Embed(
            title='⬆️ Nâng Cấp Pháp Khí',
            description='Chọn pháp khí muốn nâng cấp.',
            color=discord.Color.gold(),
        )
        view = NangCapSelectView(player.player_id, ds_pk)
        await interaction.followup.send(embed=embed, view=view)


# ============================================================
# SELECTS & VIEWS
# ============================================================

class LuyenKhiSelect(discord.ui.Select):
    def __init__(self, player_id: int, ds_pk: list):
        self.player_id = player_id
        self.ds_pk = ds_pk
        
        options = []
        for i, pk in enumerate(ds_pk[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(pk['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=pk['ten'][:100],
                description=f"{LOAI_PHAP_KHI.get(pk['loai'], pk['loai'])} — {pk['pham_cap']}",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn pháp khí muốn luyện...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        pk = self.ds_pk[idx]
        
        cong_thuc = get_phap_khi_cong_thuc(pk['id'])
        check = check_du_khoang_thach(self.player_id, cong_thuc['nguyen_lieu'])
        ti_le_data = tinh_ti_le_luyen_khi(self.player_id, pk['id'])
        
        embed = discord.Embed(
            title=f'⚒️ Luyện {pk["ten"]}',
            color=discord.Color.dark_gold(),
        )
        
        lines = []
        for nl in cong_thuc['nguyen_lieu']:
            co = check['ds_co'].get(nl['khoang_thach_id'], 0)
            can = nl['so_luong']
            status = '✅' if co >= can else '❌'
            lines.append(f'{status} **{nl["ten"]}** — `{co}/{can}`')
        
        embed.add_field(name='⛰ Nguyên liệu', value='\n'.join(lines), inline=False)
        
        if ti_le_data:
            nguon_lines = [f'{n["emoji"]} **{n["ten"]}**: `+{n["gia_tri"]:.2f}%`' 
                          for n in ti_le_data['nguon']]
            embed.add_field(
                name=f'📊 Tỉ lệ: `{ti_le_data["ti_le_cuoi"]:.2f}%`',
                value='\n'.join(nguon_lines),
                inline=False,
            )
        
        if not check['du']:
            embed.add_field(
                name='❌ Không đủ nguyên liệu',
                value='Cần thêm khoáng thạch.',
                inline=False,
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        view = XacNhanLuyenKhiView(self.player_id, pk['id'])
        await interaction.response.edit_message(embed=embed, view=view)


class LuyenKhiSelectView(discord.ui.View):
    def __init__(self, player_id: int, ds_pk: list):
        super().__init__(timeout=180)
        self.add_item(LuyenKhiSelect(player_id, ds_pk))


class XacNhanLuyenKhiView(discord.ui.View):
    def __init__(self, player_id: int, phap_khi_id: int):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.phap_khi_id = phap_khi_id
    
    @discord.ui.button(label='Xác nhận', emoji='⚒️', style=discord.ButtonStyle.success)
    async def xac_nhan(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        ket_qua = luyen_khi(self.player_id, self.phap_khi_id)
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(f'❌ {ket_qua["loi"]}', ephemeral=True)
            return
        
        if ket_qua['luyen_thanh_cong']:
            embed = discord.Embed(
                title='🎉 Luyện Khí Thành Công!',
                description=f'Bạn đã luyện thành **{ket_qua["ten_phap_khi"]}**!',
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title='💔 Luyện Khí Thất Bại',
                description=f'Bạn thất bại khi luyện **{ket_qua["ten_phap_khi"]}**.',
                color=discord.Color.red(),
            )
        
        embed.add_field(
            name='🎲 Roll',
            value=f'`{ket_qua["roll"]:.2f}` / `{ket_qua["ti_le"]:.2f}%`',
            inline=True,
        )
        embed.add_field(
            name='⚒️ Exp nghề',
            value=f'`+{ket_qua["exp_nhan"]}`',
            inline=True,
        )
        
        await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label='Hủy', emoji='❌', style=discord.ButtonStyle.danger)
    async def huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message('❌ Đã hủy.', ephemeral=True)


class TrangBiSelect(discord.ui.Select):
    def __init__(self, player_id: int, ds_pk: list):
        self.player_id = player_id
        self.ds_pk = ds_pk
        
        options = []
        for i, pk in enumerate(ds_pk[:25]):
            pc_emoji = PHAM_CAP_EMOJI.get(pk['pham_cap'], '⚪')
            status = '🟢 Đang dùng' if pk['dang_trang_bi'] else '⚪'
            options.append(discord.SelectOption(
                label=f"{pk['ten']} +{pk['cap_do']}",
                description=f"{status} — {LOAI_PHAP_KHI.get(pk['loai'], pk['loai'])}",
                emoji=pc_emoji,
                value=str(i),
            ))
        
        super().__init__(
            placeholder='Chọn pháp khí...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        pk = self.ds_pk[idx]
        
        if pk['dang_trang_bi']:
            ket_qua = thao_phap_khi(self.player_id, pk['id'])
            action = 'tháo'
        else:
            ket_qua = trang_bi_phap_khi(self.player_id, pk['id'])
            action = 'trang bị'
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(
                f'❌ {ket_qua.get("loi", "Lỗi!")}', ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f'✅ Đã {action} pháp khí',
            description=f'**{pk["ten"]}**',
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Recompute stat
        from database.player_repo import get_connection, recompute_player_stat
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            recompute_player_stat(cursor, self.player_id)
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class TrangBiSelectView(discord.ui.View):
    def __init__(self, player_id: int, ds_pk: list):
        super().__init__(timeout=180)
        self.add_item(TrangBiSelect(player_id, ds_pk))


class NangCapSelect(discord.ui.Select):
    def __init__(self, player_id: int, ds_pk: list):
        self.player_id = player_id
        self.ds_pk = ds_pk
        
        options = []
        for i, pk in enumerate(ds_pk[:25]):
            if pk['cap_do'] >= pk['cap_toi_da']:
                continue
            pc_emoji = PHAM_CAP_EMOJI.get(pk['pham_cap'], '⚪')
            options.append(discord.SelectOption(
                label=f"{pk['ten']} +{pk['cap_do']}/{pk['cap_toi_da']}",
                description=LOAI_PHAP_KHI.get(pk['loai'], pk['loai']),
                emoji=pc_emoji,
                value=str(i),
            ))
        
        if not options:
            options.append(discord.SelectOption(label='Không có pháp khí nâng được', value='-1'))
        
        super().__init__(
            placeholder='Chọn pháp khí...',
            options=options[:25],
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        if idx < 0:
            await interaction.response.send_message('❌ Tất cả pháp khí đã max!', ephemeral=True)
            return
        
        pk = self.ds_pk[idx]
        ket_qua = nang_cap_phap_khi(self.player_id, pk['id'])
        
        if not ket_qua['thanh_cong']:
            await interaction.response.send_message(f'❌ {ket_qua["loi"]}', ephemeral=True)
            return
        
        if ket_qua['nang_cap_thanh_cong']:
            embed = discord.Embed(
                title='🎉 Nâng Cấp Thành Công!',
                description=f'**{ket_qua["ten"]}** lên cấp **+{ket_qua["cap_moi"]}**!',
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title='💔 Nâng Cấp Thất Bại',
                description=f'**{ket_qua["ten"]}** giữ cấp **+{ket_qua["cap_cu"]}**.',
                color=discord.Color.red(),
            )
        
        embed.add_field(name='🎲 Roll', 
                       value=f'`{ket_qua["roll"]:.2f}` / `{ket_qua["ti_le"]:.2f}%`', 
                       inline=True)
        embed.add_field(name='⛰ Đã dùng', 
                       value=f'`{ket_qua["khoang_thach_da_dung"]}`', 
                       inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Recompute
        from database.player_repo import get_connection, recompute_player_stat
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            recompute_player_stat(cursor, self.player_id)
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class NangCapSelectView(discord.ui.View):
    def __init__(self, player_id: int, ds_pk: list):
        super().__init__(timeout=180)
        self.add_item(NangCapSelect(player_id, ds_pk))


async def setup(bot):
    await bot.add_cog(LuyenKhi(bot))