import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# MAPPING HIỂN THỊ
# ============================================================
TAB_INFO = {
    'bat_dau': {
        'ten': '🌱 Bắt đầu',
        'mo_ta': 'Các lệnh cần thiết khi mới vào game',
    },
    'tu_luyen': {
        'ten': '⚔️ Tu luyện',
        'mo_ta': 'Tu luyện, đột phá, lịch luyện, công pháp',
    },
    'vat_pham': {
        'ten': '🎒 Vật phẩm',
        'mo_ta': 'Túi đồ, đan dược, đạo cụ, đan phương',
    },
    'nghe': {
        'ten': '⚒️ Nghề nghiệp',
        'mo_ta': 'Luyện khí, trận pháp, bùa chú',
    },
    'kinh_te': {
        'ten': '🛒 Kinh tế',
        'mo_ta': 'Cửa hàng, mua bán, đổi tiền',
    },
    'khac': {
        'ten': '🎁 Khác',
        'mo_ta': 'BXH, daily, thống kê, hướng dẫn',
    },
}


# ============================================================
# BUILD EMBED CHO TỪNG TAB
# ============================================================
def build_tab_bat_dau() -> discord.Embed:
    embed = discord.Embed(
        title='🌱 Bắt đầu',
        description='Các lệnh cần thiết khi mới vào game.',
        color=discord.Color.green(),
    )
    
    embed.add_field(
        name='`/nhapmon <ten>`',
        value='Đăng ký nhân vật tu tiên. Chỉ dùng được 1 lần.',
        inline=False,
    )
    embed.add_field(
        name='`/chonnghe`',
        value=(
            'Chọn 1 trong 4 nghề: **Luyện Đan Sư**, **Luyện Khí Sư**, '
            '**Trận Pháp Sư**, **Phù Lục Sư**.\n'
            'Mỗi nghề có bonus và cơ chế khác nhau — chọn kỹ vì **không đổi được**.'
        ),
        inline=False,
    )
    embed.add_field(
        name='`/profile`',
        value='Xem thông tin nhân vật: cảnh giới, exp, HP, linh căn, nghề...',
        inline=False,
    )
    embed.add_field(
        name='`/stats`',
        value='Xem chi tiết tất cả chỉ số (40+ stat).',
        inline=False,
    )
    
    embed.set_footer(text='Bước đầu tiên: /nhapmon <tên nhân vật>')
    return embed


def build_tab_tu_luyen() -> discord.Embed:
    embed = discord.Embed(
        title='⚔️ Tu luyện',
        description='Các lệnh tu luyện, đột phá, công pháp.',
        color=discord.Color.red(),
    )
    
    embed.add_field(
        name='`/tuluyen`',
        value='Tu luyện nhận exp + tu vi. Có cooldown. Tích lũy độ tinh khiết linh căn.',
        inline=False,
    )
    embed.add_field(
        name='`/dotpha`',
        value='Đột phá cảnh giới khi ở tầng cuối. Có roll tỉ lệ + cooldown khi thất bại.',
        inline=False,
    )
    embed.add_field(
        name='`/lichluyen`',
        value=(
            'Đi lịch luyện nhận nhiều phần thưởng: linh thạch, linh thảo, '
            'khoáng thạch, đan phương... Có cooldown.'
        ),
        inline=False,
    )
    embed.add_field(
        name='`/linhcan`',
        value='Xem danh sách linh căn sở hữu.',
        inline=False,
    )
    embed.add_field(
        name='`/linhcan-chitiet <tên>`',
        value='Xem chi tiết 1 linh căn (stat bonus, độ tinh khiết).',
        inline=False,
    )
    embed.add_field(
        name='`/dotpha-linhcan`',
        value='Đột phá linh căn lên phẩm cấp cao hơn (Hạ → Trung → Thượng...).',
        inline=False,
    )
    embed.add_field(
        name='`/hoc`',
        value='Học đan phương hoặc công pháp từ túi.',
        inline=False,
    )
    embed.add_field(
        name='`/congphap`',
        value='Xem danh sách công pháp đã học.',
        inline=False,
    )
    embed.add_field(
        name='`/congphap-chitiet <tên>`',
        value='Xem chi tiết 1 công pháp (bonus, độ thuần thục).',
        inline=False,
    )
    embed.add_field(
        name='`/congphap-tuluyen <tên>`',
        value='Bật/tắt tu luyện công pháp (tối đa 2 công pháp song song).',
        inline=False,
    )
    embed.add_field(
        name='`/congphap-tangtang <tên>`',
        value='Tăng tầng công pháp (dùng tu vi).',
        inline=False,
    )
    
    return embed


