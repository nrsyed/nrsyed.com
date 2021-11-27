---
title: Asynchronously web scraping a ProBoards forum with Python (part 1)
author: Najam Syed
type: post
date: 2021-11-26T12:00:00-04:00
url: /2021/11/26/asynchronously-web-scraping-a-proboards-forum-with-python-part-1
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

{{< figure
  src="/img/proboards_scraper/overall_diagram.png"
  alt="ProBoards forum scraper" class="aligncenter"
>}}

**Code: https://github.com/nrsyed/proboards-scraper** <br>
**Documentation: https://nrsyed.github.io/proboards-scraper**

* **Part 1: Introduction and background**
  * *[Introduction](#introduction)*
  * *[Forum structure and SQL database schema](#forum_structure)*
  * *[Using asyncio for asynchronous scraping](#asyncio)*
  * *[Design and architecture](#architecture)*
* [Part 2: Implementation (project structure and scraper initialization)][0]
* [Part 3: Implementation (scraper internals)][1]

<span id="introduction" />
# Introduction

**Disclaimer: It's against ProBoards's terms of service (TOS) to scrape
content from a ProBoards forum. This project and blog post are purely for
educational purposes and should not be used to scrape any ProBoards forum or
website.**

Though niche forums still exist, they've largely been supplanted by social
media. This isn't necessarily a bad thing&mdash;I love Instagram as much as
the next guy&mdash;but there was something magical, something intangible about
those personal forums of old, and their ability to foster a close-knit
community of friends from around the world that "mega-forums" like Reddit and
real-time platforms like Discord can't quite capture. Some of that
*je ne sais quois* might be the product of nostalgia from a time when both I
and the internet were younger, when we AIMed instead of Zoomed, when the
web felt like an untamed wild west and small forums were safe
settlements&mdash;places to call "home" in the virtual world.

Philosophical waxings and wanings aside, back in the early 2000s, I was an
administrator on one such forum hosted by ProBoards, one of the more popular
forum hosting providers at the time. ProBoards is still around today and so is
that forum, even if it hasn't been active in years. I'm a sucker for nostalgia
and felt it would be nice to archive the forum's content, preserving it
forever. The founder and owner of that forum, a close friend of mine, agreed.

Unfortunately, unlike most of its competitors, ProBoards doesn't provide an
option, paid or otherwise, for exporting a forum. And, as the disclaimer above
states, scraping a forum violates the ProBoards TOS. Thus, this project is
merely an exercise that demonstrates the use of several Python libraries and
how they might be used for web scraping tasks. Furthermore, ProBoards may
introduce changes to its platform that would break any tool designed to scrape
its forums.

That said, let's examine how we might hypothetically go about such a task.
Part 1 (this post) lays the foundation for the scraper and its design.
Parts 2 and 3 take a deep dive into the codebase to see how it works in
practice.

<span id="forum_structure" />
# Forum structure and SQL database schema

Before we can design a scraper, we must first 1) understand how a
forum is organized and 2) decide how to represent this structure
in a SQL database, which is where we're going to store the information
extracted by the scraper.

I won't provide a link to an actual ProBoards forum in this post, but there is
a [directory of all ProBoards forums][2] you can peruse for yourself.

<span id="forum_schema_img" />
{{< figure
  src="/img/proboards_scraper/forum_schema.png" alt="Forum structure"
  caption="Forum structure" class="aligncenter"
>}}

A ProBoards forum consists of named categories, visible on the forum homepage.
A category is simply a group of boards. A board can have moderators,
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

<span id="asyncio" />
# Using asyncio for asynchronous scraping

Since a forum can comprise tens or hundreds of thousands of pages (user
profiles, boards, a whole lot of threads with multiple pages, etc.), some
form of concurrency or parallelism is necessary to scrape the site
efficiently. We have a few options: 1) multithreading, 2) multiprocessing,
and 3) asynchronous programming.

A Python process runs on a single core, and because of Python's [GIL][4]
(global interpreter lock), even multithreaded programs can only execute one
thread at a time (unless the program uses a library that bypasses the GIL,
like numpy). A Python program that uses the [multiprocessing module][5]
can run on multiple cores, though each process has the same limitation.
Because a process can only execute one thread at a time, multithreading is
suited for I/O-bound (input/output&ndash;bound) tasks, like making HTTP
requests or reading/writing files, since they are *non-blocking* (i.e., they
involve waiting for something to finish happening, allowing the Python
interpreter to do other things in the meantime). On the other hand,
multiprocessing is preferable for CPU-bound tasks, which are *blocking* and
actively require the CPU to be doing work (e.g., performing computations).

