#!/usr/bin/python3

import argparse
import base64
import configparser
import pathlib
import shutil
import subprocess
from typing import Dict, List


def read_secrets_file(fpath: pathlib.Path) -> dict:
    """
    Args:
        fpath: Text file where each line corresponds to a value per the schema:
            address: your email address
            ses_host: AWS SES server name
            ses_username: AWS SES SMTP username
            ses_password: AWS SES SMTP password
            isso_port: Isso server listen port (should match Apache config)
            isso_password: Isso web interface admin password
    Returns:
        a dict where each key/value corresponds to the above schema.
    """
    with open(fpath, "r") as f:
        lines = [line.strip() for line in f]

    secrets = {
        "address": lines[0],
        "ses_host": lines[1],
        "ses_username": lines[2],
        "ses_password": lines[3],
        "isso_port": lines[4],
        "isso_password": lines[5],
    }
    return secrets


def write_secrets_file(secrets: Dict[str, str], fpath: pathlib.Path) -> None:
    """
    Args:
        secrets: A dict as returned by :func:`read_secrets_file`.
        fpath: Path to output file.
    """
    keys = [
        "address", "ses_host", "ses_username", "ses_password", "isso_port",
        "isso_password",
    ]
    with open(fpath, "w") as f:
        for k in keys:
            f.write(secrets[k] + "\n")


def encode_secrets(secrets: Dict[str, str]) -> None:
    """
    Convert the values of a dict to base64.

    Args:
        secrets: Dict returned by :func:`read_secrets_file` containing
            plaintext, unencoded values.
    """
    for k, v in secrets.items():
        secrets[k] = base64.b64encode(v.encode("utf-8")).decode("utf-8")


def decode_secrets(secrets: Dict[str, str]) -> None:
    """
    Convert the values of a dict from base64 to plaintext.

    Args:
        secrets: Dict returned by :func:`read_secrets_file` containing
            base64-encoded values.
    """
    for k, v in secrets.items():
        secrets[k] = base64.b64decode(v.encode("utf-8")).decode("utf-8")


def encode_secrets_file(src_fpath: pathlib.Path, dst_fpath: pathlib.Path):
    """
    Read a secrets file `src_fpath` with unencoded values and write out a
    base64-encoded version of it to `dst_fpath`.
    """
    secrets = read_secrets_file(src_fpath)
    encode_secrets(secrets)
    write_secrets_file(secrets, dst_fpath)


def decode_secrets_file(src_fpath: pathlib.Path, dst_fpath: pathlib.Path):
    """
    Read a secrets file `src_fpath` with base64-encoded values and write out a
    decoded version of it to `dst_path`.
    """
    secrets = read_secrets_file(src_fpath)
    decode_secrets(secrets)
    write_secrets_file(secrets, dst_fpath)


def insert_isso_config_secrets(
    src_fpath: pathlib.Path, dst_fpath: pathlib.Path, secrets: Dict[str, str]
):
    """
    Args:
        src_fpath: Path to Isso config file (without secrets)
        dst_fpath: Path to output Isso config file (with secrets inserted).
        secrets: Decoded secrets dict from secrets file (see
            :func:`read_secrets_file`).
    """
    config = configparser.ConfigParser()
    config.read(src_fpath)

    config["server"]["listen"] = f"http://localhost:{secrets['isso_port']}"
    config["admin"]["password"] = secrets["isso_password"]

    config["smtp"]["username"] = secrets["ses_username"]
    config["smtp"]["password"] = secrets["ses_password"]
    config["smtp"]["host"] = secrets["ses_host"]
    config["smtp"]["to"] = secrets["address"]
    config["smtp"]["from"] = f'"Isso" <{secrets["address"]}>'

    with open(dst_fpath, "w") as f:
        config.write(f)


def build_site(secrets_fpath: pathlib.Path):
    """
    TODO
    """
    build_dir = pathlib.Path("./public")

    if build_dir.exists():
        # Delete if a previous build exists to ensure nothing from a previous
        # build is inadvertently deployed/preserved.
        shutil.rmtree(build_dir)

    proc = subprocess.run(
        "hugo", stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())

    print(proc.stdout.decode())

    # Fix invalid Last Modified date for `public` directory set by Hugo.
    build_dir.touch()

    # Update contact.php with the correct email address from secrets.
    contact_php_fpath = pathlib.Path("public/php/contact.php")

    lines = []
    with open(contact_php_fpath, "r") as f:
        for line in f:
            if line.startswith("$secrets_file ="):
                line = f"$secrets_file = '{secrets_fpath}';\n"
            lines.append(line)
    with open(contact_php_fpath, "w") as f:
        f.writelines(lines)


def deploy_site(deploy_dir: pathlib.Path, delete_existing: bool = False):
    """
    Copy the built site files (`./public/*`) to the deploy dir (e.g.,
    `/var/www/nrsyed.com/public_html`).

    Args:
        deploy_dir: Path to the Apache site directory.
        delete_existing: If `deploy_dir` exists, delete the entire directory
            tree before copying files.
    """
    if deploy_dir_exists and delete_existing:
        shutil.rmtree(deploy_dir)

    build_dir = pathlib.Path("public")
    shutil.copytree(build_dir, deploy_dir)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", type=str, choices=["build", "deploy", "encode", "decode"],
        help="build (without deploying), deploy (without building), or "
            "encode/decode a secrets file"
    )
    parser.add_argument(
        "-s", "--secrets", type=pathlib.Path,
        help="Path to (input) secrets file; required for build, encode, and "
            "decode options"
    )
    parser.add_argument(
        "-o", "--output", type=pathlib.Path,
        help="Output path; required for build --deploy, deploy, encode, and "
            "decode options"
    )
    parser.add_argument(
        "-d", "--deploy", action="store_true",
        help="Use with build option to deploy after building"
    )
    parser.add_argument(
        "--isso-src", type=pathlib.Path, default="isso.cfg.nosecrets",
        help="Path to src Isso config (without secrets or with false secrets)"
    )
    parser.add_argument(
        "--isso-dst", type=pathlib.Path, default="isso.cfg",
        help="Path to output Isso config (with secrets from secrets file)"
    )
    return parser


def validate_args(args: argparse.Namespace):
    if args.action in ("build", "encode", "decode"):
        assert args.secrets, "Path to secrets file missing"

    if (
        args.action in ("encode", "decode", "deploy")
        or (args.action == "build" and args.deploy)
    ):
        assert args.output, "Path to output file/directory missing"


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    if args.secrets:
        args.secrets = args.secrets.expanduser().resolve()
    if args.output:
        args.output = args.output.expanduser().resolve()

    validate_args(args)

    if args.action == "encode":
        encode_secrets_file(args.secrets, args.output)
    elif args.action == "decode":
        decode_secrets_file(args.secrets, args.output)
    else:
        build = args.action == "build"
        deploy = (args.action == "deploy") or (build and args.deploy)

        if build:
            secrets = read_secrets_file(args.secrets)
            decode_secrets(secrets)
            insert_isso_config_secrets(
                args.isso_src, args.isso_dst, secrets
            )
            build_site(args.secrets)
        if deploy:
            raise RuntimeWarning("Will not work unless you are superuser")
            deploy_site(args.output, delete_existing=True)
