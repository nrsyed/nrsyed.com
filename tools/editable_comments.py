"""
This simple script has a function that writes the comment content of each
comment to a text file. This makes it easier to see the formatting of the
post (e.g., newlines) and edit the comments (e.g., adding backticks around code
blocks). A second function is then used to update the content of the original
JSON file by reading the updated comment files.
"""
import json
import os


def write_editable(src_path, dst_dir):
    """
    Args:
        src_path (str): Path to post data JSON file.
        dst_dir (str): Path to directory where the editable .md files (one
            per comment) will be written. Each file will be named
            <comment_id>.md.
    """
    with open(src_path, "r") as f:
        posts = json.load(f)

    editable_posts = []

    for post in posts:
        for comment in post["comments"]:
            comment_id = comment["comment_id"]
            comment_content = comment["comment_content"]

            dst_path = os.path.join(dst_dir, f"{comment_id}.md")
            with open(dst_path, "w") as f:
                f.write(comment_content)


def editable_to_json(src_path, editable_path, dst_path):
    """
    Args:
        src_path (str): Path to post data JSON file.
        editable_path (str): Path to editable .md file or directory of
            .md files.
        dst_path (str): Path to updated JSON file (ie, a copy of `src_path`
            with the comment content updated to match the .md file(s) at
            `editable_path`).
    """
    with open(src_path, "r") as f:
        posts = json.load(f)

    # Create a mapping between comment ids and comments.
    comment_id_to_comment = {
        int(comment["comment_id"]): comment
        for post in posts for comment in post["comments"]
    }

    if os.path.isfile(editable_path):
        editable_fpaths = [editable_path]
    else:
        editable_fpaths = [
            os.path.join(editable_path, fname)
            for fname in os.listdir(editable_path)
        ]

    for fpath in editable_fpaths:
        _, fname = os.path.split(fpath)
        comment_id = int(os.path.splitext(fname)[0])
        with open(fpath, "r") as f:
            comment_content = f.read()

        comment = comment_id_to_comment[comment_id]
        comment["comment_content"] = comment_content

    with open(dst_path, "w") as f:
        json.dump(posts, f, indent=2)


if __name__ == "__main__":
    json_path = "posts.json"
    editable_dir = "editable"

    if not os.path.exists(editable_dir):
        os.makedirs(editable_dir)

    # write_editable(json_path, editable_dir)
    updated_json_path = "updated_posts.json"
    editable_to_json(json_path, editable_dir, updated_json_path) 
