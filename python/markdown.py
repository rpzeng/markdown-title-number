# -*- coding: utf-8 -*-

import re
import os
from collections import defaultdict


class SkipLevelError(Exception):
    pass


class OutMaxLevelError(Exception):
    pass


class TitleNumber:
    """计算标题行的序号

    get_title_number = TitleNumber()
    计算序号的方法就是调用一次 `get_title_number()` 以获取标题编号。
    比如:
    找到一级标题，调用 `get_title_number(1)--> '1'`
    找到一级标题，调用 `get_title_number(1)--> '2'`
    找到二级标题，调用 `get_title_number(2)--> '2.1'`
    找到二级标题，调用 `get_title_number(2)--> '2.2'`
    找到三级标题，调用 `get_title_number(3)--> '2.2.1'`
    找到三级标题，调用 `get_title_number(3)--> '2.2.2'`
    找到二级标题，调用 `get_title_number(2)--> '2.3'`
    找到三级标题，调用 `get_title_number(3)--> '2.3.1'`

    如果文本标题最高级为比如2级，那么就把 ## 当做一级标题，### 做二级... 来编号
    """

    def __init__(self):
        self.number_dict = defaultdict(int)

    def _check_skip_level(self, title_level):
        """判断标题是否越级了，比如前一个是一级标题，下一个就来了一个三级标题"""
        return title_level > 1 and self.number_dict[title_level-1] == 0

    def _update_number_dict(self, title_level: int):
        """title_level级标题序号+1，所有更低级标题序号归零"""
        def zero_all_lower_level_title(title_level):
            self.number_dict[title_level] = 0
            if title_level+1 in self.number_dict.keys():
                zero_all_lower_level_title(title_level+1)

        self.number_dict[title_level] += 1
        zero_all_lower_level_title(title_level+1)

    def __call__(self, title_level: int):
        """
        :param title_level: 代表找到一个 title_level 级标题
        :type  title_level: int
        """
        if not hasattr(self, "max_title_level"):
            self.max_title_level = title_level
        title_level = title_level - self.max_title_level + 1
        if title_level < 1:
            raise OutMaxLevelError(f"标题级别错误，文本标题最高级为 {self.max_title_level} 级")

        if self._check_skip_level(title_level):
            raise SkipLevelError("标题越级了")
        self._update_number_dict(title_level)
        return '.'.join(
            [str(self.number_dict[i]) for i in range(1, title_level+1)]
        )


