给markdown文件的标题添加或删除序号

Install

```vim
Plug 'https://gitee.com/zengrp/markdown-title-number.git'
```

command：

```vim
:MarkdownTitleNumberAdd
:MarkdownTitleNumberRemove
:MarkdownTocAdd
:MarkdownTocRemove
:MarkdownTocUpdate
```

option:

```vim
let g:toc_title_level = [1, 2, 3]  "1: #，2: ##，...
let g:auto_update_markdown_title_number_on_save = 1 (default:0)
```
