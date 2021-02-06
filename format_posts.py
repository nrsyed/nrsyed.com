"""
Fix formatting of posts exported from WP by WP to Hugo exporter.

Fix __main__ (dunder being bolded).
Ordered list formatting (parentheses become periods?)
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import glob
import os
import re
import time

import bs4
import pyparsing as pp


def get_grammar():
    punctuation = pp.Word(".,:;()/")

    word_no_angle_bracket = pp.Word(pp.printables, excludeChars="<>")
    html_tag = pp.Combine(
        pp.Optional(punctuation)
        + "<"
        + pp.delimitedList(word_no_angle_bracket, delim=" ", combine=True)
        + ">"
        + pp.Optional(punctuation)
    )

    word_no_backtick = pp.Word(pp.printables, excludeChars="`")
    code = pp.Combine(
        pp.Optional(punctuation)
        + "`"
        + pp.delimitedList(word_no_backtick, delim=" ", combine=True)
        + "`"
        + pp.Optional(punctuation)
    )

    word = pp.Or( word_no_backtick | word_no_angle_bracket)
    words = pp.delimitedList(word, delim=" ", combine=True)

    token_ = pp.Or(html_tag | code | word)

    bullet = pp.Combine("*" + pp.White() + token_)

    heading = pp.Combine(
        pp.OneOrMore("#")
        + pp.OneOrMore(" ")
        + pp.delimitedList(token_, delim=" ", combine=True)
    )

    token = pp.Or(heading | bullet | token_)

    cfg = token[1, ...]
    return cfg


def split_line(line, max_len=80):
    """
    TODO
    """
    cfg = get_grammar()
    tokens = cfg.parseString(line)

    split_lines = []

    curr_line = ""
    for token in tokens:
        if not curr_line:
            curr_line = token
        elif len(" " + token) + len(curr_line) <= max_len:
            curr_line += f" {token}"
        else:
            split_lines.append(curr_line)
            curr_line = token

    if curr_line:
        split_lines.append(curr_line)

    return split_lines


def format_hyperlinks(markdown):
    open_tags = re.finditer(r"<a", markdown)
    close_tags = re.finditer(r"</a>", markdown)

    updated_markdown = []

    split_idxs = []
    for open_tag, close_tag in zip(open_tags, close_tags):
        open_idx = open_tag.span()[0]
        close_idx = close_tag.span()[1]
        split_idxs.append(open_idx)
        split_idxs.append(close_idx)

    if split_idxs[0] != 0:
        split_idxs.insert(0, 0)

    if split_idxs[-1] != len(markdown):
        split_idxs.append(len(markdown))

    for i, to_idx in enumerate(split_idxs[1:], start=1):
        from_idx = split_idxs[i-1]
        updated_markdown.append(markdown[from_idx:to_idx])

    for i, elem in enumerate(updated_markdown):
        if elem.startswith("<a"):
            soup = bs4.BeautifulSoup(elem, "html.parser")
            a_tag = soup.find("a")
            url = a_tag["href"]
            text = a_tag.text

            # TODO: use rel/ref for links to other pages on the domain.
            link = f"[{text}]({url})"
            updated_markdown[i] = link

    return "".join(updated_markdown)


def format_file(fpath, max_line_len=80):
    formatted_lines = []

    header = []
    post = []
    with open(fpath, "r") as f:
        header_delimiter_count = 0
        for line in f:
            # Remove trailing whitespace/newline.
            line = line.rstrip()
            if header_delimiter_count >= 2:
                # Replace en dashes, em dashes, degree sign with html code.
                line = line.replace("–", "&#8211;")
                line = line.replace("—", "&#8212;")
                line = line.replace("°", "&#176;")
                post.append(line)
            else:
                if line == "---":
                    header_delimiter_count += 1
                header.append(line)

    formatted_post = []

    i = -1
    while (i := i + 1) < len(post):
        line = post[i]
        if line != "\n":
            line = post[i].strip()

        # If this is a code block enclosed in <pre><code> tags, parse with BS.
        if line.startswith("<pre"):
            code_block = []
            while "</pre>" not in post[i]:
                code_block.append(post[i])
                i += 1
            code_block.append(post[i])
            soup = bs4.BeautifulSoup("\n".join(code_block), "html.parser")
            pre_tag = soup.find("pre")
            code_tag = soup.find("code")

            # Line numbering.
            line_num_str = ""
            if "line-numbers" in pre_tag.get("class", ""):
                line_num_start_str = ""
                if pre_tag.get("data-start", ""):
                    line_num_start_str = f",linenostart={pre_tag['data-start']}"
                line_num_str = f'"linenos=true{line_num_start_str}" '

            language = "plain"
            code_tag_class = code_tag.get("class")
            if (
                code_tag_class
                and code_tag_class[0].startswith("language-")
                and code_tag_class[0] != "language-none"
            ):
                language = code_tag_class[0][len("language-"):]

            shortcode = f"{{{{< highlight {language} {line_num_str}>}}}}"

            formatted_post.append(shortcode)
            formatted_post.extend(soup.text.split("\n"))
            formatted_post.append("{{< / highlight >}}")
        else:
            # TODO: Escape double underscore filenames/variables when not in a
            # code block or an html tag.
            #if "__" in line:
            #    soup = bs4.BeautifulSoup(line, "html.parser")

            if len(line) > max_line_len:
                split_lines = split_line(line)
                formatted_post.extend(split_lines)
            else:
                formatted_post.append(line)

    
    formatted_text = header + formatted_post
    formatted_text = "\n".join(formatted_text)

    # Replace hyperlinks with markdown or hugo shortcode.
    formatted_text = format_hyperlinks(formatted_text)
    return formatted_text


def format_post(src_fpath, dst_fpath):
    formatted_text = format_file(src_fpath)
    with open(dst_fpath, "w") as f:
        f.write(formatted_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "src", type=str, help="Source markdown file or directory of files"
    )
    parser.add_argument(
        "dst", type=str, help="Destination markdown file or directory"
    )
    args = parser.parse_args()

    if "*" in args.src:
        src_fpaths = glob.glob(args.src)
        src_fnames = [os.path.split(fpath)[1] for fpath in src_fpaths]
        dst_fpaths = [os.path.join(args.dst, fname) for fname in src_fnames]
    elif os.path.isdir(args.src):
        src_fnames = os.listdir(args.src)
        src_fpaths = [os.path.join(args.src, fname) for fname in src_fnames]
        dst_fpaths = [os.path.join(args.dst, fname) for fname in src_fnames]
    else:
        src_fpaths = [args.src]
        if os.path.isdir(args.dst):
            _, src_fname = os.path.split(args.src)
            dst_fpaths = [os.path.join(args.dst, src_fname)]
        else:
            dst_fpaths = [args.dst]

    start_t = time.time()
    pool = ThreadPoolExecutor()
    for src_fpath, dst_fpath in zip(src_fpaths, dst_fpaths):
        format_post(src_fpath, dst_fpath)
        #pool.submit(format_post, src_fpath, dst_fpath)
    pool.shutdown()
    elapsed = time.time() - start_t
    print(f"Elapsed: {elapsed}")