class FindTitle:
    """判断传入的行是否是标题行

    作用是给类对象传入一行，返回一个数字，0代表非标题行，其他代表（比如2）
    相应级别的标题（2级标题##）

    除了判断行内是否存在标题标志(#)以外，还需要考虑排除代码块内的行，
    比如python代码块内的注释会以#号开头, 跟标题混淆。

    markdown 代码块的语法有两种：
    1. 一个空行开始或标题行开始，之后每行前面一个制表符或者四个空格起始。
    2. 由反三引号 ``` 包裹
    """

    def __init__(self):
        self.state = self.state_nomal
        self.preview_line_is_empty = True
        # 缩进格式代码块在紧跟标题行可以不需要空行
        self.preview_line_is_title = False

        # <<<<< 以下是一些用于行内检索的正则表达式
        # 检索标题符 ##
        self.r_title = re.compile(r"^\s*(?P<sign>#+).+")
        # 判断空行或者仅包含空白符的行
        self.r_not_empty = re.compile(r"\S+")
        # 判断缩进格式的代码块
        self.r_code_block_indent = re.compile(
            r"^(?:[ ]{4}|(?:[ ]{,3}\t))(?=\s*\S+)")
        # 判断反引号格式的代码块
        self.r_code_block_quate_start = re.compile(r"^\s*```[^`]*")
        self.r_code_block_quate_end = re.compile(r"^\s*```[^`\S]*")

    def _check_title_line(self, line: str):
        """判断 line 是否是标题行

        如果是标题行，返回标题级别(int)，否则返回0
        """
        capture = self.r_title.search(line)
        if capture is None:
            self.preview_line_is_title = False
            return 0  # 非标题行
        sign = capture.group("sign")
        return len(sign)  # 返回标题级别

    def state_code_block_indent(self, line: str):
        """缩进格式的代码块状态

        这个状态下的任务是判断传进来的行是否是缩进代码行，否的话就转换到 normal 状态，
        并且还要在 normal 状态下分析。
        """
        capture = self.r_code_block_indent.search(line)
        if capture is not None:
            return 0

        # 到这里缩进代码块结束了，本行不属于代码块，转换到 normal 状态
        self.state = self.state_nomal
        # ！line 可以是标题行，或者三引号标记的代码块开始，所以要下一步
        # 放心，此行不会从normal状态又转回来造成死循环
        return self.state(line)

    def state_code_block_backquote(self, line: str):
        """以反三引号标记的代码块状态

        这个状态下的任务是找到代码块结束的标志，并把状态转换到 normal 模式
        """
        capture = self.r_code_block_quate_end.search(line)
        if capture is None:
            return 0
        # 到这里说明 line 是反三引号代码块的结束符，转换到 normal 模式
        self.state = self.state_nomal
        return 0

    def state_nomal(self, line: str):
        """普通状态

        此状态下的任务是判断:
        是否是标题行，是否要转换到其他模式，并负责按需转换到其他模式
        """
        # 判断缩进格式代码块
        if self.preview_line_is_empty or self.preview_line_is_title:
            self.preview_line_is_empty = False
            capture = self.r_code_block_indent.search(line)
            if capture is not None:  # 表示该行是缩进格式的代码块行
                self.state = self.state_code_block_indent
                return 0

        # 判断是否是反引号包括的代码块
        capture = self.r_code_block_quate_start.search(line)
        if capture is not None:
            self.state = self.state_code_block_backquote
            return 0
        # 判断是否是标题行
        title_level = self._check_title_line(line)
        if title_level > 0:  # 找到标题
            self.preview_line_is_title = True
            return title_level
        # 到这里说明line 就一普通行
        self.preview_line_is_title = False
        return 0

    def __call__(self, line):
        if self.r_not_empty.search(line) is None:  # line 是空行
            if self.state == self.state_nomal:
                self.preview_line_is_empty = True
            return 0
        return self.state(line)


