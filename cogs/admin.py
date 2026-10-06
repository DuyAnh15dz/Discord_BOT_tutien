import discord
from discord import app_commands
from discord.ext import commands

from config import ADMIN_IDS
from database.connection import get_connection
from database.player_repo import (
    get_player_full_info,
    delete_player,
    add_exp_and_tuvi,
    xu_ly_tang_tu_dong,
    recompute_player_stat,
    restock_shop_item,
    restock_toan_bo,
    them_dan_phuong_vao_tui,
    them_cong_phap_vao_tui,
)


def is_admin(user_id: int) -> bool:
    """Check user có phải admin không."""
    return user_id in ADMIN_IDS


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ============================================================
    # /xoanhanvat
    # ============================================================
    @app_commands.command(
        name='xoanhanvat',
        description='[ADMIN] Xóa nhân vật của 1 user'
    )
    @app_commands.describe(
        user='User cần xóa nhân vật',
        xac_nhan='Gõ "XOA" để xác nhận'
    )
    async def xoanhanvat(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        xac_nhan: str,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(
                '❌ Bạn không có quyền dùng lệnh này!',
                ephemeral=True
            )
            return

        if xac_nhan != 'XOA':
            await interaction.response.send_message(
                '❌ Để xác nhận, gõ chính xác `XOA` vào tham số `xac_nhan`.\n'
                'Ví dụ: `/xoanhanvat user: @ai_do xac_nhan: XOA`',
                ephemeral=True
            )
            return

        await interaction.response.defer()

        player = get_player_full_info(user.id)
        if not player:
            await interaction.followup.send(
                f'❌ User {user.mention} không có nhân vật!'
            )
            return

        player_info = {
            'ten': player.ten_nhan_vat,
            'canh_gioi': f'{player.canh_gioi_ten} tầng {player.tang_canh_gioi}',
            'tu_vi': player.tu_vi,
            'linh_thach': player.linh_thach,
        }

        try:
            success = delete_player(player.player_id)
        except Exception as e:
            print(f'[ERROR] delete_player: {e}')
            await interaction.followup.send(
                f'❌ Có lỗi khi xóa nhân vật: `{e}`'
            )
            return

        if not success:
            await interaction.followup.send(
                '❌ Không tìm thấy nhân vật để xóa!'
            )
            return

        print(f'[ADMIN] {interaction.user} đã xóa nhân vật của {user} '
              f'(discord_id={user.id}, ten={player_info["ten"]})')

        embed = discord.Embed(
            title='🗑️ Đã xóa nhân vật',
            description=f'Nhân vật của {user.mention} đã bị xóa vĩnh viễn.',
            color=discord.Color.red()
        )
        embed.add_field(
            name='Thông tin trước khi xóa',
            value=(
                f'**Tên:** {player_info["ten"]}\n'
                f'**Cảnh giới:** {player_info["canh_gioi"]}\n'
                f'**Tu vi:** {player_info["tu_vi"]:,}\n'
                f'**Linh thạch:** {player_info["linh_thach"]:,}'
            ),
            inline=False
        )
        embed.set_footer(
            text=f'Admin: {interaction.user} | User: {user.id}'
        )
        await interaction.followup.send(embed=embed)

    # ============================================================
    # /addexp
    # ============================================================
    @app_commands.command(
        name='addexp',
        description='[ADMIN] Cộng exp cho player (test lên tầng)'
    )
    @app_commands.describe(
        user='User cần cộng exp',
        amount='Số exp cần cộng',
    )
    async def addexp(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        amount: int,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(
                '❌ Bạn không có quyền dùng lệnh này!',
                ephemeral=True
            )
            return

        if amount <= 0:
            await interaction.response.send_message(
                '❌ Số exp phải lớn hơn 0!',
                ephemeral=True
            )
            return

        if amount > 1_000_000_000:
            await interaction.response.send_message(
                '❌ Số exp quá lớn (max 1 tỷ)!',
                ephemeral=True
            )
            return

        await interaction.response.defer()

        player = get_player_full_info(user.id)
        if not player:
            await interaction.followup.send(
                f'❌ User {user.mention} chưa có nhân vật!'
            )
            return

        exp_cu = player.exp
        tang_cu = player.tang_canh_gioi
        canh_gioi_cu = player.canh_gioi_ten

        add_exp_and_tuvi(player.player_id, amount, 0)
        ket_qua_tang = xu_ly_tang_tu_dong(player.player_id)
        player_moi = get_player_full_info(user.id)

        embed = discord.Embed(
            title='✅ Đã cộng exp',
            description=(
                f'Admin {interaction.user.mention} cộng **+{amount:,}** exp '
                f'cho {user.mention}'
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name='📊 Trước',
            value=(
                f'• Exp: `{exp_cu:,}`\n'
                f'• Tầng: `{tang_cu}/{player_moi.so_tang}`\n'
                f'• Cảnh giới: `{canh_gioi_cu}`'
            ),
            inline=True
        )

        embed.add_field(
            name='📊 Sau',
            value=(
                f'• Exp: `{player_moi.exp:,}`\n'
                f'• Tầng: `{player_moi.tang_canh_gioi}/{player_moi.so_tang}`\n'
                f'• Cảnh giới: `{player_moi.canh_gioi_ten}`'
            ),
            inline=True
        )

        if ket_qua_tang and ket_qua_tang['so_tang_len'] > 0:
            lines = [
                f'⬆️ **Lên {ket_qua_tang["so_tang_len"]} tầng!**',
                f'Tầng {ket_qua_tang["tang_cu"]} → {ket_qua_tang["tang_moi"]}',
                f'Exp còn lại: `{ket_qua_tang["exp_con_lai"]:,}`',
            ]
            if ket_qua_tang['da_max_tang']:
                lines.append('🎯 **Đã đạt tầng tối đa!** Có thể `/dotpha`')

            embed.add_field(
                name='⬆️ Kết quả',
                value='\n'.join(lines),
                inline=False
            )
        else:
            embed.add_field(
                name='⬆️ Kết quả',
                value='*Chưa đủ exp để lên tầng*',
                inline=False
            )

        embed.set_footer(text=f'Admin: {interaction.user} | User: {user.id}')

        print(f'[ADMIN] {interaction.user} added {amount:,} exp to {user} '
              f'(discord_id={user.id})')

        await interaction.followup.send(embed=embed)

    # ============================================================
    # /recompute
    # ============================================================
    @app_commands.command(
        name='recompute',
        description='[ADMIN] Recompute stat player'
    )
    async def recompute(
        self,
        interaction: discord.Interaction,
        user: discord.User,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return

        player = get_player_full_info(user.id)
        if not player:
            await interaction.response.send_message('❌ User chưa có nhân vật!')
            return

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            ket_qua = recompute_player_stat(cursor, player.player_id)
            conn.commit()
        except Exception as e:
            conn.rollback()
            await interaction.response.send_message(f'❌ Lỗi: {e}')
            return
        finally:
            cursor.close()
            conn.close()

        await interaction.response.send_message(
            f'✅ Đã recompute cho {user.mention}\n'
            f'HP max: `{ket_qua.get("hp_max")}`\n'
            f'ATK: `{ket_qua.get("atk")}`'
        )

    # ============================================================
    # /restock
    # ============================================================
    @app_commands.command(
        name='restock',
        description='[ADMIN] Nhập hàng cho shop'
    )
    @app_commands.describe(
        shop_id='ID shop item (dùng 0 để nhập tất cả)',
        so_luong='Số lượng nhập thêm',
    )
    async def restock(
        self,
        interaction: discord.Interaction,
        shop_id: int,
        so_luong: int,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return

        if so_luong <= 0:
            await interaction.response.send_message('❌ Số lượng phải > 0!', ephemeral=True)
            return

        await interaction.response.defer()

        if shop_id == 0:
            ket_qua = restock_toan_bo(so_luong)
            if ket_qua['thanh_cong']:
                await interaction.followup.send(
                    f'✅ Đã nhập **+{so_luong:,}** cho **{ket_qua["so_item"]}** item.'
                )
            else:
                await interaction.followup.send(f'❌ {ket_qua["loi"]}')
        else:
            ket_qua = restock_shop_item(shop_id, so_luong)
            if ket_qua['thanh_cong']:
                await interaction.followup.send(
                    f'✅ Đã nhập **+{so_luong:,}** cho **{ket_qua["ten"]}** (ID #{shop_id})\n'
                    f'Tồn kho: `{ket_qua["so_luong_cu"]:,}` → `{ket_qua["so_luong_moi"]:,}`'
                )
            else:
                await interaction.followup.send(f'❌ {ket_qua["loi"]}')

    # ============================================================
    # /addtien
    # ============================================================
    @app_commands.command(
        name='addtien',
        description='[ADMIN] Cộng linh thạch hoặc tiên ngọc cho player'
    )
    @app_commands.describe(
        user='User cần cộng tiền',
        linh_thach='Số linh thạch cộng (mặc định 0)',
        tien_ngoc='Số tiên ngọc cộng (mặc định 0)',
    )
    async def addtien(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        linh_thach: int = 0,
        tien_ngoc: int = 0,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return

        if linh_thach == 0 and tien_ngoc == 0:
            await interaction.response.send_message(
                '❌ Phải cộng ít nhất 1 loại tiền!', ephemeral=True
            )
            return

        await interaction.response.defer()

        player = get_player_full_info(user.id)
        if not player:
            await interaction.followup.send(f'❌ User {user.mention} chưa có nhân vật!')
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE player
                SET linh_thach = GREATEST(0, linh_thach + %s),
                    tien_ngoc = GREATEST(0, tien_ngoc + %s)
                WHERE player_id = %s
            """, (linh_thach, tien_ngoc, player.player_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        embed = discord.Embed(
            title='✅ Đã cộng tiền',
            description=f'Admin {interaction.user.mention} đã cộng tiền cho {user.mention}',
            color=discord.Color.green(),
        )
        if linh_thach != 0:
            embed.add_field(
                name='💰 Linh thạch',
                value=f'`{linh_thach:+,}`',
                inline=True,
            )
        if tien_ngoc != 0:
            embed.add_field(
                name='💎 Tiên ngọc',
                value=f'`{tien_ngoc:+,}`',
                inline=True,
            )

        await interaction.followup.send(embed=embed)

    # ============================================================
    # /addtuvi
    # ============================================================
    @app_commands.command(
        name='addtuvi',
        description='[ADMIN] Cộng tu vi cho player'
    )
    @app_commands.describe(
        user='User cần cộng tu vi',
        amount='Số tu vi cộng (số âm để trừ)',
    )
    async def addtuvi(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        amount: int,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return

        if amount == 0:
            await interaction.response.send_message('❌ Số tu vi phải khác 0!', ephemeral=True)
            return

        await interaction.response.defer()

        player = get_player_full_info(user.id)
        if not player:
            await interaction.followup.send(f'❌ User {user.mention} chưa có nhân vật!')
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE player
                SET tu_vi = GREATEST(0, tu_vi + %s)
                WHERE player_id = %s
            """, (amount, player.player_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        embed = discord.Embed(
            title='✅ Đã cộng tu vi',
            description=f'Admin {interaction.user.mention} đã cộng tu vi cho {user.mention}',
            color=discord.Color.green(),
        )
        embed.add_field(
            name='🔮 Tu vi',
            value=f'`{amount:+,}`',
            inline=True,
        )

        await interaction.followup.send(embed=embed)

    # ============================================================
    # /additem
    # ============================================================
    @app_commands.command(
        name='additem',
        description='[ADMIN] Thêm item vào túi player (đan dược, đạo cụ, linh thảo, khoáng thạch, đan phương, công pháp)'
    )
    @app_commands.describe(
        user='User cần thêm item',
        loai='Loại item',
        ten='Tên item (gõ để xem gợi ý)',
        so_luong='Số lượng thêm',
    )
    @app_commands.choices(loai=[
        app_commands.Choice(name='Đan dược', value='dan_duoc'),
        app_commands.Choice(name='Đạo cụ', value='dao_cu'),
        app_commands.Choice(name='Linh thảo', value='linh_thao'),
        app_commands.Choice(name='Khoáng thạch', value='khoang_thach'),
        app_commands.Choice(name='Đan phương', value='dan_phuong'),
        app_commands.Choice(name='Công pháp', value='cong_phap'),
    ])
    async def additem(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        loai: str,
        ten: str,
        so_luong: int,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return

        if so_luong <= 0:
            await interaction.response.send_message('❌ Số lượng phải > 0!', ephemeral=True)
            return

        await interaction.response.defer()

        player = get_player_full_info(user.id)
        if not player:
            await interaction.followup.send(f'❌ User {user.mention} chưa có nhân vật!')
            return

        # ===== XỬ LÝ ITEM THƯỜNG (bảng riêng) =====
        if loai in ('dan_duoc', 'dao_cu', 'linh_thao', 'khoang_thach'):
            mapping = {
                'dan_duoc': ('tmpl_dan_duoc', 'player_dan_duoc', 'dan_duoc_id'),
                'dao_cu': ('tmpl_dao_cu', 'player_dao_cu', 'dao_cu_id'),
                'linh_thao': ('tmpl_linh_thao', 'player_linh_thao', 'linh_thao_id'),
                'khoang_thach': ('tmpl_khoang_thach', 'player_khoang_thach', 'khoang_thach_id'),
            }

            tmpl_table, player_table, id_column = mapping[loai]

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                conn.start_transaction()

                cursor.execute(f"""
                    SELECT id, ten FROM {tmpl_table} 
                    WHERE LOWER(ten) = LOWER(%s) 
                    LIMIT 1
                """, (ten,))
                item = cursor.fetchone()

                if not item:
                    conn.rollback()
                    await interaction.followup.send(
                        f'❌ Không tìm thấy item `{ten}`!\n'
                        f'Gợi ý: Dùng autocomplete để chọn tên chính xác.'
                    )
                    return

                cursor.execute(f"""
                    INSERT INTO {player_table} (player_id, {id_column}, so_luong)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE so_luong = so_luong + VALUES(so_luong)
                """, (player.player_id, item['id'], so_luong))

                conn.commit()

                embed = discord.Embed(
                    title='✅ Đã thêm item',
                    description=f'Admin {interaction.user.mention} đã thêm item cho {user.mention}',
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name='📦 Item',
                    value=f'**{item["ten"]}** × `{so_luong:,}`',
                    inline=False,
                )

                await interaction.followup.send(embed=embed)
            except Exception as e:
                conn.rollback()
                await interaction.followup.send(f'❌ Lỗi: {e}')
            finally:
                cursor.close()
                conn.close()
            return

        # ===== XỬ LÝ ĐAN PHƯƠNG / CÔNG PHÁP (misc_tui_do) =====
        elif loai in ('dan_phuong', 'cong_phap'):
            from database.player_repo import (
                them_dan_phuong_vao_tui,
                them_cong_phap_vao_tui,
            )

            if loai == 'dan_phuong':
                tmpl_table = 'tmpl_dan_duoc'
            else:
                tmpl_table = 'tmpl_cong_phap'

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(f"""
                    SELECT id, ten FROM {tmpl_table}
                    WHERE LOWER(ten) = LOWER(%s)
                    LIMIT 1
                """, (ten,))
                item = cursor.fetchone()

                if not item:
                    await interaction.followup.send(
                        f'❌ Không tìm thấy `{ten}` trong `{tmpl_table}`!'
                    )
                    return
            finally:
                cursor.close()
                conn.close()

            if loai == 'dan_phuong':
                success = them_dan_phuong_vao_tui(
                    player.player_id, item['id'], so_luong
                )
                emoji = '📜'
                ten_loai = 'đan phương'
                color = discord.Color.orange()
            else:
                success = them_cong_phap_vao_tui(
                    player.player_id, item['id'], so_luong
                )
                emoji = '📖'
                ten_loai = 'công pháp'
                color = discord.Color.purple()

            if not success:
                await interaction.followup.send(f'❌ Lỗi khi thêm {ten_loai}!')
                return

            embed = discord.Embed(
                title=f'✅ Đã thêm {ten_loai}',
                description=f'Admin {interaction.user.mention} đã thêm cho {user.mention}',
                color=color,
            )
            embed.add_field(
                name=f'{emoji} {ten_loai.capitalize()}',
                value=f'**{item["ten"]}** × `{so_luong:,}`',
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            return

        else:
            await interaction.followup.send(f'❌ Loại không hợp lệ: `{loai}`')
            return

    @additem.autocomplete('ten')
    async def additem_ten_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete tên item dựa vào loai."""
        loai = interaction.namespace.loai
        if not loai:
            return []

        mapping = {
            'dan_duoc': 'tmpl_dan_duoc',
            'dao_cu': 'tmpl_dao_cu',
            'linh_thao': 'tmpl_linh_thao',
            'khoang_thach': 'tmpl_khoang_thach',
            'dan_phuong': 'tmpl_dan_duoc',
            'cong_phap': 'tmpl_cong_phap',
        }

        tmpl_table = mapping.get(loai)
        if not tmpl_table:
            return []

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            if current:
                cursor.execute(f"""
                    SELECT ten FROM {tmpl_table}
                    WHERE ten LIKE %s
                    ORDER BY ten
                    LIMIT 25
                """, (f'%{current}%',))
            else:
                cursor.execute(f"""
                    SELECT ten FROM {tmpl_table}
                    ORDER BY ten
                    LIMIT 25
                """)

            return [
                app_commands.Choice(name=r['ten'][:100], value=r['ten'][:100])
                for r in cursor.fetchall()
            ]
        except Exception as e:
            print(f'[ERROR] autocomplete additem: {e}')
            return []
        finally:
            cursor.close()
            conn.close()

    # ============================================================
    # /test-bxh — ĐÃ SỬA: GỬI DM CHO PLAYER
    # ============================================================
    @app_commands.command(
        name='test-bxh',
        description='[ADMIN] Test trao thưởng BXH (không đợi thứ 2)'
    )
    async def test_bxh(self, interaction: discord.Interaction):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        from database.player_repo import trao_thuong_tat_ca_bxh, get_bxh_by_code
        ket_qua = trao_thuong_tat_ca_bxh()
        
        if not ket_qua['thanh_cong']:
            await interaction.followup.send(f'❌ {ket_qua["loi"]}')
            return
        
        # ⭐ LẤY COG BXHTask ĐỂ GỬI DM CHO PLAYER
        bxh_task_cog = self.bot.get_cog('BXHTask')
        
        so_dm_thanh_cong = 0
        so_dm_that_bai = 0
        ds_loi_dm = []
        
        if bxh_task_cog:
            for code, ds in ket_qua['chi_tiet'].items():
                for player in ds:
                    try:
                        await bxh_task_cog.gui_dm(player, code, ket_qua['tuan'])
                        so_dm_thanh_cong += 1
                    except Exception as e:
                        so_dm_that_bai += 1
                        ds_loi_dm.append(f'`{player.get("ten", "?")}`: {e}')
                        print(f'[TEST-BXH] Lỗi gửi DM cho {player.get("discord_id")}: {e}')
        else:
            print('[TEST-BXH] Không tìm thấy cog BXHTask!')
        
        # Build thống kê
        lines = []
        for code, ds in ket_qua['chi_tiet'].items():
            meta = get_bxh_by_code(code)
            ten = meta['ten'] if meta else code
            lines.append(f'**{ten}**: {len(ds)} player')
        
        embed = discord.Embed(
            title='✅ Đã Trao Thưởng BXH',
            description=f'Tuần: `{ket_qua["tuan"]}`',
            color=discord.Color.green(),
        )
        embed.add_field(
            name='📊 Chi tiết',
            value='\n'.join(lines) if lines else '*Không có player nào*',
            inline=False,
        )
        embed.add_field(
            name='📬 Gửi DM',
            value=(
                f'• Thành công: `{so_dm_thanh_cong}`\n'
                f'• Thất bại: `{so_dm_that_bai}`'
            ),
            inline=False,
        )
        
        if ds_loi_dm:
            embed.add_field(
                name='⚠️ Lỗi gửi DM (10 lỗi đầu)',
                value='\n'.join(ds_loi_dm[:10]),
                inline=False,
            )
        
        await interaction.followup.send(embed=embed)

    # ============================================================
    # /xoa-shopitem
    # ============================================================
    @app_commands.command(
        name='xoa-shopitem',
        description='[ADMIN] Xóa 1 item khỏi shop (vĩnh viễn hoặc ẩn tạm)'
    )
    @app_commands.describe(
        shop_id='ID shop item cần xóa',
        vinh_vien='True = xóa vĩnh viễn, False = ẩn tạm (mặc định)',
    )
    async def xoa_shopitem(
        self,
        interaction: discord.Interaction,
        shop_id: int,
        vinh_vien: bool = False,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    si.*,
                    COALESCE(dd.ten, dc.ten, kt.ten, lt.ten, cp.ten) AS ten
                FROM tmpl_shop_item si
                LEFT JOIN tmpl_dan_duoc dd ON si.item_type = 'DanDuoc' AND dd.id = si.item_id
                LEFT JOIN tmpl_dao_cu dc ON si.item_type = 'DaoCu' AND dc.id = si.item_id
                LEFT JOIN tmpl_khoang_thach kt ON si.item_type = 'KhoangThach' AND kt.id = si.item_id
                LEFT JOIN tmpl_linh_thao lt ON si.item_type = 'LinhThao' AND lt.id = si.item_id
                LEFT JOIN tmpl_cong_phap cp ON si.item_type = 'CongPhap' AND cp.id = si.item_id
                WHERE si.id = %s
            """, (shop_id,))
            item = cursor.fetchone()
            
            if not item:
                await interaction.followup.send(f'❌ Không tìm thấy shop item ID `{shop_id}`!')
                return
            
            ten_item = item.get('ten') or '?'
            
            if vinh_vien:
                cursor.execute("""
                    SELECT COUNT(*) AS so_luong FROM log_giao_dich
                    WHERE item_type = %s AND item_id = %s
                """, (item['item_type'], item['item_id']))
                row = cursor.fetchone()
                
                if row['so_luong'] > 0:
                    cursor.execute("""
                        UPDATE tmpl_shop_item SET is_active = 0 WHERE id = %s
                    """, (shop_id,))
                    conn.commit()
                    
                    embed = discord.Embed(
                        title='⚠️ Không thể xóa vĩnh viễn',
                        description=(
                            f'Item **{ten_item}** (ID `{shop_id}`) đã có `{row["so_luong"]}` giao dịch trong log.\n'
                            f'Không thể xóa do FK constraint → **đã ẩn tạm** (is_active = 0).'
                        ),
                        color=discord.Color.orange(),
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                cursor.execute("DELETE FROM tmpl_shop_item WHERE id = %s", (shop_id,))
                conn.commit()
                
                embed = discord.Embed(
                    title='🗑️ Đã Xóa Vĩnh Viễn',
                    description=f'Item **{ten_item}** (ID `{shop_id}`) đã bị xóa khỏi shop.',
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
            
            else:
                cursor.execute("UPDATE tmpl_shop_item SET is_active = 0 WHERE id = %s", (shop_id,))
                conn.commit()
                
                embed = discord.Embed(
                    title='🙈 Đã Ẩn Item',
                    description=(
                        f'Item **{ten_item}** (ID `{shop_id}`) đã bị ẩn khỏi shop.\n'
                        f'Dùng `vinh_vien: True` để xóa hẳn.'
                    ),
                    color=discord.Color.light_grey(),
                )
                await interaction.followup.send(embed=embed)
        except Exception as e:
            conn.rollback()
            print(f'[ERROR] xoa_shopitem: {e}')
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f'❌ Lỗi: {e}')
        finally:
            cursor.close()
            conn.close()

    # ============================================================
    # /xoa-shopitem-hangloat
    # ============================================================
    @app_commands.command(
        name='xoa-shopitem-hangloat',
        description='[ADMIN] Xóa hàng loạt item khỏi shop theo điều kiện'
    )
    @app_commands.describe(
        loai='Loại item',
        giai_cap='Giai cấp công pháp (chỉ dùng cho Công pháp)',
        pham_cap='Phẩm cấp (chỉ dùng cho Đan dược/Đạo cụ)',
        vinh_vien='True = xóa vĩnh viễn, False = ẩn tạm',
    )
    @app_commands.choices(loai=[
        app_commands.Choice(name='Công pháp', value='CongPhap'),
        app_commands.Choice(name='Đan dược', value='DanDuoc'),
        app_commands.Choice(name='Đạo cụ', value='DaoCu'),
    ])
    @app_commands.choices(giai_cap=[
        app_commands.Choice(name='Hoàng giai', value='Hoang'),
        app_commands.Choice(name='Huyền giai', value='Huyen'),
        app_commands.Choice(name='Địa giai', value='Dia'),
        app_commands.Choice(name='Thiên giai', value='Thien'),
    ])
    @app_commands.choices(pham_cap=[
        app_commands.Choice(name='Phàm', value='Pham'),
        app_commands.Choice(name='Linh', value='Linh'),
        app_commands.Choice(name='Bảo', value='Bao'),
        app_commands.Choice(name='Tiên', value='Tien'),
        app_commands.Choice(name='Thần', value='Than'),
    ])
    async def xoa_shopitem_hangloat(
        self,
        interaction: discord.Interaction,
        loai: str,
        giai_cap: str = None,
        pham_cap: str = None,
        vinh_vien: bool = False,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message('❌ Không có quyền!', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            if loai == 'CongPhap':
                if not giai_cap:
                    await interaction.followup.send('❌ Công pháp cần `giai_cap`!')
                    return
                
                cursor.execute("""
                    SELECT si.id AS shop_id, cp.ten, cp.giai_cap
                    FROM tmpl_shop_item si
                    JOIN tmpl_cong_phap cp ON cp.id = si.item_id
                    WHERE si.item_type = 'CongPhap' AND cp.giai_cap = %s
                """, (giai_cap,))
            
            elif loai == 'DanDuoc':
                if not pham_cap:
                    await interaction.followup.send('❌ Đan dược cần `pham_cap`!')
                    return
                
                cursor.execute("""
                    SELECT si.id AS shop_id, dd.ten, dd.pham_cap
                    FROM tmpl_shop_item si
                    JOIN tmpl_dan_duoc dd ON dd.id = si.item_id
                    WHERE si.item_type = 'DanDuoc' AND dd.pham_cap = %s
                """, (pham_cap,))
            
            elif loai == 'DaoCu':
                if not pham_cap:
                    await interaction.followup.send('❌ Đạo cụ cần `pham_cap`!')
                    return
                
                cursor.execute("""
                    SELECT si.id AS shop_id, dc.ten, dc.pham_cap
                    FROM tmpl_shop_item si
                    JOIN tmpl_dao_cu dc ON dc.id = si.item_id
                    WHERE si.item_type = 'DaoCu' AND dc.pham_cap = %s
                """, (pham_cap,))
            
            else:
                await interaction.followup.send(f'❌ Loại không hợp lệ: `{loai}`')
                return
            
            ds_items = cursor.fetchall()
            
            if not ds_items:
                await interaction.followup.send('❌ Không tìm thấy item nào khớp!')
                return
            
            ds_shop_ids = [it['shop_id'] for it in ds_items]
            
            if vinh_vien:
                so_xoa = 0
                so_an = 0
                
                for shop_id in ds_shop_ids:
                    cursor.execute("""
                        SELECT item_type, item_id FROM tmpl_shop_item WHERE id = %s
                    """, (shop_id,))
                    row = cursor.fetchone()
                    
                    cursor.execute("""
                        SELECT COUNT(*) AS so_luong FROM log_giao_dich
                        WHERE item_type = %s AND item_id = %s
                    """, (row['item_type'], row['item_id']))
                    log_row = cursor.fetchone()
                    
                    if log_row['so_luong'] > 0:
                        cursor.execute("""
                            UPDATE tmpl_shop_item SET is_active = 0 WHERE id = %s
                        """, (shop_id,))
                        so_an += 1
                    else:
                        cursor.execute("DELETE FROM tmpl_shop_item WHERE id = %s", (shop_id,))
                        so_xoa += 1
                
                conn.commit()
                
                embed = discord.Embed(
                    title='✅ Xử Lý Hàng Loạt',
                    description=(
                        f'Tìm thấy `{len(ds_items)}` item.\n'
                        f'• Xóa vĩnh viễn: `{so_xoa}`\n'
                        f'• Ẩn tạm (do có log): `{so_an}`'
                    ),
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
            
            else:
                format_strings = ','.join(['%s'] * len(ds_shop_ids))
                cursor.execute(f"""
                    UPDATE tmpl_shop_item 
                    SET is_active = 0 
                    WHERE id IN ({format_strings})
                """, tuple(ds_shop_ids))
                conn.commit()
                
                embed = discord.Embed(
                    title='🙈 Đã Ẩn Hàng Loạt',
                    description=f'Đã ẩn `{len(ds_items)}` item khỏi shop.',
                    color=discord.Color.light_grey(),
                )
                await interaction.followup.send(embed=embed)
        except Exception as e:
            conn.rollback()
            print(f'[ERROR] xoa_shopitem_hangloat: {e}')
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f'❌ Lỗi: {e}')
        finally:
            cursor.close()
            conn.close()


async def setup(bot):
    await bot.add_cog(Admin(bot))