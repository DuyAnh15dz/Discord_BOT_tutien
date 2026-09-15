import discord
from discord import app_commands
from discord.ext import commands

from database.connection import get_connection
from database.player_repo import (
    get_player_full_info,
    get_player_nghe_nghiep,
)


# ============================================================
# MAPPING NGHỀ
# ============================================================
NGHE_INFO = {
    1: {
        'ten': 'Luyện Đan Sư',
        'emoji': '🧪',
        'mo_ta_ngan': '+30% linh thảo, +20% tu luyện Hỏa/Mộc, +5% luyện đan',
        'bonus_list': [
            ('🌿', '+30%', 'Tỉ lệ gặp linh thảo khi lịch luyện'),
            ('🔥', '+20%', 'Hiệu suất tu luyện công pháp Hỏa hệ'),
            ('🌳', '+20%', 'Hiệu suất tu luyện công pháp Mộc hệ'),
            ('💊', '+20%', 'Hiệu quả tích cực khi dùng đan dược'),
            ('⚗️', '+5%',  'Tỉ lệ thành công khi luyện đan'),
        ],
    },
    2: {
        'ten': 'Luyện Khí Sư',
        'emoji': '⚒️',
        'mo_ta_ngan': '+30% linh thạch, +30% khoáng thạch, +20% tu luyện Kim/Thổ',
        'bonus_list': [
            ('💰', '+30%', 'Lượng linh thạch nhận khi lịch luyện'),
            ('🪨', '+30%', 'Tỉ lệ gặp khoáng thạch khi lịch luyện'),
            ('⚔️', '+20%', 'Hiệu suất tu luyện công pháp Kim hệ'),
            ('🏔️', '+20%', 'Hiệu suất tu luyện công pháp Thổ hệ'),
            ('🔨', '+5%',  'Tỉ lệ thành công khi luyện khí'),
        ],
    },
    3: {
        'ten': 'Trận Pháp Sư',
        'emoji': '🔮',
        'mo_ta_ngan': '+20% đạo cụ, +20% tu luyện Thủy/Phong/Âm/Dương',
        'bonus_list': [
            ('🎁', '+20%', 'Tỉ lệ rớt đạo cụ'),
            ('💧', '+20%', 'Hiệu suất tu luyện công pháp Thủy hệ'),
            ('🌪️', '+20%', 'Hiệu suất tu luyện công pháp Phong hệ'),
            ('☀️', '+20%', 'Hiệu suất tu luyện công pháp Dương hệ'),
            ('🌑', '+20%', 'Hiệu suất tu luyện công pháp Âm hệ'),
            ('🔯', '+10%', 'Tỉ lệ thành công khi bày trận'),
        ],
    },
    4: {
        'ten': 'Phù Lục Sư',
        'emoji': '📜',
        'mo_ta_ngan': '+20% linh thạch, +5% tu luyện toàn hệ, +10% vẽ phù',
        'bonus_list': [
            ('💰', '+20%', 'Tỉ lệ gặp linh thạch khi lịch luyện'),
            ('📊', '+5%',  'Hiệu suất tu luyện công pháp TOÀN BỘ 10 hệ'),
            ('✍️', '+10%', 'Tỉ lệ thành công khi vẽ phù lục'),
        ],
    },
}


# ============================================================
# DROPDOWN CHỌN NGHỀ
# ============================================================
class NgheSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info['ten'],
                description=info['mo_ta_ngan'][:100],
                emoji=info['emoji'],
                value=str(nghe_id),
            )
            for nghe_id, info in NGHE_INFO.items()
        ]
        super().__init__(
            placeholder='Chọn nghề nghiệp của bạn...',
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        nghe_id = int(self.values[0])
        player_id = self.view.player_id
        info = NGHE_INFO[nghe_id]

        # 1. Check đã chọn nghề chưa
        existing = get_player_nghe_nghiep(player_id)
        if existing:
            await interaction.response.send_message(
                f'❌ Bạn đã chọn nghề **{existing["ten"]}** rồi!',
                ephemeral=True,
            )
            return

        # 2. Insert vào DB
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO player_nghe_nghiep
                (player_id, nghe_nghiep_id, cap_do, kinh_nghiem, danh_vong)
                VALUES (%s, %s, 1, 0, 0)
            """, (player_id, nghe_id))
            conn.commit()
        except Exception as e:
            print(f'[ERROR] chon nghe: {e}')
            await interaction.response.send_message(
                '❌ Có lỗi xảy ra!', ephemeral=True
            )
            return
        finally:
            cursor.close()
            conn.close()

        # 3. Response — Embed xác nhận (public)
        embed = discord.Embed(
            title=f'{info["emoji"]} Đã chọn nghề!',
            description=f'Bạn đã trở thành **{info["ten"]}**',
            color=discord.Color.green(),
        )
        embed.add_field(
            name='📊 Cấp độ',
            value='Cấp **1/9**',
            inline=True,
        )
        embed.add_field(
            name='📈 Kinh nghiệm',
            value='`0 / 300`',
            inline=True,
        )
        embed.set_footer(text='Dùng /profile để xem chi tiết')
        await interaction.response.send_message(embed=embed)

        # 4. Response — Embed chi tiết bonus (ephemeral — chỉ user thấy)
        bonus_text = '\n'.join(
            f'{emoji} **{value}** — {desc}'
            for emoji, value, desc in info['bonus_list']
        )
        embed_bonus = discord.Embed(
            title=f'✨ Chi tiết Bonus của {info["ten"]}',
            description=bonus_text,
            color=discord.Color.gold(),
        )
        embed_bonus.set_footer(text='Bonus này áp dụng tự động khi làm các hoạt động')
        await interaction.followup.send(embed=embed_bonus, ephemeral=True)

        # 5. Disable dropdown
        self.disabled = True
        await interaction.message.edit(view=self.view)
        self.view.stop()


class NgheView(discord.ui.View):
    def __init__(self, player_id: int):
        super().__init__(timeout=300)
        self.player_id = player_id
        self.add_item(NgheSelect())


# ============================================================
# COG /chonnghe
# ============================================================
class Nghe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='chonnghe', description='Chọn nghề nghiệp')
    async def chonnghe(self, interaction: discord.Interaction):
        await interaction.response.defer()

        player = get_player_full_info(interaction.user.id)
        if not player:
            await interaction.followup.send('❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.')
            return

        existing = get_player_nghe_nghiep(player.player_id)
        if existing:
            await interaction.followup.send(
                f'❌ Bạn đã chọn nghề **{existing["ten"]}** (cấp {existing["cap_do"]}) rồi!'
            )
            return

        view = NgheView(player_id=player.player_id)   # ← DÙNG KEY
        await interaction.followup.send(
            '👇 **Chọn nghề nghiệp của bạn** (chỉ chọn được 1 lần):',
            view=view,
        )


async def setup(bot):
    await bot.add_cog(Nghe(bot))