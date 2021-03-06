import sh
import os
import pandas as pd
from io import StringIO
import re
import time
import numpy as np
from tqdm import tqdm
from pathlib import Path


def ccsinfo(host=None, use_ssh=True):
    """ Wrapper for ccsinfo.

    :param host: PC2 ssh host alias.
    """
    common_args = ['-s', '--mine', '--fmt=%.R%o%.60N%.4w%P%D%v%u', '--raw']
    if use_ssh:
        host = 'pc2' if host is None else host
        ret = sh.ssh(host, 'ccsinfo', *common_args)
    else:
        ret = sh.ccsinfo(*common_args)

    names = [
        'id', 'stdout', 'name', 'status', 'start_time', 'time_limit', 'runtime',
        'resource_set'
    ]
    df = pd.read_csv(
        StringIO(ret.stdout.decode('utf-8')),
        delim_whitespace=True,
        names=names
    )

    def _format(x):
        try:
            return Path(x).parent
        except TypeError:
            return x

    df['experiment_dir'] = df['stdout'].apply(_format)
    del df['stdout']
    return df.fillna('')


def ccskill(request_id, host=None):
    """ Wrapper for ccskill.

    :param request_id: Single request id or list of request ids.
    :param host: PC2 ssh host alias.
    """
    host = 'pc2' if host is None else host
    if isinstance(request_id, (str, int)):
        request_id = [request_id]
    print(sh.ssh(host, 'ccskill', request_id))


def get_job_id(allocation_result):
    """ Extract cluster job ID from array job allocation string.

    Args:
        allocation_result: Result just as from ``job_result = sh.ssh(command)``.

    Returns:

    """
    try:
        regex_job_id = re.compile(r'PM:Array\s([0-9]*)')
        return re.search(
            regex_job_id,
            allocation_result.stdout.decode('utf-8')
        ).groups()[0]
    except AttributeError:
        regex_job_id = re.compile(r'Request\s\(([0-9]*)')
        return re.search(
            regex_job_id,
            allocation_result.stdout.decode('utf-8')
        ).groups()[0]


def _test_finished(job_ids, host, use_ssh):
    """ Expects list of job ids as strings. """
    job_ids = [str(_id) for _id in job_ids]
    df = ccsinfo(host=host, use_ssh=use_ssh)
    jobs = df[df['id'].apply(lambda x: str(x) in job_ids)]
    next_ids = []
    new_finished_jobs = 0
    for idx, job in jobs.iterrows():
        if not job['status'] == 'STOPPED':
            next_ids.append(job['id'])
        else:
            new_finished_jobs += 1
    return next_ids, new_finished_jobs


def idle_while_jobs_are_running(
        job_ids, sleep_time=300, host='pc2', use_ssh=True
):
    """ Expects list of job ids as strings. """
    if not len(job_ids):
        return
    total_jobs = len(job_ids)
    p = tqdm(total=total_jobs, desc='Cluster jobs')
    while len(job_ids):
        time.sleep(sleep_time)
        job_ids, new_finished_jobs = _test_finished(job_ids, host, use_ssh)
        if new_finished_jobs:
            p.update(new_finished_jobs)


