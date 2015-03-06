"""processes the command line args.

"""

#relative import
import database 

#import from standard library
import ConfigParser
import tempfile
import re
import time
import prettytable
import subprocess
from textwrap import fill


###GENERAL ###

def start_process(cmd_line_args):
	"""Starts processing the command line args. Filters out unrelevant arguments.

	"""
	print cmd_line_args
	relevant_args = ({key: value for key, value in cmd_line_args.iteritems() if value})
	if not '--editor' in relevant_args:
		check_operation(relevant_args)
	else:
		write_config(relevant_args['--editor'], 'Editor')		


def split_arguments(arguments):
	"""Splits the given arguments from the command line in content and flags.

	"""
	content, flags = {}, {}
	for index, item in arguments.iteritems(): 
		if index in ('-s', '-e', '-I', '-i', '-c', '-a', '-d', '-f', '--cut'):
			flags[index] = item
		else:
			content[index] = item 

	return (content, flags)


def check_operation(relevant_args):
	""" Checks which operation (add, display, ...)
		needs to be handled. 

	"""
	
	requested_content, flags = split_arguments(relevant_args)

	if '-f' in flags:
		process_file_adding(requested_content)
	elif '-d' in flags:
		determine_display_operation(requested_content, flags)
	elif '-a' in flags:
		process_add_content(requested_content, flags)
	elif '-c' in flags:
		process_code_adding(requested_content)
	else:
		print """An unexpected error has occured 
				while processing {0} with flags {1}
				""".format(requested_content, flags)
		return "error"
		

###CONFIG ###

def write_config(item, section):
	"""Writes the item to the cfg file in the sepcified section.

	"""
	config = ConfigParser.RawConfigParser()
	path_to_cfg = '../res/codedict_config.cfg'

	if section not in config.sections():
		config.add_section(section)	

	config.set(section, 'editor', item)

	with open('../res/codedict_config.cfg', 'a') as configfile:
		    config.write(configfile)

def read_config_write_on_failure(requested_item, section):
	"""Reads the config file, writes if no entry is found.

	"""

	config = ConfigParser.RawConfigParser()
	path_to_cfg = '../res/codedict_config.cfg'
	
	try:
		config.read(path_to_cfg)
		cfg_entry = config.get(section, requested_item)
	except ConfigParser.Error as error:
		print "An error has occured: ", error
		cfg_entry = False

	if not cfg_entry:

		cfg_entry = raw_input("Enter " +section+" :").strip()
		if section not in config.sections():
			config.add_section(section)	

		config.set(section, requested_item, cfg_entry)
	
		with open('../res/codedict_config.cfg', 'a') as configfile:
		    config.write(configfile)

	return cfg_entry


def check_for_editor():
	"""Checks if the editor is set and if not prompts the user to enter it.

	"""

	return read_config_write_on_failure('editor', 'Editor')


def check_for_suffix(language):
	"""Checks if the cfg has a suffix for the requested lang, if not 
	   it prompts to specify one.

	"""

	return read_config_write_on_failure(language, 'Suffix')


###OUTPUT ###

def print_content_nice_form(results):
	"""Sets up a nice input form (editor) for viewing a large amount of content. -> Read only


	"""

	editor = [item for item in check_for_editor().split(" ")]

	initial_message = results.get_string() #prettytable to string
	
	with tempfile.NamedTemporaryFile() as tmpfile:
		tmpfile.write(initial_message)
		tmpfile.flush()
  		subprocess.call(editor + [tmpfile.name])
  	return True


def print_to_console(table):
	"""Prints to console.

	"""
	if table:
		print table
	else:
		print "No results"



def code_input_form(language, existent_code=False):
	"""Sets up a nice input form (editor) for code adding and viewing.


	"""

	editor = [item for item in check_for_editor().split(" ")]

	language_suffix = check_for_suffix(language)

	initial_message = existent_code.decode('utf-8')


	with tempfile.NamedTemporaryFile(delete=False, suffix=language_suffix) as tmpfile:
		if existent_code:
			tmpfile.write(initial_message)
		tmpfile.flush()
  		subprocess.call(editor + [tmpfile.name])
  	with open(tmpfile.name) as my_file:
  		return my_file.read() 


###CODE ###


