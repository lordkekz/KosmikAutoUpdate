from functools import total_ordering


@total_ordering
class GitSemanticVersion:
    @property
    def major(self):
        return self._major

    @property
    def minor(self):
        return self._minor

    @property
    def patch(self):
        return self._patch

    @property
    def commits(self):
        return self._commits

    def __init__(self, major: int, minor: int, patch: int, commits: int = 0):
        self._major = major
        self._minor = minor
        self._patch = patch
        self._commits = commits

    @classmethod
    def parse(cls, string: str):
        temp = string.split("+")
        (a, b, c) = [int(x) for x in temp[0].split(".")]
        if len(temp) == 1:
            return GitSemanticVersion(a, b, c)
        else:
            return GitSemanticVersion(a, b, c, int(temp[-1]))

    def __str__(self):
        if self._commits == 0:
            return f"{self.major}.{self.minor}.{self.patch}"
        else:
            return f"{self.major}.{self.minor}.{self.patch}+{self.commits}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other: 'GitSemanticVersion'):
        if type(other) is not GitSemanticVersion:
            return NotImplemented
        return (self.major == other.major and self.minor == other.minor and
                self.patch == other.patch and self.commits == other.commits)

    def __gt__(self, other: 'GitSemanticVersion'):
        if type(other) is not GitSemanticVersion:
            return NotImplemented
        if self.major != other.major:
            return self.major > other.major
        if self.minor != other.minor:
            return self.minor > other.minor
        if self.patch != other.patch:
            return self.patch > other.patch
        return self.commits > other.commits


if __name__ == "__main__":
    print(GitSemanticVersion(1, 2, 3))
    print(GitSemanticVersion(1, 2, 3, 4))
    print(GitSemanticVersion.parse("4.3.2"))
    print(GitSemanticVersion.parse("4.3.2+1"))
