import time
from multiprocessing import Pool
from functools import partial
import numpy as np
import matplotlib.pyplot as plt


Dimension = 200
grid = np.array([[np.random.randint(2) for x in range(Dimension)] for y in range(Dimension)])
gridsize = grid.shape


def neighbors_count(k, l):
    sum = 0
    offset = [-1, 0, 1]
    for i in offset:
        for j in offset:
            if(not(i == 0 and j == 0)):
                sum += grid[(k+i)%L][(l+j)%L]
    return sum

def gameoflife(grid):
  #  print(len(grid))
    newgrid = np.copy(grid)

    for i in range(len(grid)):
        for j in range(len(grid)):
            sum = neighbors_count(i, j)
            if(grid[i][j] == 0):
                if(sum == 3):
                    newgrid[i][j] == 1
            else:
                if(sum <= 1 or sum >= 4):
                    newgrid[i][j] = 0
    return newgrid

# define integration step sizes
dx = 1
dt = 1

L = 200   # system shape is square for convenience
T = 100   # integration time
D = 0.1   # diffusion constant


def sequential(grid):
    ''' sequential processing solution '''
    ts = time.time()  # measure computation time
    for t in np.arange(T/dt):
        # insert upper and lower boundary: reflecting boundary
        tmp = np.insert(grid, 0, grid_s[-1, :], axis=0)
        tmp = np.vstack((tmp, grid[0, :]))
        # insert left and right boundary: reflecting boundary
        tmp = np.insert(tmp, 0, tmp[:, -1], axis=1)
        tmp = np.hstack((tmp, np.array([tmp[:, 0]]).T)) # note: slicing gives a row vector therefore transpose to get column vector
        grid = gameoflife(grid)
    print('Sequential processing took {}s'.format(time.time() - ts))
    return grid


def parallel(grid, T, dt, units):
    ''' parallel processing solution '''
    # define number of processes
    #units = 2
    p = Pool(units)

    # define how many partitions of grid in x and y direction and their length
    (nx, ny) = (int(units / 2), 2)
    lx = int(gridsize[0] / nx)
    ly = int(gridsize[1] / ny)

    # this makes sure that D, dt, dx are the same when distributed over processes
    # for integration, so the only interface parameter that changes is the grid
    print("preeee"+str(len(grid)))
    func = partial(gameoflife)
    ts = time.time()  # measure computation time
    for t in np.arange(T/dt):  # note numpy.arange is rounding up floating points
        data = []
        # prepare data to be distributed among workers
        # 1. insert boundary conditions and partition data
        grid = np.insert(grid, 0, grid[-1, :], axis=0)       # top
        grid = np.vstack((grid, grid[0, :]))               # bottom
        grid = np.insert(grid, 0, grid[:, -1], axis=1)       # left
        grid = np.hstack((grid, np.array([grid[:, 0]]).T))   # right
        # partition into subgrids
        for i in range(nx):
            for j in range(ny):
                # subgrid
                subg = grid[i * lx + 1:(i+1) * lx + 1, j * ly + 1:(j+1) * ly + 1]
                subg = np.insert(subg, 0, grid[i * lx, j * ly + 1:(j+1) * ly + 1], axis=0)  # upper subgrid boundary
                subg = np.vstack((subg, grid[(i+1) * lx + 1, j * ly + 1:(j+1) * ly + 1]))  # lower subgrid boundary
                subg = np.insert(subg, 0, grid[i * lx:(i+1) * lx + 2, j * ly], axis=1)  # left subgrid boundary
                subg = np.hstack((subg, np.array([grid[i * lx:(i+1) * lx + 2, (j+1) * ly + 1]]).T))  # right subgrid boundary

                # collect subgrids in list to be distributed over processes
                data.append(subg)
        # 2. divide among workers
        grid = np.delete(grid, (0), axis=0)
        grid = np.delete(grid, (-1), axis=0)
        grid = np.delete(grid, (0), axis=1)
        grid = np.delete(grid, (-1), axis=1)

        print("did it work?" + str(len(grid)))

        results = p.map(func, data)
        grid = np.vstack([np.hstack((results[i * ny:(i+1) * ny])) for i in range(nx)])
    print('Concurrent processing took {}s'.format(time.time() - ts)) # alternative to write variable to string as used above

    return grid

if __name__ == '__main__':
    grid_s = np.copy(grid)  # keep original grid variable unchanged
    plt.imshow(sequential(grid_s), cmap=plt.cm.copper, extent=[-1, 1, -1, 1])
    plt.xticks([]); plt.yticks([])
    plt.show()
    grid_p = np.copy(grid)  # keep original grid variable unchanged
    plt.imshow(parallel(grid_p, T, dt, 4), cmap=plt.cm.copper, extent=[-1, 1, -1, 1])
    plt.xticks([]); plt.yticks([])
    plt.show()
