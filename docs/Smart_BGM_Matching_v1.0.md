# 智能BGM匹配系统 v1.0 - 产品需求文档

**项目**: shorts-fission  
**版本**: v1.0  
**日期**: 2026-03-10  
**状态**: 设计完成，待开发

---

## 一、背景与目标

### 1.1 背景

当前 shorts-fission 项目的 BGM 替换功能较为简单，仅支持按球类目录随机选择 BGM，缺乏智能匹配能力。需要建立一个基于视频音频特征的智能 BGM 匹配系统。

### 1.2 目标

- 建立免费 BGM 音乐库（30-45 首）
- 实现基于音频能量的智能匹配
- 保留原视频人声/解说，混音处理
- Phase 1 采用简单规则验证，后续迭代升级

### 1.3 核心原则

1. **BGM 版权**：使用免费、免版权音乐（CC0 协议）
2. **人声处理**：保留原视频解说/人声，BGM 作为背景混音
3. **匹配策略**：Phase 1 使用简单能量规则，验证效果后再升级

---

## 二、BGM 音乐库设计

### 2.1 目录结构

采用**通用能量级别分类**，不分球类：

```
sports_bgm/
├── metadata.json              # BGM 特征索引
├── high_energy/               # BPM ≥ 130，激昂、紧张、高能量
│   ├── epic_trap_beat.mp3
│   ├── energetic_electronic.mp3
│   └── ...
├── medium_energy/             # BPM 110-130，适中、激励
│   ├── motivational_pop.mp3
│   ├── uplifting_cinematic.mp3
│   └── ...
└── low_energy/                # BPM < 110，舒缓、平稳
    ├── calm_ambient.mp3
    ├── soft_background.mp3
    └── ...
```

### 2.2 metadata.json 结构

```json
{
  "version": "1.0",
  "last_updated": "2026-03-10",
  "tracks": {
    "high_energy/epic_trap_beat.mp3": {
      "bpm": 142,
      "energy": 0.85,
      "duration": 185,
      "mood": ["energetic", "aggressive"],
      "genre": "trap",
      "source": "pixabay",
      "license": "CC0"
    },
    "medium_energy/motivational_pop.mp3": {
      "bpm": 120,
      "energy": 0.55,
      "duration": 210,
      "mood": ["motivational", "upbeat"],
      "genre": "pop",
      "source": "pixabay",
      "license": "CC0"
    }
  }
}
```

### 2.3 BGM 来源

| 平台 | 优先级 | 特点 |
|------|--------|------|
| **Pixabay Music** | ⭐⭐⭐⭐⭐ | 无需登录、CC0 协议、有 BPM 标注 |
| **Mixkit** | ⭐⭐⭐⭐⭐ | 无需署名、质量高 |
| **YouTube Audio Library** | ⭐⭐⭐⭐ | 需登录、资源丰富 |
| **Bensound** | ⭐⭐⭐ | 运动类多、免费需署名 |

### 2.4 下载清单

| 能量级别 | 数量 | Pixabay 搜索关键词 |
|----------|------|-------------------|
| high_energy | 15 首 | energetic, epic, sports, trap, electronic |
| medium_energy | 15 首 | motivational, uplifting, cinematic, pop |
| low_energy | 10-15 首 | calm, ambient, soft, background |

**总计**：40-45 首

---

## 三、音频分析模块

### 3.1 功能说明

提取视频音轨的特征值，用于后续 BGM 匹配。

### 3.2 提取特征

| 特征 | 说明 | 计算方法 |
|------|------|----------|
| **BPM** | 节拍速度 | librosa.beat.beat_track() |
| **Energy** | 能量强度 | RMS 均值 (librosa.feature.rms) |
| **Duration** | 时长 | 音频长度 / 采样率 |
| **Has_Voice** | 是否有人声 | 频谱质心 > 2000Hz（简化检测） |

### 3.3 代码实现

