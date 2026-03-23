# 2026-03-22-23-22-frontend-startup-fix.md

## 任务背景
用户询问前端是否启动，经排查发现端口 5173 被其他路径下的项目占用，而非当前项目目录。

## 执行步骤
1. **排查端口占用**：使用 `lsof -i :5173` 发现 PID 30582 和 15258 占用了端口。
2. **验证路径**：通过 `lsof -p <PID>` 确认占用进程的工作目录在 `~/.openclaw/...` 而非当前项目目录。
3. **清理进程**：执行 `kill -9` 终止了占用进程。
4. **启动正确服务**：在 `/Users/vernonsong/Documents/项目/datalake_demo/frontend/` 目录下运行 `npm run dev`。
5. **验证状态**：再次确认端口 5173 的进程路径已指向当前项目。
6. **更新文档**：在 `AGENTS.md` 中补充了前端项目的启动说明。

## 验证结果
- 前端服务运行在 `http://localhost:5173`。
- 进程路径确认：`/Users/vernonsong/Documents/项目/datalake_demo/frontend`。
- 文档已同步更新。
