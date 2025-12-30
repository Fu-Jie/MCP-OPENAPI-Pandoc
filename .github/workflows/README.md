# 工作流架构与维护指南

## 总览
- `publish-container.yml`：生产发布，触发 `push tags v*.*.*`、手动、定时。执行多架构构建、GHCR 推送、冒烟测试与报告。
- `test-publish.yml`：PR/定时验证，dry-run 多架构构建，不推送产物，校验标签生成与权限。
- `pipeline.yml`：仓库原有基础 CI（未改动）。

## 关键设计决策（ADR）
1. **多架构构建方式**：采用 `docker/setup-buildx-action` + QEMU。理由：GitHub 托管 runner 默认支持，便于 registry 缓存复用。
2. **缓存策略**：三层缓存（registry、GHA、local）。理由：兼顾云端复用与单次 Job 提速，避免缓存失效导致全量重编译。
3. **标签策略**：`latest` + `vX.Y.Z` + `vX.Y` + `vX` + `SHA`。理由：同时满足生产稳定标签与可追溯性。
4. **权限最小化**：`contents:read`、`packages:write/read`、`id-token:write`。理由：仅在需要推送或签名时提升权限，减少泄露面。
5. **失败处理**：集中 `if: failure()` 通知 Slack/Email。理由：统一出口，避免遗漏告警。
6. **可选签名**：预置 Cosign 步骤，通过输入开关控制。理由：在需要合规时快速启用。

## 运行流程概述
1. 检出代码，确保完整历史供 metadata 解析。
2. 初始化 QEMU 与 buildx，恢复 GHA/Registry 缓存。
3. metadata-action 生成标签与 OCI labels。
4. build-push-action 构建推送（生产）或 dry-run（测试）。
5. 生产发布后执行 manifest 检查与跨架构冒烟测试。
6. 上传报告并在失败时发送通知。

## 维护要点
- **版本锁定**：所有外部 Action 已锁定具体版本（4.1.7/3.7.1 等）。升级前请在测试工作流验证。
- **缓存命中**：若频繁 cache miss，检查 key 计算中包含的文件是否经常变化，必要时拆分 key。
- **凭证管理**：默认使用 `GITHUB_TOKEN`。若需跨组织推送请改用具备 `write:packages` 的 PAT，设置为 `secrets.GHCR_TOKEN` 并替换登录步骤。
- **安全强化**：可将 `ENABLE_COSIGN_SIGNING` 默认置为 `true` 并配置 OIDC；可插入 Trivy 扫描步骤（放在 build 后、推送前）。
- **调试技巧**：在 `build-push-action` 中加入 `--progress=plain` 便于追踪；失败时查看上传的 `manifest.txt` 与 `smoke-tests.txt`。

## 本地复现
```bash
# dry-run 与 CI 配置对齐
docker buildx build \
  --file Dockerfile.example \
  --platform linux/amd64,linux/arm64 \
  --cache-from type=registry,ref=ghcr.io/<owner>/<repo>:buildcache \
  --cache-to type=registry,ref=ghcr.io/<owner>/<repo>:buildcache,mode=max \
  --tag ghcr.io/<owner>/<repo>:local \
  --load .
```

## 常见问题
- **QEMU 下载缓慢**：切换镜像源或预热缓存；必要时减少平台数量。
- **权限不足**：确认 workflow permissions 未被组织策略覆盖；在仓库设置中允许 GITHUB_TOKEN 写包。
- **artifact 丢失**：检查 `actions/upload-artifact` 是否因路径错误为空；本配置使用 `artifacts/` 目录集中产物。
