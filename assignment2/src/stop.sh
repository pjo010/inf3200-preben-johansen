#!/bin/bash          

# Executable
directory="/home/pjo010/inf-3200-assignment2/" #current working directory
executable="test.py";
# Lists of nodes
nodes=( "compute-11-1" "compute-11-2" "compute-11-3" "compute-12-1" 
  "compute-12-2" "compute-12-3" "compute-13-1" "compute-13-2" "compute-13-3" 
  "compute-14-1" "compute-14-2" "compute-14-3" "compute-15-1" "compute-15-2" 
  "compute-15-3" "compute-16-1" "compute-16-2" "compute-16-3" "compute-17-1" 
  "compute-17-2")
# Stop 
for node in "${nodes[@]}"
do
  ssh $node bash -c "'pgrep -f '$directory$executable' | xargs kill'"
  if ssh -q $node ps aux | grep $executable > /dev/null 2>&1 ;
  then
    echo "Error: unable to stop $node"
  else
    echo "Shut down $node"
  fi
done