def build_tab_vat_pham() -> discord.Embed:
    embed = discord.Embed(
        title='🎒 Vật phẩm',
        description='Túi đồ, đan dược, đạo cụ, đan phương.',
        color=discord.Color.purple(),
    )
    
    embed.add_field(
        name='`/bag`',
        value=(
            'Xem túi đồ với 6 tab: **Linh thảo**, **Đan dược**, **Đạo cụ**, '
            '**Khoáng thạch**, **Đan phương**, **Công pháp**.'
        ),
        inline=False,
    )
    embed.add_field(
        name='`/danduoc [tên]`',
        value='Xem chi tiết đan dược trong túi hoặc tra cứu.',
        inline=False,
    )
    embed.add_field(
        name='`/drug`',
        value='Dùng đan dược (hồi phục, buff, tăng tu vi...).',
        inline=False,
    )
    embed.add_field(
        name='`/daocu`',
        value='Xem danh sách đạo cụ sở hữu.',
        inline=False,
    )
    embed.add_field(
        name='`/daocu-chitiet <tên>`',
        value='Xem chi tiết 1 đạo cụ.',
        inline=False,
    )
    embed.add_field(
        name='`/dungdaocu`',
        value='Dùng đạo cụ tăng tinh khiết linh căn.',
        inline=False,
    )
    embed.add_field(
        name='`/danphuong`',
        value='Xem danh sách đan phương đã học.',
        inline=False,
    )
    embed.add_field(
        name='`/danphuong-chitiet <tên>`',
        value='Xem chi tiết đan phương (nguyên liệu, tỉ lệ).',
        inline=False,
    )
    embed.add_field(
        name='`/luyendan`',
        value='Luyện đan từ linh thảo (2 chế độ: theo công thức + tự do).',
        inline=False,
    )
    
    return embed


def build_tab_nghe() -> discord.Embed:
    embed = discord.Embed(
        title='⚒️ Nghề nghiệp',
        description=(
            'Hệ thống nghề nghiệp — chỉ dùng được khi đã chọn nghề tương ứng.\n'
            'Chọn nghề tại `/chonnghe` (chỉ 1 lần).'
        ),
        color=discord.Color.dark_gold(),
    )
    
    # ===== LUYỆN KHÍ SƯ =====
    embed.add_field(
        name='⚔️ **Luyện Khí Sư** — Pháp khí',
        value=(
            '`/luyenkhi` — Luyện pháp khí từ khoáng thạch\n'
            '`/phapkhi` — Xem danh sách pháp khí sở hữu\n'
            '`/trangbi` — Trang bị/tháo pháp khí (5 slot: Vũ khí, Áo, Nón, Giày, Nhẫn)\n'
            '`/nangcap-phapkhi` — Nâng cấp pháp khí (dùng khoáng thạch)'
        ),
        inline=False,
    )
    
    # ===== TRẬN PHÁP SƯ =====
    embed.add_field(
        name='🔮 **Trận Pháp Sư** — Trận pháp',
        value=(
            '`/baytran` — Bày trận pháp:\n'
            '  1. Chọn trận pháp (cần Trận Cờ + Trận Bàn + Trận Nhãn)\n'
            '  2. Trả lời **3 câu quiz** về thiên địa, ngũ hành, âm dương\n'
            '  3. Nhận buff theo thời gian (đúng câu → tăng tỉ lệ + thời gian)\n'
            '`/thutran` — Thu hồi trận pháp đang bày'
        ),
        inline=False,
    )
    
    # ===== PHÙ LỤC SƯ =====
    embed.add_field(
        name='📜 **Phù Lục Sư** — Bùa chú',
        value=(
            '`/vebua` — Vẽ bùa chú (10 lá/lần, tiêu hao MP + máu yêu thú + linh dịch)\n'
            '`/buachu` — Xem danh sách bùa chú sở hữu\n'
            '`/dungbua` — Dùng bùa (hồi phục, buff, sát thương)'
        ),
        inline=False,
    )
    
    # ===== LUYỆN ĐAN SƯ =====
    embed.add_field(
        name='💊 **Luyện Đan Sư** — Đan dược',
        value=(
            '`/luyendan` — Luyện đan (xem chi tiết ở tab Vật phẩm)\n'
            '`/danphuong` — Xem đan phương đã học'
        ),
        inline=False,
    )
    
    embed.add_field(
        name='💡 **Mẹo**',
        value=(
            '• Nguyên liệu nghề (khoáng thạch, máu yêu thú, linh dịch, trận cụ) '
            'mua tại `/shop`.\n'
            '• Nâng cấp nghề bằng cách sử dụng (mỗi lần luyện/vẽ/bày trận đều tăng exp nghề).\n'
            '• Pháp khí và trận pháp bonus **cộng trực tiếp vào stat** — '
            'dùng `/stats` để xem.'
        ),
        inline=False,
    )
    
    return embed


