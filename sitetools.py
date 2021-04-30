#!/usr/bin/python3

import argparse
import base64
import pathlib
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


def build():
    proc = subprocess.run(
        "hugo", stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    print(proc.stdout.decode())
    if proc.returncode != 0:
        print(proc.stderr.decode())

    return proc.returncode


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
    return parser


def validate_args(args: argparse.Namespace):
    if args.action in ("build", "encode", "decode"):
        assert args.secrets, "Path to secrets file missing"

    if (
        args.action in ("encode", "decode", "deploy")
        or (args.action == "build" and args.deploy)
    ):
        assert args.output, "Path to output file missing"


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
        pass
