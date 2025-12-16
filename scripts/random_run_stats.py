import json
import re
from pathlib import Path

log_path = Path('logs/random_browse.log')
if not log_path.exists():
    raise SystemExit('log file not found')

text = log_path.read_text(encoding='utf-8')
marker = '🎯 Random Browse Session 初始化 完成'
idx = text.rfind(marker)
if idx == -1:
    raise SystemExit('marker not found')

# 从标记所在行开始截取
session = text[idx:]
lines = session.splitlines()
start_time = lines[0].split(' - ')[0] if lines else ''

video_matches = re.findall(r'📺 视频 #(\d+)', session)
video_total = int(video_matches[-1]) if video_matches else 0

play_times = [float(x) for x in re.findall(r'播放视频 ([0-9.]+)秒', session)]

count = session.count

stats = {
    'start_time': start_time,
    'video_total': video_total,
    'live_skips': count('🔴 检测到直播入口视频'),
    'non_target_skips': count('⏭️ 非常规视频'),
    'probability_skips': count('🎲 命中跳过概率'),
    'play_segments': len(play_times),
    'play_avg': round(sum(play_times) / len(play_times), 2) if play_times else 0,
    'play_min': min(play_times) if play_times else 0,
    'play_max': max(play_times) if play_times else 0,
    'like_attempts': count('👍 尝试点赞'),
    'like_success': count('✅ 点赞成功'),
    'comment_attempts': count('💬 尝试评论'),
    'comment_success': count('✅ 评论成功'),
    'comment_fail': count('⚠️ 评论失败'),
    'favorite_attempts': count('⭐ 尝试收藏'),
    'favorite_success': count('✅ 收藏成功'),
}

print(json.dumps(stats, ensure_ascii=False, indent=2))
