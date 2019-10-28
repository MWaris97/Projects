SET /A port = 4000

python node.py -p %port% -n ECP01 && python initialize.py -p %port%