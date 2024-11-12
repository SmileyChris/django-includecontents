from pdm.backend.hooks.version import scm

RELEASE_TAG = r"v(?P<version>[0-9]+(\.[0-9]+)+)"


def _major(scm_version: scm.SCMVersion) -> str:
    version = scm_version.version
    return f"{version.major + 1}.0"


def _minor(scm_version: scm.SCMVersion) -> str:
    version = scm_version.version
    return f"{version.major}.{version.minor + 1}"


def _patch(scm_version: scm.SCMVersion) -> str:
    version = scm_version.version
    return f"{version.major}.{version.minor}.{version.micro + 1}"


formatters = {
    "major": _major,
    "minor": _minor,
    "patch": _patch,
}


def next_version(part: str) -> str:
    """
    Get the next version based on the current version (as the latest git tag) and the part to increment.
    """
    formatter = formatters[part]
    version = scm.get_version_from_scm(
        ".",
        tag_regex=r"v(?P<version>[0-9]+(\.[0-9]+)+)",
    )
    if version is None:
        raise ValueError("No version found in git tags")
    return formatter(version)


def check_version_is_release() -> str:
    """
    Ensure the current version is a release version.
    """
    version = scm.get_version_from_scm(".")
    if version is None:
        raise ValueError("No version found in git tags")
    version = scm.default_version_formatter(version)
    if ".dev" in version:
        raise ValueError(f"Current version ({version}) is not a release version")
    return version


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print(f"{check_version_is_release()} is a release version")
        sys.exit(0)

    if len(sys.argv) != 2:
        raise ValueError("Expected a single 'part' argument (major, minor, or patch)")
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if part not in formatters:
        raise ValueError(f"Invalid part: {part}")

    print(next_version(part))
