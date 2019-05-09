import argparse
import random
import math

GRID_LEN = 28
AGE_LIMIT = 25
DIFFUSE_RATIO = 0.5
NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def start_ratio_type(x):
    x = int(x)
    if x < 0 or x > 50:
        raise argparse.ArgumentTypeError("start % of daisy must be int in range [0,50]")
    return x


def albedo_type(x):
    x = float(x)
    if x < 0 or x >= 1:
        raise argparse.ArgumentTypeError("albedo must be float in range [0,1)")
    return x


def luminosity_type(x):
    x = float(x)
    if x <= 0 or x > 3:
        raise argparse.ArgumentTypeError("luminosity must be float in range (0,3]")
    return x


def ticks_type(x):
    x = int(x)
    if x < 1:
        raise argparse.ArgumentTypeError("tick count of simulation must be int in range [1,+inf)")
    return x


def get_options():
    parser = argparse.ArgumentParser(
        prog="daisyworld.py",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    args = parser.add_argument_group(title="optional arguments")
    args.add_argument('--white-ratio', metavar="start-%-whites",
                      type=start_ratio_type, default=20,
                      help="start % of whites")
    args.add_argument('--black-ratio', metavar="start-%-blacks",
                      type=start_ratio_type, default=20,
                      help="start % of blacks")
    args.add_argument('--white-albedo', metavar="albedo-of-whites",
                      type=albedo_type, default=0.75,
                      help="albedo of whites")
    args.add_argument('--black-albedo', metavar="albedo-of-blacks",
                      type=albedo_type, default=0.25,
                      help="albedo of blacks")
    args.add_argument('--surface-albedo', metavar="albedo-of-surface",
                      type=albedo_type, default=0.4,
                      help="albedo of surface")
    args.add_argument('--solar-luminosity', metavar="solar-luminosity",
                      type=luminosity_type, default=0.8,
                      help="solar luminosity")
    args.add_argument('--ticks', metavar="ticks",
                      type=ticks_type, default=1000,
                      help="ticks that simulator runs")
    args.add_argument('--mode', metavar="mode",
                      type=str,
                      choices=["ramp-up-ramp-down", "default"],
                      default="default", help="mode of luminosity")
    ret = parser.parse_args()
    return ret


def init(options):
    grid_size = GRID_LEN * GRID_LEN

    grid = []
    for i in range(0, GRID_LEN):
        row = []
        for j in range(0, GRID_LEN):
            row.append(("empty", 0, None))
        grid.append(row)

    num_of_white = int(options.white_ratio * grid_size / 100)
    for i in range(0, num_of_white):
        while True:
            x, y = random.randint(0, GRID_LEN-1), random.randint(0, GRID_LEN-1)
            patch_type, _, _ = grid[x][y]
            if patch_type == "empty":
                break
        grid[x][y] = ("white", 0, random.randint(0, AGE_LIMIT))
    num_of_black = int(options.black_ratio * grid_size / 100)
    for i in range(0, num_of_black):
        while True:
            x, y = random.randint(0, GRID_LEN-1), random.randint(0, GRID_LEN-1)
            patch_type, _, _ = grid[x][y]
            if patch_type == "empty":
                break
        grid[x][y] = ("black", 0, random.randint(0, AGE_LIMIT))

    update_temperature(grid, options, options.solar_luminosity)
    return grid


def update_temperature(grid, options, luminosity):
    for i in range(0, GRID_LEN):
        for j in range(0, GRID_LEN):
            patch_type, patch_temp, patch_age = grid[i][j]
            albedo = {
                "empty": options.surface_albedo,
                "white": options.white_albedo,
                "black": options.black_albedo
            }[patch_type]
            absorbed_luminosity = luminosity * (1 - albedo)
            if absorbed_luminosity > 0:
                local_heating = 80 + 72 * math.log(absorbed_luminosity)
            else:
                local_heating = 80
            grid[i][j] = (patch_type, (patch_temp + local_heating) / 2, patch_age)


def diffuse_temperature(grid):
    temp_grid = []
    for i in range(0, GRID_LEN):
        temp_row = []
        for j in range(0, GRID_LEN):
            if i == 0 or i == GRID_LEN - 1:
                neighbors = 3 if j == 0 or j == GRID_LEN - 1 else 5
            elif j == 0 or j == GRID_LEN - 1:
                neighbors = 5
            else:
                neighbors = 8

            _, t, _ = grid[i][j]
            t = t * (1 - (neighbors / 8 * DIFFUSE_RATIO))

            for patch in NEIGHBOURS:
                diff_i, diff_j = patch
                if 0 <= i + diff_i < GRID_LEN and 0 <= j + diff_j < GRID_LEN:
                    t += grid[i + diff_i][j + diff_j][1] / 8 * DIFFUSE_RATIO

            temp_row.append(t)
        temp_grid.append(temp_row)

    for i in range(0, GRID_LEN):
        for j in range(0, GRID_LEN):
            patch_type, _, patch_age = grid[i][j]
            grid[i][j] = (patch_type, temp_grid[i][j], patch_age)


def get_global_temperature(grid):
    total = 0
    for i in range(0, GRID_LEN):
        for j in range(0, GRID_LEN):
            _, t, _ = grid[i][j]
            total += t
    total /= GRID_LEN * GRID_LEN
    return total


def get_population(grid):
    white = 0
    black = 0
    for i in range(0, GRID_LEN):
        for j in range(0, GRID_LEN):
            t, _, _ = grid[i][j]
            if t == "white":
                white += 1
            elif t == "black":
                black += 1
    return white, black


def write_log_line(fp, grid, luminosity, tick):
    temp = get_global_temperature(grid)
    white, black = get_population(grid)
    fp.write("{},{},{},{},{}\n".format(tick, white, black, luminosity, temp))


def check_survivability(grid):
    for i in range(0, GRID_LEN):
        for j in range(0, GRID_LEN):
            patch_type, patch_temp, patch_age = grid[i][j]
            # age of -1 is new baby, and they should not age or reproduce until next tick
            if patch_age == -1:
                continue
            if patch_type != "empty":
                patch_age += 1
                if patch_age > AGE_LIMIT:
                    grid[i][j] = ("empty", patch_temp, None)
                    continue
                grid[i][j] = (patch_type, patch_temp, patch_age)
                seed_threshold = 0.1457 * patch_temp - 0.0032 * (patch_temp ** 2) - 0.6443
                if random.random() < seed_threshold:
                    has_space = False
                    for p in NEIGHBOURS:
                        diff_i, diff_j = p
                        if 0 <= i + diff_i < GRID_LEN and 0 <= j + diff_j < GRID_LEN:
                            if grid[i + diff_i][j + diff_j][0] == "empty":
                                has_space = True
                    # if there is, pick a empty patch randomly
                    if has_space:
                        while True:
                            diff_i, diff_j = NEIGHBOURS[random.randint(0, len(NEIGHBOURS) - 1)]
                            if 0 <= i + diff_i < GRID_LEN and 0 <= j + diff_j < GRID_LEN and \
                               grid[i + diff_i][j + diff_j][0] == "empty":
                                temp = grid[i + diff_i][j + diff_j][1]
                                # age of new babies will be inited afterwards
                                grid[i + diff_i][j + diff_j] = (patch_type, temp, -1)
                                break
    for i in range(0, GRID_LEN):
        for j in range(0, GRID_LEN):
            patch_type, patch_temp, patch_age = grid[i][j]
            if patch_type != "empty" and patch_age == -1:
                grid[i][j] = (patch_type, patch_temp, 0)


def main():
    options = get_options()
    grid = init(options)
    luminosity = options.solar_luminosity
    fp = open("output.csv", "w+")
    fp.write("tick,white population,black population,luminosity,global temperature\n")
    write_log_line(fp, grid, luminosity, 0)
    for i in range(1, options.ticks + 1):
        update_temperature(grid, options, luminosity)
        diffuse_temperature(grid)
        check_survivability(grid)
        write_log_line(fp, grid, luminosity, i)

        if 200 < i <= 400:
            luminosity += 0.005
        elif 600 < i <= 850:
            luminosity -= 0.0025

    fp.close()


if __name__ == '__main__':
    main()
