import discord
from discord import app_commands
from discord.ext import commands

from database.player_repo import get_ds_bxh_active, get_top_bxh


HANG_EMOJI = {1: '🥇', 2: '🥈', 3: '🥉'}


def format_bxh_embed(ds_top: list, bxh_meta: dict) -> discord.Embed:
    """Build embed BXH."""
    ten = bxh_meta['ten']
    emoji = bxh_meta.get('emoji') or '🏆'
    
    embed = discord.Embed(
        title=f'{emoji} Bảng Xếp Hạng — {ten}',
        description=f'Top **{len(ds_top)}** player',
        color=discord.Color.gold(),
    )
    
    if not ds_top:
        embed.description = 'Chưa có player nào!'
        return embed
    
    lines = []
    for i, player in enumerate(ds_top, 1):
        hang_emoji = HANG_EMOJI.get(i, f'#{i}')
        ten_player = player['ten_nhan_vat']
        gia_tri = player.get('gia_tri_hien_thi', '?')
        
        if i <= 3:
            lines.append(f'{hang_emoji} **{ten_player}** — `{gia_tri}`')
        else:
            lines.append(f'{hang_emoji} {ten_player} — `{gia_tri}`')
    
    embed.add_field(
        name='📊 Bảng xếp hạng',
        value='\n'.join(lines),
        inline=False,
    )
    
    loai = bxh_meta['loai']
    if loai == 'seasonal':
        embed.set_footer(text='BXH tuần - Reset mỗi thứ 2')
    else:
        embed.set_footer(text='BXH tổng - Trao thưởng 10h thứ 2 hàng tuần')
    
    return embed


class BXHSelect(discord.ui.Select):
    def __init__(self, ds_bxh: list):
        self.ds_bxh = ds_bxh
        
        options = []
        for bxh in ds_bxh[:25]:
            emoji = bxh.get('emoji') or '🏆'
            label_suffix = ' (tuần)' if bxh['loai'] == 'seasonal' else ''
            options.append(discord.SelectOption(
                label=f'{bxh["ten"]}{label_suffix}'[:100],
                emoji=emoji,
                value=bxh['code'],
            ))
        
        super().__init__(
            placeholder='Chọn loại bảng xếp hạng...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        code = self.values[0]
        bxh_meta = next((x for x in self.ds_bxh if x['code'] == code), None)
        
        if not bxh_meta:
            await interaction.response.send_message('❌ Không tìm thấy BXH!', ephemeral=True)
            return
        
        ds_top = get_top_bxh(code, limit=10)
        embed = format_bxh_embed(ds_top, bxh_meta)
        await interaction.response.edit_message(embed=embed, view=self.view)


class BXHView(discord.ui.View):
    def __init__(self, ds_bxh: list):
        super().__init__(timeout=180)
        self.add_item(BXHSelect(ds_bxh))


class BXH(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='bxh',
        description='Xem bảng xếp hạng'
    )
    async def bxh(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        ds_bxh = get_ds_bxh_active()
        
        if not ds_bxh:
            await interaction.followup.send('❌ Chưa có BXH nào!')
            return
        
        default = ds_bxh[0]
        ds_top = get_top_bxh(default['code'], limit=10)
        embed = format_bxh_embed(ds_top, default)
        
        view = BXHView(ds_bxh)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(BXH(bot))