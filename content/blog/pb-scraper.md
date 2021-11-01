---
title: ProBoards forum web scraper
type: post
date: 2021-10-25T23:14:31-04:00
url: /2021/10/25/proboards-forum-web-scraper
categories:
  - Web Scraping
tags:
  - asyncio
  - BeautifulSoup
  - forum
  - HTML
  - ProBoards
  - Python
  - selenium
  - SQL
  - SQLite
  - SQLAlchemy
  - web scraping
---

* [Introduction](#introduction)
* [Forum structure and SQL database schema](#database)
* [Design and architecture](#design)
  * [asyncio](#asyncio)

**Code: https://github.com/nrsyed/proboards-scraper** <br>
**Documentation: https://nrsyed.github.io/proboards-scraper** 

<span id="introduction" />
# Introduction

Although niche forums and message boards certainly still exist, they've
largely fallen out of favor thanks to the rise of social media. This isn't
necessarily a bad thing&mdash;I love Instagram as much as the next
guy&mdash;but there was something almost magical about the ability of those
old personal forums to foster a close-knit community of friends from around
the world that "mega-forums" like Reddit can't quite capture. Part of it might
be nostalgia from a time when both I and the internet were younger, when we
AIMed instead of Zoomed, and when the web had this untamed Wild West
quality in which small forums/communities felt like safe
settlements&mdash;places to call "home" on the internet.

Philosophical waxings and wanings aside, I was an administrator on one such
forum, started in 2002, that was hosted by ProBoards, one of many forum hosting
providers. ProBoards is still around today and so is that forum, even
if it hasn't been active in years. Being the sucker for nostalgia and posterity
that I am, I thought it would be nice to have an archived copy of the forum
and all its content, preserving it forever.

Unfortunately, unlike most of its competitors, ProBoards does not provide any
option, paid or otherwise, to export a forum. *It's also against ProBoards's
terms of service to scrape content from a ProBoards forum. This project and
blog post are purely for educational purposes and should not actually be used
to scrape any ProBoards forum or website*. This is an exercise that
demonstrates the use of several Python libraries and how they might be used
for web scraping tasks.


<span id="database" />
# Forum structure and SQL database schema

Before we can design a scraper, we must first 1) understand how the
website/forum is organized and 2) decide how to represent this structure
in a SQL database.

{{< figure
  src="/img/pb_forum_schema.png" alt="Forum structure"
  caption="Forum structure"
>}}

A ProBoards forum consists of named categories, visible on the site's homepage.
Categories are simply groups of boards. A board can have moderators,
sub-boards (represented by the loop in the diagram above), and threads. A
moderator is simply a user. A thread contains posts, may optionally have a
poll, and is created by a user (the user that created a thread is usually
the owner of the first post in the thread, but this may not be true 100% of
the time&mdash;for instance, if the first post was deleted by a moderator).
Regarding polls: we can see the poll options (and how many votes each option
has received) and which users have voted in the poll, but it's not possible to
see who voted for which option. Each post is associated with the user who made
the post.


<span id="design" />
# Design and architecture

The figure below illustrates the scraper's architecture at a high level.

{{< figure
  src="/img/pb_scraper_diagram.png" alt="Scraper architecture"
  caption="Scraper architecture"
>}}

<span id="asyncio" />
### asyncio

Because a forum comprises hundreds of pages (boards, users, threads with
multiple pages, etc.), some form of concurrency is necessary to scrape the
site efficiently. We have a few options in Python&mdash;namely `threading`,
`multiprocessing`, `concurrent.futures` (which is mostly a higher-level
wrapper/abstraction around `threading` and `multiprocessing`), and `asyncio`.
In Python, all programs that don't use `multiprocessing` (or call a library
that uses multiple CPU cores) run on a single core. Furthermore, because of the
[GIL][2] (global interpreter lock), for which Python is infamous, even in
multithreaded programs, only a single thread can be run at a time.
Consequently, multithreading is good for I/O-bound (input/output&ndash;bound)
tasks, like downloading files and reading to or writing from a database,
since they are *non-blocking* (i.e., the Python interpreter can do other
things while waiting for those tasks to finish). On the other hand,
multiprocessing is preferable for CPU-bound tasks, which are *blocking* and
actively require the CPU to be doing work (e.g., processing data and
performing computations).

The [asyncio module][1] is interesting in that it's inherently single-threaded,
but "gives a feeling of concurrency", as the aforelinked article puts it,
because it allows I/O-bound tasks, like grabbing a webpage, to run in the
background until they're complete, and schedule other tasks in the meantime,
which, similarly, the Python interpreter can switch to or step away from as
necessary).


[1]: https://realpython.com/async-io-python/
[2]: https://realpython.com/python-gil/
