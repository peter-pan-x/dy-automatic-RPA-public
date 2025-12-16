# Update Records

## 2025-11-27 Comment Section Optimization
### 1. Comment Browsing & Scanning
- **Refined Logic**: Implemented a robust loop that scans comments screen-by-screen.
- **Content Extraction**: Switched from `TextView.text` to `FrameLayout.content-desc` to accurately capture full comment content, including username, text, and timestamp.
- **Primary Comments Only**: Intentionally skip nested/secondary replies to improve efficiency and stability.
- **End Detection**: Improved "bottom of list" detection by comparing full page content hashes, preventing premature exit.
- **Optimization**: Achieved smooth, rhythmic scrolling and scanning (tested with 200+ comments).

### 2. UI Interaction
- **Tab Switching**: Optimized `switch_to_video_tab` by reducing selectors and wait times for faster navigation.
- **Logging**: Updated logging system to overwrite mode (`mode='w'`) with fixed filenames, preventing log accumulation.
- **Fullscreen Detection**: Enhanced validation using multiple UI signals (tabs, like button position).

### Next Steps
- Merge the successful logic from `test_comment_text.py` into the main `search_browse.py` script.
- Verify the keyword reply mechanism in the live environment.

---

## 2025-12-01 Search Module Performance Optimization

### 1. Speed Optimization
- **Tab Switching**: 直接坐标点击替代选择器遍历，耗时 3s→1s
- **Fullscreen Detection**: 简化检测逻辑，仅检查点赞按钮位置，timeout 2s→1s
- **Video Stats Retrieval**: 元素查找 timeout 从 2s 缩短至 1s
- **Video ID Generation**: 选择器 timeout 从 1s 缩短至 0.5s，移除冗余遍历
- **Video Click Wait**: 点击后等待从 3s 缩短至 1.5s
- **Fullscreen Retry**: 重试次数 3→2，每次等待 2s→1s

### 2. Video Watching Duration
- **优化前**: 15-30 秒
- **优化后**: 7-20 秒
- 每视频节省约 10 秒

### 3. Comment Scanning
- **max_scrolls**: 50→25（单视频最多处理25屏）
- 预计单视频扫描时间从 8分钟 降至 4分钟

### 4. Run Statistics (Latest)
| Metric | Value |
|--------|-------|
| Duration | ~2 hours |
| Videos Processed | 46 |
| Replies Sent | 113 (52% of 216 target) |
| Avg per Video | 2.5 replies |
| Avg per Reply | ~59 seconds |

### Known Issues
- 长时间运行后设备响应变慢，元素查找耗时增加
- 程序在视频 #46 处 LLM 模块卡住（可能是设备/网络问题）