def process_code_adding(content, target_code=False):
	"""Processes code adding, provides a nice input form for the user.

	"""

	if not target_code:
		existent_code = database.retrieve_content(content, "code")[0]
	else:
		existent_code = target_code

	content['data'] = code_input_form(content['<language>'], existent_code)

	if content['data'] == existent_code or not content['data'].isalnum():
		return 'No DB operation needed, nothing changed'

	#update DB on change
	content['<attribute>'] = "code"
	start = time.time()
	database.update_content(content) 
	print "end", time.time()-start 
	return "Finished adding code to DB"



###FILE ###

def process_file_adding(content):
	"""Processes adding content from a file.

	"""
	
	try:
		with open(content['<path-to-file>']) as input_file:
			file_text = input_file.read()
	except (OSError, IOError) as error:
		print "I/O error({0}): {1}".format(error.errno, error.strerror)
		return False
	#TODO: catch wrong input file
	#TODO: catch forbidden chars and words
	all_matches = re.findall(r'%.*?\|(.*?)\|[^\|%]*?\|(.*?)\|[^\|%]*\|(.*?)\|', file_text, re.UNICODE)
	
	# for single_match in all_matches:
	# 	print single_match	    
 	database.add_content(all_matches, content['<language>'])
	


###ADD ###

def process_add_content(content, flags):
	"""Processes content adding. 

	"""

	if '-I' in flags or '-i' in flags:
		update_content(content)
	else:
		insert_content()


def update_content(content):
	"""Processes how to update content.

	"""

	content['data'] = unicode(raw_input("Change "+content['<attribute>']+" : ").strip(), 'utf-8')
	start = time.time()
	print content
	success = database.update_content(content)
	print "end", time.time()-start
	if success:
		print "success"
	else: print "Failure"
	return "Finished adding content to DB"


def insert_content():
	"""Processes how to insert content.

	"""

	content_to_add = {}

	language = raw_input("language: ").strip()
	language = validate_language(language)


	for index, item in enumerate(('shortcut: ', 'command: ', 'comment: ')): 
		content_to_add[index] = raw_input(item).strip()
		content_to_add[index] = validate_content_add(content_to_add[index], item)


	start = time.time()
	
	print "Time creating table:", time.time()-start

	read_config_write_on_failure(language, 'Suffix')	

	start = time.time()
	print "Adding {0} to DB".format(content_to_add)
	value_list = [content_to_add]
	success = database.add_content(value_list, language)
	print "Time adding content to DB", time.time()-start
	return success

	
def validate_language(language):
	"""Validates the language string from the user input.

	"""
	#TODO: full list of forbidden chars and words
	forbidden_chars = (';', ':', '!')
	forbidden_words = ('select', 'where')
	while len(language.split(" ")) > 1 or is_in(forbidden_chars, language) or ( 
	is_in(forbidden_words, language)):
		language = raw_input("enter language again: ").strip()
	return unicode(language, 'utf-8')


def validate_content_add(value, string):
	"""Validates the content strings from the user input.

	"""
	#TODO: full list of forbidden chars and words
	forbidden_chars = (';', ':', '!')
	forbidden_words = ('select', 'where')
	while is_in(forbidden_chars, value) or is_in(forbidden_words, value):
		value = raw_input("enter again - " +string).strip()
	value = unicode(value, 'utf-8')
	return value


def is_in(forbidden_items, text):
	"""Checks if one of the forbidden items is in text.

	"""
	for item in forbidden_items:
		if item in text:
			return True   
	return False


### DISPLAYING ###


def determine_display_operation(location, flags):
	"""Processes display actions, checks if a nice form has to be provided or not.

	"""

	cutsearch = False
	if '--cut' in flags:
		cutsearch = location['<use_case>'] 

	if not "<use_case>" in location:
		results = display_language_content(location, cutsearch)
	
	elif not '-e' in flags:
		print "No nice form needed."
		
		if '-s' in flags:
			print "Short version requested."
			results = display_extended_content(location, cutsearch)
		else:
			print "Only command requested"
			results = display_basic_content(location, cutsearch)
			
	else:
		results = display_full_content(location, cutsearch)
	
	if results:
		process_follow_up_lookup(location, results)


