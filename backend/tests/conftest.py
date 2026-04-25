import sys
from pathlib import Path

# 确保 backend/ 在 sys.path 中，使 `from app.xxx` 在测试里可用
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
