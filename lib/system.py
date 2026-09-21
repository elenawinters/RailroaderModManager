import subprocess
import datetime
import os

def parse_iso_datetime(s):
    # print('parse_iso_datetime({!r})'.format(s))
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')

def open_url(url):
    # The webbrowser module opens the OS native browser, which in my case is FireDragon.
    # However, I use Zen on my Arch system, and I want the download page to open in the browser so that I am logged in.
    # From what I can tell, this is a common problem with webbrowser not respecting the default browser set in the OS.
    # So, I will provide OS specific commands to open the URL in the default browser.
    # I will only test this on Linux. Please PR if broken on other OSes.
    if os.name == 'nt':  # Windows
        os.startfile(url)
    elif os.name == 'mac':  # macOS
        subprocess.run(['open', url])
    else:  # Linux and other OSes
        subprocess.run(['xdg-open', url])