def display_extended_content(location, cutsearch):
	"""Processes display extended content, prints to STDOUT.

	"""

	all_results = database.retrieve_content(location, "extended")
	column_list = ["ID", "use_case", "command", "comment", "code added?"]
	
	updated_results, table = build_table(column_list, all_results)
	if len(all_results) < 10:
		print_to_console(table)
	return updated_results

	 
def display_language_content(location, cutsearch):
	"""Processes displaying extended content, prints to STDOUT.

	"""


	all_results = database.retrieve_content(location, "language")

	if not all_results:
		print "No results"
		return False

	column_list = ["ID", "use_case", "command", "code added?"]
	updated_results, table = build_table(column_list, all_results)
	
	if len(all_results) < 10:
		print_to_console(table)  
	else:
		print_content_nice_form(table)
	return updated_results


def display_full_content(location, cutsearch):
	"""Processes displaying full content

	"""

	all_results = database.retrieve_content(location, "full")

	column_list = ["ID", "use_case", "command", "comment", "code added?"]
	updated_results, table = build_table(column_list, all_results)	


	if all_results:
		print_content_nice_form(table)
	else:
		print "No results"
	print "Printing to nice form."
	return updated_results



def display_basic_content(location, cutsearch):
	"""Processes displaying basic content, prints to STDOUT by default.

	"""

	all_results = database.retrieve_content(location, "basic")
	column_list = ["ID", "use_case", "command", "code added?"]
	
	updated_results, table = build_table(column_list, all_results, cutsearch)
	if len(all_results) < 10:
		print_to_console(table)
	else:
		choice = raw_input("More than 10 results - do you wish to print to console anyway? (y/n)").strip()
		if choice in ('y', 'yes', 'Yes', 'Y'):
			print_to_console(updated_results)
		elif choice in ('n', 'no', 'No', 'N'):
			print_content_nice_form(updated_results)
		else:
			pass 
			#TODO: Handle this case
	return updated_results


def build_table(column_list, all_rows, cutsearch):
	"""Builds the PrettyTable and prints it to console.

	"""

	#column list length
	cl_length = len(column_list)-1
	print cl_length
	print cutsearch
	
	result_table = prettytable.PrettyTable(column_list)
	result_table.hrules = prettytable.ALL

	all_rows_as_list = []
	for row in all_rows:
		single_row = list(row)
		print single_row
		for index in range(1, cl_length - 1): # code doesnt need to be filled
			if cutsearch:
				single_row[1] = single_row[1].replace(cutsearch, "", 1) 
			fill(single_row[index], width=80/(cl_length+1))
		if single_row[cl_length]:
			single_row[cl_length] = "yes"
		else:
			single_row[cl_length] = "no" 
		result_table.add_row(single_row)
		all_rows_as_list.append(list(row))
	return (all_rows_as_list, result_table)


###SECOND ###

def prompt_by_index(results):
	"""Prompts the user for further commands after displaying content.
	   Valid input: <index> [attirbute] 
	"""

	valid_input = False
	while not valid_input:

		user_input = (raw_input(
		"Do you want to do further operations on the results? (CTRL-C to abort): ")
		.strip().split(" "))
		
		index = user_input[0]
		try:
			attribute = user_input[1]
		except IndexError:
			attribute = ""

		if len(user_input) <= 2 and index.isdigit() and int(index) >= 1 and int(index) <= len(results):	
			result_index = int(index)-1
			valid_input = True
			if attribute: 
				if not attribute in ('use_case', 'command', 'comment'):
					print "Wrong attribute, Please try again."
					valid_input = False
		else:
			print "Wrong index, Please try again."
	return (results[result_index], attribute) 		


def process_follow_up_lookup(original_request, results):
	"""Processes the 2nd operation of the user, e.g. code adding.

	"""

	new_target, attribute = prompt_by_index(results)

	if '<use_case>' in original_request:
		original_request['<use_case>'] += new_target[1]
	else:
		original_request['<use_case>'] = new_target[1]
	
	if attribute:
		print original_request
		original_request['<attribute>'] = attribute
		return update_content(original_request)
	else:
		target_code = new_target[len(new_target)-1]
		if not target_code:
			target_code = "\n"
		return process_code_adding(original_request, target_code=target_code)

