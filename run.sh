#!/bin/sh

#sets dir to directory containing this script
scriptpath=`realpath $0`
dir=`dirname $scriptpath`

#use $dir/ as prefix to run any programs in this dir
#so that this script can be run from any directory.
python3 $dir/elixir-data.py