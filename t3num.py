#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab:

import sys, os, platform
import time, datetime
import re
import gzip, StringIO
import urllib, urllib2, ssl
import logging
import xml.etree.ElementTree as ET
import random

class config( object ):
	LOGLEVEL = logging.DEBUG
	LOGFORMAT = '%(asctime)s %(levelname)9s:%(lineno)-4d %(filename)-20s %(funcName)-15s -> %(message)s'
	UA = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
	EXTGZFILE = 'extensions.xml.gz'
	EXTXMLFILE = os.path.normpath( os.path.join( os.path.dirname( sys.argv[ 0 ] ), 'extensions.xml' ) )
	TIMESTR = '%Y-%m-%d %H:%M:%S'

	STEPS = 100

	matchers = {
		'chomp': re.compile( r'^[\r\n\t\s]+', re.S ),
	}

	host = {
		'mirrors'   : 'http://repositories.typo3.org/mirrors.xml.gz',
		'oldinstall': 'typo3/install/index.php',
		'newinstall': 'typo3/sysext/install/Start/Install.php',
	}

	T3HINT = 'typo3/index.php'
	ext_types = {
		'ext': { 'path': 'typo3conf/ext/', 'desc': 'normal extensions', },
		'sys': { 'path': 'typo3/sysext/' , 'desc': 'system extensions', },
	}
	EXTHINT = '/ext_emconf.php'

	infopages = [
		{ 'file': 'ChangeLog',      'desc': 'ChangeLog',              'down': True,  'first': True,  },
		{ 'file': 'doc/manual.sxw', 'desc': 'Extension manual (OO)',  'down': False, 'first': False, },
		{ 'file': 'doc/manual.pdf', 'desc': 'Extension manual (PDF)', 'down': False, 'first': False, },
		{ 'file': 'README',         'desc': 'README',                 'down': True,  'first': True,  },
		{ 'file': 'README.txt',     'desc': 'README',                 'down': True,  'first': True,  },
		{ 'file': 'doc/README',     'desc': 'README',                 'down': True,  'first': True,  },
		{ 'file': 'doc/README.txt', 'desc': 'README',                 'down': True,  'first': True,  },
		{ 'file': 'doc/TODO',       'desc': 'TODO',                   'down': False, 'first': False, },
		{ 'file': 'doc/TODO.txt',   'desc': 'TODO',                   'down': False, 'first': False, },
	]

	sysexts = {
		'about'                 : 'about sysext',
		'aboutmodules'          : 'aboutmodules sysext',
		'adodb'                 : 'adodb sysext',
		'backend'               : 'backend sysext',
		'belog'                 : 'belog sysext',
		'beuser'                : 'beuser sysext',
		'cms'                   : 'cms sysext',
		'context_help'          : 'context_help sysext',
		'core'                  : 'core sysext',
		'cshmanual'             : 'cshmanual sysext',
		'css_styled_content'    : 'css_styled_content sysext',
		'dbal'                  : 'dbal sysext',
		'documentation'         : 'documentation sysext',
		'extbase'               : 'extbase sysext',
		'extensionmanager'      : 'extensionmanager sysext',
		'extra_page_cm_options' : 'extra_page_cm_options sysext',
		'feedit'                : 'feedit sysext',
		'felogin'               : 'felogin sysext',
		'filelist'              : 'filelist sysext',
		'filemetadata'          : 'filemetadata sysext',
		'fluid'                 : 'fluid sysext',
		'form'                  : 'form sysext',
		'frontend'              : 'frontend sysext',
		'func'                  : 'func sysext',
		'func_wizards'          : 'func_wizards sysext',
		'impexp'                : 'impexp sysext',
		'indexed_search'        : 'indexed_search sysext',
		'indexed_search_mysql'  : 'indexed_search_mysql sysext',
		'info'                  : 'info sysext',
		'info_pagetsconfig'     : 'info_pagetsconfig sysext',
		'install'               : 'install sysext',
		'lang'                  : 'lang sysext',
		'linkvalidator'         : 'linkvalidator sysext',
		'lowlevel'              : 'lowlevel sysext',
		'opendocs'              : 'opendocs sysext',
		'openid'                : 'openid sysext',
		'perm'                  : 'perm sysext',
		'recordlist'            : 'recordlist sysext',
		'recycler'              : 'recycler sysext',
		'reports'               : 'reports sysext',
		'rsaauth'               : 'rsaauth sysext',
		'rtehtmlarea'           : 'rtehtmlarea sysext',
		'saltedpasswords'       : 'saltedpasswords sysext',
		'scheduler'             : 'scheduler sysext',
		'setup'                 : 'setup sysext',
		'sv'                    : 'sv sysext',
		'sys_action'            : 'sys_action sysext',
		'sys_note'              : 'sys_note sysext',
		't3editor'              : 't3editor sysext',
		't3skin'                : 't3skin sysext',
		'taskcenter'            : 'taskcenter sysext',
		'tstemplate'            : 'tstemplate sysext',
		'version'               : 'version sysext',
		'viewpage'              : 'viewpage sysext',
		'wizard_crpages'        : 'wizard_crpages sysext',
		'wizard_sortpages'      : 'wizard_sortpages sysext',
		'workspaces'            : 'workspaces sysext',
	}

