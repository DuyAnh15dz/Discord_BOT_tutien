# 🔄 Hướng dẫn Backup & Restore Database

Tài liệu này ghi lại quy trình backup và restore database cho **Bot Discord Tu Tiên**.

> ⚠️ **Quan trọng:** Đọc kỹ trước khi restore để tránh mất dữ liệu.

---

## 📦 1. Hệ thống Backup

Bot sử dụng **backup 2 tầng** để đảm bảo an toàn:

| Tầng | Vị trí | Mục đích | Tần suất |
|------|--------|----------|----------|
| **Local** | `D:\TinhDeLien\backups\` | Rollback nhanh, không phụ thuộc mạng | 3h sáng hàng ngày |
| **Cloud** | `H:\My Drive\bot-tu-tien-backups\` | Offsite, chống mất máy | Sync tự động qua Google Drive |

### Luồng hoạt động

```
3:00 AM → Task Scheduler kích hoạt
        → scripts\backup.ps1 chạy
        → Dump database → nén .sql.zip
        → Lưu vào D:\TinhDeLien\backups\
        → Copy sang H:\My Drive\bot-tu-tien-backups\
        → Google Drive Desktop tự sync lên cloud
        → Xóa backup local cũ hơn 7 ngày
```

---

## ⚙️ 2. Cấu hình

### 2.1. Yêu cầu

- **MySQL** đã cài và `mysqldump` có trong PATH
- **PowerShell** (có sẵn trên Windows)
- **Google Drive Desktop** đã cài và đăng nhập

### 2.2. Kiểm tra `mysqldump`

```powershell
mysqldump --version
```

Kết quả mong đợi:
```
mysqldump  Ver 8.0.x for Win64 on x86_64 (MySQL Community Server - GPL)
```

Nếu báo lỗi `not recognized` → cần thêm MySQL `bin` vào PATH.

### 2.3. File cấu hình

Script backup nằm ở: `scripts\backup.ps1`

Các biến cần cấu hình:

```powershell
$DB_NAME    = "tu_tien_db"                          # Tên database
$DB_USER    = "root"                                # User MySQL
$DB_PASS    = "your_password_here"                  # Mật khẩu MySQL
$LOCAL_DIR  = "D:\TinhDeLien\backups"               # Thư mục backup local
$CLOUD_DIR  = "H:\My Drive\bot-tu-tien-backups"     # Thư mục backup cloud
$KEEP_LOCAL = 7                                     # Giữ 7 ngày local
$KEEP_CLOUD = 30                                    # Giữ 30 ngày cloud
```

> 🔐 **Bảo mật:** File `backup.ps1` chứa mật khẩu → **KHÔNG** commit lên GitHub. Thêm vào `.gitignore` nếu cần.

---

## 🚀 3. Backup thủ công

### 3.1. Chạy script backup

```powershell
cd "D:\TinhDeLien"
.\scripts\backup.ps1
```

### 3.2. Backup 1 lần bằng lệnh trực tiếp

```powershell
# Backup ra file .sql (không nén)
mysqldump -u root -p --result-file="D:\TinhDeLien\backups\manual_backup.sql" tu_tien_db

# Hoặc backup + nén
mysqldump -u root -p --result-file="temp.sql" tu_tien_db
Compress-Archive -Path "temp.sql" -DestinationPath "backup_$(Get-Date -Format 'yyyy-MM-dd').zip"
Remove-Item "temp.sql"
```

### 3.3. Backup tất cả database

```powershell
mysqldump -u root -p --all-databases --result-file="D:\TinhDeLien\backups\all_db.sql"
```

---

## 🔄 4. Restore (Khôi phục)

### ⚠️ CẢNH BÁO TRƯỚC KHI RESTORE

- Restore **SẼ GHI ĐÈ** dữ liệu hiện tại
- **Backup database hiện tại trước** khi restore (để có thể rollback nếu sai)
- Test restore trên **database test** trước, không restore thẳng vào production

### 4.1. Restore từ file `.sql`

```powershell
# 1. Vào thư mục chứa backup
cd "D:\TinhDeLien\backups"

