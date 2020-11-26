#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sqlite3
import os
import platform
import argparse
import logging
from logging.handlers import RotatingFileHandler 
import json

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


# ==============================================================================
#                                     UTILS
# ==============================================================================
def dict_factory(cursor, rows):
	"""Generate a list of dictionary from a result query"""

	if rows is None: return

	l = list()
	for row in rows:
		d = dict()
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		l.append(d)
	return l


def pretty_table(data):
	"""Generate a CLI table with column names as headers"""

	if len(data) == 0: return "No data"
	# store the longest string per column
	sizes = dict()
	# size of the headers
	for k in data[0].keys():
		sizes[k] = len(k)
	# size of the data
	for row in data:
		for k, v in row.items():
			if len(str(v)) > sizes[k]: sizes[k] = len(str(v))
	# total width of the table
	width = sum(sizes.values()) + (3*len(sizes)) + 1
	
	table = str()
	# generate the headers
	for k in data[0].keys():
		spaces = " "*(sizes[k] - len(k))
		table += f"| {k} {spaces}"
	table += "|"

	# separator
	table += f"\n"
	for k in data[0].keys():
		line = "=" * (sizes[k] + 2)
		table += f"|{line}"
	table += f"|\n"

	# generate the rows
	for row in data:
		for k, v in row.items():
			spaces = " "*(sizes[k] - len(str(v)))
			table += f"| {v} {spaces}"
		table += "|\n"

	return table


def load_config():
	path = os.path.join(SCRIPT_PATH, "config.json")
	if os.path.exists(path):
		with open(path, "r") as f:
			APP_LOG.debug(f"Loaded config from {path}")
			return json.load(f)
	else:
		APP_LOG.error(f"Could not load config from {path}")
		exit(1)


# ==============================================================================
#                                  DB INTERFACE
# ==============================================================================
def connect(dbPath):
	"""Connect to the sqlite database"""
	try:
		db = sqlite3.connect(dbPath)
	except Exception as e:
		APP_LOG.error(f"Connexion to the database failed. Check the path: {dbPath}", exc_info=True)
		exit(1)
	else:
		APP_LOG.debug(f"Connexion to the database successful.")
		return db, db.cursor()


def query(cursor, query_, info):
	"""Query the database with logging handling"""

	try:
		results = cursor.execute(query_)
	except Exception as e:
		APP_LOG.error(f"Query to fetch {info} failed.", exc_info=True)
		APP_LOG.error(query_)
	else:
		results = results.fetchall()
		results = dict_factory(cursor, results)

		APP_LOG.debug:gc(f"Query to fetch {info} successful: {len(results)} rows")
		APP_LOG.debug(f"\n{pretty_table(results)}")

		return results 


def query_tvshows(cursor, filter_=None, filterOut=None):
	"""Fetch all the tvshows list"""

	query_ = """
			SELECT 
				DISTINCT(ep.idShow)		id,
				ep.strTitle				title
			FROM episode_view 			ep
			"""
	if filter_ or filterOut:
		query_ += "WHERE\n"

	if filter_:
		query_ += f"\tep.idShow IN ({','.join(x for x in filter_)})"

	if filter_ and filterOut:
		query_ += "\nAND"

	if filterOut:
		query_ += f"\tep.idShow NOT IN ({','.join(x for x in filterOut)})"

	return query(cursor, query_, "tvshows list") 


def query_to_del(cursor, whitelist=tuple()):
	"""Fetch the tvshows' episodes to delete"""

	query_ = f"""
			SELECT
				ep.strTitle		AS tvshow,
				ep.c12			AS season,
				ep.c13			AS episode,
				ep.c18			AS file_path
			FROM
				episode_view ep 
			WHERE 
					ep.playCount >= 1
				AND ep.idShow NOT IN ({','.join(x for x in whitelist)})
			"""
	return query(cursor, query_, "tvshows to be deleted")


# ==============================================================================
#                                   WHITELIST
# ==============================================================================
WHITELIST_PATH = os.path.join(SCRIPT_PATH, "whitelist.json")

def input_validation(choice, validLst):

	while True:
		invalidChoice = False

		choice = [x.strip() for x in choice.split(',')]
		if choice[0] == 'q': quit()
		for x in choice:
			try: x = int(x)
			except ValueError:
				invalidChoice = True
				break
			else:
				if x not in [k['id'] for k in validLst]:
					invalidChoice = True
					break
		if invalidChoice: 
			choice = input("Wrong input.\nTry again or tape \'q\' to quit:\n")
		else: break

	return choice

def load_whitelist():

	if not os.path.exists(WHITELIST_PATH):
		APP_LOG.debug:gc(f"No json file at {WHITELIST_PATH}")
		return list()
	else: APP_LOG.debug(f"Loaded white list from {WHITELIST_PATH}")

	with open(WHITELIST_PATH, 'r') as f:
		return json.load(f)


def save_whitelist(whitelist):
	
	with open(WHITELIST_PATH, 'w') as f:
		json.dump(whitelist, f, indent=4)	


def add_whitelist():

	whitelist = load_whitelist()
	db, cursor = connect(DB_PATH)

	tvshows = query_tvshows(cursor, filterOut=whitelist)
	print(pretty_table(tvshows))
	choice = input("""
Select a tvshow to add to the whitelist by entering its number
comma-separated for multiple\nq to quit\n""")

	choice = input_validation(choice, tvshows)

	APP_LOG.debug(f"{len(choice)} tvshow(s) were added to the whitelist")
	whitelist += choice

	save_whitelist(whitelist)

	db.close()

	return whitelist