def idle_while_array_jobs_are_running(
        job_ids, sleep_time=300, host='pc2', use_ssh=True
):
    """ Idle after job array allocation to wait for remaining jobs.

    Args:
        job_ids: List of job_ids as strings.
        sleep_time: Should be more than 300 seconds.
            Otherwise, PC2 administration gets angry.
        host: PC2 ssh host alias.

    """
    regex_completed = re.compile(r'Completed\s*subjobs\s*\:\s([0-9]*)')
    regex_running = re.compile(r'Running\s*subjobs\s*\:\s([0-9]*)')
    regex_planned = re.compile(r'Planned\s*subjobs\s*\:\s([0-9]*)')
    regex_waiting = re.compile(r'Waiting\s*subjobs\s*\:\s([0-9]*)')
    regex_states = re.compile(r'State\s*\:\s(.*)')
    regex_names = re.compile(r'Name\s*\:\s(.*)')
    first_call = True

    while len(job_ids):
        if not first_call:
            time.sleep(sleep_time)
        else:
            time.sleep(5)

        completed = len(job_ids) * [0]
        running = len(job_ids) * [0]
        planned = len(job_ids) * [0]
        waiting = len(job_ids) * [0]
        states = len(job_ids) * ['UNKOWN']
        names = len(job_ids) * ['UNKOWN']

        remaining_job_ids = []
        for idx, job_id in enumerate(job_ids):
            try:
                if use_ssh:
                    res = sh.ssh(host, 'ccsinfo', job_id)
                else:
                    res = sh.ccsinfo(job_id)
                res = res.stdout.decode('utf-8')
                jobs_running, jobs_planned, jobs_waiting = 0, 0, 0
                if re.search(regex_completed, res) is not None:
                    jobs_completed = int(
                        re.search(regex_completed, res).groups()[0])
                    completed[idx] = jobs_completed
                else:
                    print(f'Could not parse completed jobs. Output was {res}')

                if re.search(regex_running, res) is not None:
                    jobs_running = int(
                        re.search(regex_running, res).groups()[0])
                    running[idx] = jobs_running
                else:
                    print(f'Could not parse running jobs. Output was {res}')

                if re.search(regex_planned, res) is not None:
                    jobs_planned = int(
                        re.search(regex_planned, res).groups()[0])
                    planned[idx] = jobs_planned
                else:
                    print(f'Could not parse planned jobs. Output was {res}')

                if re.search(regex_waiting, res) is not None:
                    jobs_waiting = int(
                        re.search(regex_waiting, res).groups()[0])
                    waiting[idx] = jobs_waiting
                else:
                    print(f'Could not parse waiting jobs. Output was {res}')

                if re.search(regex_states, res) is not None:
                    job_state = re.search(regex_states, res).groups()[0]
                    states[idx] = job_state
                else:
                    print(f'Could not parse completed jobs. Output was {res}')

                if re.search(regex_names, res) is not None:
                    job_name = re.search(regex_names, res).groups()[0]
                    names[idx] = job_name
                else:
                    print(f'Could not parse completed jobs. Output was {res}')
                if np.sum([jobs_running, jobs_planned, jobs_waiting]) > 0 \
                        and not 'STOPPED' in states[idx]:
                    remaining_job_ids.append(job_id)

            except Exception as e:
                message = 'Could not parse stats for job id {}: {}'
                print(message.format(job_id, e))

        for idx in range(len(job_ids)):
            print(f'{names[idx]} [{states[idx]}]:', end=' ')
            print(f'completed: {completed[idx]}', end=' ')
            print(f'running: {running[idx]}', end=' ')
            print(f'planned: {planned[idx]}', end=' ')
            print(f'waiting: {waiting[idx]}')

        print('Total: Completed: {} Running: {} Planned: {} Waiting: {}'.format(
            sum(completed), sum(running), sum(planned), sum(waiting)
        ))

        job_ids = remaining_job_ids
        first_call = False


def force_ncpus(ncpus=None):
    """
    The PC2 does not assign cores to a process. This function can force a
    already started python program to use only n cpus.

    When "ncpus" is not specified, use the environment variable NCPUS
    (provided from PC2).

    In Linux it is not possible to limit a process to use only n cpus.
    But it is possible to say use only specific cores
    (e.g [0,2] mean use core with id 0 and core with id 2).
    For more information search for the linux utility "taskset".

    This function selects random core IDs and limits the current program to use
    it.

    See psutil.Process.cpu_affinity
    """
    import psutil

    if ncpus is None:
        ncpus = int(os.environ['NCPUS'])

    # CB: Should we force user to set the env variables?
    # if ncpus == 1:
    #     from paderbox.utils.parallel_utils import ensure_single_thread_numeric
    #     ensure_single_thread_numeric()

    # Force NCPUS, by limiting this process to random selected cores.
    p = psutil.Process()
    p.cpu_affinity(list(sorted(
        np.random.choice(p.cpu_affinity(), ncpus, replace=False)
    )))


def write_ccsinfo_files(
        log_dir,
        reqid_file='CCS_REQID',
        info_file='CCS_INFO',
        consider_mpi=True,
):
    """
    Writes te following logs to the log dir:
     - <regid> to reqid_file
     - ccsinfo <regid> to info_file
     - STDOUT, STDERR and Trace file symlinks to the original if info_file is
       not None


    # usage
    def main(...):
        write_ccsinfo_files(sacred_dir)

        # main code
        ...

        write_ccsinfo_files(sacred_dir, reqid_file=None, info_file='CCS_INFO_END')

    """
    import paderbox as pb
    if consider_mpi:
        from paderbox.utils import mpi
    else:
        class mpi:
            IS_MASTER = True

    if mpi.IS_MASTER:
        CCS_REQID = os.environ.get('CCS_REQID', None)
        if CCS_REQID is not None:
            if reqid_file is not None:
                (Path(log_dir) / reqid_file).write_text(CCS_REQID)
            if info_file is not None:
                from paderbox.utils.process_caller import run_process
                stdout: str = run_process(
                    [
                        'ccsinfo',
                        CCS_REQID,
                    ],
                    stderr=None
                ).stdout
                (Path(log_dir) / info_file).write_text(stdout)

                lines = stdout.split('\n')

                for line in lines:
                    if (
                            line.startswith('STDOUT')
                            or line.startswith('STDERR')
                            or line.startswith('Trace file')
                    ):
                        file = Path(line.split(':', maxsplit=1)[-1].strip())
                        pb.io.symlink(file, (Path(log_dir) / file.name))
                    else:
                        continue
