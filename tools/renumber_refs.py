import argparse
import pathlib
import re


def renumber_links(fpath: pathlib.Path):
    with open(fpath, "r") as f:
        lines = f.readlines()

    old_refs = {}
    reflist_expr = r"\[(\d+)\]: (.+)$"

    i = len(lines) - 1
    while (line := lines[i]) != "\n":
        match = re.match(reflist_expr, line)
        refnum, link = match.groups()
        old_refs[int(refnum)] = link.strip()
        i -= 1

    link_to_new_refnum = {}
    updated_lines = []

    ref_expr = r"(\[.+?\])(\[\d+\])"
    for j, line in enumerate(lines[:i+1]):
        match_iter = re.finditer(ref_expr, line)
        matches = [match for match in match_iter]
        if matches:
            updated_line = []
            last_end_pos = 0

            for match in matches:
                start_pos = match.start()
                end_pos = match.end()

                preceding_text = line[last_end_pos:start_pos]
                updated_line.append(preceding_text)

                groups = match.groups()
                old_refnum = int(groups[1][1:-1])
                link = old_refs[old_refnum]

                if link in link_to_new_refnum:
                    new_refnum = link_to_new_refnum[link]
                else:
                    new_refnum = len(link_to_new_refnum)
                    link_to_new_refnum[link] = new_refnum

                updated_text = f"{groups[0]}[{new_refnum}]"
                updated_line.append(updated_text)
                last_end_pos = end_pos

            updated_line.append(line[last_end_pos:])
            updated_line = "".join(updated_line)
            line = updated_line

        updated_lines.append(line)

    # Update the reflist at the end of the file.
    new_refs = {refnum: link for link, refnum in link_to_new_refnum.items()}

    for refnum in sorted(new_refs.keys()):
        link = new_refs[refnum]
        line = f"[{refnum}]: {link}\n"
        updated_lines.append(line)

    with open(fpath, "w") as f:
        f.writelines(updated_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=pathlib.Path)
    args = parser.parse_args()
    renumber_links(args.path)
