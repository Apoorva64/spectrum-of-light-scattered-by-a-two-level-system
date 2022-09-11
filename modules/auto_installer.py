from subprocess import call
import time

try:
    call(['pip', 'install', '-r', 'requirements.txt'])
except FileNotFoundError:
    try:
        call(['conda', 'install', '-r', 'requirements.txt'])
    except FileNotFoundError:
        print("couldn't auto install the packages")
        time.sleep(1)


def install():
    pass
