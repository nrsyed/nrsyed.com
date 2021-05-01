import json
import xml.etree.ElementTree as ET


def parse(fname):
    tree = ET.parse(fname)
    root = tree.getroot()
    channel = root[0]

    posts = []

    _wp = "{http://wordpress.org/export/1.2/}"

    for elem in channel:
        if elem.tag == "item":
            guid = elem[4]

            if "?p=" in guid.text:
                post = {
                    "title": elem.find("title").text,
                    "post_id": elem.find(f"{_wp}post_id").text,
                    "post_name": elem.find(f"{_wp}post_name").text,
                    "comments": [],
                }

                for comment in elem.findall(f"{_wp}comment"):
                    comment_ = {
                        comment_elem.tag[len(f"{_wp}"):]: comment_elem.text
                        for comment_elem in comment
                    }
                    post["comments"].append(comment_)
                posts.append(post)
    return posts


if __name__ == "__main__":
    fname = "najamrsyed.WordPress.2021-01-30_2.xml"
    posts = parse(fname)

    out_fname = "posts.json"
    json.dump(posts, open(out_fname, "w"), indent=2)
