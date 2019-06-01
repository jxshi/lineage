"""
Copyright (C) 2019 Andrew Riha

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import datetime
from multiprocessing import Pool
import os

from atomicwrites import atomic_write
import pandas as pd

import lineage


class Parallelizer:
    def __init__(self, parallelize=True, processes=os.cpu_count()):
        """ Initialize a `Parallelizer`.

        Parameters
        ----------
        parallelize : bool
            utilize multiprocessing to speedup calculations
        processes : int
            processes to launch if multiprocessing
        """
        self._parallelize = parallelize
        self._processes = processes

    def __call__(self, f, tasks):
        """ Optionally parallelize execution of a function.

        Parameters
        ----------
        f : func
            function to execute
        tasks : list of dict
            tasks to pass to `f`

        Returns
        -------
        list
            results of each call to `f`
        """
        if self._parallelize:
            with Pool(self._processes) as p:
                return p.map(f, tasks)
        else:
            return map(f, tasks)


class Singleton(type):
    # https://stackoverflow.com/a/6798042
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def create_dir(path):
    """ Create directory specified by `path` if it doesn't already exist.

    Parameters
    ----------
    path : str
        path to directory

    Returns
    -------
    bool
        True if `path` exists
    """
    # https://stackoverflow.com/a/5032238
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as err:
        print(err)
        return False

    if os.path.exists(path):
        return True
    else:
        return False


def save_df_as_csv(df, path, filename, comment="", **kwargs):
    """ Save dataframe to a CSV file.

    Parameters
    ----------
    df : pandas.DataFrame
        dataframe to save
    path : str
        path to directory where to save CSV file
    filename : str
        filename of CSV file
    comment : str
        header comment(s); one or more lines starting with '#'
    **kwargs
        additional parameters to `pandas.DataFrame.to_csv`

    Returns
    -------
    str
        path to saved file, else empty str
    """
    if isinstance(df, pd.DataFrame) and len(df) > 0:
        try:
            if not create_dir(path):
                return ""

            destination = os.path.join(path, filename)

            print("Saving " + os.path.relpath(destination))

            s = (
                "# Generated by lineage v{}, https://github.com/apriha/lineage\n"
                "# Generated at {} UTC\n"
            )

            s = s.format(
                lineage.__version__,
                datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            )

            s += comment

            with atomic_write(destination, mode="w", overwrite=True) as f:
                f.write(s)
                # https://stackoverflow.com/a/29233924
                df.to_csv(f, na_rep="--", **kwargs)

            return destination
        except Exception as err:
            print(err)
            return ""
    else:
        print("no data to save...")
        return ""
