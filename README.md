# nrsyed.com

Posts and files from my blog at https://nrsyed.com

## Hugo

### Installation

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
