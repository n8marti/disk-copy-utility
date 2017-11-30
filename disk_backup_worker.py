import re
from os import walk
from subprocess import run, PIPE


""" Count files to be copied & make backup copies. """
def worker(q,s,d):

	# Count the number of files to be copied.
	files_raw = run(["rsync", "-rltzn", "--stats", "--exclude='*.sys'",
		"--exclude='*.cab'", "--exclude='*.exe'", "--exclude='*.dll'",
		"--exclude='*}'", "--exclude='*.msi'", "--max-size=250M", s, d],
		stdout=PIPE)
	# Convert output to string
	files = str(files_raw)
	# Look for a sequence of digits following "Number of created files: "
	pattern = '(?<=Number of created files:\s)[0-9,]*'
	total_raw = re.search(pattern, files).group(0)
	# Remove any commas in total
	total = total_raw.replace(',','')
	# Send total back to main process
	q.put(float(total))

	# Run actual backup command.
	run(["rsync", "-rltz", "--exclude='*.sys'", "--exclude='*.cab'", 
		"--exclude='*.exe'", "--exclude='*.dll'", "--exclude='*}'",
		"--exclude='*.msi'", "--max-size=250M", s, d])
	#"--log-file="$log""
	return


""" Count number of files already copied at a given point in time. """
def file_count(q,d):
	# list all directories and files in destination
	scan = walk(d)
	count = 0
	for i in scan:
		# count no. of dirs (i[1]) and files (i[2]) in given dir
		qty = len(i[1]) + len(i[2])
		count += qty
	# send total back to main process
	q.put(float(count))
