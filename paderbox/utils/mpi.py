"""
Wraps imports for mpi4py to allow code to run on non MPI machines, too.

http://mpi4py.readthedocs.io/en/latest/tutorial.html:
Communication of generic Python objects:
    You have to use all-lowercase ...
Communication of buffer-like objects:
    You have to use method names starting with an upper-case ...

If you want to implement Round-Robin execution, you can try this::
    for example in iterator[RANK::SIZE]:
        pass
"""
import os
from paderbox.utils.parallel_utils import ensure_single_thread_numeric


__all__ = [
    'RANK',
    'SIZE',
    'MASTER',
    'IS_MASTER',
    'barrier',
    'bcast',
    'gather',
    'map_unordered',
]


try:
    from mpi4py import MPI
    if MPI.COMM_WORLD.size > 1:
        if 'PC2SYSNAME' in os.environ:
            pass
            # Tensorflow may read the environment variables. And since it is
            # difficult to force TF to a single thread, allow higher ncpus on
            # PC2 for Tensorflow. Furthermore, TF has better concepts to use
            # multicores.
        else:
            ensure_single_thread_numeric()
except ImportError:

    if 'PC2SYSNAME' in os.environ:
        # CCS indicate PC2
        # PC2SYSNAME is 'OCULUS' or 'Noctua'
        raise

    if int(os.environ.get('OMPI_COMM_WORLD_SIZE', '1')) != 1:
        print(
            f'WARNING: Something is wrong with your mpi4py installation.\n'
            f'Environment size: {os.environ["OMPI_COMM_WORLD_SIZE"]}\n'
            f'mpi4py size: {os.environ["OMPI_COMM_WORLD_SIZE"]}\n'
        )
        raise

    if int(os.environ.get('PMI_SIZE', '1')) != 1:
        # MPICH_INTERFACE_HOSTNAME=ntws25
        # PMI_RANK=0
        # PMI_FD=6
        # PMI_SIZE=1
        print(
            f'WARNING: Something is wrong with your mpi4py installation.\n'
            f'You use intel mpi while we usually use openmpi.\n'
            f'This is usually caused from "conda install mpi4py" instead of '
            f'"pip install mpi4py".\n'
            f'Try to deinstall mpi4py and install it with "pip install mpi4py"'
        )
        raise

    class DUMMY_COMM_WORLD:
        size = 1
        rank = 0
        Barrier = lambda self: None
        bcast = lambda self, data, *args, **kwargs: data
        gather = lambda self, data, *args, **kwargs: [data]

    class _dummy_MPI:
        COMM_WORLD = DUMMY_COMM_WORLD()

    MPI = _dummy_MPI()


class RankInt(int):
    def __bool__(self):
        raise NotImplementedError(
            'Bool is disabled for rank. '
            'It is likely that you want to use IS_MASTER.'
        )


COMM = MPI.COMM_WORLD
RANK = RankInt(COMM.rank)
SIZE = COMM.size
MASTER = RankInt(0)
IS_MASTER = (RANK == MASTER)


def barrier():
    COMM.Barrier()


def bcast(obj, root: int=MASTER):
    return COMM.bcast(obj, root)


def gather(obj, root: int=MASTER):
    return COMM.gather(obj, root=root)


def call_on_master_and_broadcast(func, *args, **kwargs):
    if IS_MASTER:
        result = func(*args, **kwargs)
    else:
        result = None
    return bcast(result)


def map_unordered(
        func,
        iterable,
        progress_bar=False,
        indexable=True,

):
    """
    A master process push tasks to the workers and receives the result.
    Pushing tasks mean, send an index to the worker and the worker iterates
    through the iterable until the worker reaches this index.

    Required at least 2 mpi processes, but to produce a speedup 3 are required.
    Only rank 0 get the results.
    This map is lazy.

    Assume function body is fast.

    Parallel: The execution of func.

    """
    from tqdm import tqdm
    from enum import IntEnum, auto

    if SIZE == 1:
        if progress_bar:
            yield from tqdm(map(func, iterable))
            return
        else:
            yield from map(func, iterable)
            return

    status = MPI.Status()
    workers = SIZE - 1

    class tags(IntEnum):
        """Avoids magic constants."""
        start = auto()
        stop = auto()
        default = auto()

    COMM.Barrier()

    if RANK == 0:
        i = 0
        with tqdm(total=len(iterable), disable=not progress_bar) as pbar:
            pbar.set_description(f'busy: {workers}')
            while workers > 0:
                result = COMM.recv(
                    source=MPI.ANY_SOURCE,
                    tag=MPI.ANY_TAG,
                    status=status)
                if status.tag == tags.default:
                    COMM.send(i, dest=status.source)
                    yield result
                    i += 1
                    pbar.update()
                elif status.tag == tags.start:
                    COMM.send(i, dest=status.source)
                    i += 1
                    pbar.update()
                elif status.tag == tags.stop:
                    workers -= 1
                    pbar.set_description(f'busy: {workers}')
                else:
                    raise ValueError(status.tag)

        assert workers == 0
    else:
        try:
            COMM.send(None, dest=0, tag=tags.start)
            next_index = COMM.recv(source=0)
            if indexable:
                while True:
                    try:
                        val = iterable[next_index]
                    except IndexError:
                        break
                    result = func(val)
                    COMM.send(result, dest=0, tag=tags.default)
                    next_index = COMM.recv(source=0)
            else:
                for i, val in enumerate(iterable):
                    if i == next_index:
                        result = func(val)
                        COMM.send(result, dest=0, tag=tags.default)
                        next_index = COMM.recv(source=0)
        finally:
            COMM.send(None, dest=0, tag=tags.stop)
