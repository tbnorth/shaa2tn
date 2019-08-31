"""
trilium_io.py - write Trilium Notes format tar files.

Terry N. Brown terrynbrown@gmail.com Sat Aug 31 10:46:31 CDT 2019
"""

import json
import os
import random
import tarfile

# used to generate Trilium node IDs
ID_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def make_node_id():
    return ''.join(random.choices(ID_CHARS, k=12))


def node_template(init=None):
    template = {
        'attributes': [],
        'format': "markdown",
        'isClone': False,
        'isExpanded': 0,
        'links': [],
        'mime': "text/html",
        'noteId': make_node_id(),
        'notePosition': 0,
        'prefix': None,
        'title': "NO TITLE",
        'type': "text",
        '_ext': {'tags': []},
    }
    if init is not None:
        template.update(init)
    return template


def attr_template(init=None):
    template = {
        'type': "label",
        'name': "tag",
        'value': "EXAMPLE TAG",
        'isInheritable': False,
        'position': 0,
    }
    if init is not None:
        template.update(init)
    return template


def order_nodes_attrs(items):
    """recursively update node / attribute position"""
    for pos in range(len(items)):
        items[pos]['notePosition'] = pos
        for apos in range(len(items[pos]['attributes'])):
            items[pos]['attributes'][apos]['position'] = apos
            order_nodes_attrs(items[pos].get('children', []))


def write_tar(tarname, items):
    """writes metadata and .md files to folder and creates .tar"""
    tardir = tarname + '.d'
    rootdir = os.path.join(tardir, 'ImportRoot')
    os.makedirs(rootdir)  # fail if exists, avoid accidental overwrite
    files = []  # list of metadata dicts for files in archive
    outputs = []  # list of (filesystem-path, archive-name) pairs

    for item_i, item in enumerate(items):
        attrs = item.setdefault('attrs', [])
        _ext = item.get('_ext', {})
        for tag in _ext.get('tags', []):
            attrs.append(
                attr_template({"type": "label", "name": "tag", "value": tag})
            )
        files.append(node_template(item))
        if '_ext' in files[-1]:
            del files[-1]['_ext']
        if item['_ext'].get('body'):
            datafile = "md%07d.md" % item_i
            files[-1]['dataFileName'] = datafile
            datapath = os.path.join(rootdir, datafile)
            outputs.append((datapath, datafile))
            with open(datapath, 'w') as out:
                out.write(item['_ext']['body'])

    order_nodes_attrs(files)

    # FIXME: could scan for clones by duplicate IDs here

    root = node_template(
        {
            "title": "Import root",
            "dirFileName": "ImportRoot",
            "children": files,
        }
    )
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
