#!/bin/bash          

# Executable
directory="/home/pjo010/inf-3200-assignment1/precode/" #current working directory
executable="node.py";

# Lists of nodes
nodes=( "compute-11-1" "compute-11-2" "compute-11-3")

# Stop any running processes
for node in "${nodes[@]}"
do
  ssh $node bash -c "'pgrep -f '$directory$executable' | xargs kill'"
done

# Boot all processes
for node in "${nodes[@]}"
do
  echo "Booting node" $node
  nohup ssh $node bash -c "'python $directory$executable grep da * 2> grep_errors$node.txt'"  > /dev/null 2>&1 &
done

# Wait/Run benchmarks
HEALTY=1
while [ $HEALTY -eq 1  ]; do 
  sleep 1
  echo "Checking if each node is alive and well..."
  for node in "${nodes[@]}"
  do
    if ssh -q $node ps aux | grep $executable > /dev/null 2>&1 ;
    then
      echo "$node is alive"
    else
      echo "$node is dead"
      let HEALTY=0
    fi
  done
done

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