Then there's option 3: asynchronous programming via the [asyncio module][6],
which is single-threaded but "gives a feeling of concurrency," as the
aforelinked article puts it, because it allows I/O-bound tasks to run in the
background while performing other tasks, which the Python interpreter can
switch to or step away from as necessary. This is similar to Python
multithreading except that, with asyncio, *you* tell the program when to step
away from a task using the `await` keyword. In a multithreaded program, on the
other hand, it's up to the Python interpreter to determine how to schedule
different threads. Spawning threads also comes with overhead, which can make
multithreading less performant than asyncio.

I'm of the opinion that, in Python, one should use asyncio instead of
multithreading whenever possible. Naturally, asyncio has its limitations
and multithreading certainly has its place. However, we can get away with using
asyncio instead of multithreading for a web scraper.

Not all I/O operations are [*awaitable*][7] by default in Python's asyncio
module. That includes making HTTP requests and reading/writing files. Luckily,
the [aiohttp][8] and [aiofiles][9] libraries, respectively, fill these gaps.
Although database read/write operations fall into the same category, SQLAlchemy
doesn't support asyncio at the moment. However, SQLAlchemy support for asyncio
is [in development and currently a beta feature][10]. This is a relatively
recent development that wasn't available when I originally created this
project, but it doesn't really matter. The amount of time database
I/O takes is negligible compared to the amount of time taken by HTTP
requests&mdash;which comprise the bulk of the scraper's work&mdash;and the
aiohttp library already addresses that.

<span id="architecture" />
# Design and architecture

The figure below illustrates the scraper's architecture and data flow at a
high level.

{{< figure
  src="/img/proboards_scraper/scraper_diagram.png" alt="Scraper architecture"
  caption="Scraper architecture" class="aligncenter"
>}}

Let's start at the right and work our way leftward.

<span id="sqlite_database" />
### SQLite database

{{< figure
  src="/img/proboards_scraper/database_expanded.png" alt="SQLite database"
  class="aligncenter"
>}}

I used SQLite for the SQL database backend, as opposed to other dialects like
MySQL or PostgreSQL, because it's lightweight and more than sufficient for
our needs. A SQLite database is just a single file on disk.

