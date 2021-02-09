import os
import re


def copy_posts(src_dir, dst_dir):
    num_untitled = 0

    for fname in os.listdir(src_dir):
        src_fpath = os.path.join(src_dir, fname)
        
        expr = r"\d{4}-\d{2}-\d{2}-(.*)"
        match = re.match(expr, fname)

        dst_fname = match.groups()[0]
        if dst_fname == ".md":
            dst_fname = f"untitled_{num_untitled}.md"
            num_untitled += 1

        print(dst_fname)


if __name__ == "__main__":
    src_dir = os.path.expanduser("~/nrsyed.com/hugo-export/posts")
    copy_posts(src_dir, "")
