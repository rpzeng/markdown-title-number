给markdown文件的标题添加或删除序号

Install

```vim
Plug 'rpzeng/markdown-title-number'
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
```