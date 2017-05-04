export PYTHONPATH=..

xvfb-run -a -s "-screen 0 1400x900x24 +extension RANDR" -- python -u trpo_gym.py
#python -u trpo_gym.py