class T3Update( object ):
	__version__ = '1.0.0'
	SLOGAN = 'update ALL the exts!'

	def __init__( self, args ):
		self.log = logging.getLogger( self.__class__.__name__ )
		self.log.debug( 'begin' )
		self.my_time = datetime.datetime.now()
		self.args = args
		ctx = ssl.create_default_context()
		if args[ 'no_check_certificate' ]:
			self.log.debug( 'disabling https certificate check...' )
			ctx.check_hostname = False
			ctx.verify_mode = ssl.CERT_NONE
		http_handler = urllib2.HTTPHandler()
		https_handler = urllib2.HTTPSHandler( context = ctx )
		self.ua = urllib2.build_opener( http_handler, https_handler )
		self.ua.addheaders = [ ( 'User-Agent', config.UA ) ]

	def get_mirrors( self ):
		self.log.debug( 'begin' )
		self.log.info( 'downloading list of TER mirrors ...' )
		try:
			req = urllib2.Request( config.host[ 'mirrors' ] )
			res = self.ua.open( req )
		except ( urllib2.HTTPError, urllib2.URLError ) as e:
			self.log.warning( 'error while downloading list of mirrors: %s' % e )
			return None
		else:
			body = res.read()
			mirrors_xml = gzip.GzipFile( 'mirrors.xml.gz', mode = 'rb', fileobj = StringIO.StringIO( body ) ).read()
			mirrors = ET.fromstring( mirrors_xml )
			return mirrors

	def get_ext_file( self, mirrors ):
		self.log.debug( 'begin' )
		all_mirrors = mirrors.findall( 'mirror' )
		mirror = random.choice( all_mirrors )
		ter_host = mirror.find( 'host' )
		ter_path = mirror.find( 'path' )
		ter_title = mirror.find( 'title' )
		if ter_title is None:
			ter_title = 'NO NAME'
		if ter_host is None or ter_path is None:
			self.log.warning( 'invalid mirror entry' )
			return 2
		ter_host = ter_host.text
		ter_path = ter_path.text
		if type( ter_title ) != str:
			ter_title = ter_title.text
		url = 'http://%s%s%s' % ( ter_host, ter_path, config.EXTGZFILE )
		self.log.info( 'downloading %s from mirror "%s" ...' % ( config.EXTGZFILE, ter_title ) )
		self.log.debug( 'mirror url: %s' % url )
		try:
			req = urllib2.Request( url )
			res = self.ua.open( req )
		except ( urllib2.HTTPError, urllib2.URLError ) as e:
			self.log.warning( 'error while downloading list of extensions: %s' % e )
			return 3
		else:
			body = res.read()
			self.log.info( 'unpacking %s to %s ...' % ( config.EXTGZFILE, config.EXTXMLFILE ) )
			open( config.EXTXMLFILE, 'wb' ).write( gzip.GzipFile( config.EXTGZFILE, mode = 'rb', fileobj = StringIO.StringIO( body ) ).read() )
			self.log.info( '%s unpacked.' % config.EXTXMLFILE )
		return 0

	def launch( self ):
		self.log.debug( 'begin' )
		mirrors = self.get_mirrors()
		if mirrors is None:
			self.log.warning( 'no TER mirrors found.' )
			return 1
		ret = self.get_ext_file( mirrors )
		if ret != 0:
			self.log.warning( 'error downloading %s' % config.EXTXMLFILE )
		else:
			self.log.info( '%s successfully updated.' % config.EXTXMLFILE )
		return ret