# 2. Restore (dùng cmd, không phải PowerShell trực tiếp)
cmd /c "mysql -u root -p tu_tien_db < backup_file.sql"
```

### 4.2. Restore từ file `.sql.zip` (nén)

```powershell
# 1. Vào thư mục backup
cd "D:\TinhDeLien\backups"

# 2. Tìm file mới nhất
$latest = Get-ChildItem "*.sql.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "File mới nhất: $($latest.Name)"

# 3. Giải nén
Expand-Archive -Path $latest.FullName -DestinationPath "." -Force

# 4. Lấy tên file .sql
$sqlFile = $latest.Name -replace "\.zip$", ""

# 5. Restore
cmd /c "mysql -u root -p tu_tien_db < `"$sqlFile`""
```

### 4.3. Restore vào database test (KHUYẾN NGHỊ)

```powershell
# 1. Tạo DB test
mysql -u root -p -e "CREATE DATABASE tu_tien_test;"

# 2. Restore vào DB test
cd "D:\TinhDeLien\backups"
$latest = Get-ChildItem "*.sql.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Expand-Archive -Path $latest.FullName -DestinationPath "." -Force
$sqlFile = $latest.Name -replace "\.zip$", ""
cmd /c "mysql -u root -p tu_tien_test < `"$sqlFile`""

# 3. Kiểm tra data
mysql -u root -p -e "USE tu_tien_test; SHOW TABLES; SELECT COUNT(*) FROM player;"

# 4. Nếu OK, xóa DB test
mysql -u root -p -e "DROP DATABASE tu_tien_test;"
```

---

## 🆘 5. Khôi phục khẩn cấp (Disaster Recovery)

### Tình huống: Mất toàn bộ dữ liệu local

1. **Cài lại môi trường:**
   ```powershell
   # Cài MySQL, Python
   # Clone code từ GitHub
   git clone https://github.com/DuyAnh15dz/Discord_BOT_tu_tien.git D:\TinhDeLien
   ```

2. **Tải backup mới nhất từ Google Drive:**
   - Vào https://drive.google.com
   - Tìm thư mục `bot-tu-tien-backups`
   - Tải file `.sql.zip` mới nhất về `D:\TinhDeLien\backups\`

3. **Tạo database mới:**
   ```powershell
   mysql -u root -p -e "CREATE DATABASE tu_tien_db;"
   ```

4. **Restore:**
   ```powershell
   cd "D:\TinhDeLien\backups"
   $latest = Get-ChildItem "*.sql.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
   Expand-Archive -Path $latest.FullName -DestinationPath "." -Force
   $sqlFile = $latest.Name -replace "\.zip$", ""
   cmd /c "mysql -u root -p tu_tien_db < `"$sqlFile`""
   ```

5. **Verify:**
   ```powershell
   mysql -u root -p -e "USE tu_tien_db; SELECT COUNT(*) FROM player;"
   ```

6. **Chạy bot:**
   ```powershell
   python bot.py
   ```

---

## 📅 6. Lịch Backup & Test

| Công việc | Tần suất | Ngày |
|-----------|----------|------|
| Backup tự động | Hàng ngày | 3:00 AM |
| Kiểm tra backup log | Hàng tuần | Thứ 2 |
| **Test restore** | **Hàng tháng** | **Ngày 1** |
| Kiểm tra dung lượng Google Drive | Hàng tháng | Ngày 1 |
| Đổi mật khẩu MySQL | 6 tháng | - |

### Test restore hàng tháng

