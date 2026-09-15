import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta

from database.player_repo import trao_thuong_tat_ca_bxh, get_bxh_by_code


class BXHTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_run_week = None
        self.check_bxh.start()
    
    def cog_unload(self):
        self.check_bxh.cancel()
    
    @tasks.loop(minutes=30)
    async def check_bxh(self):
        """Check mỗi 30 phút. Nếu 10h sáng thứ 2 (VN) và chưa chạy tuần này → chạy."""
        tz_vn = timezone(timedelta(hours=7))
        now = datetime.now(tz_vn)
        
        if now.weekday() != 0 or now.hour != 10:
            return
        
        tuan = now.strftime('%Y-%m-%d')
        if self.last_run_week == tuan:
            return
        
        self.last_run_week = tuan
        await self.trao_thuong()
    
    async def trao_thuong(self):
        try:
            print('[BXH] Bắt đầu trao thưởng...')
            ket_qua = trao_thuong_tat_ca_bxh()
            
            if not ket_qua['thanh_cong']:
                print(f'[BXH] Lỗi: {ket_qua["loi"]}')
                return
            
            for code, ds in ket_qua['chi_tiet'].items():
                for player in ds:
                    await self.gui_dm(player, code, ket_qua['tuan'])
            
            print(f'[BXH] Đã trao thưởng tuần {ket_qua["tuan"]}')
        except Exception as e:
            print(f'[BXH] Lỗi: {e}')
            import traceback
            traceback.print_exc()
    
    async def gui_dm(self, player: dict, loai_bxh: str, tuan: str):
        try:
            meta = get_bxh_by_code(loai_bxh)
            ten_bxh = meta['ten'] if meta else loai_bxh
            emoji_bxh = meta.get('emoji', '🏆') if meta else '🏆'
            
            user = await self.bot.fetch_user(player['discord_id'])
            if not user:
                return
            
            hang = player['hang']
            hang_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(hang, f'#{hang}')
            thuong = player['thuong']
            
            embed = discord.Embed(
                title=f'{hang_emoji} Chúc Mừng Top {hang}!',
                description=(
                    f'Bạn đạt **hạng {hang}** trong BXH '
                    f'{emoji_bxh} **{ten_bxh}** tuần này!'
                ),
                color=discord.Color.gold(),
            )
            
            embed.add_field(
                name='🎁 Phần thưởng',
                value=(
                    f'💰 Linh thạch: `+{thuong["linh_thach"]:,}`\n'
                    f'📈 Exp: `+{thuong["exp"]:,}`\n'
                    f'🔮 Tu vi: `+{thuong["tu_vi"]:,}`\n'
                    f'✨ Hệ số: `×{thuong["he_so"]}`'
                ),
                inline=False,
            )
            
            if player.get('dan_phuong_nhan'):
                lines = [f'• **{dp["ten"]}**' for dp in player['dan_phuong_nhan']]
                embed.add_field(
                    name=f'📜 Đan phương ({len(player["dan_phuong_nhan"])})',
                    value='\n'.join(lines),
                    inline=False,
                )
            
            if thuong.get('linh_dich'):
                embed.add_field(
                    name='💧 Đặc biệt',
                    value='**Linh Dịch Nhỏ** (Phàm) × 1',
                    inline=False,
                )
            
            if player.get('la_lien_tiep'):
                embed.add_field(
                    name='⚠️ Lưu ý',
                    value='Bạn đã top 1 tuần trước → tuần này **không nhận đặc biệt**. Tuần sau sẽ nhận lại!',
                    inline=False,
                )
            
            embed.set_footer(text=f'Tuần {tuan}')
            await user.send(embed=embed)
        except Exception as e:
            print(f'[BXH] Lỗi gửi DM cho {player["discord_id"]}: {e}')
    
    @check_bxh.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BXHTask(bot))