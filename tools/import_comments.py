import datetime
import json
import os
import re
import sqlite3


def nest_comments(posts):
    _posts = []

    for post in posts:
        if post["comments"]:
            comment_id_to_comment = dict()

            for comment in post["comments"]:
                comment["replies"] = []
                comment_id = int(comment["comment_id"])
                comment_id_to_comment[comment_id] = comment

            for comment in post["comments"]:
                parent_id = int(comment["comment_parent"])
                if parent_id != 0:
                    parent = comment_id_to_comment[parent_id]
                    parent["replies"].append(comment)

            _posts.append(post)
    return _posts


def insert_replies(cursor, thread_id, parent_id, comment):
    """
    Recursively insert comments/replies into the DB.
    """
    insert_template = [
        "insert into comments", "(tid, parent, created, mode,",
        "remote_addr, text, author, email, website, voters, notification)"
        "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ]
    insert_template = " ".join(insert_template)

    # First insert the current comment, then recursively insert replies to it.
    create_time = datetime.datetime.strptime(
        comment["comment_date_gmt"], "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        insert_template,
        (
            thread_id, parent_id, create_time.timestamp(), 1,
            comment["comment_author_IP"], comment["comment_content"],
            comment["comment_author"], comment["comment_author_email"],
            comment["comment_author_url"], "", 1
        )
    )

    inserted_comment_id = cursor.lastrowid

    for reply in comment["replies"]:
        insert_replies(cursor, thread_id, inserted_comment_id, reply)


def import_into_db(db_path, json_path, hugo_posts_dir):
    post_name_to_uri = dict()

    expr = "(\d{4}-\d{2}-\d{2}-)(.*)\.md"
    for fname in os.listdir(hugo_posts_dir):
        match = re.match(expr, fname)
        uri_date, post_name = match.groups()
        uri = f"/{uri_date.replace('-', '/')}{post_name}/"
        post_name_to_uri[post_name] = uri

    with open(json_path, "r") as f:
        posts = json.load(f)

    posts = nest_comments(posts)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for post in posts:
        uri = post_name_to_uri[post["post_name"]]

        # Check if thread for this post already exists. Create if not.
        c.execute("select * from threads where uri=?", (uri,))
        result = c.fetchone()

        if result:
            thread_id = result[0]
        else:
            c.execute(
                "insert into threads (uri, title) values (?, ?)", (uri, "")
            )
            thread_id = c.lastrowid

        for comment in post["comments"]:
            comment_wp_id = int(comment["comment_parent"])
            if comment_wp_id == 0:
                # Only call function on top-level comments (not replies to
                # other comments). Function will recursively insert children.
                insert_replies(c, thread_id, None, comment)

    conn.commit()


if __name__ == "__main__":
    db_path = "comments.db"
    json_path = "posts.json"
    hugo_posts_dir = "/home/najam/nrsyed.com/content/blog"

    import_into_db(db_path, json_path, hugo_posts_dir)
