"""
Contains utilities which are mainly useful in a REPL environment.
"""
import itertools
import collections
import functools
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from pprint import pprint as original_pprint

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import IPython.lib.pretty
from IPython.display import HTML
from IPython.display import display
# from paderbox.database.chime import Chime3, Chime4
# from paderbox.database.reverb import Reverb
from paderbox.io import dump_json
from paderbox.io import load_json
from paderbox.io.play import play
from paderbox.transform import fbank
from paderbox.transform import istft
from paderbox.transform import stft
from paderbox.array import morph
from paderbox.utils.pandas_utils import py_query
from paderbox.visualization import figure_context
from paderbox.visualization import axes_context
from paderbox.visualization import facet_grid
from paderbox.visualization import plot
from tqdm import tqdm
# from paderbox.database.iterator import AudioReader
# from paderbox.database.iterator import LimitAudioLength
# from paderbox.database.iterator import AlignmentReader

__all__ = [
    "pprint",
    "itertools",
    "os",
    "re",
    "defaultdict",
    "Path",
    "pd",
    "sns",
    "HTML",
    "display",
    "plt",
    "load_json",
    "dump_json",
    "play",
    "axes_context",
    "figure_context",
    "facet_grid",
    "plot",
    "fbank",
    "istft",
    "stft",
    "tqdm",
    "morph",
    "np",
    "datetime",
    "py_query",
]


def pprint(obj, verbose=False, max_width=79, newline='\n',
           max_seq_length=IPython.lib.pretty.MAX_SEQ_LENGTH,
           max_array_length=50,
           ):
    """
    Copy of IPython.lib.pretty.pprint.
    Modifies the __repr__ of np.ndarray and torch.Tensor compared to the
    original.

    >>> pprint([np.array([1]), np.array([1]*100)])
    [array([1]), ndarray(shape=(100,), dtype=int64)]
    >>> print([np.array([1])])
    [array([1])]
    """

    class MyRepresentationPrinter(IPython.lib.pretty.RepresentationPrinter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            def _ipy_pprint_ndarray(obj, p, cycle):
                if obj.size <= max_array_length:
                    # Use repr or str?
                    # repr -> array([...])
                    # str -> [...]
                    p.text(repr(obj))
                else:
                    p.text(
                        f'{obj.__class__.__name__}'
                        f'(shape={obj.shape}, dtype={obj.dtype})'
                    )

            def _ipy_pprint_tensor(obj, p, cycle):
                p.text(
                    f'{obj.__class__.__name__}'
                    f'('
                    f'shape={tuple(obj.shape)}, '
                    f'dtype={str(obj.dtype).replace("torch.", "")}'
                    f')'
                )

            self.type_pprinters[np.ndarray] = _ipy_pprint_ndarray
            self.deferred_pprinters[('torch', 'Tensor')] = _ipy_pprint_tensor

    printer = MyRepresentationPrinter(sys.stdout, verbose, max_width, newline,
                                      max_seq_length=max_seq_length)
    printer.pretty(obj)
    printer.flush()
    sys.stdout.write(newline)
    sys.stdout.flush()