class EditTitle:
    def __init__(self):
        """
        :param toc_title_level: 限制加入目录的标题级别，1 代表 #，2 代表 ##
        :type  toc_title_level: list
        """
        toc_title_level = vim.eval("g:toc_title_level")
        if toc_title_level:
            toc_title_level = [int(i) for i in toc_title_level]
        self.toc_title_level = toc_title_level

        self.r_title_content = re.compile(r"#+(?P<title>.+)")
        self.r_sign_number = re.compile(r"(?P<sign>#+)\s+[\d.]*\s*")
        self.r_is_toc_line = re.compile(
            r"\s*\* \[(?P<title>.+)\]\((?P<ref>.+)\)")
        self._get_all_title_lines()

    def get_title_ref_GFM(self, title_content):
        """
        规则：小圆点省略，空格换成-
        """
        ref = '#' + title_content.lower().replace(' ', '-').replace('.', '')
        return title_content, ref

    def _get_all_title_lines(self):
        "获取所有标题行，并保存标题行号、级别、序号、内容、目录索引"
        find_title = FindTitle()
        get_title_number = TitleNumber()
        self.buffer = vim.current.buffer
        try:
            self.found_title = []
            ref_set = set()
            for i, line in enumerate(self.buffer):
                title_level = find_title(line)
                if title_level > 0:
                    title_content = self.r_title_content.search(
                        line).group("title").strip()
                    title, title_ref = self.get_title_ref_GFM(title_content)

                    ####### 需要的话给标题索引 title_ref 添加后缀 #################
                    ####### 两个索引名一样的话需要添加后缀加以区别 ################
                    n = 1
                    title_ref_tmp = title_ref
                    while title_ref_tmp in ref_set:
                        title_ref_tmp = title_ref + ('-' + str(n))
                        n += 1
                    ref_set.add(title_ref_tmp)
                    title_ref = title_ref_tmp
                    ###############   添加后缀结束   #######################

                    title_number = get_title_number(title_level)  # 标题序号
                    title_level_relative = title_level - get_title_number.max_title_level + 1

                    self.found_title.append({
                        'line_num': i,
                        'title_level': title_level,
                        'title_level_relative': title_level_relative,
                        'title_number': title_number,
                        'title': title,
                        'title_ref': title_ref,
                    })
        except SkipLevelError as e:
            print(f"line：{i+1}, ", e)
            raise
        except OutMaxLevelError as e:
            print(f"line：{i+1}, ", e)
            raise

    def add_title_number(self):
        for t in self.found_title:
            line = self.buffer[t['line_num']]
            line_with_title_num = self.r_sign_number.sub(
                lambda m: f"{m.group('sign')} {t['title_number']} ",
                line, count=1)
            self.buffer[t['line_num']] = line_with_title_num
        toc_old_start, toc_old_end = self._find_old_toc()
        if toc_old_start is not None:  # 找到目录了
            self._get_all_title_lines()
            self.update_toc()

    def remove_title_number(self):
        for t in self.found_title:
            line = self.buffer[t['line_num']]
            line_with_title_num = self.r_sign_number.sub(
                lambda m: f"{m.group('sign')} ",
                line, count=1)
            self.buffer[t['line_num']] = line_with_title_num
        toc_old_start, toc_old_end = self._find_old_toc()
        if toc_old_start is not None:  # 找到目录了
            self._get_all_title_lines()
            self.update_toc()

    def _get_toc(self):
        def indent(title_level):
            return ' ' * (title_level-1) * 4

        toc = []
        for t in self.found_title:
            title = t['title']  # 标题行中 ## 标志后的内容经过 strip()
            ref = t['title_ref']
            i = t['title_level_relative']
            if self.toc_title_level and i not in self.toc_title_level:
                continue
            toc.append(f"{indent(i)}* [{title}]({ref})")
        return toc

    def add_toc(self):
        toc = self._get_toc()
        win_obj = vim.current.window
        cursor_line = win_obj.cursor[0]-1
        self.buffer.append(toc, cursor_line)

    def _is_toc_line(self, line):
        capture = self.r_is_toc_line.match(line)
        if capture is not None:
            title, ref = capture['title'], capture['ref']
            title_, ref_ = self.get_title_ref_GFM(title)
            if ref_ in ref:
                return True
        return False

    def _find_old_toc(self):
        toc_old_start, toc_old_end = None, None
        try:
            for i, line in enumerate(self.buffer):
                if self._is_toc_line(line):
                    if toc_old_start is None:
                        toc_old_start = i
                elif toc_old_start is not None:
                    raise IndexError
            if toc_old_start is not None:  # 最后一行也是toc
                raise IndexError
            raise TypeError
        except IndexError:  # 找到目录
            toc_old_end = i-1
        except TypeError:  # 找不到目录
            pass
        return toc_old_start, toc_old_end

    def update_toc(self):
        toc_old_start, toc_old_end = self._find_old_toc()
        if toc_old_end is not None:  # 找到目录了
            toc = self._get_toc()
            self.buffer[toc_old_start:toc_old_end+1] = toc
        else:
            print('目录找不到或着损坏了')

    def remove_toc(self):
        toc_old_start, toc_old_end = self._find_old_toc()
        if toc_old_end is not None:  # 找到目录了
            self.buffer[toc_old_start:toc_old_end+1] = ['']
        else:
            print('目录找不到或着损坏了')
