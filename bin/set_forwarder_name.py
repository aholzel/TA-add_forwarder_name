#!/usr/bin/python
#==============================================================================#
#
#	Auteur		: SMT - Arnold Holzel
#	Description	: Script to add a extra field to all events with the name of the
#		system that the message came from. This is usefull if you have intermediate
#		Splunk forwarders and you want to see via with forwarder the message came in.
#		This also requires an props.conf and an transforms.conf on the indexers to
#		store the field as a metadata field.
#
#==============================================================================#
#	TODO		: 
#	
#
#==============================================================================#
#	Change log	:
#	Date		Name		Version	Description
#	2016-03-03	Arnold		1.0		Initial script.
#
#==============================================================================#
import os, sys, tempfile
# Set some variables
field_name = "splunk_forwarder" # NOTE if you change this field name also change it on the indexer in transforms.conf and on the searchhead in fields.conf
exit_script = "false"
add_default_stanza = "true"
use_forwarder_manager = "true"
tmp_dir = "/tmp"
tmp_file = tmp_dir + "/" + "splunk_temp"
# Get the current directory the script is in
current_dir = sys.path[0]

# Get the app directory (i.e. current dir minus /bin)
app_dir = current_dir[:-3]

# Set the variables for the local inputs file
local_dir = 'local/'
inputs_file = 'inputs.conf'
app_local_dir = app_dir + local_dir
local_inputs = app_local_dir + inputs_file

# find the /etc dir within the current dir path
splunk_home = current_dir.find("/etc/")
splunk_home = current_dir[:splunk_home+1]
etc_dir = splunk_home + "etc/"
bin_dir = splunk_home + "bin/"

# set the system local dir
sys_local_inputs = etc_dir + "system/" + local_dir + inputs_file

# if we use a forwarder manager we cannot write to the app/local dir because after every
# home calling the local dir will be removed... so in that case we write to system/local
# which by default already has an inputs.conf with a default stanza (for the hostname)
# we just need to check if the _meta tag is already there with our field name
if use_forwarder_manager == "true":
  local_inputs = sys_local_inputs
  add_default_stanza = "false"
  
  with open(local_inputs, 'r') as file:
      for line in file:
        if field_name in line:
          exit_script = "true"
else:
  # check if there is already a app local dir. if not create it.
  if not os.path.exists(app_local_dir):
    os.makedirs(app_local_dir)
  # Check if there already is a local inputs file and if it contains the additional field
  if os.path.isfile(local_inputs):
    with open(local_inputs, 'r') as file:
      for line in file:
        if field_name in line:
          exit_script = "true"
        if "[default]" in line:
          add_default_stanza = "false"

if not os.path.isfile(local_inputs) or exit_script == "false":
  # read the system local inputs to find the line current hostname of the system is on
  host = ""
  with open(sys_local_inputs, 'r') as file:
    for line in file:
      if 'host' in line:
        host = line

  # find the hostname (i.e. everthing behind the =)
  hostpos = host.find("=")
  hostpos = hostpos+1
  
  # strip of the spaces
  hostname = host[hostpos:].strip()

  # write the hostname to the local inputs.conf file in the app dir.
  # If there is no default stanza just append everything to the file
  if add_default_stanza == "true":
    writeFile = open(local_inputs, 'a')
    writeFile.write("\n[default]\n")
    writeFile.write("_meta = " + field_name + "::" + hostname + "\n")
    writeFile.close()
  
  # If there is already a default stanza make sure the additional line is added below that stanza.
  if add_default_stanza == "false":
    temp = open(tmp_file, "w")
    with open(local_inputs, "r") as f:
      for line in f:
        if line.startswith("[default]"):
          line = line.strip() + "\n_meta = " + field_name + "::" + hostname + "\n"
        temp.write(line)
    temp.close()
    os.rename(tmp_file, local_inputs)
    restart_splunk = bin_dir + "splunk restart"
    os.system(restart_splunk)
