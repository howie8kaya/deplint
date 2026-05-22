"""Parser for requirements.txt style dependency files."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Requirement:
    name: str
    version: Optional[str] = None
    operator: Optional[str] = None
    line_number: int = 0
    raw: str = ""
    extras: list = field(default_factory=list)

    def is_pinned(self) -> bool:
        return self.operator == "=="


# Matches: package[extra1,extra2]>=1.0.0
REQ_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)"
    r"(?:\[(?P<extras>[^\]]+)\])?"
    r"(?:\s*(?P<op>==|>=|<=|!=|~=|>|<)\s*(?P<version>[\w.*+-]+))?"
    r"\s*(?:#.*)?$"
)


def parse_requirements(content: str) -> list[Requirement]:
    """Parse requirements.txt content and return a list of Requirement objects."""
    requirements = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        line = line.strip()

        # Skip empty lines, comments, and options like -r or --index-url
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        match = REQ_PATTERN.match(line)
        if not match:
            continue

        extras_raw = match.group("extras")
        extras = [e.strip() for e in extras_raw.split(",")] if extras_raw else []

        req = Requirement(
            name=match.group("name"),
            version=match.group("version"),
            operator=match.group("op"),
            line_number=line_number,
            raw=line,
            extras=extras,
        )
        requirements.append(req)

    return requirements


def parse_requirements_file(filepath: str) -> list[Requirement]:
    """Read and parse a requirements file from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_requirements(content)
