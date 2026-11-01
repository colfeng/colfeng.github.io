# 个人主页修改与回退

网址：https://colfeng.github.io/  
仓库：https://github.com/colfeng/colfeng.github.io  
发布分支：`master`。网站沿用原有 GitHub Pages 和 Jekyll。

## 最常改的地方

| 想修改什么 | 编辑文件 | 怎么改 |
| --- | --- | --- |
| About 自我介绍 | [_pages/about.md](_pages/about.md) | 修改顶部 `---` 下面的正文，支持 Markdown |
| 邮箱、头像、社交链接 | [_data/profile.yml](_data/profile.yml) | 修改对应字段；头像文件放 `images/` |
| 教育、交换、实习经历 | [_data/cv.yml](_data/cv.yml) | 修改或复制一段经历；About 与 CV 共用研究经历 |
| 一篇论文、作者、链接、贡献说明 | [_publications/](_publications/) | 每篇论文一个 Markdown 文件 |
| 首页精选论文与顺序 | [_data/profile.yml](_data/profile.yml) | 调整 `selected_papers` 下的论文 key |
| 论文类别名称与顺序 | [_data/publication_groups.yml](_data/publication_groups.yml) | 修改 `title`、`short`；列表顺序即展示顺序 |
| Area Chair、PC、组织工作 | [_data/services.yml](_data/services.yml) | 修改或复制一个 `entries` 条目 |
| 人名跳转 | [_data/people.yml](_data/people.yml) | 姓名必须与正文或作者列表完全一致 |
| 导航文字与顺序 | [_data/profile_navigation.yml](_data/profile_navigation.yml) | 修改 `label` 或调整条目顺序 |
| 字体、背景和强调色 | [assets/css/profile.css](assets/css/profile.css) | 顶部集中定义颜色与字体 |

**普通内容修改只需要改对应内容文件。** 页面模板在 `_layouts/profile*.html`，论文展示模板在 `_includes/profile/`。

## 直接在 GitHub 网页修改

1. 打开仓库，确认左上角分支为 `master`。
2. 打开上表对应文件，点击铅笔按钮 **Edit this file**。
3. 修改文字，点击 **Commit changes**，写一句修改说明并保存。
4. 在 **Actions → Check homepage** 查看检查结果；GitHub Pages 的部署完成后刷新网站。

想先检查大改动，可以在保存时选择 **Create a new branch for this commit and start a pull request**。检查通过、核对修改后，再合并到 `master`。

YAML 使用空格缩进，不使用 Tab。时间范围建议加英文引号，例如 `period: "2025 – PRESENT"`；含英文冒号的标题也加引号。修改前后的差别可在 **Preview changes** 或提交的 **Files changed** 中查看。

## 修改或添加论文

打开 `_publications/` 中对应文件。顶部两条 `---` 之间是信息，下面是论文的一句话介绍。

| 字段 | 作用 |
| --- | --- |
| `key` | 唯一标识，例如 `legend`；首页精选通过它找到论文 |
| `title` | 完整论文题目 |
| `year`、`venue`、`abbr` | 年份、完整会议/期刊信息、左侧短标签 |
| `category` | 分类 key，目前为 `llm`、`graph`、`science`、`data`、`vision` |
| `sort_order` | 分类内顺序，数字小的排在前面；可使用负数将新文章置顶 |
| `authors` | 完整作者名单，按论文顺序，每行一位 |
| `paper_url` | 统一的 **PAPER** 按钮和标题跳转地址 |
| `resources` | 额外的 **CODE**、**DATA** 或项目链接；没有则写 `[]` |
| `equal` | 共同一作名单，姓名与作者列表一致，对应 `*`；没有则删掉此字段 |
| `corresponding` | 通讯作者名单，对应 `†`；没有则删掉此字段 |
| `role` | 贡献身份说明，例如 `Research guidance and student mentoring` |
| `contribution` | 具体做了什么；普通句子，不写在作者符号里 |
| `note` | 个人说明，例如对 DPO 理论工作的偏爱；可选 |
| `scholar_id` | Scholar 单篇文章完整 ID；默认 `null`，更新器用完整标题精确匹配 |

添加论文时，最方便的方法是复制相近的一篇到新文件，例如 `_publications/new-paper.md`，然后依次替换上表字段和正文。把 `key` 改成新的唯一值，删除不适用的贡献字段。保留 `layout: profile-paper`。

想让它同时出现在首页，在 `_data/profile.yml` 的 `selected_papers` 中增加这个 key。它也会自动出现在 Publications 对应分类中。

