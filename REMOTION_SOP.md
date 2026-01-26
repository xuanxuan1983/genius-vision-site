# Remotion 动态视觉工业化生产 SOP (V1.0)

## 0. 核心理念：审美驱动，逻辑执行
**"代码即剪辑"**。通过 AI (Gemini) 完成审美决策，通过 Remotion 完成工业化渲染，将原本昂贵的品牌片制作成本降至极致。

---

## 1. 流程闭环 (The 5-Step Loop)

### STEP 1：Gemini 战略策划
*   **指令要求**：要求模型输出 30-45 秒的短视频脚本，包含角色矩阵、核心痛点、交付价值。
*   **审美对齐**：明确指出需要“Apple 风格快闪”、“暴力美学”、“高信息密度压迫感”。

### STEP 2：精准素材匹配 (Media-Download)
*   **技巧**：不仅下载原始视频，更要利用模型优化搜索关键词（如：*Minimalist abstract red scan line*, *Cyberpunk grid landscape*）。
*   **关键资产**：Portrait.webp（高清肖像）、Audio.mp3（背景乐/配音）。

### STEP 3：TTS 高级感配音
*   **要求**：选择沉稳、具有科技感或商业领袖气质的音色。
*   **数据对接**：导出配音时长（frames），作为 Remotion `durationInFrames` 的驱动参数。

### STEP 4：Remotion 自动化剪辑
*   **组件化逻辑**：使用 `AgentFlash`（角色闪现）、`PunchWord`（重力打字）等预设组件。
*   **动态对齐**：视频长度随音频自动伸缩。

### STEP 5：BGM 与全局氛围
*   **处理**：配上符合“商业帝国”主题的 BGM（重低音、金属质感、快节奏转场）。

---

## 2. 暴力美学核心参数 (Black Box Logic)

要在视觉上产生“眼前一亮”的效果，必须执行以下代码级参数：

### A. 角色矩阵快闪 (The Strobe Effect)
**逻辑**：黑白底色高频反转，文字占据 80% 视觉中心。
```tsx
// 关键逻辑：每 3-4 帧切换一个角色，并反转底色
const isStrobe = Math.floor(frame / step) % 2 === 0;
return (
  <AbsoluteFill style={{ 
    backgroundColor: isStrobe ? 'white' : 'black',
    color: isStrobe ? 'black' : 'white'
  }}>
    {AGENT_LIST[currentIndex]}
  </AbsoluteFill>
);
```

### B. 动态网格背景 (Animated Grid)
**逻辑**：背景线条以极慢速度向斜上方漂移，增加空间感。
```tsx
// 关键逻辑：平移量与帧数挂钩
transform: `translate(${-offset % 80}px, ${-offset % 80}px) rotate(-5deg)`
```

### C. 肖像推近 (Ken Burns Portrait)
**逻辑**：从 1.2 倍缩放到 1.0 倍，产生身临其境的“入侵感”。
```tsx
const scale = interpolate(frame, [0, 100], [1.2, 1]);
```

### D. Cinematic Overlay (电影滤镜)
**逻辑**：边缘暗角 + 红色扫描纹理，消除数码味，增加质感。

---

## 3. 一键成片检查清单 (Checklist)

1. [ ] **AGENT_LIST**：确保 18-20 个岗位名称已经根据业务更新。
2. [ ] **Pricing**：全局搜索并移除具体价格，代之以“价值陈述”。
3. [ ] **Cinematic Overlay**：是否开启暗角和发光特效？
4. [ ] **Typography**：中英文字号是否统一？（推荐：大字 160px+）。
5. [ ] **Multi-Format**：是否同时生成了 16:9 (横屏) 和 9:16 (竖屏)？

---
**制作者：XUANYI | GENIUS VISION AI CLONE**
**日期：2026-01-26**
