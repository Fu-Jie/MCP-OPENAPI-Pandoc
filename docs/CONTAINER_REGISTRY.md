# 容器发布与运行手册（GHCR）

本手册覆盖从构建、发布、验证到回滚的全流程，并给出性能优化与故障排查建议。所有命令默认在仓库根目录执行。

---

## 1. 预备条件
- 已配置 `GITHUB_TOKEN`（自动）或具备 `packages:write` 的 PAT。
- Docker 24+ 与 buildx 插件。
- QEMU 已安装（跨架构测试需要）。
- 语义化标签：`vMAJOR.MINOR.PATCH`。

## 2. 本地构建与测试
```bash
# 单架构构建
docker build -f Dockerfile.example -t ghcr.io/${GITHUB_REPOSITORY}:dev .

# 启动并进行健康检查
docker run --rm -p 8000:8000 ghcr.io/${GITHUB_REPOSITORY}:dev --help
curl -f http://127.0.0.1:8000/docs
```

## 3. 多架构构建（不推送）
```bash
docker buildx create --name mcp-bx --use
docker buildx build \
  --file Dockerfile.example \
  --platform linux/amd64,linux/arm64 \
  --cache-from type=local,src=/tmp/.buildx-cache \
  --cache-to type=local,dest=/tmp/.buildx-cache,mode=max \
  --tag ghcr.io/${GITHUB_REPOSITORY}:dry-run \
  --load .
```

## 4. GHCR 登录
```bash
echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GITHUB_ACTOR:-your-username}" --password-stdin
```

## 5. 发布流程（CI 等价）
```bash
# 假设当前 git tag 为 v1.2.3
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --file Dockerfile.example \
  --tag ghcr.io/${GITHUB_REPOSITORY}:latest \
  --tag ghcr.io/${GITHUB_REPOSITORY}:v1.2.3 \
  --tag ghcr.io/${GITHUB_REPOSITORY}:v1.2 \
  --tag ghcr.io/${GITHUB_REPOSITORY}:v1 \
  --tag ghcr.io/${GITHUB_REPOSITORY}:${GIT_SHA} \
  --cache-from type=registry,ref=ghcr.io/${GITHUB_REPOSITORY}:buildcache \
  --cache-to type=registry,ref=ghcr.io/${GITHUB_REPOSITORY}:buildcache,mode=max \
  --push .
```

## 6. 发布后验证
- 清单验证：`docker buildx imagetools inspect ghcr.io/${GITHUB_REPOSITORY}:latest`
- 冒烟测试：
  ```bash
  docker run --rm --platform linux/amd64 ghcr.io/${GITHUB_REPOSITORY}:latest --help
  docker run --rm --platform linux/arm64 ghcr.io/${GITHUB_REPOSITORY}:latest --help
  ```
- SBOM/签名：若启用 Cosign，验证 `cosign verify ghcr.io/${GITHUB_REPOSITORY}:latest`。

## 7. 回滚步骤
1. 拉取上一个稳定版本：`docker pull ghcr.io/${GITHUB_REPOSITORY}:v<prev>`
2. 覆盖 latest：`docker tag ghcr.io/${GITHUB_REPOSITORY}:v<prev> ghcr.io/${GITHUB_REPOSITORY}:latest && docker push ghcr.io/${GITHUB_REPOSITORY}:latest`
3. 更新服务：重新部署指向最新的镜像摘要。

## 8. 故障排查
- **登录失败**：确认 PAT scope 包含 `write:packages`；检查 SSO 授权。
- **QEMU 架构失败**：重新运行 `docker run --privileged --rm tonistiigi/binfmt --install all`。
- **缓存未命中**：确认 `cache-from` 引用的标签存在；hash key 是否因为 Dockerfile 变更导致。
- **镜像过大**：启用多阶段；删除构建产物与包管理缓存；使用 `docker history` 定位大层。
- **构建超时**：减少并行平台，或在 workflow_dispatch 输入中暂时限制平台。

## 9. 性能优化建议
- 使用 Registry cache + GHA cache 双层缓存；关键文件变更时重建 key。
- 依赖安装前先 COPY 元数据，最大化缓存命中。
- 使用 `provenance=false` 与 `sbom=true` 平衡元数据体积与可追溯性。
- QEMU 仅在需要跨架构时启用，避免无谓开销。

## 10. 安全要点
- 不在 Dockerfile 中硬编码 secrets；使用 GitHub OIDC 或 secrets mount。
- 使用非 root 用户运行；开启 tini 处理信号。
- 建议启用 Cosign + OIDC 进行签名，并在部署侧强制验证。
- 在 PR 流程中运行 dependency-review 与镜像扫描（可集成 Trivy）。

## 11. 本地快速清理
```bash
docker buildx rm mcp-bx || true
docker image prune -f
docker builder prune -f
```

---

如需企业级多环境扩展（dev/stage/prod）、分支保护或额外合规扫描，可在 `publish-container.yml` 中增加 gated approvals 与专用注册表命名空间。
