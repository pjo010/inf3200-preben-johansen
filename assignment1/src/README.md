#How to run

Open three terminals
bash startup.sh -to run the backend nodes
python frontend_storage.py (argument list: -runtests(for running 100 puts and gets) compute-11-1 compute-11-2 compute-11-3(nodes used in script))
ssh -q compute-11-1 ps
ssh -q compute-11-1 kill (PID) - for shutdown
