import subprocess, os, os.path, yaml, shlex, re, urllib.parse, shutil, urllib.request, threading


def exe(cmd):
	if type(cmd) != type([]):
		cmd = shlex.split(cmd)
	return subprocess.Popen(cmd)
def exe_pipes(cmd):
	if type(cmd) != type([]):
		cmd = shlex.split(cmd)
	return subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
def exe_flos(cmd, fout, ferr):
	if type(cmd) != type([]):
		cmd = shlex.split(cmd)
	out = open(fout, "w") #io.StringIO()
	err = open(ferr, "w") #io.StringIO()
	return subprocess.Popen(cmd, stdout = out, stderr = err), out, err

def dw_file_to(url, path, callback):
	"""Saves file from url to path
	"""
	#with urllib.request.urlopen(url) as response, open(path, 'wb') as out_file:
	#	shutil.copyfileobj(response, out_file)
	urllib.request.urlretrieve(url, path, callback)

def set_dir(directory, create=True):
	if os.path.isdir(directory):
		return directory
	else:
		if create:
			os.makedirs(directory)
			return directory
		else:
			raise Exception("Tried to assign invalid directory: \"%s\"" % directory)

def set_file(f, create=True):
	if os.path.isfile(f):
		return f
	else:
		if create:
			open(f, 'wb').close()
			return f
		else:
			Exception("Tried to assign invalid file: \"%s\"" % f)

def write_to_file(path, content):
	fd = open(path, "w")
	fd.write(content)
	fd.close()

def get_url_info(url):
	"""Retrieves information about given url
	"""
	settings = load_config()

	try:
		download_link_getter = exe_pipes(
			'plowdown --9kweu ' +
			settings["captcha-api-key"] +
			' -v1 --skip-final --printf "%%f%%n%%d" %s' % url
		)
		stdout, stderr = download_link_getter.communicate()
		res_list = stdout.decode("utf8").split("\n")
		res_err = stderr.decode("utf8")
		retc = download_link_getter.returncode
	except:
		# nasty hack to try to download file directly if plowshare is not installed (TODO: make this better!)
		res_list = []
		retc = 2
		res_err = ''

	return url, res_list, res_err, retc

def parse_url_info(url, res_list, res_err, retc):
	"""Parses information about given url, returns false on error
	"""
	if len(res_list) != 3:
		if retc == 2 or retc == 0: # -> No available module or something weird (e.g. ftp)
			fname = url_to_filename(url)
			if len(fname) != 0:
				# download file directly
				return fname, url

		print((
			"Error while getting link info: " +
			repr(res_err) +
			" (" +
			str(retc) +
			")"
		))
		return False
	else:
		return res_list[0], res_list[1]

def load_file(url, path, callback):
	"""Downloads url to file.
		Returns (False, False) on success, otherwise (True, <x>)
		If <x> is True this is considered to be a fatal error, link will be skipped
		If <x> is False this link will be retried.
	"""
	print(("Saving '%s' to '%s'" % (url, path)))

	try:
		dw_file_to(url, path, callback)
	except Exception as e:
		print(("Error while downloading: " + str(e)))

		# check for fatal error
		if e.code == 404:
			return (None, True)

		return (True, False)
	else:
		return (False, False)		

def set_config_path(path):
	global config_path
	config_path = path

def load_config():
	# set_config_path(..) *must* be called by now
	if os.path.isfile(config_path):
		return yaml.load(open(config_path, "r"))
	else:
		# return defaults
		print(('No config file present, creating default one (path: %s)' % config_path))
		create_default_config(config_path)
		
		try:
			return yaml.load(open(config_path, "r"))
		except:
			raise Exception('[FATAL] - Could not create config (path: %s)' %  config_path)

def create_default_config(path='./config.yaml'):
	basic_conf = {
		'download-dir': 'downloads',
		'captcha-api-key': 'xyz',
		'port': 50505,
		'parallel-download-num': 1
	}
	yaml.dump(basic_conf, open(path, 'w'), default_flow_style=False)

def clean_links(raw_data):
	return re.findall('(?:ftp|https|http)?://(?:[a-zA-Z]|[0-9]|[$-_@.&+~]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', raw_data)

def url_to_filename(url):
	res = urllib.parse.urlparse(url)
	return os.path.basename(res.path)

def sizeof_fmt(num):
	for x in ['bytes','KB','MB','GB']:
		if num < 1024.0:
			return "%3.1f%s" % (num, x)
		num /= 1024.0
	return "%3.1f%s" % (num, 'TB')

def start_thread(func, callback=None):
	thread = threading.Thread(target=func, kwargs={'on_finish': callback})
	thread.daemon = True
	thread.start()

def get_user_dir():
	return os.path.expanduser('~')

def get_application_dir():
	return set_dir(os.path.join(get_user_dir(), '.ploader'))