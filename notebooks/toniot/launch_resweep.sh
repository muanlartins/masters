#!/bin/zsh
# Boundary-fair extended re-sweep: 7 per-device bases in parallel (resumable;
# only NEW configs run), then the combined task from the new best cfgs.
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
ROOT=/Users/muanlartins/repos/masters/notebooks/toniot
PY=/Users/muanlartins/repos/masters/venv/bin/python3
LOG=$ROOT/results/_consolidado/logs
mkdir -p $LOG
cd $ROOT
echo "resweep START $(date +%T)"
for base in Fridge Garage_Door GPS_Tracker Modbus Motion_Light Thermostat Weather; do
  $PY run_wisard_grid.py --base "$base" > "$LOG/resweep_${base}.log" 2>&1 &
done
wait
echo "per-device DONE $(date +%T); running combined..."
$PY run_wisard_grid.py --combined > "$LOG/resweep_combined.log" 2>&1
echo "resweep ALL DONE $(date +%T)"
