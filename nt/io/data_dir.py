"""

>>> from pathlib import Path
>>> p = Path('/') / 'net' # /storage/python_unittest_data
>>> p
>>> p = p / 'storage'
>>> p
>>> str(p)

"""

import os
from pathlib import Path


def _get_path(environment_name, default):
    return Path(os.getenv(environment_name, default)).expanduser()

database_jsons = _get_path(
    'NT_DATABASE_JSONS_DIR',
    '/net/storage/database_jsons'
)
db_dir = _get_path(
    'NT_DB_DIR',
    '/net/db'
)
testing = _get_path(
    'NT_TESTING_DIR',
    '/net/storage/python_unittest_data'
)
kaldi_root = _get_path(
    'KALDI_ROOT',
    '/net/ssd/jheymann/software/kaldi_latest'
    # '/net/ssd/software/kaldi'
)
matlab_toolbox = _get_path(
    'MATLAB_TOOLBOX_DIR',
    '/net/ssd/software/matlab_toolbox'
)
matlab_r2015a = _get_path(
    'MATLAB_R2015a',
    '/net/ssd/software/MATLAB/R2015a'
)
matlab_license = _get_path(
    'MATLAB_LICENSE',
    '/opt/MATLAB/R2016b_studis/licenses/network.lic'
)

ami = _get_path(
    'NT_AMI_DIR',
    db_dir / 'ami'
)
timit = _get_path(
    'NT_TIMIT_DIR',
    db_dir /'timit'
)
tidigits = _get_path(
    'NT_TIDIGITS_DIR',
    db_dir /'tidigits'
)
chime_3 = _get_path(
    'NT_CHIME_3_DIR',
    db_dir / 'chime3'
)
chime_4 = _get_path(
    'NT_CHIME_4_DIR',
    db_dir / 'chime4'
)
merl_mixtures = _get_path(
    'NT_MERL_MIXTURES_DIR',
    '/net/db/merl_speaker_mixtures'
)
german_speechdata = _get_path(
    'NT_GERMAN_SPEECHDATA_DIR',
    '/net/storage/jheymann/speech_db/german-speechdata-package-v2/'
)
noisex92 = _get_path(
    'NT_NoiseX_92_DIR',
    db_dir / 'NoiseX_92'
)
reverb = _get_path(
    'NT_REVERB_DIR',
    db_dir / 'reverb'
)
wsj = _get_path(
    'NT_WSJ_DIR',
    db_dir / 'wsj'
)
dcase = _get_path(
    'NT_DCASE_DIR',
    '/home/parora/Documents/DCASE/DCASE 2016/'
)
wsjcam0 = _get_path(
    'NT_WSJCAM0_DIR',
    db_dir / 'wsjcam0'
)
language_model = _get_path(
    'LANGUAGE_MODEL',
    '/net/storage/jheymann/__share/ldrude/2016/2016-05-10_lm'
)

if __name__ == "__main__":
    import doctest

    doctest.testmod()
