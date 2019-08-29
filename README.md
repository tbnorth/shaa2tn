# shaa2tn.py

Export [Shaarli](https://github.com/shaarli/Shaarli) bookmarks / notes
to [Trilium](https://github.com/zadam/trilium) Notes.

Requires Python 3.

Export your Shaarli content to `bookmarks_all_20190829_081031.html`
or similar with Tools -> Export database.  Then:

```shell
python shaa2tn.py bookmarks_all_20190829_081031.html imp.tar
```

will create `imp.tar` and `imp.tar.d`.  `imp.tar.d` is the unpacked content of
`imp.tar`.  `imp.tar` is the file that can be imported into Trilium.  Right
click on a Trilium node and use `Import into node`.

`task ~~done~~` in Shaarli body text will be converted to `task <s>done</s>` to
support strike through in Trilium.

License is CC0 1.0 Universal (CC0 1.0) Public Domain
