import os
import math

# E'tibordan chetda qoldiriladigan papkalar
IGNORE_DIRS = {
    'node_modules', '.git', '__pycache__', 'dist', 'build', 
    'images', 'assets', '.vscode', '.idea', 'venv', '.venv',
    'voice_reports'
}

# E'tibordan chetda qoldiriladigan kengaytmalar (binar, media, ma'lumotlar bazasi va h.k.)
IGNORE_EXTENSIONS = {
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.db', '.db-shm', '.db-wal', '.sqlite', '.sqlite3',
    '.pyc', '.pyo', '.pyd', '.exe', '.dll', '.so',
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp',
    '.mp3', '.mp4', '.ogg', '.wav', '.m4a', '.aac', '.flac',
    '.pdf', '.flag', '.lock'
}

# Skript natijasida hosil bo'ladigan yoki ilgari eksport qilingan fayllar
IGNORE_FILES = {
    'BilimGo_kod_1.txt', 'BilimGo_kod_2.txt', 'BilimGo_kod_3.txt',
    'BilimGo_ALL_CODE.txt', 'export_to_3_parts.py', 'bun.lock', 'package-lock.json'
}

def get_tree_files(root_dir='.'):
    """Fayllarni daraxt (tree) tartibida tepadan pastga saralangan holda yig'ish"""
    collected_files = []
    
    for root, dirs, files in os.walk(root_dir):
        # Keraksiz papkalarni chetlab o'tish
        dirs[:] = sorted([d for d in dirs if d not in IGNORE_DIRS])
        files = sorted(files)
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IGNORE_EXTENSIONS or file in IGNORE_FILES:
                continue
            
            # Eski yoki boshqa .txt eksportlarini ham olmaslik
            if file.startswith('BilimGo_kod_') and file.endswith('.txt'):
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.normpath(full_path).replace('\\', '/')
            collected_files.append((rel_path, full_path))
            
    return collected_files

def main():
    print("🔍 Fayllar ro'yxati tree tartibida olinmoqda...")
    files = get_tree_files('.')
    print(f"✅ Jami {len(files)} ta haqiqiy kod va konfiguratsiya fayli topildi.")

    blocks = []
    total_chars = 0

    # Har bir faylni o'qib, blok shaklida yig'ish
    for rel_path, full_path in files:
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            content = f"// Xatolik faylni o'qishda: {e}"

        block = f"\n{'='*80}\n"
        block += f"FAYL: {rel_path}\n"
        block += f"{'='*80}\n\n"
        block += content + "\n"
        
        blocks.append(block)
        total_chars += len(block)

    target_per_part = math.ceil(total_chars / 3)
    print(f"📊 Jami hajm: ~{total_chars:,} belgi (Har bir qism maqsadli ~{target_per_part:,} belgi).")

    parts = [[], [], []]
    current_part = 0
    current_size = 0

    for block in blocks:
        block_len = len(block)
        # Agar joriy qism maqsadli hajmga yetgan bo'lsa va bu oxirgi (3-qism) bo'lmasa:
        if current_part < 2 and (current_size + block_len > target_per_part) and len(parts[current_part]) > 0:
            current_part += 1
            current_size = 0

        parts[current_part].append(block)
        current_size += block_len

    # 3 ta faylga yozish
    for i in range(3):
        out_name = f"BilimGo_kod_{i+1}.txt"
        with open(out_name, 'w', encoding='utf-8') as out_f:
            header = f"# BILIMGO LOYIHA KODI - QISM {i+1} / 3\n"
            header += f"# Ushbu qismdagi fayllar soni: {len(parts[i])} ta\n"
            header += f"# Fayllar daraxt (Tree) tartibida ketma-ket joylashtirilgan\n\n"
            out_f.write(header)
            out_f.writelines(parts[i])
        
        part_chars = sum(len(b) for b in parts[i])
        print(f"💾 Saqlandi: {out_name} -> {len(parts[i])} ta fayl (~{part_chars:,} belgi)")

    print("\n🎉 Barcha 3 ta fayl muvaffaqiyatli va teng taqsimotda tayyorlandi!")

if __name__ == '__main__':
    main()