The SQL database schema consists of tables corresponding to the elements
from [the figure in the previous section](#forum_schema_img). Each of these
tables contains numerous attributes detailed in the
[documentation for the scraper's database submodule][11]. For example,
the [Users table][12] includes the user id, age, birthdate, date registered,
email, display name, signature, and other pieces of information that can
be obtained from a user's profile.

<span id="database_class" />
## Database class

{{< figure
  src="/img/proboards_scraper/database_class.png" alt="Database class"
  class="aligncenter"
>}}

The [Database class][13] serves as an interface for the SQLite database.
It provides convenient methods for querying the database and/or inserting
objects into the tables described above. This way, the client (user or
calling code) never has to worry about the mechanics of interacting directly
with the database or writing SQL queries. In fact, I also didn't have to
worry about writing SQL queries because I used [SQLAlchemy][14], an
[ORM][15] that maps a SQL database's schema to Python objects, thereby
abstracting away the SQL and allowing me to write everything in pure Python.
The Database class interacts with the SQL database via SQLAlchemy, and the
client code interacts indirectly with the database via the Database class,
whose methods return Python objects corresponding to items in the database.

<span id="scrapermanager_class" />
### ScraperManager class

{{< figure
  src="/img/proboards_scraper/scraper_manager_class.png"
  alt="ScraperManager class" class="aligncenter"
>}}

The [ScraperManager class][16] has a few purposes:

1. Asynchronously handles all HTTP requests and adds delays between requests
as needed to prevent request throttling by the server.
2. Holds references to the Database class instance, as well as to the
`aiohttp` and Selenium Chromedriver session objects
(which are used for making HTTP requests).
3. Acts as an intermediary between the core scraper functions (which
actually parse HTML, deciding which links/pages to grab, etc.) and the
database, determining which Database methods need to be called to insert
items from the queues into the database.

#3 is mainly handled by the [run() method][17], which continuously reads from
two queues: a "users" queue and a "content" queue. Recall from the
[forum structure diagram](#forum_schema_img) above that many elements are
associated with users. Therefore, it makes sense to add all the site's members
to the database, *then* add all other content. Because the site is scraped
asynchronously, the scraper might be concurrently scraping/parsing both user
profiles&mdash;which it adds to the users queue&mdash;and other content
(boards, threads, posts, etc.), which it adds to the content queue. run()
ensures that all users from the users queue are consumed and added to the
database *before* it begins popping and processing items from the content
queue.

<span id="scraper_module" />
### scraper module

{{< figure
  src="/img/proboards_scraper/scraper_module.png"
  alt="scraper module" class="aligncenter"
>}}

Lastly, there's the [scraper module][18], which is a sub-module in the
proboards_scraper package that contains several async functions used to
actually do the scraping (via a ScraperManager class instance to make HTTP
requests and indirectly interact with the database, as described above). The
scraper calls these functions as needed, some of which recursively call
each other. For example, the scrape_forum() function grabs shoutbox posts,
the site favicon, and categories from the main page, then calls scrape_board()
on each board in each category. scrape_board(), in turns, calls itself
recursively on any sub-boards, then iterates over all pages in the board and
calls scrape_thread() on all the threads on each page.

Similarly, scrape_users() runs through each page of the member list and calls
an async helper function named, predictably, scrape_user(), on each user
profile.

<span id="guests" />
### Guests

Guests are users who aren't actually registered on the site, i.e., they don't
show up in the site's member list. Not all forums allow guests to make
posts&mdash;the forum administrators can disable guest privileges if they so
choose. Guests can also be deleted users. In any case, the scraper needs a
way to handle them.

There are two issues: 1) guests have no user ID and 2) as mentioned in the
[ScraperManager class section](#scrapermanager_class) above, we scrape all
users first so that they already exist in the database when other content
references them&mdash;however, guests don't show up in the member list and
cannot be scraped in advance.

The first issue has an easy solution: assign guests user IDs of our choosing
for the purpose of the database. Actual users have positive integer IDs on
a forum. Therefore, I opted to assign guests negative IDs and identify them
by name. In other words, if guest "Bob" is encountered, they're assigned
user ID `-1`. If guest "cindy_123" is encountered next, they're assigned user
ID `-2`. If a guest named "Bob" is encountered again, we query the database
User table for existing guests by that name (instead of querying by ID as we
would a registered user), find that guest Bob already exists with ID `-1`,
and simply use that.

This also hints at how I've chosen to handle adding guests to the database:
when a post by a guest is encountered, we have to first query the database
for existing guests with the same name. If one already exists, use the existing
(negative) user ID; if not, assign a new negative ID and use that. This
requires the scraper to query the database, which is facilitated by the
ScraperManager's [insert_guest()][19] method.

The [download_image()][20] and [insert_image()][21] functions serve a similar
purpose, allowing us to download and add a user's avatar to the database and
reference it while scraping a user profile.

<span id="architecture_summary" />
### Putting it all together

We now have a complete picture of

{{< figure
  src="/img/proboards_scraper/overall_diagram.png"
  alt="ProBoards forum scraper"
  class="aligncenter"
>}}


[0]: {{< ref "2021-11-26-asynchronously-web-scraping-a-proboards-forum-with-python-part-2.md" >}}
[1]: {{< ref "2021-11-26-asynchronously-web-scraping-a-proboards-forum-with-python-part-3.md" >}}
[2]: https://www.proboards.com/forum-directory
[3]: https://en.wikipedia.org/wiki/Favicon
[4]: https://realpython.com/python-gil/
[5]: https://docs.python.org/3/library/multiprocessing.html
[6]: https://realpython.com/async-io-python/
[7]: https://docs.python.org/3/library/asyncio-task.html#awaitables
[8]: https://docs.aiohttp.org/en/stable/
[9]: https://github.com/Tinche/aiofiles
[10]: https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html
[11]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html
[12]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.User
[13]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.Database
[14]: https://www.sqlalchemy.org/
[15]: https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping
[16]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager
[17]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.run
[18]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.scraper.html
[19]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.insert_guest
[20]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.download_image
[21]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.insert_image
