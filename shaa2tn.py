"""
shaa2tn.py - convert a Shaarli HTML export to a Trilium Notes
markdown.tar import.

Terry N. Brown terrynbrown@gmail.com Tue Aug 27 19:21:47 CDT 2019
"""

import argparse
import json
import os
import random
import tarfile
import xml.etree.ElementTree as ET

# used to generate Trilium node IDs
ID_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def make_parser():
    """Prepare an argument parser"""
    parser = argparse.ArgumentParser(
        description="""convert a Shaarli HTML export to a Trilium Notes
        markdown.tar import.""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("shaarli", help="The shaarli file to process")
    parser.add_argument("trilium", help="Trilium output file")

    return parser


def get_options(args=None):
    """
    get_options - use argparse to parse args, and return a
    argparse.Namespace, possibly with some changes / expansions /
    validatations.

    Client code should call this method with args as per sys.argv[1:],
    rather than calling make_parser() directly.

    Args:
        args ([str]): arguments to parse

    Returns:
        argparse.Namespace: options with modifications / validations
    """
    opt = make_parser().parse_args(args)

    # modifications / validations go here

    return opt


def strike_through(text):
    """Replace ~~foo~~ with <s>foo</s> to support strike-through in output"""
    text = text.split('\n')
    for line_i, line in enumerate(text):
        if '~~' not in line:
            continue
        line = line.split('~~')
        parts = []
        for part_i, part in enumerate(line):
            if part_i % 2 == 0:
                parts.append(part)
            else:
                parts.append("<s>%s</s>" % part)
        text[line_i] = ''.join(parts)
    return '\n'.join(text)


def get_bookmarks(htmlpath):
    """Read Shaarli .html database export"""
    dom = ET.parse(htmlpath)
    # filter out a couple of empty <p/>s
    dlist = [i for i in dom.findall('.//dl/*') if i.tag in ('dt', 'dd')]

    # An error in Shaarli export of bodyless (no dd) links:
    # <dt link 1 stuff><dt link 2 stuff></dt></dt><dd>link 2 stuff</dd>
    # instead of
    # <dt link 1 stuff></dt><dt link 2 stuff></dt><dd>link 2 stuff</dd>
    # this digs all the buried <dt>s out
    dlist2 = []
    for ele in dlist:
        dlist2.append(ele)
        dlist2.extend(ele.findall(".//dt"))
    dlist = dlist2

    bookmarks = []
    while dlist:
        title = dlist.pop(0)
        assert title.tag == 'dt', title.tag
        title = title.find('a')
        body = dlist.pop(0).text if dlist and dlist[0].tag == 'dd' else ""
        if title.get('href', '').startswith('?'):
            href = None  # a Shaarli note with no link
        else:
            href = title.get('href')
            body = ("[link](%s)\n\n%s" % (href, body)).strip()
        body = strike_through(body)
        bookmarks.append(
            {
                'title': title.text,
                'tags': title.get('tags', "").split(','),
                'body': body,
                'add_date': title.get('add_date'),
                'href': href,
            }
        )
        if title.get('private'):
            bookmarks[-1]['tags'].append("shaarli_private")
        bookmarks[-1]['tags'].append("shaarli_import")

    return bookmarks


def make_node_id():
    return ''.join(random.choices(ID_CHARS, k=12))


def write_bookmarks(tarname, bookmarks):
    """writes metadata and .md files to folder and creates .tar"""
    tardir = tarname + '.d'
    rootdir = os.path.join(tardir, 'ImportRoot')
    os.makedirs(rootdir)  # fail if exists, avoid accidental overwrite
    files = []  # list of metadata dicts for files in archive
    outputs = []  # list of (filesystem-path, archive-name) pairs

    for bookmark_i, bookmark in enumerate(bookmarks):
        attrs = []
        for attr_i, tag in enumerate(bookmark['tags'] or []):
            attrs.append(
                {
                    "type": "label",
                    "name": "tag",
                    "value": tag,
                    "isInheritable": False,
                    "position": attr_i + 1,
                }
            )
        attrs.append(
            {
                "type": "label",
                "name": "shaarli_date",
                "value": bookmark['add_date'],
                "isInheritable": False,
                "position": len(attrs) + 1,
            }
        )
        files.append(
            {
                "isClone": False,
                "noteId": make_node_id(),
                "title": bookmark['title'],
                "notePosition": bookmark_i,
                "prefix": None,
                "isExpanded": 1,
                "type": "text",
                "mime": "text/html",
                "attributes": attrs,
                "links": [],
                "format": "markdown",
            }
        )
        if bookmark['body']:
            datafile = "md%07d.md" % bookmark_i
            files[-1]['dataFileName'] = datafile
            datapath = os.path.join(rootdir, datafile)
            outputs.append((datapath, datafile))
            with open(datapath, 'w') as out:
                out.write(bookmark['body'])

    root = {
        "isClone": False,
        "noteId": make_node_id(),
        "title": "Import root",
        "notePosition": 0,
        "prefix": None,
        "isExpanded": 1,
        "type": "text",
        "mime": "text/html",
        "attributes": [],
        "links": [],
        "format": "markdown",
        "dirFileName": "ImportRoot",
        "children": files,
    }
    data = {"formatVersion": 1, "appVersion": "0.34.3", "files": [root]}
    metafile = os.path.join(tardir, '!!!meta.json')
    json.dump(data, open(metafile, 'w'), indent='\t')
    tar = tarfile.open(tarname, mode='w')
    tar.add(metafile, '!!!meta.json')
    tar.add(rootdir, "ImportRoot/")  # add the directory by itself
    for path, name in outputs:
        # add the files
        tar.add(path, "ImportRoot/%s" % name)
    tar.close()


def main():
    opt = get_options()
    if not os.path.exists(opt.shaarli):
        html = opt.shaarli + '.html'
        if os.path.exists(html):
            opt.shaarli = html
    if not os.path.exists(opt.shaarli):
        print("Can't find '%s'" % opt.shaarli)
        exit(10)
    if not opt.trilium.lower().endswith('.tar'):
        opt.trilium += '.tar'
    bookmarks = get_bookmarks(opt.shaarli)
    write_bookmarks(opt.trilium, bookmarks)


if __name__ == "__main__":
    main()
