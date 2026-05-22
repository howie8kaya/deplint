"""Built-in checks for dependency file analysis."""

from collections import defaultdict

from .models import Issue, IssueCode, IssueSeverity
from .parser import Requirement


def check_unpinned(requirements: list[Requirement]) -> list[Issue]:
    """Flag any dependency that is not pinned to an exact version."""
    issues = []
    for req in requirements:
        if not req.is_pinned():
            issues.append(
                Issue(
                    code=IssueCode.UNPINNED_DEPENDENCY,
                    severity=IssueSeverity.WARNING,
                    message=f"'{req.name}' is not pinned to an exact version",
                    package=req.name,
                    line_number=req.line_number,
                    suggestion=f"pin with {req.name}=={req.version or '<version>'}" ,
                )
            )
    return issues


def check_duplicates(requirements: list[Requirement]) -> list[Issue]:
    """Detect the same package listed more than once."""
    seen: dict[str, list[Requirement]] = defaultdict(list)
    for req in requirements:
        seen[req.name.lower()].append(req)

    issues = []
    for name, reqs in seen.items():
        if len(reqs) > 1:
            lines = ", ".join(str(r.line_number) for r in reqs)
            issues.append(
                Issue(
                    code=IssueCode.DUPLICATE_DEPENDENCY,
                    severity=IssueSeverity.ERROR,
                    message=f"'{reqs[0].name}' is listed {len(reqs)} times (lines {lines})",
                    package=reqs[0].name,
                    line_number=reqs[0].line_number,
                    suggestion="remove duplicate entries",
                )
            )
    return issues


def check_conflicts(requirements: list[Requirement]) -> list[Issue]:
    """Detect obvious version conflicts (e.g. ==1.0 and ==2.0 for same package)."""
    pinned: dict[str, Requirement] = {}
    issues = []

    for req in requirements:
        key = req.name.lower()
        if req.is_pinned():
            if key in pinned and pinned[key].version != req.version:
                issues.append(
                    Issue(
                        code=IssueCode.CONFLICTING_VERSIONS,
                        severity=IssueSeverity.ERROR,
                        message=(
                            f"'{req.name}' pinned to conflicting versions: "
                            f"{pinned[key].version} (line {pinned[key].line_number}) "
                            f"vs {req.version} (line {req.line_number})"
                        ),
                        package=req.name,
                        line_number=req.line_number,
                    )
                )
            else:
                pinned[key] = req
    return issues


ALL_CHECKS = [check_unpinned, check_duplicates, check_conflicts]
