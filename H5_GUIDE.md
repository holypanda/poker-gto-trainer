# Poker GTO Trainer H5 移动端优化指南

## 📱 H5 特性概览

Poker GTO Trainer 已全面适配移动端 H5 环境，支持以下特性：

### ✅ 移动端优化

- **响应式布局**: 自适应手机、平板、桌面端
- **底部导航栏**: 移动端专属底部 tab 导航
- **触摸优化**: 按钮点击反馈、防止双击缩放
- **PWA 支持**: 可添加到主屏幕，离线访问
- **安全区域适配**: iPhone 刘海屏、底部手势条适配

### 📲 PWA 功能

- **添加到主屏幕**: 像原生 App 一样使用
- **离线缓存**: 静态资源本地缓存
- **Service Worker**: 后台更新、推送通知支持

## 🎯 移动端界面

### 1. 底部导航栏
```
┌─────────────────────────────────┐
│           内容区域               │
│                                 │
├─────────┬──────┬──────┬────────┤
│  🏠 首页 │ 🎯训练│ 📊统计│ 💎VIP │
└─────────┴──────┴──────┴────────┘
         ↑ 底部固定导航栏
```

### 2. 训练界面
- 大按钮设计，方便单手操作
- 手牌数字放大显示
- 滑动选择训练数量
- 触摸反馈效果

### 3. 统计图表
- 响应式图表尺寸
- 支持手势缩放
- 简化的数据展示

## 🚀 添加到主屏幕

### iOS Safari
1. 打开网站 https://your-domain.com
2. 点击底部分享按钮 ⬆️
3. 选择 "添加到主屏幕"
4. 点击 "添加"

### Android Chrome
1. 打开网站 https://your-domain.com
2. 点击菜单按钮 ⋮
3. 选择 "添加到主屏幕"
4. 点击 "添加"

## 📐 设计规范

### 断点
- **移动端**: < 768px
- **平板**: 768px - 1024px
- **桌面**: > 1024px

### 字体大小
| 元素 | 移动端 | 桌面端 |
|-----|-------|-------|
| 标题 | 18-20px | 24-30px |
| 正文 | 14px | 16px |
| 小字 | 12px | 14px |
| 按钮 | 14px | 16px |

### 间距
| 场景 | 移动端 | 桌面端 |
|-----|-------|-------|
| 卡片内边距 | 12-16px | 24px |
| 元素间距 | 8-12px | 16-24px |
| 底部安全区 | env(safe-area-inset-bottom) | 0 |

### 触摸目标
- 最小点击区域: 44x44px
- 按钮高度: 44-52px
- 按钮间距: 8-12px

## 🔧 开发说明

### 移动端检测 Hook
```typescript
import { useMobile, useViewport } from './hooks/useMobile';

function MyComponent() {
  const { isMobile, isStandalone } = useMobile();
  const { height, width } = useViewport();
  
  return (
    <div className={isMobile ? 'p-2' : 'p-6'}>
      {isStandalone && <span>App 模式</span>}
    </div>
  );
}
```

### 触摸反馈
```typescript
import { useTouchFeedback } from './hooks/useMobile';

function Button() {
  const { touched, onTouchStart, onTouchEnd } = useTouchFeedback();
  
  return (
    <button
      onTouchStart={() => onTouchStart('btn1')}
      onTouchEnd={onTouchEnd}
      className={touched === 'btn1' ? 'scale-95' : ''}
    >
      点击我
    </button>
  );
}
```

## 📊 性能优化

### 图片资源
- 使用 WebP 格式
- 提供多种分辨率
- 懒加载非首屏图片

### 代码分割
- 路由级别代码分割
- 组件懒加载
- Tree shaking

### 缓存策略
```javascript
// Service Worker 缓存
const CACHE_NAME = 'poker-gto-v1';
// 静态资源: Cache First
// API 请求: Network First
```

## 🧪 测试清单

### 功能测试
- [ ] 注册/登录流程
- [ ] 训练答题流程
- [ ] 支付宝支付
- [ ] 图表显示
- [ ] 下拉刷新

### 兼容性测试
- [ ] iOS Safari (iPhone 12/13/14/15)
- [ ] Android Chrome (主流机型)
- [ ] 微信内置浏览器
- [ ] 不同屏幕尺寸

### 性能测试
- [ ] 首屏加载 < 3s
- [ ] 交互响应 < 100ms
- [ ] 内存占用 < 100MB
- [ ] 耗电量测试

## 🐛 常见问题

### 1. iOS 键盘弹出页面错位
**解决**: 使用 `position: fixed` + `transform`

### 2. Android 返回键处理
**解决**: 监听 `popstate` 事件

### 3. 300ms 点击延迟
**解决**: 已设置 `touch-action: manipulation`

### 4. 底部导航栏被手势条遮挡
**解决**: 使用 `env(safe-area-inset-bottom)`

## 📱 推荐测试设备

### iOS
- iPhone SE (小屏)
- iPhone 12/13/14 (标准)
- iPhone 14 Pro Max (大屏)

### Android
- Xiaomi 13 (MIUI)
- Samsung Galaxy S23 (OneUI)
- Google Pixel 7 (原生)
- Huawei P60 (鸿蒙)

---

**Poker GTO Trainer H5 版本 - 随时随地练习 GTO！** 🚀
