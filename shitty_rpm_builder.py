#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
###

###
# Set up logging
import logging
from util import color_stream

handler = color_stream.ColorizingStreamHandler()
handler.setFormatter(logging.Formatter(\
"%(asctime)s [%(levelname)5s] %(name)s - %(message)s"))
root = logging.getLogger()
root.addHandler(handler)
root.setLevel(logging.WARN)
logger = logging.getLogger(__name__)
# will apply to all child modules of this package, as well
logger.setLevel(logging.DEBUG)
###

import os, platform, sys, re, shutil, errno
import subprocess
import urllib2
import tarfile
import hashlib
import pytoml as toml

###
# For the record this is terrible...
c_path  = os.getcwd()
config  = c_path+"/"+"util/config.toml"
with open(config, 'rb') as fin: 
  config_obj = toml.load(fin)

###
# turn the toml config values into strings
conf_source_url           = str(config_obj["source"]["url"])
conf_source_chk_sum       = str(config_obj["source"]["chk_sum"])
conf_package_name         = str(config_obj["package"]["name"])
conf_package_version      = str(config_obj["package"]["version"])
conf_package_destination  = str(config_obj["package"]["destination"])
conf_package_summary      = str(config_obj["package"]["summary"])
conf_package_license      = str(config_obj["package"]["license"])


###
# Download the source Tarball
def get_the_damn_tarball(
  url,
  cksum
):
  """
  This will download the source code provided in the url variable in the toml config file util/config.toml
  it will also check that the sha512 hash matches so we don't unpack someething else by accident

  * in the util/config.toml file under the [source] section url needs to be set to your source code
  * in the util/config.toml file under the [source] section chk_sum needs to be set to the sha512 
    hash of the source code above
  * this creates a directory called SRC/ and unpacks the tarball into it
  """
  file_name = url.split('/')[-1]
  my_working_dir = os.getcwd()
  u = urllib2.urlopen(url)
  f = open(my_working_dir+"/"+file_name, 'wb')
  meta = u.info()
  file_size = int(meta.getheaders("Content-Length")[0])
  logger.info("Downloading: %s Bytes: %s", file_name, file_size)

  file_size_dl = 0
  block_sz = 8192
  while True:
    buffer = u.read(block_sz)
    if not buffer:
      break
    file_size_dl += len(buffer)
    f.write(buffer)
    status = r"%10d [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
    status = status + chr(8)*(len(status)+1)
    print status,
  f.close()

  # Check that the file is the file we thought it was with the sha512 chksum
  logger.info('Checking the checksums...')
  myappdir = "SRC" 
  logger.info(myappdir)
  build_dir = my_working_dir+"/"+myappdir
  m = hashlib.sha512()
  m.update(open(file_name,'rb').read())
  ret_str = m.hexdigest()
  if ret_str != conf_source_chk_sum:
    logger.warn("ERROR: The downloaded archive %s does not match the sha512 checksum!", file_name)
    logger.warn("sha512 checksum from %s %s", url, tomcat_chksum)
    logger.critical("local tar archive %s sha512 checksum %s", file_name, ret_str)
    sys.exit()

  logger.info("Extracting tar file: %s"+"/"+"%s", my_working_dir, file_name)
  tar = tarfile.open(file_name)
  tar.extractall(path=build_dir)
  tar.close()

  return build_dir


###
# Here is where you need to compile the source code.
def make_some_shit(
  name,
  build
):
  """
  Run make to compile the source you would like to package.

  * This takes the extracted tar file and runs ./configure make make install
    to make a bianary of your source code.
  """
  logger.info(os.getcwd())
  install_dir = os.getcwd()+"/"+name
  logger.info(os.makedirs(install_dir))
  install_cmds = [
    ["./configure", "--prefix=%s" % install_dir],
    ['make'],
    ['make', 'install']
  ]

  logger.info("starting to compile %s" % name)
  os.chdir(build+"/"+name+"-"+conf_package_version)
  for cmd in install_cmds:
    logger.info(subprocess.check_output(cmd))

  return install_dir


###
# Build the RPM from the Tarball and the install/ directory
def build_rpm(build_dir):
  """
  Build an RPM with FPM from the compiled software you've provided

  * takes the build_dir as an argument
  * this will create an RPM and uses the following variables set in the
    util/config.toml file:
    * [package] name
    * [package] version
    * [package] destination
  """
  assert build_dir is not None, 'The build directory is not set'
  logger.info("the Builder Directory is: %s", build_dir)

  # Run FPM to create the  RPM:
  cmds = [
    ['/usr/local/bin/fpm',
    '-s',
    'dir',
    '-t',
    'rpm',
    '--name', conf_package_name,
    '-v', conf_package_version,
    '--prefix', conf_package_destination,
    build_dir]
  ]

  os.chdir(c_path)
  for cmd in cmds:
    logger.info(cmd)
    logger.info(subprocess.check_output(cmd))


###
# cleanup steps
def cleanup_after():
  """
  Cleanup after the RPM has been built.

  * remove the SRC directory
  * remove the compiled software directory
  * move the rpm into RPMS/
  """
  rpm_dir     = os.getcwd()+"/RPMS/"
  if not os.path.isdir(rpm_dir):
    logger.info(os.makedirs(rpm_dir))

  rpm_file    = conf_package_name+"-"+conf_package_version+'-1.x86_64.rpm'
  source_path = os.getcwd()+"/"+rpm_file
  destination = rpm_dir+rpm_file
  src_dir     = os.getcwd()+"/SRC"
  install_dir = os.getcwd()+"/"+conf_package_name
  logger.info("Moving %s to RPMS" % source_path)
  logger.info(shutil.move(source_path, destination))

  # Check that the rpm is in the preferred directory
  if os.path.exists(destination):
    logger.info("deleting the source directory")
    logger.info(shutil.rmtree(src_dir))
    logger.info("deleting the install directory")
    logger.info(shutil.rmtree(install_dir))
    logger.info("deleting the tar file")
    logger.info(os.remove(os.getcwd()+"/"+conf_package_name+"-"+conf_package_version+".tar.gz"))
  else:
    logger.warn("Could not locate %s rpm file" % destination)
    logger.critical("could not move rpm to RPMS direcotry stopping")
    sys.exit()


###
# Final section Create the RPM:
builder_dir = get_the_damn_tarball(conf_source_url,conf_source_chk_sum)
#make_some_shit(conf_package_name,builder_dir)
build_rpm(make_some_shit(conf_package_name,builder_dir))

###
# Post section to clean up sources and things
cleanup_after()

