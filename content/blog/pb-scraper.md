---
title: ProBoards Forum Web Scraper
type: post
date: 2021-10-25T23:14:31-04:00
url: /2021/10/25/proboards-forum-web-scraper
categories:
  - Web Scraping
tags:
  - web scraping
  - ProBoards
  - forum
  - HTML
  - Python
  - asyncio
  - selenium
  - BeautifulSoup
  - SQL
  - SQLite
  - SQLAlchemy
---

* [Introduction](#introduction)
* [Design and architecture](#design)
  * [asyncio](#asyncio)
  * [Database](#database)

Link to code: https://github.com/nrsyed/proboards-scraper

<span id="introduction" />
# Introduction

Although niche forums and message boards certainly still exist, they've
largely fallen out of favor with the rise of social media. This isn't
necessarily a bad thing&mdash;I love Instagram as much as the next guy&mdash;
but there was something almost magical about the ability of those old personal
forums to foster a close-knit community of friends from around the world that
"mega-forums" like Reddit can't quite capture. Part of it might be nostalgia
from a time when both I and the internet were younger, when we AIMed instead
of Zoomed, and when the web had this untamed "wild west" quality in which small
forums/communities felt like safe settlements&mdash;places to call one's
home on the internet.

Philosophical waxings and wanings aside, I was an administrator on one such
forum, started in 2002, that was hosted by ProBoards, one of many forum hosting
providers. ProBoards is still around today and that forum still exists, even
if it hasn't been active in years. Being the sucker for nostalgia and posterity
that I am, I thought it would be nice to have an archived copy of the forum
and all its content, preserving it forever.

Unfortunately, unlike most of its competitors, ProBoards does not provide any
option, paid or otherwise, to export a forum. **It's also against ProBoards's
terms of service to scrape content from a ProBoards forum. This project and
blog post are purely for educational purposes and should not be used to
scrape any ProBoards forum or website**. This is an exercise that demonstrates
the use of several Python libraries and how they might hypothetically be used
for web scraping tasks.


<span id="design" />
# Design and architecture

{{< figure
  src="/img/pb_scraper_diagram.png" alt="Scraper architecture"
  caption="Scraper architecture"
>}}

<span id="asyncio" />
### asyncio


<span id="database" />
### Database


[1]: https://realpython.com/async-io-python/
[2]: https://realpython.com/python-gil/
