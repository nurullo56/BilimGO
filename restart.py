import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

base_dir = os.path.abspath(os.path.dirname(__file__))
flag_file = os.path.join(base_dir, "restart.flag")
with open(flag_file, "w", encoding="utf-8") as f:
    f.write(str(time.time()))
print("BilimGo: Barcha xizmatlarga restart signali muvaffaqiyatli yuborildi!")