class T3Num( object ):
	__version__ = '1.0.0'
	SLOGAN = 'enum ALL the exts!'

	def __init__( self, args ):
		self.log = logging.getLogger( self.__class__.__name__ )
		self.log.debug( 'begin' )
		self.my_time = datetime.datetime.now()
		self.args = args
		ctx = ssl.create_default_context()
		if args[ 'no_check_certificate' ]:
			self.log.debug( 'disabling https certificate check...' )
			ctx.check_hostname = False
			ctx.verify_mode = ssl.CERT_NONE
		http_handler = urllib2.HTTPHandler()
		https_handler = urllib2.HTTPSHandler( context = ctx )
		self.ua = urllib2.build_opener( http_handler, https_handler )
		self.ua.addheaders = [ ( 'User-Agent', config.UA ) ]
		self.ext_found = 0
		self.ext_xml = None
		self.results = ''
		self.target_base = args[ 'target' ]
		if not self.target_base.endswith( '/' ):
			self.target_base += '/'
		self.http_method = lambda: 'HEAD'
		if args[ 'use_get' ]:
			self.http_method = lambda: 'GET'

	def is_typo3( self ):
		self.log.debug( 'begin' )
		url = '%s%s' % ( self.target_base, config.T3HINT )
		self.log.info( 'trying to access %s ...' % url )
		req = urllib2.Request( url )
		req.get_method = self.http_method
		try:
			res = self.ua.open( req )
		except urllib2.HTTPError as e:
			if e.code != 404:
				self.log.debug( 'unusual error: %s' % e )
			return False
		else:
			if res.getcode() != 200:
				self.log.warning( 'unusual http response: %s' % res.getcode() )
				return False
			if res.geturl() != url:
				self.log.warning( 'request got redirected to %s' % res.geturl() )
				return False
			return True

	def check_inst_tool( self ):
		self.log.debug( 'begin' )
		self.log.info( 'checking whether the install tool is present...' )
		for tool in ( 'oldinstall', 'newinstall' ):
			url = '%s%s' % ( self.target_base, config.host[ tool ] )
			req = urllib2.Request( url )
			req.get_method = self.http_method
			try:
				res = self.ua.open( req )
			except urllib2.HTTPError as e:
				if e.code == 401 or e.code == 403:
					self.log.info( 'install tool %s locked with code %s' % ( url, e.code ) )
					self.results += 'install tool     : %s locked with code %s\n' % ( url, e.code )
				elif e.code == 404:
					self.results += 'install tool     : %s not found\n' % ( url )
				else:
					self.log.debug( 'unusual error: %s' % e )
					self.results += 'install tool     : %s produced unusual error %s\n' % ( url, e.code )
			else:
				if res.getcode() != 200:
					self.log.warning( 'unusual http response: %s' % res.getcode() )
					self.results += 'install tool     : %s with unusual code %s\n' % ( url, res.getcode() )
				elif res.geturl() != url:
					self.log.warning( 'request got redirected to %s' % res.geturl() )
					self.results += 'install tool     : %s redirected to %s\n' % ( url, res.geturl() )
				else:
					self.log.info( 'install tool found at %s' % res.geturl() )
					self.results += 'install tool     : %s\n' % url
		self.results += '\n'

	def load_ext_xml( self ):
		self.log.debug( 'begin' )
		self.log.info( 'loading %s, this may take a while...' % config.EXTXMLFILE )
		self.ext_xml = ET.parse( config.EXTXMLFILE )
		self.log.info( '%s loaded.' % config.EXTXMLFILE )

	def get_infopage( self, ext_base, ext_key, page, url, code ):
		self.log.debug( 'begin' )
		info_page = {
			'path' : '%s%s/%s' % ( ext_base, ext_key, page[ 'file' ] ),
			'desc' : page[ 'desc' ],
			'first': None,
			'code' : code,
		}
		if page[ 'down' ] and page[ 'first' ]:
			req = urllib2.Request( url )
			body = ''
			try:
				res = self.ua.open( req )
				body = res.read()
			except urllib2.HTTPError as e:
				if e.code == 401 or e.code == 403:
					info_page[ 'first' ] = '%s locked with HTTP code %s' % ( url, e.code )
			else:
				body = config.matchers[ 'chomp' ].sub( '', body )
				first = body.split( '\n' )[ 0 ].strip()
				info_page[ 'first' ] = first
		return info_page

	def ext_details( self, ext_base, ext_key, in_sysext ):
		self.log.debug( 'begin' )
		self.log.info( 'enumerating extension "%s" ...' % ext_key )
		ext_details = {
			'key'      : ext_key,
			'path'     : '%s%s' % ( ext_base, ext_key ),
			'infopages': [
			],
		}
		for page in config.infopages:
			url = '%s%s%s/%s' % ( self.target_base, ext_base, ext_key, page[ 'file' ] )
			req = urllib2.Request( url )
			req.get_method = self.http_method
			try:
				res = self.ua.open( req )
			except urllib2.HTTPError as e:
				if e.code == 401 or e.code == 403:
					info_page = self.get_infopage( ext_base, ext_key, page, url, e.code )
					ext_details[ 'infopages' ].append( info_page )
				elif e.code != 404:
					self.log.debug( 'unusual error: %s' % e )
			else:
				info_page = self.get_infopage( ext_base, ext_key, page, url, res.getcode() )
				ext_details[ 'infopages' ].append( info_page )
		txt = '-----\nextension key    : %s\nextension path   : %s\n' % ( ext_details[ 'key' ], ext_details[ 'path' ] )
		if len( ext_details[ 'infopages' ] ) > 0:
			txt += 'info pages       : %s\n' % len( ext_details[ 'infopages' ]  )
			for infopage in ext_details[ 'infopages' ]:
				txt += '\t%s : "%s" (HTTP CODE %s)\n' % ( infopage[ 'path' ], infopage[ 'desc'], infopage[ 'code' ] )
				if infopage[ 'first' ] is not None:
					txt += '\t\t"%s"\n\n' % infopage[ 'first' ]
		txt += '-----\n\n'
		self.results += txt

	def get_ext( self, url, ext_base, ext_key, in_sysext ):
		#self.log.debug( 'begin' )
		req = urllib2.Request( url )
		req.get_method = self.http_method
		try:
			res = self.ua.open( req )
		except urllib2.HTTPError as e:
			if e.code == 401 or e.code == 403:
				self.log.info( 'extension path %s locked with code %s' % ( url, e.code ) )
				self.ext_found += 1
				self.log.info( 'FOUND: %s%s' % ( ext_base, ext_key ) )
				if not in_sysext and ext_key in config.sysexts:
					del( config.sysexts[ ext_key ] )
				self.ext_details( ext_base, ext_key, in_sysext )
			elif e.code != 404:
				self.log.debug( 'unusual error: %s' % e )
		else:
			self.ext_found += 1
			self.log.info( 'FOUND: %s%s' % ( ext_base, ext_key ) )
			if not in_sysext and ext_key in config.sysexts:
				del( config.sysexts[ ext_key ] )
			self.ext_details( ext_base, ext_key, in_sysext )

	def enum_ext( self ):
		self.log.debug( 'begin' )
		ext_base = config.ext_types[ 'ext' ][ 'path' ]
		ext_desc = config.ext_types[ 'ext' ][ 'desc' ]
		if args[ 'sysext' ]:
			ext_base = config.ext_types[ 'sys' ][ 'path' ]
			ext_desc = config.ext_types[ 'sys' ][ 'desc' ]
		self.log.info( 'starting enumeration of %s (%s)' % ( self.target_base, ext_desc ) )

		ext_cnt = 0
		for ext in self.ext_xml.iter( 'extension' ):
			ext_key = ext.get( 'extensionkey' )
			if ext_key is None:
				continue
			if ext_cnt % config.STEPS == 0:
				self.log.info( '%s extensions tested. next up: %s' % ( str( ext_cnt ).zfill( 5 ), ext_key ) )
			ext_cnt += 1
			url = '%s%s%s%s' % ( self.target_base, ext_base, ext_key, config.EXTHINT )
			self.get_ext( url, ext_base, ext_key, False )
		if not args[ 'sysext' ] or len( config.sysexts ) == 0:
			self.results += 'extensions found : %s\n' % self.ext_found
			return
		for ext_key in config.sysexts:
			ext_desc = config.sysexts[ ext_key ]
			if ext_cnt % config.STEPS == 0:
				self.log.info( '%s extensions tested. next up: %s' % ( str( ext_cnt ).zfill( 5 ), ext_key ) )
			ext_cnt += 1
			url = '%s%s%s%s' % ( self.target_base, ext_base, ext_key, config.EXTHINT )
			self.get_ext( url, ext_base, ext_key, True )
		self.results += 'extensions found : %s\n' % self.ext_found

	def write_results( self ):
		self.log.debug( 'begin' )
		self.log.info( 'writing results to %s' % self.args[ 'output' ] )
		open( self.args[ 'output' ], 'wb' ).write( self.results )

	def launch( self ):
		self.log.debug( 'begin' )
		if not os.path.isfile( config.EXTXMLFILE ):
			self.log.warning( '"%s" is not a file. does it even exist? maybe try %s --update' % ( config.EXTXMLFILE, sys.argv[ 0 ] ) )
			return 1
		if not ( self.is_typo3() or self.args[ 'force' ] ):
			self.log.warning( 'can not access %s%s . is this a Typo3 installation? use --force to continue anyways.' % ( self.target_base, config.T3HINT ) )
			return 2
		self.results = 'Typo3 extension enumeration started at %s\n\nbase target url  : %s\nhttp method      : %s\nextension type   : %s\n\n' % (
			self.my_time.strftime( config.TIMESTR ), self.target_base,
			'GET' if self.args[ 'use_get' ] else 'HEAD',
			config.ext_types[ 'sys' ][ 'desc' ] if self.args[ 'sysext' ] else config.ext_types[ 'ext' ][ 'desc' ],
		)
		self.check_inst_tool()
		self.load_ext_xml()
		self.enum_ext()
		self.write_results()
		ret = 0
		return ret

