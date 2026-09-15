import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import random
import json

from database.connection import get_connection
from database.player_repo import (
    get_player_full_info_with_cursor,
    get_cooldown_with_cursor,
    set_cooldown_with_cursor,
    get_random_dia_diem_with_cursor,
    get_xac_suat_su_kien_with_cursor,
    lay_nhieu_config_with_cursor,
    lay_nhieu_bonus_nghe_with_cursor,
    get_player_linh_can_active_with_cursor,
    get_random_linh_thao_with_cursor,
    get_random_dan_phuong_with_cursor,
    get_linh_can_ky_ngo_range_with_cursor,
    update_player_sau_lichluyen_with_cursor,
    ghi_log_lichluyen_with_cursor,
    get_random_khoang_thach_with_cursor,
    them_dan_phuong_vao_tui,           # ⭐ MỚI
)
from utils.lichluyen_events import SU_KIEN, tinh_gia_tri_reward


def format_thoi_gian(giay: int) -> str:
    """Format giây thành '1h 30m'."""
    gio = giay // 3600
    phut = (giay % 3600) // 60
    if gio > 0 and phut > 0:
        return f'{gio}h {phut}m'
    elif gio > 0:
        return f'{gio}h'
    return f'{phut}m'


class LichLuyen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name='lichluyen',
        description='Đi lịch luyện nhận thưởng'
    )
    async def lichluyen(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        # ⭐ MỞ CONNECTION 1 LẦN DUY NHẤT
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # ===== 1. Check player =====
            player = get_player_full_info_with_cursor(cursor, interaction.user.id)
            if not player:
                await interaction.followup.send(
                    '❌ Bạn chưa đăng ký! Dùng `/nhapmon` trước.'
                )
                return

            # ===== 2. Lấy config + cooldown 1 lần =====
            configs = lay_nhieu_config_with_cursor(cursor, [
                'lichluyen_cooldown_sec',
                'lichluyen_so_su_kien',
            ])
            cd_sec = configs.get('lichluyen_cooldown_sec', 180)
            so_su_kien = configs.get('lichluyen_so_su_kien', 3)

            san_sang = get_cooldown_with_cursor(cursor, player.player_id, 'lichluyen')
            if san_sang and san_sang > datetime.now():
                con_lai = int((san_sang - datetime.now()).total_seconds())
                await interaction.followup.send(
                    f'⏳ Bạn đang mệt! Còn **{format_thoi_gian(con_lai)}** '
                    f'nữa mới lịch luyện được.'
                )
                return

            # ===== 3. Random địa điểm =====
            dia_diem = get_random_dia_diem_with_cursor(cursor)
            if not dia_diem:
                await interaction.followup.send('❌ Không tìm được địa điểm!')
                return
            for key in ['he_so_linh_thach', 'he_so_exp', 'he_so_linh_thao', 
            'he_so_khoang_thach', 'he_so_dan_phuong']:
                if key in dia_diem and dia_diem[key] is not None:
                    dia_diem[key] = float(dia_diem[key])
            # ===== 4. Lấy bonus nghề (1 query) =====
            bonus_dict = lay_nhieu_bonus_nghe_with_cursor(cursor, player.player_id, [
                'bonus_linh_thao_lichluyen',
                'bonus_linh_thach_lichluyen',
                'bonus_khoang_thach_lichluyen',
            ])
            bonus_linh_thao = bonus_dict.get('bonus_linh_thao_lichluyen', 0.0)
            bonus_linh_thach = bonus_dict.get('bonus_linh_thach_lichluyen', 0.0)
            bonus_khoang_thach = bonus_dict.get('bonus_khoang_thach_lichluyen', 0.0)

            # ===== 5. Roll sự kiện =====
            ds_xac_suat = get_xac_suat_su_kien_with_cursor(cursor, dia_diem['id'])
            if not ds_xac_suat:
                await interaction.followup.send('❌ Địa điểm chưa cấu hình sự kiện!')
                return

            codes = [r['su_kien_code'] for r in ds_xac_suat]
            weights = [r['trong_so'] for r in ds_xac_suat]
            su_kien_chon = random.choices(codes, weights=weights, k=so_su_kien)

            # ===== 6. Chuẩn bị biến =====
            tong_linh_thach = 0
            tong_tu_vi = 0
            tong_exp = 0
            tong_hp_mat = 0
            tong_linh_thach_mat = 0
            linh_thao_list = []
            tinh_khiet_list = []
            dan_phuong_list = []           # ⭐ MỚI
            chi_tiet = []
            khoang_thach_list = []

            ds_lc = get_player_linh_can_active_with_cursor(cursor, player.player_id)
            cap_bac = player.canh_gioi_id

            # Lấy HP max
            cursor.execute(
                "SELECT hp_max FROM player_stat WHERE player_id = %s",
                (player.player_id,)
            )
            stat = cursor.fetchone()
            hp_max = stat['hp_max'] if stat else 100
            linh_thach_hien_tai = player.linh_thach

            # ===== 7. Xử lý từng sự kiện =====
            for code in su_kien_chon:
                info = SU_KIEN.get(code, {})
                emoji = info.get('emoji', '❓')
                ten_sk = info.get('ten', code)

                if code == 'linh_thach':
                    min_v, max_v = tinh_gia_tri_reward('linh_thach', cap_bac)
                    gia_tri = random.randint(min_v, max_v)
                    gia_tri = int(gia_tri * dia_diem['he_so_linh_thach'] * (1 + bonus_linh_thach / 100))
                    tong_linh_thach += gia_tri
                    chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'+{gia_tri:,} linh thạch'})

                elif code == 'exp_tuvi':
                    min_v, max_v = tinh_gia_tri_reward('exp_tuvi', cap_bac)
                    gia_tri = random.randint(min_v, max_v)
                    gia_tri = int(gia_tri * dia_diem['he_so_exp'])
                    tong_exp += gia_tri
                    tong_tu_vi += gia_tri
                    chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'+{gia_tri:,} exp & tu vi'})

                elif code == 'linh_thao':
                    lt, so_luong = get_random_linh_thao_with_cursor(cursor)
                    if lt:
                        so_luong = int(so_luong * dia_diem['he_so_linh_thao'] * (1 + bonus_linh_thao / 100))
                        so_luong = max(1, so_luong)
                        linh_thao_list.append((lt['id'], so_luong))
                        chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'+{so_luong}× {lt["ten"]}'})

                elif code == 'khoang_thach':
                    kt, so_luong = get_random_khoang_thach_with_cursor(cursor)  # ⭐ Sửa: thêm cursor
                    if kt:
                        # Áp dụng hệ số địa điểm + bonus nghề
                        he_so = float(dia_diem['he_so_khoang_thach']) * (1 + bonus_khoang_thach / 100)
                        so_luong = int(so_luong * he_so)
                        so_luong = max(1, so_luong)
                        
                        khoang_thach_list.append((kt['id'], so_luong))
                        chi_tiet.append({
                            'emoji': emoji,
                            'ten': ten_sk,
                            'mo_ta': f'+{so_luong}× **{kt["ten"]}**'
                        })
                    else:
                        chi_tiet.append({
                            'emoji': emoji,
                            'ten': ten_sk,
                            'mo_ta': 'Không tìm thấy khoáng thạch'
                        })

                # ⭐ ĐAN PHƯƠNG — LƯU VÀO TÚI
                elif code == 'dan_phuong':
                    ti_le = 20 * dia_diem['he_so_dan_phuong']
                    if random.random() * 100 < ti_le:
                        dan = get_random_dan_phuong_with_cursor(cursor)
                        if dan:
                            dan_phuong_list.append((dan['id'], dan['ten']))
                            chi_tiet.append({
                                'emoji': emoji,
                                'ten': ten_sk,
                                'mo_ta': f'+1× Đan phương: **{dan["ten"]}**'
                            })
                        else:
                            chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': 'Không có gì'})
                    else:
                        chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': 'Không có gì'})

                elif code == 'ky_ngo':
                    ds_chua_max = [lc for lc in ds_lc if lc['do_tinh_khiet'] < 100]
                    if not ds_chua_max:
                        chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': 'Nhưng tất cả linh căn đã max!'})
                    else:
                        lc_chon = random.choice(ds_chua_max)
                        min_v, max_v = get_linh_can_ky_ngo_range_with_cursor(cursor)
                        amount = random.randint(min_v, max_v)
                        amount = min(amount, 100 - lc_chon['do_tinh_khiet'])
                        if amount > 0:
                            tinh_khiet_list.append((lc_chon['linh_can_id'], amount))
                            do_tinh_khiet_moi = lc_chon['do_tinh_khiet'] + amount
                            chi_tiet.append({
                                'emoji': emoji, 'ten': ten_sk,
                                'mo_ta': f'**{lc_chon["ten"]}** +{amount}% → `{do_tinh_khiet_moi:.2f}%`'
                            })

                elif code == 'sap_bay':
                    hp_mat_pct = random.randint(info['hp_mat_pct_min'], info['hp_mat_pct_max'])
                    hp_mat = int(hp_max * hp_mat_pct / 100)
                    tong_hp_mat += hp_mat
                    chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'-{hp_mat:,} HP ({hp_mat_pct}%)'})

                elif code == 'yeu_thu':
                    hp_mat_pct = random.randint(info['hp_mat_pct_min'], info['hp_mat_pct_max'])
                    hp_mat = int(hp_max * hp_mat_pct / 100)
                    tong_hp_mat += hp_mat
                    chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'Chiến đấu! -{hp_mat:,} HP'})

                elif code == 'ta_tu':
                    lt_mat_pct = random.randint(info['linh_thach_mat_pct_min'], info['linh_thach_mat_pct_max'])
                    lt_mat = int(linh_thach_hien_tai * lt_mat_pct / 100)
                    tong_linh_thach_mat += lt_mat
                    chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'-{lt_mat:,} linh thạch ({lt_mat_pct}%)'})

                elif code == 'thuong_nhan':
                    loai_buff = random.choice(['linh_thach', 'exp'])
                    if loai_buff == 'linh_thach':
                        bonus = random.randint(50, 200) * cap_bac
                        tong_linh_thach += bonus
                        chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'Tặng +{bonus:,} linh thạch'})
                    else:
                        bonus = random.randint(50, 200) * cap_bac
                        tong_exp += bonus
                        tong_tu_vi += bonus
                        chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': f'Tặng +{bonus:,} exp & tu vi'})

                elif code == 'binh_yen':
                    chi_tiet.append({'emoji': emoji, 'ten': ten_sk, 'mo_ta': 'Không có gì xảy ra'})

            # ===== 8. Update DB (chưa commit) =====
            update_player_sau_lichluyen_with_cursor(
                cursor, player.player_id,
                linh_thach=tong_linh_thach,
                tu_vi=tong_tu_vi,
                exp=tong_exp,
                hp_mat=tong_hp_mat,
                linh_thach_mat=tong_linh_thach_mat,
                linh_thao_list=linh_thao_list,
                tinh_khiet_list=tinh_khiet_list,
                khoang_thach_list=khoang_thach_list,
            )

            # ⭐ 8b. Lưu đan phương vào túi (dùng cùng cursor để cùng transaction)
            for dan_id, dan_ten in dan_phuong_list:
                item_code = f'dan_phuong_{dan_id}'
                
                # Check đã có chưa
                cursor.execute("""
                    SELECT id FROM misc_tui_do
                    WHERE player_id = %s AND item_code = %s
                    LIMIT 1
                """, (player.player_id, item_code))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("""
                        UPDATE misc_tui_do
                        SET so_luong = so_luong + 1
                        WHERE id = %s
                    """, (existing['id'],))
                else:
                    metadata = json.dumps(
                        {'dan_duoc_id': dan_id, 'ten': dan_ten},
                        ensure_ascii=False
                    )
                    cursor.execute("""
                        INSERT INTO misc_tui_do (player_id, item_code, so_luong, metadata)
                        VALUES (%s, %s, 1, %s)
                    """, (player.player_id, item_code, metadata))

            # ===== 9. Ghi log (chưa commit) =====
            ghi_log_lichluyen_with_cursor(
                cursor, player.player_id, dia_diem['id'],
                chi_tiet, tong_linh_thach, tong_tu_vi
            )

            # ===== 10. Set cooldown (chưa commit) =====
            set_cooldown_with_cursor(cursor, player.player_id, 'lichluyen', cd_sec)

            # ⭐ COMMIT TẤT CẢ 1 LẦN
            conn.commit()

            # ===== 11. Build embed =====
            embed = discord.Embed(
                title=f'🗺️ Lịch Luyện — {dia_diem["ten"]}',
                description=dia_diem['mo_ta'],
                color=discord.Color.teal()
            )
            lines = [f'{ct["emoji"]} **{ct["ten"]}**: {ct["mo_ta"]}' for ct in chi_tiet]
            embed.add_field(name=f'📋 Sự kiện ({len(chi_tiet)})', value='\n'.join(lines), inline=False)

            if tong_linh_thach > 0:
                embed.add_field(name='💰 Linh thạch', value=f'`+{tong_linh_thach:,}`', inline=True)
            if tong_exp > 0:
                embed.add_field(name='📈 Exp', value=f'`+{tong_exp:,}`', inline=True)
            if tong_tu_vi > 0:
                embed.add_field(name='🔮 Tu vi', value=f'`+{tong_tu_vi:,}`', inline=True)
            if tong_hp_mat > 0:
                embed.add_field(name='💔 HP mất', value=f'`-{tong_hp_mat:,}`', inline=True)
            if tong_linh_thach_mat > 0:
                embed.add_field(name='💸 Linh thạch mất', value=f'`-{tong_linh_thach_mat:,}`', inline=True)

            embed.add_field(name='⏱️ Cooldown', value=format_thoi_gian(cd_sec), inline=True)

            bonus_lines = []
            if bonus_linh_thao > 0:
                bonus_lines.append(f'🌿 Linh thảo: `+{int(bonus_linh_thao)}%`')
            if bonus_linh_thach > 0:
                bonus_lines.append(f'💰 Linh thạch: `+{int(bonus_linh_thach)}%`')
            if bonus_khoang_thach > 0:
                bonus_lines.append(f'🪨 Khoáng thạch: `+{int(bonus_khoang_thach)}%`')
            if bonus_lines:
                embed.add_field(name='🛠️ Bonus nghề', value='\n'.join(bonus_lines), inline=False)

            embed.set_footer(text=f'Cảnh giới: {player.canh_gioi_ten} tầng {player.tang_canh_gioi}')
            await interaction.followup.send(embed=embed)

        except Exception as e:
            conn.rollback()
            print(f'[ERROR] lichluyen: {e}')
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send(f'❌ Có lỗi xảy ra: `{e}`')
            except:
                pass
        finally:
            # ⭐ TRẢ CONNECTION VỀ POOL 1 LẦN DUY NHẤT
            cursor.close()
            conn.close()


async def setup(bot):
    await bot.add_cog(LichLuyen(bot))