# 抖音高仿真引流RPA项目 (V4 - 混合动力·最终版)

## 📋 项目概述

这是一个基于Python + Appium的抖音自动化RPA项目，专门设计用于学习测试目的。项目采用"混合会话模式"，通过"伪装会话"（无聊刷）和"攻击会话"（精准打击）的随机交替执行，实现高仿真的引流操作。

## ⚠️ 重要声明

- **本项目仅用于学习、测试和研究目的**
- 请遵守抖音平台的服务条款和社区准则
- 自动化操作可能导致账号受到限制或封禁
- 使用者需自行承担所有风险和责任
- 开发者不承担任何法律责任

## 🚀 核心特性

### 🛡️ 高健壮性
- 完整的异常处理和恢复机制
- 网络断连自动重连
- 应用崩溃自动重启
- 弹窗智能识别和处理

### 📱 高仿真度
- 人性化滑动轨迹和速度
- 随机触摸位置偏移
- 真实用户行为模拟
- 智能时间窗口控制

### 🧠 智能调度
- 混合会话自动切换
- 自适应参数调整
- 成功率动态优化
- 智能休息机制

### 💾 数据持久化
- SQLite数据库存储
- 详细运行统计
- 历史数据分析
- 数据导出功能

### 🔧 热更新支持
- 运行时参数修改
- 无需重启配置
- 实时生效调整

## 📁 项目结构

```
/douyin_autoclient
├── src/                    # 核心源代码
│   ├── __init__.py
│   ├── main.py            # 唯一的启动入口 (轻量)
│   ├── app_driver.py      # 专职：初始化和关闭 Appium Driver
│   ├── core_utils.py      # 原子操作：find_safe, swipe_humanized, send_keys_safe
│   ├── interactions.py    # 业务逻辑：like, comment, perform_search, dismiss_popups
│   ├── task_manager.py    # 状态机：(项目的灵魂) 负责会话切换、编排
│   └── tracker.py         # 统计器：SQLite数据持久化
├── config/                # 所有配置
│   ├── __init__.py
│   ├── settings.py        # Appium配置, 概率, 会话长度定义
│   ├── comments.txt       # 营销评论库 (一行一个)
│   └── keywords.txt       # 搜索关键词库 (一行一个)
├── logs/                  # 日志输出
│   └── app.log
├── requirements.txt       # 依赖库
└── README.md             # 项目说明
```

## 🛠️ 环境要求

- Python 3.7+
- Android设备（已开启USB调试）
- Appium Server
- ADB驱动

## 📦 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd douyin_autoclient
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **设备准备**
   - Android设备开启USB调试
   - 通过USB连接到电脑
   - 安装抖音应用

4. **启动Appium Server**
   ```bash
   appium
   ```

5. **运行程序**
   ```bash
   python src/main.py
   ```

## 🎯 使用方法

### 基本运行
```bash
python src/main.py
```

### 自动接受协议
```bash
python src/main.py --auto-accept
```

### 仅检查环境
```bash
python src/main.py --check-only
```

### 导出数据
```bash
python src/main.py --export-data
```

## ⚙️ 配置说明

### 运行时配置
程序运行时会生成 `config/runtime_config.json` 文件，支持热更新：

```json
{
  "appium": {
    "server_url": "http://127.0.0.1:4723",
    "caps": {
      "platformName": "Android",
      "deviceName": "Android Device",
      "appPackage": "com.ss.android.ugc.aweme",
      "appActivity": ".main.MainActivity"
    }
  },
  "sessions": {
    "for_you_min_videos": 15,
    "for_you_max_videos": 25,
    "search_min_videos": 30,
    "search_max_videos": 50
  },
  "behavior": {
    "for_you_like_prob": 0.1,
    "search_like_prob": 0.8,
    "search_comment_prob": 0.2
  },
  "anti_detection": {
    "random_session_interval": true,
    "daily_active_hours": [9, 10, 11, 14, 15, 16, 19, 20, 21]
  }
}
```

### 关键参数说明

- `for_you_like_prob`: 推荐页面点赞概率 (0.1 = 10%)
- `search_like_prob`: 搜索页面点赞概率 (0.8 = 80%)
- `search_comment_prob`: 搜索页面评论概率 (0.2 = 20%)
- `daily_active_hours`: 每日活跃时间数组

## 📊 统计功能

程序会自动统计以下数据：
- 观看视频数量
- 点赞、评论、收藏、关注次数
- 搜索执行次数
- 会话完成情况
- 错误发生次数
- 运行时间统计

### 查看统计
统计摘要会在每次会话结束后自动显示，也可以在 `logs/` 目录中查看详细数据。

### 导出数据
```bash
python src/main.py --export-data
```

## 🔧 高级功能

### 1. 智能调度
- 自动在推荐页面和搜索页面间切换
- 根据成功率自适应调整参数
- 智能休息机制避免被检测

### 2. 反检测措施
- 人性化操作间隔
- 随机触摸位置偏移
- 模拟真实用户行为
- 变化的滑动速度

### 3. 异常恢复
- 网络连接自动恢复
- 应用崩溃自动重启
- 元素定位失败处理
- 弹窗智能识别

### 4. 热更新
- 运行时修改 `config/runtime_config.json`
- 无需重启程序即可生效
- 实时调整行为参数

## 🚨 注意事项

1. **合规使用**：仅用于学习测试，不要用于商业用途
2. **风险控制**：建议使用测试账号，避免主账号被封
3. **频率控制**：不要24小时连续运行，给账号休息时间
4. **监控日志**：定期查看运行日志，及时发现问题

## 🐛 常见问题

### Q: 提示"设备未连接"
A: 确保Android设备已开启USB调试并通过USB连接电脑

### Q: Appium连接失败
A: 检查Appium Server是否启动，端口是否正确

### Q: 找不到抖音应用
A: 确保设备上已安装抖音应用，包名是否正确

### Q: 程序崩溃
A: 查看日志文件中的错误信息，通常是元素定位失败

## 📝 更新日志

### V4.0 (当前版本)
- ✅ 添加SQLite数据持久化
- ✅ 实现智能调度系统
- ✅ 增强反检测措施
- ✅ 支持配置热更新
- ✅ 完善异常处理机制

### V3.x (历史版本)
- 基础自动化功能
- 简单的配置系统
- 基本的异常处理

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 📄 许可证

本项目仅用于学习目的，请勿用于商业用途。

## ⚖️ 免责声明

本项目仅供学习研究使用，使用者需自行承担所有风险。开发者不对任何因使用本项目而产生的损失承担责任。