添加新分类时，先在 `_data/publication_groups.yml` 增加一个条目，再把论文的 `category` 设为这个条目的 `key`。分类顺序由配置列表决定，论文顺序由 `sort_order` 决定。

## 修改经历和服务

在 `_data/cv.yml` 复制一整段研究经历，修改 `period`、`role`、`institution`、`short_institution`、`department`、`focus` 和 `advisor`。`research_experience` 同时供 About 和 CV 使用，交换时间只需要改一次。

在 `_data/services.yml` 对应分组的 `entries` 下复制一个条目，修改 `period`、`title`、`description`。可选的 `venue` 用于显示会议名称。需要增加一个分组时，复制整个 `heading` 与其 `entries`。

在 `_data/people.yml` 增加 `姓名: https://个人主页地址`，该姓名在论文作者列表中会自动变成链接。About 正文中可以使用：

```liquid
{% include profile/person.html name="Wenqiang Lei" %}
```

## 引用量和访客地图

- **引用来源**：Google Scholar。工作流计划每天北京时间 08:17 刷新，页面显示最近一次成功取得的缓存，不是每次打开网页时抓取。
- **手动刷新**：Actions → **Refresh publication citations** → **Run workflow**。自动任务首次成功前，按钮显示 `CITED BY —`。被限流、出现验证页、解析失败或未匹配的文章，会保留原有数据；不会把缺失值写成 0。
- **匹配方式**：默认使用完整标题。Scholar 上标题不一致时，可以填写 `scholar_id`，即该论文 Scholar 链接中的 `citation_for_view` 参数值，例如 `用户ID:文章ID`。
- **数据文件**：`_data/citations.yml` 自动维护。成功后工作流提交缓存，并显式请求 GitHub Pages 重建。
- **访客地图**：沿用原站 MapMyVisitors 的脚本和标识，保留原统计记录。配置在 `_data/profile.yml` 的 `visitor_script_url` 和 `visitor_statistics_url`，保留原值即可。

引用工作流适配当前从 `master` 根目录发布的 GitHub Pages。如果以后主动改用自定义 Actions 部署，需要相应调整引用更新后的发布步骤。

## 调整字体和颜色

打开 `assets/css/profile.css`，顶部 `#duanyu-folio` 中：

- `--folio-bg`：整页背景，目前 `light-dark(#f5f5f5,#1c1c1d)`。
- `--folio-surface`：内容方块，目前 `light-dark(#ffffff,#252526)`。
- `--folio-primary`：链接强调色；`--folio-tag`：会议标签颜色。
- `font-family`、`font-size`、`font-weight`：字体、正文大小、字重。

`light-dark(浅色值,深色值)` 的两个值分别对应浅色与深色模式。顶部导航、页面外侧和页脚共用同一个背景值。

## 回退

这次改版前的原版提交为：

[`98b6c4a63bf308a62b3e4dd061e5900658348120`](https://github.com/colfeng/colfeng.github.io/commit/98b6c4a63bf308a62b3e4dd061e5900658348120)

只改错一处文字时，打开该文件的 **History**，查看修改前的版本，把对应内容复制回去并重新提交即可。

撤销整次改版时，优先打开本次改版的已合并 Pull Request，点击 **Revert**，创建并合并回退 PR。GitHub Pages 会重新部署；Git 历史仍保留新版，之后还可以重新应用。

如果需要精确恢复到上述原版快照，可以在本地仓库执行以下命令，先创建恢复分支，再提交 PR：

```bash
git switch master
git pull --ff-only
git switch -c restore/pre-redesign
git restore --source=98b6c4a63bf308a62b3e4dd061e5900658348120 --staged --worktree -- .
git commit -m "Restore homepage before redesign"
git push -u origin restore/pre-redesign
```

快照恢复会让网站文件回到那个时间点。若发布后又增加了论文或改过文字，恢复前先在分支中保留这些内容，或在回退后重新添加。整个过程不需要强制推送。

## 本地预览与检查

已安装 Ruby、Bundler 和 Python 后，在仓库目录运行：

```bash
bundle install
python -m pip install PyYAML
python scripts/validate_content.py
bundle exec jekyll build --safe
python scripts/validate_content.py
bundle exec jekyll serve
```

打开命令输出的本地地址。校验会检查论文 key、分类、作者符号、链接配置，以及构建后的站内链接。

原项目基于 [Academic Pages](https://academicpages.github.io/)，保留原模板文件及许可证；当前四个页面使用独立的 profile 模板。
