"""Generate the repository's portfolio dashboard README."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = ROOT / "dashboard"
CONFIG_PATH = DASHBOARD_DIR / "config.json"
TEMPLATE_PATH = DASHBOARD_DIR / "README_TEMPLATE.md"
README_PATH = ROOT / "README.md"
VALID_STATUSES = {"completed", "in_progress", "planned"}


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    repository = config["repository"]
    for field in ("owner", "name"):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", repository[field]):
            raise ValueError(f"Invalid GitHub repository {field}: {repository[field]!r}")

    if not isinstance(config["recent_commit_limit"], int) or config["recent_commit_limit"] < 1:
        raise ValueError("recent_commit_limit must be a positive integer")

    for section in ("roadmap", "milestones"):
        for item in config[section]:
            if item["status"] not in VALID_STATUSES:
                raise ValueError(f"Invalid {section} status: {item['status']!r}")

    return config


def fetch_json(url: str, token: str | None, timeout: int) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "portfolio-dashboard",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def github_data(config: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    repository = config["repository"]
    owner = quote(repository["owner"], safe="")
    name = quote(repository["name"], safe="")
    base_url = f"https://api.github.com/repos/{owner}/{name}"
    token = os.environ.get("GITHUB_TOKEN")
    timeout = config["api_timeout_seconds"]
    warnings: list[str] = []

    try:
        repo_data = fetch_json(base_url, token, timeout)
    except (HTTPError, URLError, TimeoutError) as error:
        repo_data = None
        warnings.append(f"Repository statistics unavailable: {error}")

    try:
        commit_data = fetch_json(
            f"{base_url}/commits?per_page={config['recent_commit_limit']}",
            token,
            timeout,
        )
    except (HTTPError, URLError, TimeoutError) as error:
        commit_data = []
        warnings.append(f"Recent commits unavailable: {error}")

    if not isinstance(commit_data, list):
        raise ValueError("GitHub returned an unexpected response for recent commits")
    return repo_data, commit_data, warnings


def format_date(value: str | None) -> str:
    if not value:
        return "Unavailable"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "Unavailable"
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d")


def markdown_text(value: str) -> str:
    return " ".join(value.replace("|", "\\|").split())


def status_label(status: str) -> str:
    return {
        "completed": "✅ Complete",
        "in_progress": "🔄 In progress",
        "planned": "◻️ Planned",
    }[status]


def render_list(items: list[str]) -> str:
    return " · ".join(f"`{markdown_text(item)}`" for item in items)


def render_roadmap(roadmap: list[dict[str, str]]) -> tuple[str, str]:
    completed = sum(item["status"] == "completed" for item in roadmap)
    progress = round(completed / len(roadmap) * 100) if roadmap else 0
    filled = round(progress / 10)
    progress_bar = f"`{'█' * filled}{'░' * (10 - filled)}` **{progress}%**"
    rows = [
        "| Status | Focus | Description |",
        "|:--|:--|:--|",
    ]
    rows.extend(
        f"| {status_label(item['status'])} | **{markdown_text(item['title'])}** | "
        f"{markdown_text(item['description'])} |"
        for item in roadmap
    )
    return progress_bar, "\n".join(rows)


def render_milestones(milestones: list[dict[str, str]]) -> str:
    return "\n".join(
        f"| {status_label(item['status'])} | **{markdown_text(item['title'])}** | "
        f"{markdown_text(item['description'])} |"
        for item in milestones
    )


def render_commits(commits: list[dict[str, Any]]) -> str:
    if not commits:
        return "_No recent commit data is available._"

    rows = [
        "| Commit | Message | Author | Date (UTC) |",
        "|:--|:--|:--|:--|",
    ]
    for item in commits:
        commit = item["commit"]
        sha = item["sha"]
        author = item.get("author") or {}
        author_name = author.get("login") or commit["author"]["name"]
        rows.append(
            f"| [`{sha[:7]}`]({item['html_url']}) | "
            f"{markdown_text(commit['message'].splitlines()[0])} | "
            f"{markdown_text(author_name)} | {format_date(commit['author'].get('date'))} |"
        )
    return "\n".join(rows)


def render_readme(config: dict[str, Any]) -> str:
    repo_data, commits, warnings = github_data(config)
    repository = config["repository"]
    if repo_data:
        stats = {
            "STARS": f"{repo_data.get('stargazers_count', 0):,}",
            "FORKS": f"{repo_data.get('forks_count', 0):,}",
            "WATCHERS": f"{repo_data.get('subscribers_count', repo_data.get('watchers_count', 0)):,}",
            "OPEN_ISSUES": f"{repo_data.get('open_issues_count', 0):,}",
            "REPO_UPDATED": format_date(repo_data.get("pushed_at")),
        }
        repository_url = repo_data.get("html_url", f"https://github.com/{repository['owner']}/{repository['name']}")
    else:
        stats = {
            "STARS": "—",
            "FORKS": "—",
            "WATCHERS": "—",
            "OPEN_ISSUES": "—",
            "REPO_UPDATED": "Unavailable",
        }
        repository_url = f"https://github.com/{repository['owner']}/{repository['name']}"

    generated_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    progress_bar, roadmap_table = render_roadmap(config["roadmap"])
    milestone_table = render_milestones(config["milestones"])
    warning_section = (
        "> **GitHub API notice:** " + " · ".join(markdown_text(warning) for warning in warnings) + "\n\n"
        if warnings
        else ""
    )
    replacements = {
        "OWNER_NAME": markdown_text(config["owner"]["name"]),
        "OWNER_DESCRIPTION": markdown_text(config["owner"]["description"]),
        "REPOSITORY_NAME": markdown_text(repository["name"]),
        "REPOSITORY_URL": repository_url,
        "PROFILE_URL": repository["profile_url"],
        "WEBSITE_URL": repository["website_url"],
        "GENERATED_DATE": generated_date,
        "REPO_UPDATED": stats["REPO_UPDATED"],
        "STARS": stats["STARS"],
        "FORKS": stats["FORKS"],
        "WATCHERS": stats["WATCHERS"],
        "OPEN_ISSUES": stats["OPEN_ISSUES"],
        "TECHNOLOGIES": render_list(config["technologies"]),
        "PROGRESS_BAR": progress_bar,
        "ROADMAP_TABLE": roadmap_table,
        "MILESTONE_TABLE": milestone_table,
        "RECENT_COMMITS": render_commits(commits),
        "API_NOTICE": warning_section.rstrip(),
    }

    with TEMPLATE_PATH.open(encoding="utf-8") as template_file:
        readme = template_file.read()
    for key, value in replacements.items():
        readme = readme.replace(f"{{{{{key}}}}}", value)

    unresolved = re.findall(r"\{\{[A-Z_]+\}\}", readme)
    if unresolved:
        raise ValueError(f"Unresolved README template placeholders: {', '.join(unresolved)}")
    return readme.rstrip() + "\n"


def main() -> int:
    config = load_config()
    readme = render_readme(config)
    README_PATH.write_text(readme, encoding="utf-8", newline="\n")
    print(f"Generated {README_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
