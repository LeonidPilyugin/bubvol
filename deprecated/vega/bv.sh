#!/usr/bin/zsh

source ~/.zshrc

STEPS=$1
FILE=$2
SEED=$3
K=$4

maa bubblecut

cd ~/opt/bubvol/python
./main.py -i $STEPS -s $SEED -f $FILE -k $K > /dev/stdout

DIR=$(dirname $FILE)

mkdir -p $DIR/bubvol/
NSTEPS=$(basename $FILE)

cp hit.lammpsdump $DIR/bubvol/$NSTEPS-$K.lammpsdump
