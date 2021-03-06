import http.server, threading, socketserver
import os, yaml

from ploader.utils import set_config_path


def create_http_server(port):
	httpd = socketserver.TCPServer(("0.0.0.0", port), http.server.SimpleHTTPRequestHandler)
	thread = threading.Thread(target = httpd.serve_forever)
	thread.start()
	return httpd

def handle_cwd(path='ploader/tests/cwd'):
	# looks like a workaround, is ...errr... a suitable solution...
	# background: this function is called many times, but I only want to go here if necessary
	try:
		os.chdir(path)
	except FileNotFoundError:
		pass
	set_config_path('../../../config.yaml')

def create_case_config(path='./config.yaml'):
	basic_conf = {
		'download-dir': 'somewhere',
		'captcha-api-key': 'foo',
		'port': 42424,
		'parallel-download-num': 2
	}
	yaml.dump(basic_conf, open(path, 'w'), default_flow_style=False)