def build_tab_kinh_te() -> discord.Embed:
    embed = discord.Embed(
        title='🛒 Kinh tế',
        description='Cửa hàng, mua bán, đổi tiền.',
        color=discord.Color.gold(),
    )
    
    embed.add_field(
        name='`/shop`',
        value=(
            'Xem cửa hàng với 8 tab: **Đan dược**, **Đạo cụ**, **Linh thảo**, '
            '**Khoáng thạch**, **Công pháp**, **Trận cụ**, **Máu yêu thú**, **Linh dịch**.'
        ),
        inline=False,
    )
    embed.add_field(
        name='`/mua <id> <số lượng>`',
        value='Mua item từ shop. VD: `/mua 21 3`.',
        inline=False,
    )
    embed.add_field(
        name='`/sell <loại>`',
        value=(
            'Bán khoáng thạch, linh thảo, công pháp. '
            'VD: `/sell loai:Khoáng thạch`.'
        ),
        inline=False,
    )
    embed.add_field(
        name='`/exchange <số tiên ngọc>`',
        value='Đổi linh thạch → tiên ngọc. Tỉ lệ: 1 tiên ngọc = 10,000 linh thạch.',
        inline=False,
    )
    
    return embed


def build_tab_khac() -> discord.Embed:
    embed = discord.Embed(
        title='🎁 Khác',
        description='BXH, daily, thống kê, hướng dẫn.',
        color=discord.Color.blue(),
    )
    
    embed.add_field(
        name='`/bxh`',
        value=(
            'Xem bảng xếp hạng (cảnh giới, linh thạch, tu vi, nghề nghiệp).\n'
            'Trao thưởng 10h sáng thứ 2 hàng tuần.'
        ),
        inline=False,
    )
    embed.add_field(
        name='`/daily`',
        value=(
            'Điểm danh hàng ngày nhận linh thạch.\n'
            'Có streak bonus (+1.5%/ngày).'
        ),
        inline=False,
    )
    embed.add_field(
        name='`/help`',
        value='Xem hướng dẫn này.',
        inline=False,
    )
    
    return embed


# ============================================================
# DROPDOWN CHỌN TAB
# ============================================================
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=TAB_INFO[key]['ten'],
                description=TAB_INFO[key]['mo_ta'][:100],
                value=key,
            )
            for key in TAB_INFO
        ]
        
        super().__init__(
            placeholder='Chọn mục muốn xem hướng dẫn...',
            options=options,
            min_values=1, max_values=1,
        )
    
    async def callback(self, interaction: discord.Interaction):
        tab = self.values[0]
        
        if tab == 'bat_dau':
            embed = build_tab_bat_dau()
        elif tab == 'tu_luyen':
            embed = build_tab_tu_luyen()
        elif tab == 'vat_pham':
            embed = build_tab_vat_pham()
        elif tab == 'nghe':
            embed = build_tab_nghe()
        elif tab == 'kinh_te':
            embed = build_tab_kinh_te()
        elif tab == 'khac':
            embed = build_tab_khac()
        else:
            embed = build_tab_bat_dau()
        
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(HelpSelect())


# ============================================================
# COG
# ============================================================
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name='help',
        description='Xem hướng dẫn sử dụng bot'
    )
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        
        embed = discord.Embed(
            title='📖 Hướng Dẫn Sử Dụng Bot',
            description=(
                '**Chào mừng đến với Bạch Liên Giới!**\n\n'
                'Chọn mục muốn xem hướng dẫn từ dropdown bên dưới.\n\n'
                '🌱 **Bắt đầu** — Lệnh cơ bản cho người mới\n'
                '⚔️ **Tu luyện** — Tu luyện, đột phá, công pháp\n'
                '🎒 **Vật phẩm** — Túi đồ, đan dược, đạo cụ\n'
                '⚒️ **Nghề nghiệp** — Luyện khí, trận pháp, bùa chú\n'
                '🛒 **Kinh tế** — Cửa hàng, mua bán\n'
                '🎁 **Khác** — BXH, daily, thống kê'
            ),
            color=discord.Color.blurple(),
        )
        
        embed.set_footer(text='Dùng /nhapmon để bắt đầu hành trình tu tiên!')
        
        view = HelpView()
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Help(bot))