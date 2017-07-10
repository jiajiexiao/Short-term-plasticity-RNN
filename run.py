from parameters import *
import hud
import model
import threading
import psutil
import sys
import os

def run_model():
    if par['use_HUD']:
        t_HUD = threading.Thread(target=hud.main, args=(switch,))
        t_HUD.start()
    else:
        model.main(switch)


def switch(iteration, prev_switch_iteration, savename):
    """
    if iteration == (prev_switch_iteration + 10):
        if par['allowed_categories'] == [0]:
            par['allowed_categories'] = [1]
            print("Switching to category 1.\n")
            with open(savename, 'a') as f:
                f.write('Switching to category 1.\n')
            return iteration
        elif par['allowed_categories'] == [1]:
            par['allowed_categories'] = [0]
            print("Switching to category 0.\n")
            with open(savename, 'a') as f:
                f.write('Switching to category 0.\n')
            return iteration
        else:
            print("ERROR: Bad category.")
            quit()
    else:
        return prev_switch_iteration
    """
    return prev_switch_iteration


def script():
    par['df_num'] = '0007'

    run_model()


script()