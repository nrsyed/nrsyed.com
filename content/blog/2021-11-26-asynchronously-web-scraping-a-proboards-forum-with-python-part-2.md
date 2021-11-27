---
title: Asynchronously web scraping a ProBoards forum with Python (part 2)
author: Najam Syed
type: post
date: 2021-11-26T12:01:00-04:00
url: /2021/11/26/asynchronously-web-scraping-a-proboards-forum-with-python-part-2
categories:
  - Web Scraping
tags:
  - aiohttp
  - asyncio
  - BeautifulSoup
  - forum
  - HTML
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

* [Part 1: Introduction and background][0]
* **Part 2: Implementation (project structure and scraper initialization)**
  * *[Project structure](#structure)*
  * *[Creating a SQLAlchemy database session](#create_db)*
  * *[Initializing an authenticated HTTP session](#authentication)*
* [Part 3: Implementation (scraper internals)][1]

This post and the next will detail the implementation of the web scraper and
dive into the code. These posts are intended to go into significantly more
depth than the average web scraping tutorial. We won't run through all ~1400
lines of code in the repository, but will touch on key components. Moreover,
rather than discuss each component of the scraper one by one, we'll follow
the flow of data through the program and through those components as it runs.
This means we'll jump between different files and functions, but in a manner
that illustrates how the moving parts work together.

<span id="structure" />
# Project structure

The project&mdash;a Python package I've named `proboards_scraper`&mdash;is
organized as follows:

{{< highlight plain >}}
proboards_scraper/
├── __init__.py
├── __main__.py
├── core.py
├── http_requests.py
├── scraper_manager.py
├── database
│   ├── __init__.py
│   ├── database.py
│   └── schema.py
└── scraper
    ├── __init__.py
    ├── scrape.py
    └── utils.py
{{< / highlight >}}

At the top level, the package has functions for HTTP session management and
making HTTP requests, which reside in http_requests.py. The ScraperManager
class is defined in scraper_manager.py. core.py is what ties everything
together and actually runs the scraper.

The package also contains two submodules. The
database submodule encapsulates the Database class (defined in database.py)
and the SQLAlchemy table schema (in schema.py), which maps tables in the SQLite
database to SQLAlchemy Python objects. The scraper submodule contains async
functions (and non-async helpers) for parsing HTML returned by HTTP requests.

Finally, there's a command-line interface (CLI), which is defined in
\_\_main.py\_\_. For more information on the CLI, refer to
[the documentation][2].

<span id="create_db" />
# Creating a SQLAlchemy database session

The scraper is initialized and kicked off by the [run_scraper()][3] function
in [core.py][4]. First, we create an instance of the Database class by
pointing it to the database file (named forum.db by default); if the file
doesn't exist, it will automatically be created in the process.

{{< highlight python "linenos=true,linenostart=97" >}}
    db_path = dst_dir / "forum.db"
    db = Database(db_path)
{{< / highlight >}}

To see what happens in Database.\_\_init\_\_(), let's jump to the Database
class constructor in [database.py][5]:

{{< highlight python "linenos=true,linenostart=81" >}}
class Database:
    def __init__(self, db_path: pathlib.Path):
        """
        This class serves as an interface for the SQLite database, and allows
        items to be inserted/updated or queried using a variety of specific
        functions that abstract away implementation details of the database
        and its schema.

        Args:
            db_path: Path to SQLite database file.
        """
        engine_str = f"sqlite:///{db_path}"
        engine = sqlalchemy.create_engine(engine_str)
        Session = sqlalchemy.orm.sessionmaker(engine)
        session = Session()
        Base.metadata.create_all(engine)

        self.engine = engine
        self.session = session
{{< / highlight >}}

Here, we create a SQLAlchemy engine, which we then bind to a SQLAlchemy
session. [This StackOverflow answer][6] provides a helpful definition of
these terms. An "engine" is a low-level object that maintains a pool of
connections to actually talk to the database. A "session," on the other hand,
is a higher level object that handles the ORM functionality, i.e.,
mapping Python objects to SQL database tables/queries. A session uses an
engine under the hood to perform database operations.

The `Base` object on line 95 is a SQLAlchemy metaclass, returned by the
factory function [declarative_base()][7], from which all database table
classes must inherit. In simpler terms, Base.metadata.create_all() links
the engine to the tables we've defined.

Those tables are defined in [schema.py][8]. Specifically, we've defined a
Python class for each table. For example, this is the definition for the
Board class:

{{< highlight python "linenos=true,linenostart=34" >}}
class Board(Base):
    """
    This table contains information on boards and their associated metadata.

    Attributes:
        id (int): Board number obtained from the board URL, eg,
            ``https://yoursite.proboards.com/board/42/general`` refers to the
            "General" board with id 42.
        category_id (int): Category id of the category to which this board
            belongs; see :class:`Category`.
        description (str): Board description.
        name (str): Board name. Required.
        parent_id (int): Board id of this board's parent board, if it is a
            sub-board.
        password_protected (bool): Whether the board is password-protected.
        url (str): Board URL.

        moderators: List of this board's moderators, if any; see
            :class:`Moderator`.
        sub_boards: List of this board's sub-boards, if any.
        threads: List of this board's threads; see :class:`Thread`.
    """
    __tablename__ = "board"

    id = Column("id", Integer, primary_key=True, autoincrement=False)
    category_id = Column("category_id", ForeignKey("category.id"))
    description = Column("description", String)
    name = Column("name", String, nullable=False)
    parent_id = Column("parent_id", ForeignKey("board.id"))
    password_protected = Column("password_protected", Boolean)
    url = Column("url", String)

    _moderators = relationship("Moderator")
    moderators = association_proxy("_moderators", "_users")

    sub_boards = relationship("Board")
    threads = relationship("Thread")
{{< / highlight >}}

SQLAlchemy takes care of creating these tables (as well as the database) if
they don't already exist. Note that the `relationship` and `association_proxy`
attributes in the class definition are SQLAlchemy constructs that exist
for our convenience; they aren't in the actual SQL database schema. In the
Board class, these attributes make it such that when we query the
database for a board, the resulting Board instance will have attributes
named `moderators`, `sub_boards`, and `threads`; these are lists of User
objects, Board objects, and Thread objects, respectively, with foreign keys
that tie them to the Board instance. Normally, each of these would involve a
separate SQL query, but SQLAlchemy handles this for us.

<span id="authentication" />
# Initializing an authenticated HTTP session

Next, run_scraper() creates a Selenium WebDriver and an aiohttp session:

{{< highlight python "linenos=true,linenostart=100" >}}
    chrome_driver = get_chrome_driver()

    base_url, url_path = split_url(url)

    # Get cookies for parts of the site requiring login authentication.
    if username and password:
        logger.info(f"Logging in to {base_url}")
        cookies = get_login_cookies(
            base_url, username, password, chrome_driver
        )

        # Create a persistent aiohttp login session from the cookies.
        client_session = get_login_session(cookies)
        logger.info("Login successful")
    else:
        logger.info(
            "Username and/or password not provided; proceeding without login"
        )
        client_session = aiohttp.ClientSession()
{{< / highlight >}}

Creating an HTTP session without logging in ("authenticating") isn't required,
but any password-protected or restricted areas of the forum won't be accessible
without it. We'll use Selenium to log in, since it allows us to interact with
webpages and do things like fill out and submit forms. However, Selenium has
limitations; a Selenium WebDriver is essentially just a browser window and
doesn't support asynchronous programming, which is vital for the scraper.
Furthermore, it doesn't handle multiple simultaneous connections. In theory,
because a Selenium WebDriver "session" is a browser, we could open multiple
tabs, but keeping track of those tabs and switching between them adds a
considerable amount of complexity and overhead. It also doesn't address the
lack of async support, hence why I opted to use aiohttp scraping and HTTP
requests via [aiohttp.ClientSession][9].

However, there's an obstacle here. When we log in with Selenium, the login
cookies are stored in the Selenium WebDriver session. There's no simple way
to transfer these cookies to the aiohttp session, and the two libraries store
cookies in different formats. We must convert them manually.

All of the aforementioned functionality lives in [http_requests.py][10]. The
function [get_login_cookies()][11] takes the Selenium WebDriver instance, as
well as the login username/password, and returns a list of dictionaries,
where each dictionary represents a cookie. The function
[get_login_session()][12] uses these to construct a dictionary of [morsel][13]
objects and add them to the aiohttp session's cookie jar:

{{< highlight python "linenos=true,linenostart=129" >}}
    session = aiohttp.ClientSession()

    morsels = {}
    for cookie in cookies:
        # https://docs.python.org/3/library/http.cookies.html#morsel-objects
        morsel = http.cookies.Morsel()
        morsel.set(cookie["name"], cookie["value"], cookie["value"])
        morsel["domain"] = cookie["domain"]
        morsel["httponly"] = cookie["httpOnly"]
        morsel["path"] = cookie["path"]
        morsel["secure"] = cookie["secure"]

        # NOTE: ignore expires field; if it's absent, the cookie remains
        # valid for the duration of the session.
        # if "expiry" in cookie:
        #     morsel["expires"] = cookie["expiry"]

        morsels[cookie["name"]] = morsel

    session.cookie_jar.update_cookies(morsels)
{{< / highlight >}}

# Defining async tasks

The scraper is flexible in that it can be run on any of:

1. the entire forum, including all users and all content (if given the URL to
the homepage)
2. all users (if given the URL to the members page)
3. a single user (if given the URL to a specific user profile)
4. a single board (if given the URL to a specific board)
5. a single thread (if given the URL to a specific thread)

Recall the scraper's architecture, whereby the scraper module functions add
items to either an async "users queue" or an async "content queue":

{{< figure
  src="/img/proboards_scraper/scraper_diagram.png" alt="Scraper architecture"
  class="aligncenter"
>}}

In the list above, option 1 has both a "user" task (responsible for scraping
all users and adding them to the users queue) and a "content" task (responsible
for scraping all other content and adding it to the content queue). Options
2 and 3 have just a "user" task (responsible for scraping all users or a
single user and adding them to the users queue). Options 4 and 5 have just a
"content" task. However, each one calls a different function; option 1
calls scrape_users() and scrape_forum(), option 2 calls scrape_users(),
option 3 calls scrape_user() (which isn't shown in the diagram but is an
async helper function for scrape_users()), option 4 calls scrape_board(),
and option 5 calls scrape_thread().

To simplify the act of creating an async task for a given function with the
appropriate queue, we use a private helper function named \_task\_wrapper():

{{< highlight python "linenos=true,linenostart=22" >}}
async def _task_wrapper(
    func: Callable,
    queue_name: Literal["user", "content", "both"],
    url: str,
    manager: ScraperManager
):
    """
    Args:
        func: The async function to be called for scraping user(s) or content.
        queue_name: The queue(s) in which ``None`` should be put after ``func``
            completes, signaling to :meth:`ScraperManager.run` that that
            queue's task is complete.
        url: The URL to be passed to ``func``.
        manager: The ``ScraperManager`` instance to be passed to ``func``.
    """
    await func(url, manager)

    if queue_name == "both" or queue_name == "user":
        await manager.user_queue.put(None)

    if queue_name == "both" or queue_name == "content":
        await manager.content_queue.put(None)
{{< / highlight >}}

To see how this is put into practice, we return to run_scraper.py:

{{< highlight python "linenos=true,linenostart=134" >}}
    tasks = []

    users_task = None
    content_task = None

    if url_path is None:
        # This represents the case where the forum homepage URL was provided,
        # i.e., we scrape the entire site.
        logger.info("Scraping entire forum")

        content_task = _task_wrapper(
            scrape_forum, "content", base_url, manager
        )

        if skip_users:
            logger.info("Skipping user profiles")
        else:
            users_page_url = f"{base_url}/members"
            users_task = _task_wrapper(
                scrape_users, "user", users_page_url, manager
            )
    elif url_path.startswith("/members"):
        users_task = _task_wrapper(scrape_users, "both", url, manager)
    elif url_path.startswith("/user"):
        users_task = _task_wrapper(scrape_user, "both", url, manager)
    elif url_path.startswith("/board"):
        content_task = _task_wrapper(
            scrape_board, "content", url, manager
        )
    elif url_path.startswith("/thread"):
        content_task = _task_wrapper(
            scrape_thread, "content", url, manager
        )
{{< / highlight >}}

Note how we add the async task(s) to a list. This allows us to kick off all
tasks in the list and run the [asyncio event loop][14] until all tasks have
completed, as in this block of code at the end of run_scraper(), where we
also add ScraperManager.run() and call it `database_task`, since it pops
items from the queues and calls the appropriate Database instance methods
for inserting those items into the database:

{{< highlight python "linenos=true,linenostart=168" >}}
    if users_task is not None:
        tasks.append(users_task)
    else:
        manager.user_queue = None

    if content_task is not None:
        tasks.append(content_task)

    database_task = manager.run()
    tasks.append(database_task)

    task_group = asyncio.gather(*tasks)
    asyncio.get_event_loop().run_until_complete(task_group)
{{< / highlight >}}

In this manner, we can kick off a variable number of tasks (depending on
whether we're scraping content, users, or both). Now, the actual scraping can
begin. This will be covered in the next post.

[0]: {{< ref "2021-11-26-asynchronously-web-scraping-a-proboards-forum-with-python-part-1.md" >}}
[1]: {{< ref "2021-11-26-asynchronously-web-scraping-a-proboards-forum-with-python-part-3.md" >}}
[2]: https://nrsyed.github.io/proboards-scraper
[3]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.run_scraper
[4]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/core.py
[5]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/database/database.py
[6]: https://stackoverflow.com/a/42772654
[7]: https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/api.html#sqlalchemy.ext.declarative.declarative_base
[8]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/database/schema.py
[9]: https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession
[10]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/http_requests.py
[11]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.get_login_cookies
[12]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.get_login_session
[13]: https://docs.python.org/3/library/http.cookies.html#morsel-objects
[14]: https://docs.python.org/3/library/asyncio-eventloop.html
