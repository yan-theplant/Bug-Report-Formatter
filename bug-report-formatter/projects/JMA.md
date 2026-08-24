# JMA 项目（McDJP MOP FE）—— 已基本停用，见 `MDX.md`

> **麦当劳日本的 app bug 现在开在 `MDX`，不是 `JMA`。** 请加载 `projects/MDX.md`。

- `JMA` 项目最后一张 bug：**<JMA-xxxx>（2026-07-28）**；此后 QA 的 app bug 全部开在 `MDX`。
- 5.5.60 回归的 18 张 bug 全在 MDX（<MDX-xxxx> ~ <MDX-xxxx>），回归总票 `<MDX-xxxx>` 也在 MDX。
- 只有在**用户明确要求开在 JMA**、或**处理 JMA-xxxx 老票**时才用本项目。

## 仅在动 JMA 老票时需要知道的差异

| 项 | JMA | MDX |
|---|---|---|
| Bug 必填字段 | `project` / `issuetype` / `summary` | 多一个 **`reporter`** |
| 环境段写法 | `UAT` / `Prod` / `STG` | `UAT` / **`PROD`** / `STG` |
| 正文小标题 | 部分老票用 `Pre-condition: / Description: / Expected result: / Actual result:`（如 <JMA-xxxx>） | 通用模板 `Steps to reproduce / Expected / Actual / Note` |
| 回归总票 | 历史 `5.3.10 QA regression testing` 等，**2023 年后停更** | `[QA] JMA <ver> Regression Testing` |

标题风格、版本号体系（build vs release）、功能区白名单、经办人 accountId、查重词对 —— **全部与 MDX 相同，直接看 `MDX.md`**，不在此重复。