```powershell
# Chạy full test restore (script)
mysql -u root -p -e "CREATE DATABASE tu_tien_test;"
cd "D:\TinhDeLien\backups"
$latest = Get-ChildItem "*.sql.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Expand-Archive -Path $latest.FullName -DestinationPath "." -Force
$sqlFile = $latest.Name -replace "\.zip$", ""
cmd /c "mysql -u root -p tu_tien_test < `"$sqlFile`""
mysql -u root -p -e "USE tu_tien_test; SELECT COUNT(*) FROM players;"
mysql -u root -p -e "DROP DATABASE tu_tien_test;"
```

> ✅ Nếu player count khớp → backup hoạt động tốt.
> ❌ Nếu lỗi → kiểm tra ngay, đừng đợi đến khi cần.

---

## 🔍 7. Kiểm tra & Giám sát

### 7.1. Xem log backup

```powershell
# Xem log local
Get-Content "D:\TinhDeLien\backups\backup.log" -Tail 20

# Kiểm tra file backup hôm nay
Get-ChildItem "D:\TinhDeLien\backups" | Where-Object {
    $_.LastWriteTime -gt (Get-Date).AddDays(-1)
}
```

### 7.2. Kiểm tra Task Scheduler

```powershell
# Xem thông tin task
Get-ScheduledTaskInfo -TaskName "Backup Bot Tu Tien"

# Xem lịch sử chạy
Get-ScheduledTask -TaskName "Backup Bot Tu Tien" | Get-ScheduledTaskInfo
```

Kết quả mong đợi:
```
LastRunTime        : 9/16/2026 3:00:00 AM
LastTaskResult     : 0x0  ← 0 = thành công
NextRunTime        : 9/17/2026 3:00:00 AM
```

### 7.3. Kiểm tra Google Drive sync

- Mở https://drive.google.com
- Vào `My Drive` → `bot-tu-tien-backups`
- File mới nhất phải có ngày hôm nay

---

## 📋 8. Checklist trước khi Restore Production

Trước khi restore vào database thật:

- [ ] Đã **backup database hiện tại** trước khi restore?
- [ ] Đã **test restore** trên database test thành công?
- [ ] Đã **thông báo** cho người dùng bot (nếu có)?
- [ ] Đã **tắt bot** trước khi restore?
- [ ] Đã **chọn đúng file backup** (kiểm tra ngày, size)?
- [ ] Đã **ghi lại** thời gian restore (để đối chiếu nếu có vấn đề)?

---

## 🛠️ 9. Troubleshooting

### Lỗi: `mysqldump: not recognized`

**Nguyên nhân:** MySQL chưa có trong PATH.

**Fix:** Thêm `<MySQL>\bin` vào System Environment Variables → restart terminal.

### Lỗi: `Can't create/write to file 'D:\Tinh Để Liên\...'`

**Nguyên nhân:** Đường dẫn có dấu tiếng Việt hoặc dấu cách.

**Fix:** Đổi đường dẫn thành không dấu, ví dụ `D:\TinhDeLien\`.

### Lỗi: `Expand-Archive: The path ... does not exist`

**Nguyên nhân:** Tên file sai (thiếu `.zip`).

**Fix:** Chạy `Get-ChildItem "*.zip"` để xem tên chính xác.

### Lỗi: File backup có size 0 KB

**Nguyên nhân:** Sai mật khẩu MySQL hoặc database không tồn tại.

**Fix:** Kiểm tra lại tên DB và mật khẩu trong script.

### Lỗi: Google Drive không sync

**Nguyên nhân:** Google Drive Desktop chưa chạy hoặc mất mạng.

**Fix:** 
- Kiểm tra icon Google Drive ở system tray
- Mở app → xem **Sync status**
- Nhấn **Resume** nếu bị pause

---

## 📚 10. Tham khảo

- [MySQL Backup Documentation](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)
- [PowerShell Scheduled Tasks](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/)
- [Google Drive Desktop](https://www.google.com/drive/download/)

---

## 📝 11. Changelog

| Ngày | Thay đổi | Người thực hiện |
|------|----------|-----------------|
| 2026-09-16 | Tạo file, setup backup 2 tầng | DuyAnh15dz |
| | | |

---

**Cập nhật lần cuối:** 2026-09-16  
**Người duy trì:** DuyAnh15dz
