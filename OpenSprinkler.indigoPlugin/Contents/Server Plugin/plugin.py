#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# OpenSprinkler plugin for indigo
# Based on sample code that is:
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo

import requests
import hashlib

zoneSep = ","
commaSep = "|"

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super().__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = True

	########################################
	def startup(self):
		# self.debugLog(u"startup called")
		pass

	def shutdown(self):
		# self.debugLog(u"shutdown called")
		pass

	########################################
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		return (True, valuesDict)

	########################################
	def deviceStartComm(self, dev):
		# Called when communication with the hardware should be established.
		# Get station status
		try:
			opts = self.querySprinkler(dev, "jo")
			if opts['fwv'] < 213:
				raise Exception(u'OpenSprinkler plugin requires firmware 2.1.3 or newer')
			status = self.querySprinkler(dev, "jn")
			nStations = len(status['snames'])
			stn_dis = status['stn_dis']
			activeStations = [idx for idx in range(nStations) if (stn_dis >> idx) & 1 == 0]
			stationNames = [status['snames'][i].replace(",",commaSep) for i in activeStations]
			self.logger.info(u'Station names: %s' % (','.join(stationNames)))
			self.logger.info(u'%i stations are active' % len(activeStations))
			newProps = dev.pluginProps
			newProps['ZoneNames'] = zoneSep.join(stationNames)
			# TODO: Implement if activeStations is not contiguous
			newProps['NumZones'] = len(activeStations)
			dev.replacePluginPropsOnServer(newProps)
		except Exception as e:
			self.logger.info(u'Unable to start communication: %s' % str(e))

	########################################
	# Query OpenSprinkler device
	######################
	def querySprinkler(self, dev, keyword, data={}):
		props = dev.pluginProps
		url, pw = props['address'], props['password']
		if not url.startswith("http"):
			url = f"http://{url}"
		data['pw'] = hashlib.md5(pw.encode()).hexdigest()
		try:
			r = requests.get(f"{url}/{keyword}", data)
			r.raise_for_status()
			output = r.json()
			errno = output.get('result',1)
			strerror = {
				1:	u'Success',
				2:	u'Unauthorized',
				3:	u'Mismatch',
				16: u'Data Missing',
				17: u'Out of Range',
				18: u'Data Format Error',
				32: u'Page Not Found',
				48: u'Not Permitted'}.get(errno, u'Unknown')
			if errno != 1:
				raise EnvironmentError(errno, u'%s - %s' % (dev.name, strerror))
			for k,v in output.items():
				if type(v)==list and len(v)==1:
					output[k] = v[0]
			return output
		except ValueError as e:
			raise ValueError(u'Cannot parse output for "%s", error: %s' % (dev.name, e.msg))
	
	def hasRain(self, dev):
		data = self.querySprinkler(dev, 'jc')
		try:
			return data['rs'] == 1
		except KeyError:
			return False
	
	def allZonesOff(self, dev, skip=-1):
		try:
			props = dev.pluginProps
			for i in range(props['NumZones']):
				if i != skip:
					self.querySprinkler(dev, "cm", {'sid': i, 'en': 0})
			if skip < 0:
				self.logger.info(u"sent \"%s\" %s" % (dev.name, "all zones off"))
				dev.updateStateOnServer("activeZone", 0)
		except Exception as e:
			self.logger.info(u"send \"%s\" %s failed: %s" % (dev.name, "all zones off", str(e)), isError=True)
	
	########################################
	# Sprinkler Control Action callback
	######################
	def actionControlSprinkler(self, action, dev):
		########################################
		# Required plugin sprinkler actions: These actions must be handled by the plugin.
		########################################
		###### ZONE ON ######
		if action.sprinklerAction == indigo.kSprinklerAction.ZoneOn:
			# Command hardware module (dev) to turn ON a specific zone here.
			zoneName = u'Unknown'
			try:
				sid = action.zoneIndex - 1
				zoneName = dev.zoneNames[sid].replace(commaSep,",")
				props = dev.pluginProps
				if not props['ignorerain'] and self.hasRain(dev):
					self.logger.info(u"Rain detected - cannot water \"%s - %s\"" % (dev.name, zoneName))
					return
				# Disable any current program
				self.allZonesOff(dev, sid)
				self.sleep(5) # Workaround when switching manual stations
				self.querySprinkler(dev, "cm", {'sid': sid, 'en': 1, 't': props['maxtime']})
				self.logger.info(u"sent \"%s - %s\" on" % (dev.name, zoneName))
				dev.updateStateOnServer("activeZone", action.zoneIndex)
			except Exception as e:
				self.logger.info(u"send \"%s\" zone \"%s\" on failed: %s" % (dev.name, zoneName, str(e)), isError=True)

		###### ALL ZONES OFF ######
		elif action.sprinklerAction == indigo.kSprinklerAction.AllZonesOff:
			self.allZonesOff(dev)

	########################################
	# General Action callback
	######################
	def actionControlUniversal(self, action, dev):
		###### BEEP ######
		if action.deviceAction == indigo.kUniversalAction.Beep:
			# Beep the hardware module (dev) here:
			self.logger.info(u"\"%s\" %s is not supported" % (dev.name, "beep request"))

		###### STATUS REQUEST ######
		elif action.deviceAction == indigo.kUniversalAction.RequestStatus:
			# Query hardware module (dev) for its current status here:
			try:
				status = self.querySprinkler(dev, "js")
				props = dev.pluginProps
				zoneNames = props['ZoneNames'].split(zoneSep)
				for i in range(props['NumZones']):
					if status['sn'][i] == 1:
						state = "On"
					else:
						state = "Off"
					self.logger.info(u'"%s": %s' % (zoneNames[i], state))
			except Exception as e:
				self.logger.info(u'Unable to get status: %s' % str(e))
