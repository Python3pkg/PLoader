import threading
import subprocess
import os, os.path
import time
import re
import sys

import ploader.utils as utils
import ploader.rar_handler, rarfile


class Download(object):
	def __init__(self, name, link_list, passwd = None):
		self.name = name
		self.links = link_list
		self.passwd = passwd

		self.settings = utils.load_config();

		self.dw_dir = utils.set_dir(os.path.join(self.settings["download-dir"], self.name.replace(" ", "_")))
		self.log_dir = utils.set_dir(os.path.join(self.dw_dir, "logs"))

		self.saver = None

		self.cur_item = None

		self.acquired = False

	def __str__(self):
		out = "\n"
		out += "%s (%i) - %s\n" % (self.name, len(self.links), self.passwd)
		for ele in self.links:
			out += "[%s] %s (%s)\n" % (ele["status"], ele["link"], ele["progress"] if "progress" in list(ele.keys()) else "-")
		out += "-> %s\n" % self.dw_dir
		return out

	def __repr__(self):
		return repr(str(self))

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
		if nots and not self.acquired:
			return "not started"

		# TODO: include 'skip' status in final status

		return "loading"

	def execute(self, on_finish):
		self.download()
		self.unpack()

		on_finish()

	def unpack(self):
		if self.get_status() == "success":
			for ele in self.links:
				fn = ele["filename"]
				if ploader.rar_handler.is_rar(os.path.join(self.dw_dir, fn)):
					rar = ploader.rar_handler.RAR(os.path.join(self.dw_dir, fn), self.passwd)
					if rar.all_files_present():
						if rar.is_first_vol():
							sys.stdout.write("Extracting \"%s\"..." % fn)
							sys.stdout.flush()
							try:
								rar.extract()
								print(" Done")
							except rarfile.RarNoFilesError:
								print(" Fail: No files found")
							except rarfile.RarCRCError:
								print(" Fail: CRC error")
					else:
						print(("Could not find all compressed files for \"%s\"" % fn))
				else:
					print(("No decompression method found for \"%s\"" % fn))

	def download(self):
		"""Handles complete download
			Puts link to end of list if error occurs
		"""
		error_item = None
		for ele in self.links:
			if ele["status"] == "success" or ele["status"] == "skip":
				# skip if already successfully (or completely broken) downloaded
				continue

			# init progress bar
			ele["progress"] = "-"
			self.cur_item = ele

			# get item info
			link = ele["link"]
			fname = ele["filename"]

			# set identifiers
			ele["status"] = "loading"
			self.loading = True

			# get url info (name, direct link)
			answ = utils.parse_url_info(*utils.get_url_info(link))
			parse_error = not answ # answ == False on error

			load_error = load_fatal = False
			if not parse_error:
				# try to actually download file
				fname, download_link = answ
				if not ele["filename"]:
					ele["filename"] = fname
			
				final_path = os.path.join(self.dw_dir, fname)
				load_error, load_fatal = utils.load_file(download_link, final_path, self.handle_download_progress)

			# handle errors if needed
			self.loading = False
			if load_fatal:
				ele["status"] = "skip"
				error_item = ele
			elif load_error or parse_error:
				ele["status"] = "error"
				error_item = ele
			else:
				ele["status"] = "success"

			if error_item:
				# move error to end of list
				self.links.remove(error_item)
				self.links.append(error_item)
				error_item = None

				ele["progress"] = "-"
			else:
				# fix size
				if '/' in ele["progress"]:
					ele["progress"] = ele["progress"].split('/')[1]

			# save current changes
			self.saver()

	def handle_download_progress(self, loaded_block_num, block_size, total_size):
		self.cur_item["progress"] = str(utils.sizeof_fmt(loaded_block_num * block_size)) + "/" + str(utils.sizeof_fmt(total_size))
