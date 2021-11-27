# nrsyed.com

This repo contains posts and files from my blog at https://nrsyed.com. The
site is generated using Hugo.

# Hugo

## Installation

The site is currently built using Hugo v0.81.0-DEV/extended.

1. Install [Go &ge; 1.11](https://golang.org/doc/install). Add user go bin
directory to path: `export PATH=$PATH:$HOME/go/bin`.

For the SASS/SCSS support required to build the site correctly, use
Hugo Extended.

```
git clone git@github.com:gohugoio/hugo.git
cd hugo
git checkout v0.81.0
go install --tags extended
```

# Building

The script `sitetools.py` is used to build the site.

```
python sitetools.py \
  build \
  -s /path/to/secrets \
  -o /path/to/public_html \
  --isso-src isso.cfg.nosecrets \
  --isso-dst isso.cfg
```
