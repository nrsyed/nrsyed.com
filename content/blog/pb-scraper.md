---
title: ProBoards forum asynchronous web scraper
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

**Disclaimer: It's against ProBoards's terms of service to scrape content from
a ProBoards forum. This project and blog post are purely for educational
purposes and should not be used to scrape any ProBoards forum or website.**

Although niche forums and message boards certainly still exist, they've
largely fallen out of favor thanks to the rise of social media. This isn't
necessarily a bad thing&mdash;I love Instagram as much as the next
guy&mdash;but there was something almost magical about the ability of those
old personal forums to foster a close-knit community of friends from around
the world that "mega-forums" like Reddit and real-time platforms like Discord
can't quite capture. Part of it might be nostalgia from a time when both I
and the internet were younger, when we AIMed instead of Zoomed, and when the
web had this untamed Wild West quality in which small forums/communities felt
like safe settlements&mdash;places to call "home" on the internet.

Philosophical waxings and wanings aside, I was an administrator on one such
forum, started in 2002, that was hosted by ProBoards, one of many forum hosting
providers. ProBoards is still around today and so is that forum, even
if it hasn't been active in years. Being the sucker for nostalgia and posterity
that I am, I felt it would be nice to have an archived copy of the forum's
content and preserve it forever. I spoke to the founder of said forum, who
agreed with me.

Unfortunately, unlike most of its competitors, ProBoards does not provide any
option, paid or otherwise, for exporting a forum. And, as the disclaimer above
states, scraping a forum violates the ProBoards TOS. Thus, this project is
merely an exercise that demonstrates the use of several Python libraries and
how they might be used for web scraping tasks. Furthermore, ProBoards may
update its site-rendering functionality from time to time, which could break
the ability of any given scraping tool to extract information from a forum.

With that out of the way, let's get to the meat of this post.


<span id="database" />
# Forum structure and SQL database schema

Before we can design a scraper, we must first 1) understand how the
website/forum is organized and 2) decide how to represent this structure
in a SQL database, which is where we're going to store the information
extracted from the scraper.

<span id="pb_forum_schema" />
{{< figure
  src="/img/proboards_scraper/forum_schema.png" alt="Forum structure"
  caption="Forum structure" class="aligncenter"
>}}

A ProBoards forum consists of named categories, visible on the site's homepage.
Categories are simply groups of boards. A board can have moderators,
sub-boards (represented by the loop in the diagram above), and threads. A
moderator is simply a user. A thread contains posts, may optionally have a
poll, and is created by a user (the user that created a thread is usually
the first poster in the thread, but this may not be true 100% of the
time&mdash;for instance, if the first post was deleted by a moderator).
Regarding polls: we can see the poll options (and how many votes each option
has received) and which users have voted in the poll, but it's not possible to
see who voted for which option. Each post in a thread is associated with the
user who made the post.

A forum also contains various images, including post smileys (aka emojis),
the [favicon][3], site background/style elements, and user avatars. In the
diagram above, I've made avatars their own entity, which simply links a user to
the image corresponding to their avatar. This isn't strictly necessary;
rather, it's a design choice.

Some forums may also have a "shoutbox" enabled. This is simply a persistent
chatbox that appears on the homepage. Shoutbox posts are, like normal posts,
associated with the user that made them.

Breaking the site into these elements gives us a roadmap for building the
scraper, as well as the schema for the SQL database. Each element in the
figure above will be a table in the database.

<span id="design" />
# Design and architecture

The figure below illustrates the scraper's architecture and data flow at a
high level.

{{< figure
  src="/img/proboards_scraper/scraper_diagram.png" alt="Scraper architecture"
  caption="Scraper architecture" class="aligncenter"
>}}

Let's start at the right and work our way leftward. I've opted to use SQLite
for the SQL database backend, as opposed to other dialects like MySQL or
PostgreSQL, because it's lightweight and more than sufficient for our needs.
The SQL database schema consists of tables corresponding to the elements
from [the figure in the previous section](#pb_forum_schema). Each of these
tables contains numerous attributes detailed in the
[documentation for the scraper's `database` submodule][4]. For example,
the [Users table][5] includes the user id, age, birthdate, date registered,
email, display name, signature, and other pieces of information that can
be obtained from a user's profile.

{{< figure
  src="/img/proboards_scraper/database_class.png" alt="Database class"
  class="aligncenter"
>}}

The [`Database` class][6] serves as an interface for the SQLite database.
It provides convenient methods for querying the database and/or inserting
objects into the tables described above. This way, the client (user or
calling code) never has to worry about the mechanics of interacting directly
with the database or writing SQL queries. In fact, I also didn't have to
worry about writing SQL queries, because I opted to use [SQLAlchemy][7], an
[ORM][8] that maps a SQL database's schema to Python objects, thereby
abstracting away the SQL and allowing me to write everything in pure Python.
The `Database` class interacts with the SQL database via SQLAlchemy, and the
client code interacts indirectly with the database via the `Database` class,
whose methods return Python objects corresponding to items in the database.

{{< figure
  src="/img/proboards_scraper/scraper_manager_class.png"
  alt="ScraperManager class" class="aligncenter"
>}}

{{< figure
  src="/img/proboards_scraper/scraper_module.png"
  alt="scraper module" class="aligncenter"
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
[3]: https://en.wikipedia.org/wiki/Favicon
[4]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html
[5]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.User
[6]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.Database
[7]: https://www.sqlalchemy.org/
[8]: https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping
