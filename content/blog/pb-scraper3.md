---
title: Asynchronously web scraping a ProBoards forum with Python (part 3)
type: post
date: 2021-10-25T23:20:31-04:00
url: /2021/10/25/proboards-forum-web-scraper-part-3
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

# Scraping the forum

To understand how the scraper proceeds with, well, actually scraping, let's
use scraping user profiles as a demonstrative example and follow the flow of
data through the program. In the last post, we saw that this starts with
defining an async task for scraping user profiles in [run_scraper()][26]
(in [core.py][27]), adding that task to the list of async tasks to complete,
and running those tasks in the [asyncio event loop][37]. The relevant lines
are shown together below:

{{< highlight python >}}
    users_task = _task_wrapper(scrape_users, "both", url, manager)

    ...

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

This tells the event loop to asynchronously run [scrape_users()][38], which is
defined in [scrape.py][32], a task for scraping content if selected (e.g.,
[scrape_forum()][39]), and [ScraperManager.run()][10]. This is the definition
for scrape_users():

{{< highlight python "linenos=true,linenostart=225" >}}
async def scrape_users(url: str, manager: ScraperManager) -> None:
    """
    Asynchronously iterate over all user profile pages and add them to the
    the ScraperManager user queue for insertion into the database.
    Args:
        url: Main members page URL, e.g.,
            `https://yoursite.proboards.com/members`.
        manager: ScraperManager instance.
    """
    logger.info(f"Getting user profile URLs from {url}")

    base_url, _ = split_url(url)
    member_hrefs = []

    source = await manager.get_source(url)
    _member_hrefs, next_href = scrape_user_urls(source)
    member_hrefs.extend(_member_hrefs)

    while next_href:
        next_url = f"{base_url}{next_href}"
        source = await manager.get_source(next_url)
        _member_hrefs, next_href = scrape_user_urls(source)
        member_hrefs.extend(_member_hrefs)

    member_urls = [f"{base_url}{member_href}" for member_href in member_hrefs]
    logger.info(f"Found {len(member_urls)} user profile URLs")

    loop = asyncio.get_running_loop()
    tasks = []

    for member_url in member_urls:
        task = loop.create_task(scrape_user(member_url, manager))
        tasks.append(task)

    await asyncio.wait(tasks)
{{< / highlight >}}

On line 239, we get the page source (note that ScraperManager.get_source() is
awaitable, which means that, at this point, the event loop can suspend
execution of this task and switch to a different task). We'll examine
ScraperManager.get_source() later&mdash;for now, just know that it's a wrapper
around [asyncio.ClientSession.get()][40] and fetches the HTML page source of
a URL. The next few lines grab links to all the user profiles from the list of
members on the current page and on all subsequent pages. Lines 252-259 create
an async task for each user profile (by calling [scrape_user()][19] on the
profile URL) and add them to the event loop, then wait for them to finish.


Here are the first few lines of scrape_user():

{{< highlight python "linenos=true,linenostart=19" >}}
async def scrape_user(url: str, manager: ScraperManager) -> None:
    """
    Scrape a user profile and add the user to the ScraperManager's user queue
    (from which the user will be inserted into the database), as well as
    download the user's avatar and insert the image into the database.
    Args:
        url: User profile page URL.
        manager: ScraperManager instance.
    """
    # Get user id from URL, eg, "https://xyz.proboards.com/user/42" has
    # user id 42. We can exploit os.path.split() to grab everything right
    # of the last backslash.
    user = {
        "url": url,
        "id": int(os.path.split(url)[1])
    }

    source = await manager.get_source(url)
{{< / highlight >}}

This initializes the dictionary that will later be used to construct a
[SQLAlchemy User object][5]. The items in this dictionary will serve as
keyword arguments to the User constructor.

We won't go through the entire function, as there's a considerable amount of
code that parses the HTML via BeautifulSoup, but the following snippet provides
a glimpse of what some of that code looks like. Observe how the extracted
information is added to the `user` dictionary.

{{< highlight python "linenos=true,linenostart=51" >}}
    # Get username and last online datetime.
    controls = user_container.find("div", class_="float-right controls")
    user_datetime = controls.find("div", class_="float-right clear pad-top")
    children = [child for child in user_datetime.children]
    for i, child in enumerate(children):
        if isinstance(child, bs4.element.NavigableString):
            if child.strip() == "Username:":
                user["username"] = children[i+1].text
            elif child.strip() == "Last Online:":
                # Get Unix timestamp string from <abbr> tag.
                lastonline_block = children[i+1]
                unix_ts = int(lastonline_block.find("abbr")["data-timestamp"])
                user["last_online"] = unix_ts
            elif child.strip() == "Member is Online":
                # This will be the case for the aiohttp session's logged-in
                # user (and for any other user that happens to be logged in).
                # Multiply time.time() value by 1000 for milliseconds.
                unix_ts = int(time.time()) * 1000
                user["last_online"] = unix_ts
{{< / highlight >}}

Near the end of the function, we put `user` in the queue:

{{< highlight python "linenos=true,linenostart=160" >}}
    await manager.user_queue.put(user)
{{< / highlight >}}

Let's jump to ScraperManager.run(), which lives in [scraper_manager.py][33],
and see how it handles items in the user queue.

{{< highlight python "linenos=true,linenostart=191" >}}
        if self.user_queue is not None:
            all_users_added = False
            while not all_users_added:
                user = await self.user_queue.get()

                if user is None:
                    all_users_added = True
                else:
                    self.db.insert_user(user)
{{< / highlight >}}

Above, we see that it pops items (dictionaries like `user`) from the queue
and calls [Database.insert_user()][41] to insert them into the database.
Let's jump to [database.py][28] to see how Database.insert_user() is defined:

{{< highlight python "linenos=true,linenostart=460" >}}
    def insert_user(self, user_: dict, update: bool = False) -> User:
        """
        Insert a user into the database; this method wraps :meth:`insert`.

        Args:
            user\_: A dict containing the keyword args (attributes)
                needed to instantiate a :class:`User` object.
            update: See :meth:`insert`.

        Returns:
            The inserted (or updated) :class:`User` object.
        """
        user = User(**user_)
        inserted, user = self.insert(user, update=update)
        self._insert_log_msg(f"User {user.name}", inserted)
        return user
{{< / highlight >}}

Database.insert_user() wraps a more generic method, [Database.insert()][42],
which accepts a table metaclass instance of any type (e.g., Board, Thread,
User). The definition for Database.insert() is shown below with its lengthy
docstring removed for brevity.

{{< highlight python >}}
    def insert(
        self,
        obj: sqlalchemy.orm.DeclarativeMeta,
        filters: dict = None,
        update: bool = False
    ) -> Tuple[int, sqlalchemy.orm.DeclarativeMeta]:
        if filters is None:
            filters = {"id": obj.id}

        Metaclass = type(obj)
        result = self.session.query(Metaclass).filter_by(**filters).first()

        inserted = 0
        if result is None:
            self.session.add(obj)
            self.session.commit()
            inserted = 1
            ret = obj
        elif result is not None and update:
            for attr, val in vars(obj).items():
                if not attr.startswith("_"):
                    setattr(result, attr, val)
            self.session.commit()
            inserted = 2
            ret = result
        else:
            ret = result
        return inserted, ret
{{< / highlight >}}

The method returns an "insert code" and the SQLAlchemy table object&mdash;i.e.,
a User instance. In this case, ScraperManager.run(), which called
Database.insert_user(), doesn't use the return value, but in other cases, the
value returned by the insert method will be used. Recall the scraper
architecture diagram, whose arrows illustrate this:

{{< figure
  src="/img/proboards_scraper/scraper_diagram.png" alt="Scraper architecture"
  class="aligncenter"
>}}

In fact, ScraperManager.run() doesn't care about the return values at all,
hence the single-ended arrows that point from run() to the insert methods.
ScraperManager.insert_guest() and ScraperManager.insert_image(), on the
other hand, do need to capture and return those values. We'll see this in
action in the next section.

# Downloading and adding images

Unlike other objects, images are actually downloaded to disk, and an Image
item that references said file is inserted into the database.

Continuing through the scrape_user() function from the last section, after
getting the user avatar URL, the image is downloaded:

{{< highlight python "linenos=true,linenostart=168" >}}
    avatar_ret = await manager.download_image(avatar_url)
{{< / highlight >}}

The ScraperManager.download_image() method looks like this:

{{< highlight python "linenos=true,linenostart=106" >}}
    async def download_image(self, url: str) -> dict:
        """
        Download an image to :attr:`image_dir`.
        Args:
            url: URL of the image to be downloaded.
        Returns:
            Image download status and metadata; see
            :func:`proboards_scraper.download_image`.
        """
        if "proboards.com" in url:
            await self._delay()
            self.request_count += 1
        return await download_image(url, self.client_session, self.image_dir)
{{< / highlight >}}

In other words, this is just a wrapper around a helper function (not part of
the ScraperManager class) named download_image(), with the delay added in if
the request is to a ProBoards URL. The download_image() function
is located in [http_requests.py][24]. It returns a dictionary containing
information on the download HTTP request and, if successful, the downloaded
file itself. The function first initializes this dictionary with `None` values:

{{< highlight python "linenos=true,linenostart=211" >}}
    ret = {
        "status": {
            "get": None,
            "exists": None,
            "valid": None
        },
        "image": {
            "url": url,
            "filename": None,
            "md5_hash": None,
            "size": None,
        },
    }
{{< / highlight >}}

As you can see

The rest of the function makes an awaitable HTTP request, handles the response,
and does some error checking, writes the downloaded image to disk (if it's
a valid image and the file doesn't already exist), and updates/returns the
dictionary.

{{< highlight python "linenos=true,linenostart=1" >}}
    try:
        response = await session.get(url, timeout=45)
    except aiohttp.client_exceptions.ClientConnectorError as e:
        logger.warning(
            f"Failed to download image at {url}: {str(e)} "
            "(it is likely the image or server no longer exists)"
        )
    else:
        ret["status"]["get"] = response.status

        if response.status == 200:
            img = await response.read()

            # The file extension doesn't necessarily match the filetype, so we
            # manually check the file header and set the correct extension. If
            # the file doesn't correspond to a supported image filetype, we
            # assume the downloaded file is invalid and skip it.
            ret["status"]["valid"] = False

            filetype = imghdr.what(None, h=img)

            if filetype == "jpeg":
                filetype = "jpg"

            if filetype is not None:
                ret["status"]["valid"] = True

                # Set the filestem to the md5 hash of the image.
                img_md5 = hashlib.md5(img).hexdigest()

                new_fname = f"{img_md5}.{filetype}"

                ret["image"]["filename"] = new_fname
                ret["image"]["size"] = len(img)
                ret["image"]["md5_hash"] = img_md5

                img_fpath = dst_dir / new_fname

                if not img_fpath.exists():
                    ret["status"]["exists"] = False
                    async with aiofiles.open(img_fpath, "wb") as f:
                        await f.write(img)
                else:
                    ret["status"]["exists"] = True
    finally:
        return ret
{{< / highlight >}}

Jumping back to scrape_user(), the function takes the nested dictionary from
the returned dictionary that, not coincidentally, contains keys needed
to instantiate a database Image object:

{{< highlight python "linenos=true,linenostart=169" >}}
    image = avatar_ret["image"]
    image["description"] = "avatar"
{{< / highlight >}}

Note that we also add a description that marks this image as an avatar.

Finally, we insert the image into the database via
ScraperManager.insert_image():

{{< highlight python "linenos=true,linenostart=180" >}}
    image_id = manager.insert_image(image)
{{< / highlight >}}


## Content example: scraping a thread

Scraping content is similar to scraping user profiles, but there are a few
differences. Let's look at scraping a thread to see how we handle those
differences.

Back to [scrape.py][32] scrape_thread() function. The function first grabs the
page source as before, scrapes some basic information about the thread (thread
ID, the thread title, whether the thread is locked or stickied, the create
user ID, etc.). Before
proceeding with posts, we first check whether the create user is a guest:

{{< highlight python "linenos=true,linenostart=378" >}}
    # If the create user id is 0, it means the user who created the thread
    # is a guest. In this case, we jump ahead to the first post to grab the
    # guest user name and get a database user id for the guest.
    if user_id == 0:
        first_post = source.select("tr.post.first")[0]
        guest_user_name = first_post.find("span", class_="user-guest").text
        user_id = manager.insert_guest(guest_user_name)
{{< / highlight >}}

This is one of the exceptions where we bypass the content queue and etc.
Let's look at the code for the insert_guest() method in the ScraperManager
class:

{{< highlight python "linenos=true,linenostart=141" >}}
    def insert_guest(self, name: str) -> int:
        """
        Insert a guest user into the database.
        Args:
            name: The guest's username.
        Returns:
            The user ID of the guest returned by
            :meth:`proboards_scraper.database.Database.insert_guest`.
        """
        guest = {
            "id": -1,
            "name": name,
        }

        # Get guest user id.
        guest_db_obj = self.db.insert_guest(guest)
        guest_id = guest_db_obj.id
        return guest_id
{{< / highlight >}}

In this case, we construct a dictionary similar to that for a User (since a
guest is a special case of user), but there's no information on the guest
besides their name. We then call the Database class insert_guest() method,
which looks like this (docstring removed):

{{< highlight python >}}
    def insert_guest(self, guest_: dict) -> User:
        guest = User(**guest_)

        # Query the database for all existing guests (negative user id).
        query = self.session.query(User).filter(User.id < 0)

        # Of the existing guests, query for the name of the current guest.
        this_guest = query.filter_by(name=guest.name).first()

        if this_guest:
            # This guest user already exists in the database.
            guest.id = this_guest.id
        else:
            # Otherwise, this particular guest user does not exist in the
            # database. Iterate through all guests and assign a new negative
            # user id by decrementing the smallest guest user id already in
            # the database.
            lowest_id = 0
            for existing_guest in query.all():
                lowest_id = min(existing_guest.id, lowest_id)
            new_guest_id = lowest_id - 1
            guest.id = new_guest_id

        inserted, guest = self.insert(guest)
        self._insert_log_msg(f"Guest {guest.name}", inserted)
        return guest
{{< / highlight >}}

Here, we bla bla bla return the User instance corresponding to the (existing
or newly added guest). As shown above, ScraperManager.insert_guest() returns
only the integer ID from this instance to scrape_thread(), which now has a
valid user ID that exists in the database for the create user.

Returning now to scrape_thread(), the function next scrapes a poll (if any).
The way ProBoards forums work, poll modal windows (the box that pops up when
you click on a poll) are inserted into the page HTML source by JavaScript.
This means we need to use Selenium to get load the page source if a poll is
present instead of relying on the source obtained from the aiohttp session.

{{< highlight python "linenos=true,linenostart=386" >}}
    if poll:
        manager.driver.get(url)
        time.sleep(1)

        # Click the "View Voters" button, which causes a modal to load.
        manager.driver.find_element_by_link_text("View Voters").click()
        time.sleep(1)

        selenium_source = manager.driver.page_source
        selenium_source = bs4.BeautifulSoup(selenium_source, "html.parser")
        selenium_post_container = selenium_source.find(
            "div", class_="container posts"
        )
        poll_container = selenium_post_container.find("div", class_="poll")
        voters_container = selenium_source.find("div", {"id": "poll-voters"})
        await scrape_poll(thread_id, poll_container, voters_container, manager)
{{< / highlight >}}

Why `time.sleep()` and not `await asyncio.sleep()`? Because a Selenium
WebDriver is effectively a single browser window; we could theoretically
open a new tab for each URL, keep track of them, and switch between them
as needed, or create a new WebDriver instance for each call, but this
introduces much more complexity and overhead. I figured it was simpler to
just wait for each URL GET request to load. Afterward we parse the HTML
with BeautifulSoup like we've been doing.

We won't delve into the scrape_poll() function because it doesn't really
demonstrate anything new that we haven't seen already. In the middle of
the scrape_thread() function, we add the thread to the content queue:

{{< highlight python "linenos=true,linenostart=407" >}}
    thread = {
        "type": "thread",
        "announcement": announcement,
        "board_id": board_id,
        "id": thread_id,
        "locked": locked,
        "sticky": sticky,
        "title": thread_title,
        "url": url,
        "user_id": user_id,
        "views": views,
    }
    await manager.content_queue.put(thread)
{{< / highlight >}}

This is similar to adding a user except there's a `"type"` key that tells
ScraperManager.run() which Database method to call. In this case, its value
is `"thread`". Here's how the ScraperManager uses that info:

{{< highlight python "linenos=true,linenostart=201" >}}
        type_to_insert_func = {
            "board": self.db.insert_board,
            "category": self.db.insert_category,
            "image": self.db.insert_image,
            "moderator": self.db.insert_moderator,
            "poll": self.db.insert_poll,
            "poll_option": self.db.insert_poll_option,
            "poll_voter": self.db.insert_poll_voter,
            "post": self.db.insert_post,
            "shoutbox_post": self.db.insert_shoutbox_post,
            "thread": self.db.insert_thread,
        }

        all_content_added = False
        while not all_content_added:
            content = await self.content_queue.get()

            if content is None:
                all_content_added = True
            else:
                type_ = content["type"]
                del content["type"]

                insert_func = type_to_insert_func[type_]
                insert_func(content)
{{< / highlight >}}

The rest of scrape_thread() iterates over the pages of the thread and grabs
all the posts on each page. This is achieved with a while loop in which the
following logic is placed at the end of the loop:

{{< highlight python "linenos=true,linenostart=483" >}}
        # Continue to next page, if any.
        control_bar = post_container.find("div", class_="control-bar")
        next_btn = control_bar.find("li", class_="next")

        if "state-disabled" in next_btn["class"]:
            pages_remaining = False
        else:
            next_href = next_btn.find("a")["href"]
            next_url = f"{base_url}{next_href}"
            source = await manager.get_source(next_url)
            post_container = source.find("div", class_="container posts")
{{< / highlight >}}

Here, we search for a clickable button that links to the next page (if any).
If the class attribute of the HTML tag corresponding to that button contains
`"state-disabled"`, we set the sentinel variable `pages_remaining` to `False`,
which terminates the loop.

# Rate limiting

Let's take a closer look at the ScraperManager.get_source() method:

{{< highlight python "linenos=true,linenostart=122" >}}
    async def get_source(self, url: str) -> bs4.BeautifulSoup:
        """
        Wrapper around :func:`proboards_scraper.get_source` with an
        added short delay via call to :func:`time.sleep` before each
        request, and a longer delay after every ``self.request_threshold``
        calls to :meth:`ScraperManager.get_source`. This rate-limiting is
        performed to help avoid request throttling by the server, which may
        result from a large number of requests in a short period of time.
        Args:
            url: URL whose page source to retrieve.
        Returns:
            BeautifulSoup page source object.
        """
        await self._delay()
        self.request_count += 1
        return await get_source(url, self.client_session)
{{< / highlight >}}

Here, we can see that this method calls a private method named
ScraperManager.\_delay(), which looks like this:

{{< highlight python "linenos=true,linenostart=86" >}}
    async def _delay(self) -> None:
        """
        Asynchronously sleep for an amount of time based on the number of
        requests, the request threshold, and the short/long delay times.
        """
        if not self.short_delay_time and not self.long_delay_time:
            return

        delay = self.short_delay_time

        if self.request_threshold is not None and self.long_delay_time:
            mod = self.request_threshold - 1
            if self.request_count % self.request_threshold == mod:
                delay = self.long_delay_time
                logger.debug(
                    f"Request count = {self.request_count + 1}, "
                    f"sleeping {delay} s"
                )
        await asyncio.sleep(delay)
{{< / highlight >}}

All that's happening here is we're waiting for a "short" amount of time (1.5 seconds by
default) between each HTTP request, and after every `request_threshold`
requests (15 by default), we wait for a "long" amount of time (20 seconds by
default). There's nothing special about these numbers. They're just the result of
experimentation.

# Conclusion

That's all, folks.

[0]: {{< ref "pb-scraper.md" >}}
[1]: https://realpython.com/async-io-python/
[2]: https://realpython.com/python-gil/
[3]: https://en.wikipedia.org/wiki/Favicon
[4]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html
[5]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.User
[6]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.Database
[7]: https://www.sqlalchemy.org/
[8]: https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping
[9]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager
[10]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.run
[11]: https://docs.python.org/3/library/multiprocessing.html
[12]: https://numpy.org/
[13]: https://www.proboards.com/forum-directory
[14]: https://docs.python.org/3/library/asyncio-task.html#awaitables
[15]: https://docs.aiohttp.org/en/stable/
[16]: https://github.com/Tinche/aiofiles
[17]: https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html
[18]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.scraper.html
[19]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.scraper.html#proboards_scraper.scraper.scrape_user
[20]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.insert_guest
[21]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.download_image
[22]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.ScraperManager.insert_image
[23]: https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession
[24]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/http_requests.py
[25]: https://docs.python.org/3/library/http.cookies.html#morsel-objects
[26]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.run_scraper
[27]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/core.py
[28]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/database/database.py
[29]: https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/api.html#sqlalchemy.ext.declarative.declarative_base
[30]: https://stackoverflow.com/a/42772654
[31]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/database/schema.py
[32]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/scraper/scrape.py
[33]: https://github.com/nrsyed/proboards-scraper/blob/main/proboards_scraper/scraper_manager.py
[34]: https://nrsyed.github.io/proboards-scraper
[35]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.get_login_cookies
[36]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.html#proboards_scraper.get_login_session
[37]: https://docs.python.org/3/library/asyncio-eventloop.html
[38]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.scraper.html#proboards_scraper.scraper.scrape_users
[39]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.scraper.html#proboards_scraper.scraper.scrape_forum
[40]: https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession.get
[41]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.Database.insert_user
[42]: https://nrsyed.github.io/proboards-scraper/html/proboards_scraper.database.html#proboards_scraper.database.Database.insert