def display_whitelist():
	whitelist = load_whitelist()

	if len(whitelist) == 0:
		print("No tvshow in the whitelist.")
		return
	db, cursor = connect(DB_PATH)

	print("Tvshows in the white list:\n")	
	tvshows = query_tvshows(cursor, whitelist)
	print(pretty_table(tvshows))
	
	return tvshows


def remove_whitelist():

	whitelist = load_whitelist()
	db, cursor = connect(DB_PATH)

	tvshows = display_whitelist()

	choice = input("""
Select a tvshow to remove from the whitelist by entering its number
comma-separated for multiple\n""")

	choice = input_validation(choice, tvshows)

	APP_LOG.debug:gc(f"{len(choice)} tvshow(s) were removed from the whitelist")
	for x in choice: whitelist.remove(x)

	save_whitelist(whitelist)

	db.close()

	return whitelist
# ==============================================================================
#                                 USER INTERFACE
# ==============================================================================

def cli():
	"""Command line interface options."""

	parser = argparse.ArgumentParser()

	parser.add_argument("-s",
						"--simu",
						help="Display which episodes are going to be deleted without processing.",
						action="store_true"
						)
	parser.add_argument("-c",
						"--clean",
						help="Delete all the watched episodes.",
						action="store_true"
						)


	parser.add_argument("-t",
						"--tvshows",
						help="Display the list of tvshows in the database",
						action="store_true"
						)

	parser.add_argument("-a",
						"--add",
						help="Add a tvshow to the whitelist",
						action="store_true"
						)

	parser.add_argument("-d",
						"--display",
						help="Display the tvshows in the whitelist",
						action="store_true"
						)
	parser.add_argument("-r",
						"--remove",
						help="Remove tvshows from the whitelist",
						action="store_true"
						)
	parser.add_argument("-v", 
						"--verbose",
						help="Increase output verbosity",
                        action="store_const",
						const=logging.DEBUG,
						default=logging.INFO
						)

	return parser, parser.parse_args()


def logger(level):
	strFormat = "%(asctime)s - %(levelname)-7s - %(filename)s:%(funcName)-20s:%(lineno)-3s - %(message)s"
	logFormatter = logging.Formatter(strFormat,
									datefmt="%d-%b-%y %H:%M")
	logFile = os.path.join(SCRIPT_PATH, "EpCleansing.log")
	# file handler
	handler = RotatingFileHandler(logFile,
								mode='a',
								maxBytes=5*1024*1024, 
                                backupCount=1,
								encoding=None,
								delay=0
								)
	handler.setFormatter(logFormatter)
	handler.setLevel(level)
	# console handler
	console = logging.StreamHandler()
	console.setFormatter(logFormatter)

	appLog = logging.getLogger('root')
	appLog.setLevel(level)

	appLog.addHandler(handler)
	appLog.addHandler(console)

	return appLog


if __name__ == "__main__":
	# CLI args
	parser, args = cli()

	# Logger config
	APP_LOG = logger(args.verbose)

	# Config
	CONFIG = load_config()
	DB_PATH = CONFIG["kodiPaths"].get(platform.system())[0]
	if platform.system() == "Windows":
		DB_PATH = os.path.expandvars(DB_PATH)
	else:
		DB_PATH = os.path.expanduser(DB_PATH)
	if not os.path.exists(DB_PATH):
		APP_LOG.error(f"Kodi\'s data directory couldnot be found: {DB_PATH}")
		exit(1)
	else:
		APP_LOG.debug(f"Kodi\'s data directory exists: {DB_PATH}")

	# TODO: check db version
	DB_PATH = os.path.join(DB_PATH, CONFIG["dbNames"][0])
	if not os.path.exists(DB_PATH):
		APP_LOG.error(f"Kodi\'s database couldnot be found: {DB_PATH}")
		exit(1)
	else:
		APP_LOG.debug(f"Kodi\'s database exists: {DB_PATH}")

	# Delete all
	if args.clean:
		whitelist = load_whitelist()
		db, cursor = connect(DB_PATH)
		results = query_to_del(cursor, whitelist)
		for row in results:
			try:
				os.remove(row['file_path'])
			except FileNotFoundError:
				APP_LOG.error(f"Error while deleting, file not found:\n {row['file_path']}")
			except Exception:
				APP_LOG.error(f"Error while deleting {row['file_path']}", exc_info=True)
			else:
				APP_LOG.info(f"{row['tvshow']} - S{row['season']}E{row['episode']} deleted.")
		db.close()

	# Display the list of available tvshows
	elif args.tvshows:
		db, cursor = connect(DB_PATH)
		results = query_tvshows(cursor)
		db.close()
		print(pretty_table(results))

	# simulation - show which episodes would be deleted
	elif args.simu:
		
		whitelist = load_whitelist()
		db, cursor = connect(DB_PATH)
		results = query_to_del(cursor, whitelist)
		db.close()
		print(f"Number of episodes to delete: {len(results)}\n")
		print(pretty_table(results))

	# add - tvshows to whitelist
	elif args.add:
		add_whitelist()

	# Display the whitelist
	elif args.display:
		display_whitelist()

	# Remove tvshows from the whitelist
	elif args.remove:
		remove_whitelist()
	
	# default
	else:
		APP_LOG.warn(f"No option selected. No action done.\nPlease choose an option.")
		parser.print_help()	
	# TODO: run and clean kodi's lib
	# TODO: safe SQL
