"""Generic, standard-library-only client archive builder and verified publisher."""

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

POLICY_VERSION = "public-client-v1"
REPOSITORY = "letterZhao/bi-agent-client"
SKILL = ".agents/skills/bi-query/"
CLIENT_FILES = (
    SKILL + "SKILL.md",
    *(
        SKILL + "references/" + name + ".md"
        for name in ("interfaces", "cohort-metrics", "report-templates", "report-authorization")
    ),
    *(
        "docs/" + name
        for name in (
            "codex.toml.example",
            "claude.mcp.json.example",
            "deepseek-harness.yaml.example",
            "workbuddy.mcp.json.example",
            "client-compatibility.md",
        )
    ),
    "README.md",
)
SUPPORT_FILES = ("scripts/client_release.py", ".github/workflows/release.yaml", "release-notes.md")
TREE_FILES = set(CLIENT_FILES) | set(SUPPORT_FILES) | {"release-input.json"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def fail(rule):
    # Reports deliberately exclude the matching value, arbitrary paths and API bodies.
    raise ValueError("PUBLIC_" + rule)


def scan_text(name, data):
    if len(data) > 1_000_000 or b"\x00" in data:
        fail("TEXT_FORMAT")
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        fail("TEXT_FORMAT")
    rules = {
        "PRIVATE_KEY": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "PROVIDER_TOKEN": r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b",
        "IP_ADDRESS": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        "COOKIE_HEADER": r"(?im)^\s*(?:set-cookie|cookie)\s*:\s*[^\r\n]+",
        "LOCAL_PATH": r"/(?:Users|home)/[\w.-]+/|[A-Z]:[\\/](?:Users|work)[\\/]",
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "INTERNAL_ROUTE": r"/(?:hologres|system|project|template)/[A-Za-z]",
        "SQL": r"(?i)\b(?:select\s+.+?\s+from|insert\s+into|update|join)\s+[\w]+\.[\w]+",
        "PROVENANCE": r"(?:src/" + r"main/java/|src/" + r"views/|\.java:[0-9]+|bi_" + r"dim\.)",
    }
    for rule, pattern in rules.items():
        matches = list(re.finditer(pattern, text))
        if rule == "EMAIL":
            matches = [m for m in matches if m[0] != "client-release@users.noreply.github.com"]
        if matches:
            fail(rule)
    for match in re.finditer(
        r"(?im)^\s*(?:[\"']?)(?:password|passwd|token|cookie|username|account|api_key|access_key|secret_key|client_secret)[\"']?\s*[:=]\s*[\"']?([^\s\"',;]+)",
        text,
    ):
        if not re.fullmatch(r"<[A-Z_]+>|\$\{[A-Z_:]+\}", match[1]):
            fail("CREDENTIAL_ASSIGNMENT")
    placeholder = r"(?:\$\{(?:credential:)?BI_ACCESS_TOKEN\}|<PERSONAL_BI_TOKEN>)"
    for match in re.finditer(r"(?i)\bBearer\s+([^\s\"'`,}]+(?:\})?)", text):
        value = match[1].rstrip("。；，.")
        # Descriptive prose is permitted; literal header values are not.
        if not re.fullmatch(placeholder, value) and re.search(
            r"(?i)(?:Authorization[^\n]{0,40}|['\"])\s*$", text[max(0, match.start() - 60) : match.start()]
        ):
            fail("BEARER_VALUE")
    for match in re.finditer(
        r"(?i)\b(?:password|passwd|api_key|access_key|secret_key|client_secret)\s*[\"']?\s*[:=]\s*[\"']([^\"'\n]+)",
        text,
    ):
        if not re.fullmatch(r"<[A-Z_]+>|\$\{[A-Z_]+\}", match[1]):
            fail("CREDENTIAL_VALUE")
    for match in re.finditer(r"https?://[^\s<>\"'`)}]+", text):
        url = urllib.parse.urlsplit(match[0])
        fixed_tag = (
            url.hostname == "github.com"
            and url.path == "/" + REPOSITORY + ".git"
            and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+_test|v[0-9]+\.[0-9]+\.[0-9]+", url.fragment)
        )
        if url.username or url.password or url.query or (url.fragment and not fixed_tag):
            fail("URL_CREDENTIAL")
        if url.hostname not in {
            "mcp.example.com",
            "github.com",
            "api.github.com",
            "uploads.github.com",
            "release-assets.githubusercontent.com",
        }:
            fail("SERVICE_ADDRESS")
        if url.hostname == "github.com" and not url.path.startswith("/" + REPOSITORY):
            fail("DESTINATION")


def descriptor(source_commit, version, count, files):
    return {
        "sourceCommit": source_commit,
        "serverVersion": version,
        "expectedToolCount": count,
        "audience": "public",
        "policyVersion": POLICY_VERSION,
        "files": {name: digest(data) for name, data in sorted(files.items())},
    }


def validate_payload(files, metadata):
    allowed = {"sourceCommit", "serverVersion", "expectedToolCount", "audience", "policyVersion", "files"}
    if set(metadata) not in (allowed, allowed | {"supportFiles"}):
        fail("DESCRIPTOR_FIELDS")
    if set(files) != set(CLIENT_FILES):
        fail("FILE_ALLOWLIST")
    if not re.fullmatch(r"[a-f0-9]{40}", metadata.get("sourceCommit", "")):
        fail("SOURCE_COMMIT")
    if not re.fullmatch(r"\d+\.\d+\.\d+", metadata.get("serverVersion", "")):
        fail("VERSION")
    if type(metadata.get("expectedToolCount")) is not int or metadata["expectedToolCount"] <= 0:
        fail("TOOL_COUNT")
    if metadata.get("audience") != "public" or metadata.get("policyVersion") != POLICY_VERSION:
        fail("POLICY")
    if metadata.get("files") != {name: digest(data) for name, data in sorted(files.items())}:
        fail("UNREVIEWED_CONTENT")
    for name, data in files.items():
        scan_text(name, data)


def read_payload(root):
    root = Path(root).resolve()
    files = {}
    for name in CLIENT_FILES:
        path = Path(root) / name
        if path.is_symlink() or not path.is_file() or any(p.is_symlink() for p in path.parents):
            fail("FILE_TYPE")
        files[name] = path.read_bytes()
    return files


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


def validate_tree(root):
    root = Path(root).resolve()
    actual = {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() or p.is_symlink()
        if ".git" not in p.relative_to(root).parts
    }
    if actual != TREE_FILES:
        fail("TREE_ALLOWLIST")
    for name in actual:
        path = root / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            fail("FILE_TYPE")
        scan_text(name, path.read_bytes())
    metadata = json.loads((root / "release-input.json").read_bytes())
    files = read_payload(root)
    validate_payload(files, metadata)
    if metadata.get("supportFiles") != {name: digest((root / name).read_bytes()) for name in SUPPORT_FILES}:
        fail("UNREVIEWED_SUPPORT")
    if (root / ".git").exists():
        if git(root, "status", "--porcelain", "--untracked-files=all"):
            fail("DIRTY_TREE")
        commits = git(root, "rev-list", "--all").splitlines()
        for commit in commits:
            # All reachable snapshots, messages and identities are public output.
            entries = git(root, "ls-tree", "-r", commit).splitlines()
            if any(not entry.startswith("100644 blob ") for entry in entries):
                fail("HISTORY_FILE_TYPE")
            names = [entry.split("\t", 1)[1] for entry in entries]
            if set(names) != TREE_FILES:
                fail("HISTORY_ALLOWLIST")
            message = git(root, "show", "-s", "--format=%B", commit)
            if not re.fullmatch(r"Client distribution [0-9]+\.[0-9]+\.[0-9]+(?:_test)?", message):
                fail("COMMIT_MESSAGE")
            identities = git(root, "show", "-s", "--format=%an%n%ae%n%cn%n%ce", commit).splitlines()
            if identities != ["Client Release Bot", "client-release@users.noreply.github.com"] * 2:
                fail("COMMIT_IDENTITY")
            raw = git(root, "cat-file", "commit", commit)
            headers = raw.split("\n\n", 1)[0].splitlines()
            for header in headers:
                if not re.fullmatch(
                    r"(?:tree|parent) [a-f0-9]{40}|(?:author|committer) Client Release Bot <client-release@users.noreply.github.com> [0-9]+ [+-][0-9]{4}",
                    header,
                ):
                    fail("COMMIT_HEADER")
            historical = {}
            for name in names:
                data = subprocess.check_output(["git", "-C", str(root), "show", commit + ":" + name])
                scan_text(name, data)
                historical[name] = data
            old_metadata = json.loads(historical["release-input.json"])
            validate_payload({name: historical[name] for name in CLIENT_FILES}, old_metadata)
            if old_metadata.get("supportFiles") != {name: digest(historical[name]) for name in SUPPORT_FILES}:
                fail("HISTORY_HASH")
        for tag in git(root, "tag", "--list").splitlines():
            if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+_test|v[0-9]+\.[0-9]+\.[0-9]+", tag):
                fail("TAG_NAME")
            raw = git(root, "cat-file", "tag", "refs/tags/" + tag)
            header, message = raw.split("\n\n", 1)
            if not re.fullmatch(
                r"object [a-f0-9]{40}\ntype commit\ntag "
                + re.escape(tag)
                + r"\ntagger Client Release Bot <client-release@users.noreply.github.com> [0-9]+ [+-][0-9]{4}",
                header,
            ):
                fail("TAG_METADATA")
            if message != "Client distribution " + tag:
                fail("TAG_MESSAGE")
    return files, metadata


def build(files, metadata, distribution_commit, tag, output):
    validate_payload(files, metadata)
    version = metadata["serverVersion"]
    if tag not in (version + "_test", "v" + version) or not re.fullmatch(
        r"[a-f0-9]{40}", distribution_commit
    ):
        fail("TAG_IDENTITY")
    target = Path(output) / tag
    if target.exists():
        raise FileExistsError("PUBLIC_OUTPUT_EXISTS")
    identity = {
        k: metadata[k]
        for k in ("sourceCommit", "serverVersion", "expectedToolCount", "audience", "policyVersion")
    }
    identity.update(distributionCommit=distribution_commit, releaseTag=tag)
    client = dict(files)
    client["release.json"] = encoded({**identity, "files": metadata["files"]})
    skill = {name.removeprefix(SKILL): data for name, data in files.items() if name.startswith(SKILL)}
    skill["release.json"] = encoded({**identity, "files": {n: digest(d) for n, d in sorted(skill.items())}})
    tar_data = io.BytesIO()
    with (
        gzip.GzipFile(filename="", mode="wb", fileobj=tar_data, mtime=0) as gz,
        tarfile.open(fileobj=gz, mode="w") as archive,
    ):
        for name, data in sorted(client.items()):
            info = tarfile.TarInfo("bi-agent-client/" + name)
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            archive.addfile(info, io.BytesIO(data))
    zip_data = io.BytesIO()
    with zipfile.ZipFile(zip_data, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(skill.items()):
            info = zipfile.ZipInfo("bi-query/" + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    artifacts = {
        f"bi-agent-client-{tag}.tar.gz": tar_data.getvalue(),
        f"bi-query-skill-{tag}.zip": zip_data.getvalue(),
    }
    artifacts["SHA256SUMS"] = "".join(
        digest(data) + "  " + name + "\n" for name, data in artifacts.items()
    ).encode()
    # Scan every uncompressed member, including manifests; metadata is generated with fixed ownership/time.
    for name, data in [*client.items(), *skill.items()]:
        scan_text(name, data)
    target.mkdir(parents=True)
    for name, data in artifacts.items():
        (target / name).write_bytes(data)
    return target


def verify_artifacts(files, metadata, distribution_commit, tag, directory):
    with tempfile.TemporaryDirectory() as tmp:
        expected = build(files, metadata, distribution_commit, tag, tmp)
        actual = Path(directory)
        if {p.name for p in actual.iterdir()} != {p.name for p in expected.iterdir()}:
            fail("ASSET_ALLOWLIST")
        for path in expected.iterdir():
            candidate = actual / path.name
            if candidate.is_symlink() or candidate.read_bytes() != path.read_bytes():
                fail("ASSET_MISMATCH")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


class Publisher:
    def __init__(self, token):
        if not token or any(c.isspace() for c in token):
            fail("PUBLISH_CREDENTIAL")
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, method, path, data=None, *, upload=False, missing_ok=False):
        host = "uploads.github.com" if upload else "api.github.com"
        url = "https" + f"://{host}/repos/{REPOSITORY}{path}"
        headers = {
            "Authorization": "Bear" + "er " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "client-release",
        }
        if data is not None:
            headers["Content-Type"] = "application/octet-stream" if upload else "application/json"
            data = data if upload else encoded(data)
        try:
            with self.opener.open(
                urllib.request.Request(url, data, headers, method=method), timeout=60
            ) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if missing_ok and error.code == 404:
                return None
            raise ValueError("PUBLIC_API_HTTP_" + str(error.code)) from None

    def download(self, asset_id):
        if type(asset_id) is not int or asset_id <= 0:
            fail("ASSET_ID")
        url = f"https://api.github.com/repos/{REPOSITORY}/releases/assets/{asset_id}"
        for _ in range(6):
            parts = urllib.parse.urlsplit(url)
            if parts.scheme != "https" or parts.username or parts.password:
                fail("DOWNLOAD_URL")
            headers = {"User-Agent": "client-release", "Accept": "application/octet-stream"}
            if parts.hostname == "api.github.com" and (parts.port or 443) == 443:
                headers["Authorization"] = "Bear" + "er " + self.token
            try:
                with self.opener.open(urllib.request.Request(url, headers=headers), timeout=60) as response:
                    return response.read()
            except urllib.error.HTTPError as error:
                if error.code not in (301, 302, 303, 307, 308):
                    raise ValueError("PUBLIC_DOWNLOAD_HTTP_" + str(error.code)) from None
                location = error.headers.get("Location")
                if not location:
                    fail("DOWNLOAD_REDIRECT")
                url = urllib.parse.urljoin(url, location)
        fail("DOWNLOAD_REDIRECT")

    def publish(self, root, tag, directory, ci_url):
        files, metadata = validate_tree(root)
        sha = git(root, "rev-parse", "HEAD")
        if git(root, "rev-parse", "refs/tags/" + tag + "^{commit}") != sha:
            fail("TAG_IDENTITY")
        verify_artifacts(files, metadata, sha, tag, directory)
        if not re.fullmatch(
            re.escape("https" + "://github.com/" + REPOSITORY) + r"/actions/runs/[1-9][0-9]*", ci_url
        ):
            fail("CI_URL")
        body = (Path(root) / "release-notes.md").read_text() + "\nCI: " + ci_url + "\n"
        body += "\nSHA256:\n" + (Path(directory) / "SHA256SUMS").read_text()
        scan_text("release-notes.md", body.encode())
        obj = self.request("GET", "/git/ref/tags/" + tag)["object"]
        if obj["type"] == "tag":
            obj = self.request("GET", "/git/tags/" + obj["sha"])["object"]
        if obj["type"] != "commit" or obj["sha"] != sha:
            fail("REMOTE_TAG")
        if self.request("GET", "/releases/tags/" + tag, missing_ok=True) is not None:
            fail("RELEASE_EXISTS")
        release = self.request(
            "POST",
            "/releases",
            {
                "tag_name": tag,
                "name": "BI client " + tag,
                "body": body,
                "draft": True,
                "prerelease": True,
            },
        )
        rid = release["id"]
        for path in sorted(Path(directory).iterdir()):
            self.request(
                "POST",
                f"/releases/{rid}/assets?name=" + urllib.parse.quote(path.name),
                path.read_bytes(),
                upload=True,
            )
        assets = self.request("GET", f"/releases/{rid}/assets?per_page=100")
        expected = {p.name: p.read_bytes() for p in Path(directory).iterdir()}
        if len(assets) != len(expected) or {a["name"] for a in assets} != set(expected):
            fail("REMOTE_ASSETS")
        for asset in assets:
            if self.download(asset["id"]) != expected[asset["name"]]:
                fail("REMOTE_BYTES")
        final = self.request("GET", "/git/ref/tags/" + tag)["object"]
        if final["type"] == "tag":
            final = self.request("GET", "/git/tags/" + final["sha"])["object"]
        if final["type"] != "commit" or final["sha"] != sha:
            fail("REMOTE_TAG")
        return self.request("PATCH", f"/releases/{rid}", {"draft": False, "prerelease": True})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build", "publish"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ci-url")
    args = parser.parse_args()
    try:
        files, metadata = validate_tree(args.root)
        sha = git(args.root, "rev-parse", "HEAD")
        if args.tag not in (metadata["serverVersion"] + "_test", "v" + metadata["serverVersion"]):
            fail("TAG_IDENTITY")
        if args.command == "build":
            if args.output is None or args.output.resolve().is_relative_to(args.root.resolve()):
                fail("OUTPUT_OUTSIDE_SOURCE")
            print(build(files, metadata, sha, args.tag, args.output))
        elif args.command == "publish":
            if not args.output or not args.ci_url:
                fail("ARGUMENTS")
            result = Publisher(os.environ.get("GH_TOKEN")).publish(
                args.root, args.tag, args.output, args.ci_url
            )
            print(
                json.dumps({"id": result["id"], "draft": result["draft"], "prerelease": result["prerelease"]})
            )
        else:
            print("PUBLIC_CHECK_OK")
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        message = (
            str(error)
            if isinstance(error, ValueError) and re.fullmatch(r"PUBLIC_[A-Z0-9_]+", str(error))
            else "PUBLIC_CHECK_FAILED"
        )
        parser.exit(1, message + "\n")


if __name__ == "__main__":
    main()
