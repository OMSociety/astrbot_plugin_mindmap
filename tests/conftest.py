import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT.parent))  # 使 astrbot_plugin_mindmap 以包形式可导入
