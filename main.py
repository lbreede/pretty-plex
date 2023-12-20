import os
import re
from dataclasses import dataclass, field
from typing import Optional, Self
from enum import Enum, auto

HOME_DIR = os.path.expanduser("~")
PLEX_DIR = os.path.join(HOME_DIR, "Plex")
PLEX_MOVIES_DIR = os.path.join(PLEX_DIR, "Movies")


IGNORED_FILES = {".DS_Store"}


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


@dataclass
class Movie:
    title: str
    year: int
    extension: Optional[str] = None
    edition: Optional[str] = None
    imdb: Optional[str] = None
    tmdb: Optional[str] = None

    @classmethod
    def parse(cls, name: str, extension: Optional[str] = None) -> Self:
        regexp = r"(.+) \((\d{4})\)(.*)"
        match = re.match(regexp, name)
        if match is None:
            raise ValueError(f"Invalid name: {name!r}")
        title, year, metadata = match.groups()
        movie = cls(title=title, year=int(year), extension=extension)

        # Scuffed but working
        # TODO: Handle more pt/cd/disc numbers (cd1, cd2, etc.)
        if metadata:
            metadata = metadata.lstrip(" {").rstrip(" }")
            metadata = metadata.split("} {")
            for item in metadata:
                key, value = item.split("-", 1)
                if key == "imdb":
                    movie.imdb = value
                elif key == "tmdb":
                    movie.tmdb = value
                elif key == "edition":
                    movie.edition = value
                else:
                    raise ValueError(f"Invalid metadata key: {key!r}")
        return movie

    @classmethod
    def parse_directory(cls, dirname: str) -> Self:
        return cls.parse(dirname)

    @classmethod
    def parse_file(cls, filename: str) -> Self:
        filename, file_extension = os.path.splitext(filename)
        return cls.parse(filename, file_extension)

    @property
    def full_title(self) -> str:
        title = self.title
        if self.edition is not None:
            title += f" [{self.edition}]"

        # Uncomment to include file extension in title
        # if self.extension is not None:
        #     title += f"{self.extension}"

        return title

    def __str__(self) -> str:
        string = f"{self.title} ({self.year})"
        if self.edition:
            string += f" [{self.edition}]"
        return string


@dataclass
class Collection:
    collection: list[Movie] = field(default_factory=list)

    @classmethod
    def parse_path(cls, path: str) -> Self:
        _, dirs, files = next(os.walk(path))
        collection = cls()
        for dirname in dirs:
            movie = Movie.parse_directory(dirname)
            collection.add_movie(movie)
        for filename in files:
            if filename in IGNORED_FILES:
                continue
            movie = Movie.parse_file(filename)
            collection.add_movie(movie)
        return collection

    def extend_from_path(self, path: str) -> None:
        _, dirs, files = next(os.walk(path))
        for dirname in dirs:
            movie = Movie.parse_directory(dirname)
            self.add_movie(movie)
        for filename in files:
            if filename in IGNORED_FILES:
                continue
            movie = Movie.parse_file(filename)
            self.add_movie(movie)

    def add_movie(self, movie: Movie, do_sort: bool = True) -> None:
        self.collection.append(movie)
        if do_sort:
            self.sort()

    def sort(self) -> None:
        self.collection.sort(key=lambda movie: movie.title)

    def _get_width(self, attr: str) -> int:
        width = len(attr)
        for movie in self.collection:
            if getattr(movie, attr) is not None:
                width = max(width, len(getattr(movie, attr)))
        return width

    @staticmethod
    def _strong(string: str) -> str:
        return f"{bcolors.BOLD}{bcolors.OKGREEN}{string}{bcolors.ENDC}"

    def _table(self) -> str:
        title_width = self._get_width("full_title")
        imdb_width = self._get_width("imdb")
        tmdb_width = self._get_width("tmdb")

        title_line = "─" * title_width
        imdb_line = "─" * imdb_width
        tmdb_line = "─" * tmdb_width

        index_head = self._strong("   #")
        title_head = self._strong("Title".ljust(title_width))
        year_head = self._strong("Year")
        imdb_head = self._strong("IMDb".center(imdb_width))
        tmdb_head = self._strong("TMDB".center(tmdb_width))

        string = f"╭──────┬─{title_line}─┬──────┬─{imdb_line}─┬─{tmdb_line}─╮\n"
        string += f"│ {index_head} │ {title_head} │ {year_head} │ {imdb_head} │ {tmdb_head} │\n"
        string += f"├──────┼─{title_line}─┼──────┼─{imdb_line}─┼─{tmdb_line}─┤\n"

        for i, movie in enumerate(self.collection):
            index = self._strong(str(i + 1).rjust(4))
            title = movie.full_title.ljust(title_width)
            if movie.extension is not None:
                title = f"{bcolors.OKBLUE}{title}{bcolors.ENDC}"
            year = movie.year
            imdb = (movie.imdb or " -").ljust(imdb_width)
            tmdb = (movie.tmdb or " -").ljust(tmdb_width)
            string += f"│ {index} │ {title} │ {year} │ {imdb} │ {tmdb} │\n"

        string += f"╰──────┴─{title_line}─┴──────┴─{imdb_line}─┴─{tmdb_line}─╯"
        return string

    def __str__(self) -> str:
        return self._table()


def main() -> None:
    collection = Collection.parse_path(PLEX_MOVIES_DIR)
    print(collection)


if __name__ == "__main__":
    main()
