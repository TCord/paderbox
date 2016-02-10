import unittest
import os.path
import numpy as np
from nt.io import audioread, audiowrite
from nt.speech_enhancement import wpe
import time
from nt import testing

from nt.io.data_dir import testing as data_dir
from nt.io.data_dir import DataDir

class TestWPEWrapper(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.settings_file_path = DataDir(data_dir.join('speech_enhancement', 'utils'))
        self.audiofiles_path = DataDir(data_dir.join('speech_enhancement', 'data'))
        self.sample_rate = 16000

    def test_dereverb_one_channel(self):
        input_file_paths =\
            {self.audiofiles_path('sample_ch1.wav'): 1, }
        self.process_dereverbing_framework(input_file_paths)
        time.sleep(2) # wait 2 seconds for audio files to pop up in file manager

        # check if audio files exist
        for utt, num_channels in input_file_paths.items():
            for cha in range(num_channels):
                self.assertTrue(
                    os.path.isfile(
                        utt.replace('ch1', 'ch'+str(cha+1)+'_derev')))

    def test_dereverb_eight_channels(self):
        input_file_paths =\
            {self.audiofiles_path('sample_ch1.wav'): 8, }
        self.process_dereverbing_framework(input_file_paths)
        time.sleep(2) # wait 2 seconds for audio files to pop up in file manager

        # check if audio files exist
        for utt, num_channels in input_file_paths.items():
            for cha in range(num_channels):
                utt_to_check = utt.replace('ch1', 'ch'+str(cha+1)+'_derev')
                # print('ch'+str(cha+1)+'_derev')
                self.assertTrue(os.path.isfile(utt_to_check))


    def process_dereverbing_framework(self, input_file_paths):
        file_no = 0
        for utt, num_channels in input_file_paths.items():
            file_no += 1
            print("Processing file no. {0} ({1} file(s) to process in total)"
                  .format(file_no, len(input_file_paths)))
            noisy_audiosignals = np.ndarray(
                shape=[audioread.getparams(utt).nframes, num_channels],
                dtype=np.float32)

            for cha in range(num_channels):

                # erase old written audio files
                utt_to_be_written = utt.replace('ch1', 'ch'+str(cha+1)+'_derev')
                if os.path.isfile(utt_to_be_written):
                    os.remove(utt_to_be_written)

                # read microphone signals (each channel)
                print(" - Reading channel "+str(cha+1))
                utt_to_read = utt.replace('ch1', 'ch'+str(cha+1))
                signal = audioread.audioread(path=utt_to_read,
                                             sample_rate=self.sample_rate
                                             )
                if not noisy_audiosignals.shape[0] == len(signal):
                    raise Exception("Signal " + utt_to_read +
                                    " has a different size than other signals.")
                else:
                    noisy_audiosignals[:, cha] = signal

            # dereverb
            y = wpe.dereverb(self.settings_file_path, noisy_audiosignals)

            # write dereverbed signals (each channel)
            for cha in range(num_channels):
                utt_to_write = utt.replace('ch1', 'ch'+str(cha+1)+'_derev')
                print(" - Writing channel "+str(cha+1))
                audiowrite.audiowrite(y[:, cha],
                                      utt_to_write,
                                      self.sample_rate )
        print("Finished successfully.")


class TestMultichannelWPE(unittest.TestCase):

    def test_vecotrized_dereverb(self):
        K = 10
        Delta = 1
        y = np.random.uniform(0, 1, (10, 3, 20))
        G_hat = np.random.uniform(0, 1, (10, K, 3, 3))
        ref = wpe._dereverberate(y, G_hat, K, Delta)
        vec = wpe._dereverberate_vectorized(y, G_hat, K, Delta)
        testing.assert_allclose(ref[:, :, K+Delta:], vec[:, :, K+Delta:],
                                rtol=1e-2)

    def test_vectorized_get_crazy_matrix(self):
        K = 10
        Delta = 1
        y = np.random.uniform(0, 1, (10, 3, 20))
        ref = wpe._get_crazy_matrix(y, K, Delta)
        vec = wpe._get_crazy_matrix_vectorized(y, K, Delta)
        testing.assert_equal(ref, vec)

    def test_alphabet_example(self):
        L = 1
        N = 6
        T = 2
        Y = np.empty((L, N, T), dtype='<U6')
        for page in range(L):
            for row in range(N):
                for column in range(T):
                    Y[page, row, column] = 'l{}n{}t{}'.format(page, row, column)
        Y

        def replace(x):
            if x == '':
                return '      '
            else:
                return x
        vreplace = np.vectorize(replace)

        psi_bar = wpe._get_crazy_matrix(Y, K=1, Delta=0)
        psi_bar = vreplace(psi_bar)
        print(psi_bar.shape)