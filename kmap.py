from dataclasses import dataclass


class CycleList(list):
    def __getitem__(self, index):
        if len(self) == 0:
            if index > 0:
                raise IndexError()
            else:
                return super().__getitem(index)
        return super().__getitem__(index % len(self))


@dataclass
class Point:
    x: int
    y: int

    def __hash__(self):
        return self.x ** 3 + self.y ** 4


@dataclass
class Coordinates:
    top_x: int
    top_y: int
    bot_x: int
    bot_y: int

    def to_points(self, row_size=None, column_size=None):
        if row_size != column_size and None in (row_size, column_size):
            raise ValueError(
                "row_size and column_size must be both None or both integer"
            )
        # TODO? do more type checking here

        points = set()
        for x in range(self.top_x, self.bot_x + 1):
            for y in range(self.top_y, self.bot_y + 1):
                points.add(Point(x=x, y=y))

        if row_size is None:
            return points

        points_ = set()
        for point in points:
            points_.add(Point(x=point.x % column_size, y=point.y % row_size))

        return points_

    def __add__(self, coords):
        if isinstance(coords, Coordinates):
            return Coordinates(
                self.top_x + coords.top_x,
                self.top_y + coords.top_y,
                self.bot_x + coords.bot_x,
                self.bot_y + coords.bot_y,
            )
        else:
            raise TypeError()

    def __hash__(self):
        return sum(
            map(
                lambda iv: 2 ** iv[0] + iv[1],
                enumerate((self.top_x, self.top_y, self.bot_x, self.bot_y)),
            )
        )


class MultiCharVarError(ValueError):
    pass


class TooManyMintermsError(ValueError):
    pass


class TooGreatMintermError(ValueError):
    pass


class InvalidVarNumber(ValueError):
    pass


class KMap:
    def __init__(self, minterms, variables):
        if any(filter(lambda v: len(v) != 1, variables)):
            raise MultiCharVarError()
        if any(filter(lambda v: 2 ** len(variables) <= v, minterms)):
            raise TooGreatMintermError()
        if len(minterms) > 2 ** len(variables):
            raise TooManyMintermsError()
        if len(variables) not in (2, 3, 4):
            raise InvalidVarNumber()

        self.variables = variables
        self.minterms = minterms
        self.row_size = 4 if len(variables) in (3, 4) else 2
        self.column_size = 2 if len(variables) in (2, 3) else 4
        flatten_map = [0] * (2 ** len(variables))
        for minterm in minterms:
            flatten_map[minterm] = 1

        self.map_ = CycleList()
        for i in range(0, len(flatten_map), self.row_size):
            self.map_.append(CycleList(flatten_map[i : i + self.row_size]))

        self.simplified = ""
        self.taken = set()
        if all(flatten_map):
            self.simplified = "1"
            self.taken.add(Coordinates(0, 0, self.row_size, self.column_size))

        if all(map(lambda i: not i, flatten_map)):
            self.simplified = "0"

        if self.simplified == "":
            flatten_map_prototype = []
            for i in range(2 ** len(variables)):
                flatten_map_prototype.append(bin(i)[2:].zfill(len(variables)))

        self.map_prototype = CycleList()
        if self.simplified == "":
            for i in range(0, len(flatten_map_prototype), self.row_size):
                self.map_prototype.append(
                    CycleList(flatten_map_prototype[i : i + self.row_size])
                )

        self.__grayify_maps()

    def __grayify_maps(self):  # Make maps look like gray code
        for map_ in (self.map_, self.map_prototype):
            # These two IFs make the map look like gray code
            if len(self.variables) > 2:
                for x, row in enumerate(map_):
                    map_[x][2], map_[x][3] = map_[x][3], map_[x][2]

            if len(self.variables) > 3:
                map_[2], map_[3] = map_[3], map_[2]

    def __binary_to_vars(self, binary):
        return "".join(
            map(
                lambda ch_v: {"-": "", "0": f"{ch_v[1]}'", "1": ch_v[1]}[
                    ch_v[0]
                ],
                zip(binary, self.variables),
            )
        )

    def _is_taken(self, coords):
        if len(self.taken) == 0:
            return False

        points = coords.to_points(self.row_size, self.column_size)
        taken_points = set()
        for taken_coords in self.taken:
            taken_points.update(
                taken_coords.to_points(self.row_size, self.column_size)
            )

        return taken_points.issuperset(points)

    def _are_all1(self, coords):
        for point in coords.to_points():
            if not self.map_[point.x][point.y]:
                return False
        return True

    def __find_all8(self):
        coords8 = (Coordinates(0, 0, 1, 3),)
        if self.column_size == 4:
            coords8 += (
                Coordinates(0, 0, 3, 1),
                Coordinates(0, 2, 3, 3),
                Coordinates(2, 0, 3, 3),
            )

        for coords in coords8:
            if self._are_all1(coords):
                self.taken.add(coords)

    def __find_all4(self, coords):
        coords4 = (
            coords + Coordinates(0, 0, 0, 3),
            coords + Coordinates(0, 0, 1, 1),
        )
        if self.column_size == 4:
            coords4 += (Coordinates(0, 0, 3, 0),)

        for coords in coords4:
            if self._are_all1(coords) and not self._is_taken(coords):
                self.taken.add(coords)

    def __find_all2(self, coords):
        coords2 = (
            coords + Coordinates(0, 0, 1, 0),
            coords + Coordinates(0, 0, 0, 1),
        )

        for coords in coords2:
            if self._are_all1(coords) and not self._is_taken(coords):
                self.taken.add(coords)

    def __find_all1(self, coords):
        if self._are_all1(coords) and not self._is_taken(coords):
            self.taken.add(coords)

    def simplify(self, just_take=False):
        if self.simplified != "":
            return  # if already simplified, don't do it again

        self.__find_all8()
        for x, row in enumerate(self.map_):
            for y, minterm in enumerate(row):
                if minterm:
                    self.__find_all4(Coordinates(x, y, x, y))

        for x, row in enumerate(self.map_):
            for y, minterm in enumerate(row):
                if minterm:
                    self.__find_all2(Coordinates(x, y, x, y))

        for x, row in enumerate(self.map_):
            for y, minterm in enumerate(row):
                if minterm:
                    self.__find_all1(Coordinates(x, y, x, y))

        if just_take:
            return

        simplified = []

        for taken in self.taken:
            terms = []
            for point in taken.to_points(self.row_size, self.column_size):
                terms.append(self.map_prototype[point.x][point.y])

            simplified.append(
                self.__binary_to_vars(map(self.__simplify_terms, *terms))
            )

        self.simplified = " + ".join(simplified)

    def __simplify_terms(self, *t):
        s = sum(int(i) for i in t)
        if s == len(t):
            return "1"
        elif s == 0:
            return "0"
        else:
            return "-"


if __name__ == "__main__":
    from pprint import pprint

    minterms = input("Minterms: ")
    variables = input("Variables: ")
    kmap = KMap([int(x) for x in minterms.split()], variables)
    pprint(kmap.map_, width=3 * kmap.row_size + 4)
    kmap.simplify()
    pprint(kmap.taken)
    print(kmap.simplified)
