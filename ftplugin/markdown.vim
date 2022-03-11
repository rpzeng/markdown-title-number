if !has('python3')
    echo "Error: Required vim compiled with +python"
    finish
endif

" Only do this when not done yet for this buffer
if exists("b:did_ftplugin_markdown_title_number")
    finish
endif
let b:did_ftplugin_markdown_title_number = 1

if !exists("g:toc_title_level")
    let g:toc_title_level = []
endif

let s:pyfile = expand('<sfile>:p:h:h') . '/python/markdown.py'

execute "py3file " . s:pyfile

command! -buffer MarkdownTitleNumberAdd :py3 EditTitle().add_title_number()
command! -buffer MarkdownTitleNumberRemove :py3 EditTitle().remove_title_number()
command! -buffer MarkdownTocAdd :py3 EditTitle().add_toc()
command! -buffer MarkdownTocRemove :py3 EditTitle().remove_toc()
command! -buffer MarkdownTocUpdate :py3 EditTitle().update_toc()