def banner( cls ):
	txt = '%s v%s - "%s" (c) 2014 Rene Mathes\n' % ( os.path.basename( __file__ ), cls.__version__, cls.SLOGAN )
	print txt

if __name__ == '__main__':
	import argparse
	logging.basicConfig( level = config.LOGLEVEL, format = config.LOGFORMAT )
	banner( T3Num )

	argp = argparse.ArgumentParser()
	arg_target = argp.add_argument_group( 'target', 'target options' )
	arg_target.add_argument( '--target', '--url', '-t', required = False, help = 'base url of the Typo3 site' )
	arg_target.add_argument( '--force', '-f', required = False, help = 'force enumeration even when %s can not be accessed' % config.T3HINT, action = 'store_true' )
	arg_output = argp.add_argument_group( 'output', 'output selection' )
	arg_output.add_argument( '--output', '-o', required = False, help = 'output file for enumeration results' )
	arg_ext = argp.add_argument_group( 'extension', 'extension type' )
	arg_ext.add_argument( '--sysext', '-s', required = False, help = 'enumerate sysext (default: ext)', action = 'store_true' )
	arg_upd = argp.add_argument_group( 'update', 'update extensions.xml' )
	arg_upd.add_argument( '--update', '-u', required = False, help = 'update extensions.xml from TER mirror', action = 'store_true' )
	arg_req = argp.add_argument_group( 'requests', 'request handling' )
	arg_req.add_argument( '--use-get', '-g', required = False, help = 'use GET instead of HEAD requests', action = 'store_true' )
	arg_req.add_argument( '--no-check-certificate', required = False, help = 'do not check SSL/TLS certificates', action = 'store_true' )
	args = vars( argp.parse_args() )

	if args.get( 'update', False ):
		print 'launching T3Update ...'
		t3 = T3Update( args )
		ret = t3.launch()
		if ret != 0:
			print 'update failed, aborting'
			sys.exit( ret )
		print ''

	if args.get( 'target', None ) is not None and args.get( 'output', None ) is not None:
		print 'launching T3Num ...'
		t3 = T3Num( args )
		sys.exit( t3.launch() )
	else:
		if args.get( 'target', None ) is None:
			print 'no scan target given.'
		if args.get( 'output', None ) is None:
			print 'no output file given.'
		sys.exit( -1 )
