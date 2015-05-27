#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: lonewolf
# Date: 2015-05-25 21:06:25
#
import os.path
import optparse
import builder


def run():
    parser = optparse.OptionParser()
    parser.add_option("-d", "--dir", dest="dir", help="指定目录位置")
    (options, args) = parser.parse_args()
    dir1 = options.dir
    if dir1 is None:
        parser.print_help()
        return
    elif not os.path.exists(dir1):
        print("Error: 指定目录不存在")
        print("")
        parser.print_help()
        return
    else:
        post = os.path.join(dir1, "_post")
        if not os.path.exists(post):
            print("Error: _post目录不存在")
            print("")
            parser.print_help()
            return

    root = dir1
    builder.build_wiki(root)


if __name__ == '__main__':
    run()