```python
class AudioAnalyzer:
    """音频特征分析器"""
    
    def analyze(self, audio_path: str) -> dict:
        """
        提取音频特征
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            {
                'bpm': 125.5,
                'energy': 0.72,
                'duration': 65.3,
                'has_voice': True
            }
        """
        import librosa
        import numpy as np
        
        y, sr = librosa.load(audio_path, sr=22050)
        
        # 1. BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo)
        
        # 2. 能量 (RMS)
        rms = librosa.feature.rms(y=y)
        energy = float(np.mean(rms))
        
        # 3. 时长
        duration = len(y) / sr
        
        # 4. 人声检测（简化：高频能量比例）
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        has_voice = np.mean(spectral_centroid) > 2000
        
        return {
            'bpm': round(bpm, 1),
            'energy': round(energy, 3),
            'duration': round(duration, 1),
            'has_voice': has_voice
        }
```

---

## 四、BGM 匹配模块

### 4.1 匹配规则（Phase 1 简单规则）

基于视频音频能量级别匹配对应 BGM：

| 视频能量 | 能量级别 | BGM 目录 |
|----------|----------|----------|
| ≥ 0.7 | high | high_energy/ |
| 0.4 - 0.7 | medium | medium_energy/ |
| < 0.4 | low | low_energy/ |

### 4.2 代码实现

```python
class BGMMatcher:
    """BGM 匹配器 v1 - 基于能量规则"""
    
    ENERGY_THRESHOLDS = {
        'high': 0.7,
        'medium': 0.4,
        'low': 0.0
    }
    
    def match(self, audio_features: dict, bgm_library_path: str = "sports_bgm") -> str:
        """
        匹配 BGM
        
        Args:
            audio_features: {'bpm': 125, 'energy': 0.75, 'duration': 60}
            bgm_library_path: BGM 音乐库根目录
        
        Returns:
            BGM 文件路径
        """
        energy = audio_features['energy']
        
        # 根据能量级别选择目录
        if energy >= self.ENERGY_THRESHOLDS['high']:
            energy_level = 'high_energy'
        elif energy >= self.ENERGY_THRESHOLDS['medium']:
            energy_level = 'medium_energy'
        else:
            energy_level = 'low_energy'
        
        # 从对应目录随机选一首
        bgm_dir = Path(bgm_library_path) / energy_level
        candidates = list(bgm_dir.glob("*.mp3"))
        
        if not candidates:
            # 降级到 medium_energy
            candidates = list(Path(bgm_library_path / "medium_energy").glob("*.mp3"))
        
        if not candidates:
            raise ValueError("BGM 音乐库为空，请先添加 BGM 文件")
        
        return str(random.choice(candidates))
```

---

## 五、混音模块

### 5.1 功能说明

将原视频人声与匹配的 BGM 进行混音，保留原解说/人声。

### 5.2 混音参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **原人声音量** | 1.0 | 保持原样 |
| **BGM 音量** | 0.10 - 0.20 | 背景级别，不盖过人声 |
| **BGM 淡入** | 2 秒 | 平滑开始 |
| **BGM 淡出** | 3 秒 | 平滑结束 |
| **BGM 循环** | 是 | 视频 > BGM 时循环播放 |

### 5.3 代码实现

```python
class AudioMixer:
    """音频混音器 - 保留原人声"""
    
    def __init__(self, config: dict = None):
        config = config or {}
        self.bgm_volume = config.get('bgm_volume', 0.15)
        self.fade_in = config.get('fade_in', 2.0)
        self.fade_out = config.get('fade_out', 3.0)
    
    def mix(
        self, 
        video_path: str, 
        bgm_path: str, 
        output_path: str
    ) -> bool:
        """
        混音：原人声 + BGM
        
        Args:
            video_path: 输入视频路径
            bgm_path: BGM 文件路径
            output_path: 输出视频路径
        
        Returns:
            是否成功
        """
        duration = self._get_duration(video_path)
        
        cmd = [
            'ffmpeg', '-i', video_path, '-i', bgm_path,
            '-filter_complex',
            f"[0:a]volume=1.0[voice];"
            f"[1:a]volume={self.bgm_volume},"
            f"afade=t=in:st=0:d={self.fade_in},"
            f"afade=t=out:st={duration-self.fade_out}:d={self.fade_out},"
            f"aloop=loop=-1:size=2e+09[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=3[audio]",
            '-map', '0:v', '-map', '[audio]',
            '-c:v', 'copy', '-c:a', 'aac',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"混音超时: {video_path}")
            return False
        except Exception as e:
            logger.error(f"混音错误: {e}")
            return False
    
    def _get_duration(self, video_path: str) -> float:
        """获取视频时长"""
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
```

