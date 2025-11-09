# AI Auto-Annotation Tool - Web Frontend

基于 React + TypeScript + Ant Design 的 Web 前端应用

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **UI 组件库**: Ant Design 5
- **状态管理**: TanStack Query (React Query)
- **路由**: React Router v6
- **HTTP 客户端**: Axios

## 功能特性

### 已实现 (MVP)

- ✅ Dashboard - 项目概览
- ✅ 项目管理 - CRUD 操作
- ✅ 图片生成 - 任务创建和进度监控
- ✅ 图片审核 - 批量审核操作

### 计划中

- ⏳ 标注管理 - 标注查看和校验
- ⏳ 数据集管理 - 版本控制和导出
- ⏳ 训练管理 - 模型训练和监控
- ⏳ 实时进度更新 (WebSocket)
- ⏳ 图片预览和可视化
- ⏳ 用户认证和权限管理

## 快速开始

### 安装依赖

```bash
npm install
# 或
pnpm install
# 或
yarn install
```

### 开发环境

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

构建输出在 `dist/` 目录

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend-web/
├── public/              # 静态资源
├── src/
│   ├── api/            # API 客户端
│   │   ├── client.ts
│   │   ├── projects.ts
│   │   ├── generation.ts
│   │   ├── images.ts
│   │   └── index.ts
│   ├── components/     # 组件
│   │   └── Layout/
│   │       └── MainLayout.tsx
│   ├── pages/          # 页面
│   │   ├── Dashboard/
│   │   ├── Projects/
│   │   ├── Generation/
│   │   └── Images/
│   ├── types/          # TypeScript 类型
│   │   └── index.ts
│   ├── App.tsx         # 应用根组件
│   ├── main.tsx        # 应用入口
│   └── router.tsx      # 路由配置
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## API 代理配置

开发环境下，API 请求会自动代理到后端服务器：

```typescript
// vite.config.ts
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 页面路由

- `/` - 重定向到 Dashboard
- `/dashboard` - Dashboard 概览
- `/projects` - 项目列表
- `/projects/:id` - 项目详情
- `/projects/:projectId/generation` - 图片生成
- `/projects/:projectId/images` - 图片审核

## 开发说明

### 添加新页面

1. 在 `src/pages/` 创建页面组件
2. 在 `src/App.tsx` 添加路由
3. 在 `src/components/Layout/MainLayout.tsx` 添加菜单项

### 添加 API

1. 在 `src/api/` 创建 API 模块
2. 使用 `apiClient` 发起请求
3. 在 `src/api/index.ts` 导出

### 使用 React Query

```typescript
import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/api'

const { data, isLoading, error } = useQuery({
  queryKey: ['projects'],
  queryFn: () => projectsApi.getProjects().then(res => res.data),
})
```

## 环境变量

创建 `.env.local` 文件:

```env
VITE_API_URL=http://localhost:8000
```

## 待办事项

- [ ] 添加图片预览组件
- [ ] 实现标注可视化（Canvas/SVG）
- [ ] 添加实时进度更新（WebSocket）
- [ ] 完善错误处理和加载状态
- [ ] 添加单元测试
- [ ] 添加 E2E 测试
- [ ] 性能优化（代码分割、懒加载）
- [ ] 主题切换（暗黑模式）
- [ ] 国际化支持

## License

MIT
