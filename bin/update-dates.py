#!/usr/bin/env python3
import os
import re
import subprocess

def get_git_root():
    try:
        return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()
    except Exception:
        return os.getcwd()

def get_git_date(filepath=None):
    cmd = ["git", "log", "-1", "--format=%cs"]
    if filepath:
        cmd += ["--", os.path.relpath(filepath)]
    try:
        date_str = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
        return date_str if date_str else None
    except Exception:
        return None

def get_changed_files():
    if "GITHUB_EVENT_PATH" in os.environ:
        try:
            import json
            with open(os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8") as f:
                event = json.load(f)
            before = event.get("before")
            if before and before != "0000000000000000000000000000000000000000":
                files = subprocess.check_output(["git", "diff", "--name-only", before, "HEAD"]).decode("utf-8").splitlines()
                return {f.strip() for f in files if f.strip()}
        except Exception as e:
            print(f"Note: failed to get changes using GITHUB_EVENT_PATH: {e}")

    try:
        subprocess.check_call(
            ["git", "rev-parse", "--verify", "HEAD~1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        files = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"]).decode("utf-8").splitlines()
        return {f.strip() for f in files if f.strip()}
    except Exception:
        try:
            files = subprocess.check_output(["git", "ls-files"]).decode("utf-8").splitlines()
            return {f.strip() for f in files if f.strip()}
        except Exception:
            return set()

def update_frontmatter_text(frontmatter_text, file_date):
    # Remove last_reviewed line
    lines = []
    for line in frontmatter_text.splitlines():
        if re.match(r"^\s*last_reviewed\s*:", line):
            continue
        lines.append(line)

    # Let's check if substitutions: exists as a top-level key
    substitutions_idx = -1
    date_idx = -1
    in_substitutions = False

    for idx, line in enumerate(lines):
        if re.match(r"^substitutions\s*:", line):
            substitutions_idx = idx
            in_substitutions = True
            continue
        if in_substitutions:
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                in_substitutions = False
            elif re.match(r"^\s+date\s*:", line):
                date_idx = idx
                break

    if substitutions_idx != -1:
        if date_idx != -1:
            indent = re.match(r"^(\s+)", lines[date_idx]).group(1)
            lines[date_idx] = f'{indent}date: "{file_date}"'
        else:
            lines.insert(substitutions_idx + 1, f'  date: "{file_date}"')
    else:
        lines.append("substitutions:")
        lines.append(f'  date: "{file_date}"')

    return "\n".join(lines) + "\n"

def update_markdown_frontmatter(filepath, file_date):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if match:
        frontmatter_content = match.group(1)
        body_content = match.group(2)
        new_frontmatter = update_frontmatter_text(frontmatter_content, file_date)
        new_content = f"---\n{new_frontmatter.strip()}\n---\n{body_content}"
    else:
        new_frontmatter = f"substitutions:\n  date: \"{file_date}\"\n"
        new_content = f"---\n{new_frontmatter.strip()}\n---\n{content}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated front-matter in {os.path.relpath(filepath)} (date: {file_date})")

def update_myst_yml_text(myst_text, repo_date):
    lines = myst_text.splitlines()
    in_project = False
    in_substitutions = False
    project_indent = -1
    substitutions_indent = -1

    for idx, line in enumerate(lines):
        if re.match(r"^project\s*:", line):
            in_project = True
            project_indent = len(line) - len(line.lstrip())
            continue

        if in_project:
            stripped = line.lstrip()
            if stripped and not line.startswith(" ") and not line.startswith("\t"):
                in_project = False
                in_substitutions = False
                continue

            if not in_substitutions and re.match(r"^\s+date\s*:", line):
                indent = re.match(r"^(\s+)", line).group(1)
                lines[idx] = f'{indent}date: {repo_date}'
                continue

            if re.match(r"^\s+substitutions\s*:", line):
                in_substitutions = True
                substitutions_indent = len(line) - len(line.lstrip())
                continue

            if in_substitutions:
                indent_len = len(line) - len(line.lstrip())
                if stripped and indent_len <= substitutions_indent:
                    in_substitutions = False
                elif re.match(r"^\s+date\s*:", line):
                    indent = re.match(r"^(\s+)", line).group(1)
                    lines[idx] = f'{indent}date: "{repo_date}"'
                    in_substitutions = False

    return "\n".join(lines) + "\n"

def update_myst_yml(repo_date):
    if not os.path.exists("myst.yml"):
        return
    with open("myst.yml", "r", encoding="utf-8") as f:
        content = f.read()

    new_content = update_myst_yml_text(content, repo_date)

    with open("myst.yml", "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated myst.yml (date: {repo_date})")

def main():
    git_root = get_git_root()
    cwd_myst = os.path.abspath("myst.yml")
    cwd_readme = os.path.abspath("README.md")

    repo_date = get_git_date()
    if not repo_date:
        print("⚠️ Could not retrieve repository-wide git date. Skipping updates.")
        return

    print(f"Repository-wide last updated date: {repo_date}")
    if os.path.exists(cwd_myst):
        update_myst_yml(repo_date)

    if os.path.exists(cwd_readme):
        update_markdown_frontmatter(cwd_readme, repo_date)

    changed_files = get_changed_files()
    for filepath in changed_files:
        abs_path = os.path.join(git_root, filepath)
        if not abs_path.endswith(".md"):
            continue
        if abs_path == cwd_readme:
            continue
        if not os.path.exists(abs_path):
            continue
        
        file_date = get_git_date(abs_path)
        if not file_date:
            file_date = repo_date

        update_markdown_frontmatter(abs_path, file_date)

if __name__ == "__main__":
    main()
