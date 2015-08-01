#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: lonewolf
# Date: 2015-05-25 21:06:25
#
import os
import os.path
import json
import codecs
import shutil
import re
import markdown

# 文章和列表模板
_template_article = ""
_template_list = ""

# markdown解析器
_markdown = None

# 根目录
_root = ""

# md文件夹名称
_md_dir = "_post"


# 初始化
def init():
    global _markdown, _template_article, _template_list

    extensions = []
    extensions.append("markdown.extensions.toc")
    extensions.append("markdown.extensions.tables")
    extensions.append("markdown.extensions.footnotes")
    extensions.append("markdown.extensions.fenced_code")
    _markdown = markdown.Markdown(extensions=extensions)

    _template_article = read_file("template_article.html")
    _template_list = read_file("template_list.html")


# 读取文件，UTF-8
def read_file(filepath):
    input_file = codecs.open(filepath, mode="r", encoding="utf-8")
    text = input_file.read()
    input_file.close()
    return text


# 写入文件
def write_file(filepath, content):
    output_file = codecs.open(filepath, mode="w+", encoding="utf-8")
    output_file.write(content)
    output_file.close()


# 解析单个文件
# return node {type:file, title, filename, html}
def build(filepath):
    text = read_file(filepath)
    filename = os.path.split(filepath)[1]
    filename = os.path.splitext(filename)[0]
    # 找出是否有title
    # 配置文件在两个---之间
    title = filename
    # date = ""
    m1 = re.compile("^---")
    m2 = re.compile("^title:(.*)")
    # m3 = re.compile("^date:(.*)")
    arr = text.split("\n")
    if m1.match(arr[0]):
        # 正文
        context = ""
        # 是否已完成头信息
        config_complete = False
        for i in range(1, len(arr)):
            line = arr[i]
            if config_complete:
                context += line+"\n"
                continue
            if m1.match(line):
                config_complete = True
            else:
                p2 = m2.match(line)
                # p3 = m3.match(line)
                if p2:
                    title = p2.group(1)
                # elif p3:
                #     date = p3.group(1)
        text = context

    html = _markdown.convert(text)
    html = _template_article.replace("{{html}}", html)
    html = html.replace("{{toc}}", _markdown.toc)
    return {"root": False, "type": "file", "title": title, "filename": filename, "html": html}


# 解析文件夹
# 返回文件夹结点结构 node
# 节点有两种类型：
# 文件夹 dir {root:False, type:dir, parent, title, filename, children:[]}
# 文件 file {root:False, type:file, parent, title, filename, html}
# 最上层的parent=None
def build_folder(folder):
    # 文件夹名称
    dirname = os.path.split(folder)[1]

    # 结点结构
    node = {"root": False, "type": "dir", "parent": None, "title": dirname,
            "filename": dirname, "children": []}

    # 读取配置信息
    config_path = os.path.join(folder, "config.json")
    if os.path.exists(config_path):
        data = read_file(config_path)
        data = json.loads(data)
        if data["title"]:
            node["title"] = data["title"]

    for item in os.listdir(folder):
        path = os.path.join(folder, item)
        if os.path.isdir(path):
            n = build_folder(path)
            # 加上父类
            n["parent"] = node
            node["children"].append(n)
        elif os.path.isfile(path) and os.path.splitext(item)[1][1:] == "md":
            n = build(path)
            # 加上父类
            n["parent"] = node
            node["children"].append(n)
    return node


# 解析树结构
def analyse_tree(node):
    # 导航条
    nav = generate_nav(node)
    root = get_root(node)
    path = get_write_folder(node)
    path = os.path.join(_root, path)

    html = ""
    # 目录
    if node["type"] == "dir":
        # 先生成文件夹
        if not node["root"] and not os.path.exists(path):
            os.mkdir(path)

        # 生成列表
        text = generate_list(node["children"])
        html = _template_list.replace("{{list}}", text)
        path = os.path.join(path, "index.html")

        # 解析子类
        l = len(node["children"])
        for i in range(0, l):
            analyse_tree(node["children"][i])
    else:
        # 文件
        html = node["html"]
        path = os.path.join(path, node["filename"]+".html")
    html = html.replace("{{title}}", node["title"])
    html = html.replace("{{root}}", root)
    html = html.replace("{{nav}}", nav)
    write_file(path, html)


# 生成列表文本
def generate_list(children):
    text = ""
    l = len(children)
    for i in range(0, l):
        node = children[i]
        if node["type"] == "dir":
            # 目录
            text += '<a href="'+node["filename"] + \
                '/index.html">'+node["title"]+'</a> <br />\r\n'
        else:
            # 文件
            text += '<a href="'+node["filename"] + \
                '.html">'+node["title"]+'</a> <br />\r\n'
    return text


# 生成导航nav
def generate_nav(node):
    nav = ""
    np = node["parent"]
    if np is None:
        return nav

    loc = ""
    if node["type"] == "dir":
        loc = "../"
    p = np
    while p is not None:
        n = ""
        if p["root"]:
            n = '<a href="' + loc +  \
                'index.html">'+p["title"]+'</a> '
        else:
            n = '<a href="'+loc + \
                'index.html">'+p["title"]+'</a> '
        if p != np:
            # 第一个点
            n += " > "
        nav = n+nav
        loc += "../"
        p = p["parent"]
    nav = ' >> '+nav
    return nav


# 获取root ../../../ ...
def get_root(node):
    root = ""
    # 根节点
    if node["root"]:
        return root

    # 目录节点，即index.html，要加上另一个
    if node["type"] == "dir":
        root += "../"

    p = node["parent"]
    while not p["root"]:
        root += "../"
        p = p["parent"]
    return root


# 写入的目录test
def get_write_folder(node):
    path = ""
    # 根节点
    if node["root"]:
        return path

    # 目录节点
    if node["type"] == "dir":
        path = os.path.join(node["filename"], path)

    p = node["parent"]
    while not p["root"]:
        path = os.path.join(p["filename"], path)
        p = p["parent"]
    return path


# 拷贝文件到目标目录
def copy_res():
    source = "wiki_res"
    target = os.path.join(_root, "wiki_res")
    if os.path.exists(target):
        delete_folder(target)
    shutil.copytree(source, target)


# 删除目录或文件
def delete_folder(folder):
    if os.path.isfile(folder):
        try:
            os.remove(folder)
        except:
            pass
    elif os.path.isdir(folder):
        for item in os.listdir(folder):
            itemsrc = os.path.join(folder, item)
            delete_folder(itemsrc)
        try:
            os.rmdir(folder)
        except:
            pass


# 解析项目
# root为项目文件夹
def build_wiki(root):
    global _root
    _root = root

    init()

    # 拷贝文件
    copy_res()

    # 解析整个根目录
    post = os.path.join(_root, _md_dir)
    node = build_folder(post)
    # 第一个节点要改成root
    node["root"] = True
    node["filename"] = ""
    # print(json.dumps(node))

    # 生成文件
    analyse_tree(node)
