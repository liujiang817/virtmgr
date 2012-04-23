# -*- coding: utf-8 -*-
import libvirt, re, time, socket
import virtinst.util as util
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def vm_conn(host_ip, creds):
	flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
  	auth = [flags, creds, None]
	uri = 'qemu+tcp://' + host_ip + '/system'
	try:
	   	conn = libvirt.openAuth(uri, auth, 0)
	   	return conn
	except:
		return "error"

def index(request, host_id):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')

	kvm_host = Host.objects.get(user=request.user.id, id=host_id)

	def creds(credentials, user_data):
		for credential in credentials:
			if credential[0] == libvirt.VIR_CRED_AUTHNAME:
				credential[4] = kvm_host.login
				if len(credential[4]) == 0:
					credential[4] = credential[3]
			elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
				credential[4] = kvm_host.passwd
			else:
				return -1
		return 0

	def get_all_vm():
		try:
			vname = {}
			for id in conn.listDomainsID():
				id = int(id)
				dom = conn.lookupByID(id)
				vname[dom.name()] = dom.info()[0]
			for id in conn.listDefinedDomains():
				dom = conn.lookupByName(id)
				vname[dom.name()] = dom.info()[0]
			return vname
		except:
			return "error"

	def get_info():
		try:
			info = []
			xml_cap = conn.getCapabilities()
			xml_inf = conn.getSysinfo(0)
			info.append(conn.getHostname())
			info.append(conn.getInfo()[0])
			info.append(conn.getInfo()[2])
			info.append(util.get_xml_path(xml_inf, "/sysinfo/processor/entry[6]"))
			return info
		except:
			return "error"

	def get_mem_usage():
		try:
			allmem = conn.getInfo()[1] * 1048576
			freemem = conn.getMemoryStats(-1,0)
			freemem = (freemem.values()[0] + freemem.values()[2] + freemem.values()[3]) * 1024
			percent = (freemem * 100) / allmem
			percent = 100 - percent
			memusage = (allmem - freemem)
			return allmem, memusage, percent
		except:
			return "error"

	def get_cpu_usage():
		try:
			prev_idle = 0
			prev_total = 0
			for num in range(2):
			        idle = conn.getCPUStats(-1,0).values()[1]
			        total = sum(conn.getCPUStats(-1,0).values())
			        diff_idle = idle - prev_idle
			        diff_total = total - prev_total
			        diff_usage = (1000 * (diff_total - diff_idle) / diff_total + 5) / 10
			        prev_total = total
			        prev_idle = idle
			        if num is 0: 
		        		time.sleep(1)
		        	else:
		        		if diff_usage < 0:
		        			diff_usage == 0
			return diff_usage
		except:
			return "error"		

	error = []
	conn = vm_conn(kvm_host.ipaddr, creds)
	if conn != "error":
		all_vm = get_all_vm()
		host_info = get_info()
		mem_usage = get_mem_usage()
		cpu_usage = get_cpu_usage()
		lib_virt_ver = conn.getLibVersion()
		conn_type = conn.getURI()

		conn.close()
		
	return render_to_response('overview.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')
	else:
		return HttpResponseRedirect('/dashboard/')
