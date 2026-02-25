# PWA 图标制作指南

## 所需图标尺寸

在发布到生产环境前，需要准备以下尺寸的 PNG 图标：

```
frontend/public/
├── icon-72x72.png      # Android 图标
├── icon-96x96.png      # Android 图标
├── icon-128x128.png    # Chrome Web Store
├── icon-144x144.png    # iOS/iPad
├── icon-152x152.png    # iOS
├── icon-192x192.png    # Android/iOS 主屏幕
├── icon-384x384.png    # PWA 启动画面
└── icon-512x512.png    # PWA 必需
```

## 快速生成

### 方法1: 使用在线工具
1. 访问 https://appicon.co/
2. 上传 `icon.svg`
3. 下载生成的图标包
4. 解压到 `frontend/public/` 目录

### 方法2: 使用 ImageMagick
```bash
for size in 72 96 128 144 152 192 384 512; do
  convert icon.svg -resize ${size}x${size} icon-${size}x${size}.png
done
```

## 图标设计
- 背景: #1a3d18 (绿色)
- 主体: ♠️ (扑克黑桃)
- 文字: GTO (金色 #ffd700)
