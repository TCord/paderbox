# This code is intended to be used in all test cases which require Kaldi.
JENKINS_KALDI_ROOT=/net/vol/jenkins/kaldi/
CURRENT_WORKING_KALDI_ROOT=$JENKINS_KALDI_ROOT/2018-08-08_10-09-05_8e97639b7066b5d8a649827975263b6fc288e6ef
CURRENT_BUILDING_KALDI_ROOT=$JENKINS_KALDI_ROOT/2018-08-08_10-09-05_8e97639b7066b5d8a649827975263b6fc288e6ef

if [[ $(hostname) =~ ^ntjenkins ]]; then
    if [ $# -eq 0 ]; then
            export KALDI_ROOT=$CURRENT_WORKING_KALDI_ROOT
    else
        if [ $1 -eq 1 ]; then
            export KALDI_ROOT=$CURRENT_BUILDING_KALDI_ROOT
        fi
    fi
fi