---

## 六、完整工作流

```
┌─────────────────────┐
│     输入视频        │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   提取音频轨        │  ffmpeg -i video.mp4 -vn -acodec pcm_s16le audio.wav
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   音频特征分析      │  AudioAnalyzer.analyze()
│   (BPM + Energy)    │  librosa
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   规则匹配 BGM      │  BGMMatcher.match()
│   energy → BGM 级别 │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   混音合成          │  AudioMixer.mix()
│   原人声 + BGM      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│     输出视频        │
└─────────────────────┘
```

---

## 七、集成方案

### 7.1 文件结构

```
backend/app/services/
├── variant_engine.py          # 现有：视觉变体引擎
├── audio_analyzer.py          # 新增：音频分析器
├── bgm_matcher.py             # 新增：BGM 匹配器
└── audio_mixer.py             # 新增：音频混音器

sports_bgm/
├── metadata.json
├── high_energy/
├── medium_energy/
└── low_energy/
```

### 7.2 替换现有 AudioVariantEngine

将现有的 `AudioVariantEngine` 替换为新的智能匹配系统：

```python
# 旧代码
class AudioVariantEngine:
    def replace_bgm(self, input_path, output_path, sport_type="default"):
        bgm_dir = self.sports_bgm.get(sport_type, self.sports_bgm['default'])
        # ... 随机选择 BGM

# 新代码
class AudioVariantEngine:
    def __init__(self, config: Dict):
        self.analyzer = AudioAnalyzer()
        self.matcher = BGMMatcher()
        self.mixer = AudioMixer(config)
    
    def replace_bgm(self, input_path, output_path, sport_type=None):
        # 1. 提取音频特征
        audio_features = self.analyzer.analyze(input_path)
        
        # 2. 智能匹配 BGM
        bgm_path = self.matcher.match(audio_features)
        
        # 3. 混音
        success = self.mixer.mix(input_path, bgm_path, output_path)
        
        return {
            'success': success,
            'bgm_replaced': success,
            'bgm_file': Path(bgm_path).name if success else None,
            'audio_features': audio_features
        }
```

---

## 八、依赖安装

```bash
pip install librosa numpy
```

---

## 九、实现计划

| 阶段 | 任务 | 时间 | 负责人 |
|------|------|------|--------|
| **Step 1** | BGM 采集（40-45 首） | 2-3 天 | 手动下载 |
| **Step 2** | BGM 特征提取 + metadata.json 生成 | 1 天 | T.W |
| **Step 3** | AudioAnalyzer 实现 + 测试 | 1 天 | T.W |
| **Step 4** | BGMMatcher + AudioMixer 实现 | 1 天 | T.W |
| **Step 5** | 集成到 shorts-fission + 端到端测试 | 1 天 | T.W |
| **Step 6** | 效果评估 + 参数调优 | 1 天 | T.W + William |

**总计**：7-8 天

---

## 十、验收标准

1. **BGM 音乐库**：40-45 首，按能量级别分类，metadata.json 正确生成
2. **音频分析**：能正确提取 BPM、Energy、Duration、Has_Voice
3. **BGM 匹配**：根据视频能量正确匹配对应级别 BGM
4. **混音效果**：
   - 原人声清晰可听
   - BGM 音量适中，不盖过人声
   - 淡入淡出平滑
5. **端到端测试**：10 个测试视频全部成功处理

---

## 十一、后续迭代方向（Phase 2+）

1. **人声情绪分析**：使用 Whisper ASR + LLM 分析解说情绪
2. **BGM 向量化**：使用 Chroma/FAISS 进行相似度检索
3. **动态 BGM**：根据视频关键帧切换 BGM 风格
4. **BGM 自动生成**：使用 AI 生成定制 BGM

---

## 十二、参考资源

- [librosa 文档](https://librosa.org/doc/latest/index.html)
- [Pixabay Music](https://pixabay.com/music/)
- [Mixkit Free Music](https://mixkit.co/free-stock-music/)
- [YouTube Audio Library](https://studio.youtube.com/channel/UC/music)
- [FFmpeg Audio Filters](https://ffmpeg.org/ffmpeg-filters.html#Audio-Filters)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-10  
**作者**: T.W (Twin William)
