# Happy Coder · 懒猫微服自动更新适配器

本仓库适配现有应用 `cloud.lazycat.app.happycoder`，上游是
[slopus/happy](https://github.com/slopus/happy)。适配器只维护懒猫清单和构建流程，
不会修改上游仓库。

## 更新流程

每六小时检查上游稳定 `v*` 标签。发现新标签后，Runner 会从该提交同时构建 Happy
Web 与 Happy Server，合并为一个 amd64 镜像，推送到匿名临时仓库 `ttl.sh`，再由懒猫
应用商店转存到官方仓库。随后构建 LPK、提交应用审核并创建带版本号的 GitHub Release。

当前应用商店版本是 `1.5.0`。上游 `v1.1.6` 低于该版本时，共享执行器会分配下一个
修订版本 `1.5.1`，以后继续按修订号递增。

## GitHub Actions 配置

仓库使用组织级 `LZC_API_TOKEN`，工作流通过 `secrets: inherit` 继承。对应开发者账号
需要拥有 `cloud.lazycat.app.happycoder` 的开发者或协作者权限。工作流中的 `dry-run`
默认勾选，取消后才会构建、转存、打包并送审。
如果适配器清单发生变化但上游源版本没有变化，手动运行时同时取消 `dry-run` 并勾选 `force-rebuild`，共享 Action 会分配下一个修订版本重新送审。

## 应用结构

- `happyweb.<微服域名>` 提供 Web 客户端。
- `happyserver.<微服域名>` 提供 Happy Server API 和 WebSocket。
- `happycoder` 是清单中的服务名，与应用包名最后一段保持一致。
- `HANDY_MASTER_SECRET` 在安装时由部署参数随机生成。
- 服务端数据持久化在 `/lzcapp/var/data`。
- `application.public_path: [/]` 保持旧应用的访问方式，客户端和 API 请求无需再次输入微服账号密码。

本地检查命令如下。

```bash
python3 -m unittest discover -s tests -v
python3 -B scripts/verify_package.py
```
