import threading
import subprocess
import os, os.path
import utils
import time
import re

import rar_handler, rarfile


settings = utils.load_settings();

class Download(object):
	def __init__(self, name, link_list, passwd = None):
		self.name = name
		self.links = link_list
		self.passwd = passwd

		self.dw_dir = utils.set_dir(os.path.join(settings["download-dir"], self.name.replace(" ", "_")))
		self.log_dir = utils.set_dir(os.path.join(self.dw_dir, "logs"))

		self.saver = None

	def __str__(self):
		out = "\n"
		out += "%s (%i) - %s\n" % (self.name, len(self.links), self.passwd)
		for ele in self.links:
			out += "[%s] %s\n" % (ele["status"], ele["link"])
		out += "-> %s\n" % self.dw_dir
		return out

	def set_save_function(self, save_fun):
		self.saver = save_fun

	def get_status(self):
		suc = True
		for ele in self.links:
			if ele["status"] != "success":
				suc = False
		if suc:
			return "success"

		nots = True
		for ele in self.links:
			if ele["status"] != "not started":
				nots = False
		if nots:
			return "not started"

		return "loading"

	def unpack(self):
		if self.get_status() == "success":
			for ele in self.links:
				fn = ele["filename"]
				if fn != "unknown":
					if rar_handler.is_rar(os.path.join(self.dw_dir, fn)):
						rar = rar_handler.RAR(os.path.join(self.dw_dir, fn), self.passwd)
						if rar.is_first_vol():
							print("Extracting \"%s\"..." % fn, end="")
							try:
								rar.extract()
								print(" Done")
							except rarfile.RarNoFilesError:
								print(" Fail: No files found")
							except rarfile.RarCRCError:
								print(" Fail: CRC error")
					else:
						print("No compression method found for \"%s\"" % fn)
				else:
					print("Could not estimate filename")

	def download(self):
		def load():
			error_item = None
			for ele in self.links:
				if ele["status"] == "success":
					continue

				link = ele["link"]
				if ele["filename"] == None:
					ele["filename"] = utils.get_filename(link)
				fname = ele["filename"]

				cur_files = set(os.listdir(self.dw_dir))
				ele["status"] = "loading"

				self.loading = True
				proc, stdout, stderr = utils.exe_flos(
						["plowdown", "-o", self.dw_dir, "--9kweu", settings["captcha-api-key"], "--fallback", link],
						os.path.join(self.log_dir, "stdout.log"),
						os.path.join(self.log_dir, "stderr.log")
				)

				poll = proc.poll()
				while poll == None:
					poll = proc.poll()
					print("> \"%s\" => \"%s\" - Loading" % (link, os.path.join(self.dw_dir, fname)))
					print("\033[1A", end="") # moves cursor one row up
					time.sleep(1)
				print("> \"%s\" => \"%s\" - Done ($? = %i)" % (link, os.path.join(self.dw_dir, fname), poll))
				self.loading = False

				if poll != 0:
					ele["status"] = "error"
					error_item = ele
				else:
					ele["status"] = "success"

				# move error to end of list
				if error_item:
					self.links.remove(error_item)
					self.links.append(error_item)
					error_item = None

				# try to estimate file name if not given
				if fname == "unknown":
					new_file = list(set(os.listdir(self.dw_dir)) - cur_files)
					if len(new_file) == 1:
						# newly created file
						ele["filename"] = new_file[0]
					else:
						# guess filename from url
						ele["filename"] = url_to_filename(link)

				# save current changes
				self.saver()

#		self.thread = threading.Thread(target = load)
#		self.thread.start()
		load()
