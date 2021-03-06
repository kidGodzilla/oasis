#!/usr/bin/python
import os.path
from subprocess import call
from subprocess import check_output
import yaml
import readline
import getpass
import sys
import getopt
import shutil

def rlinput(prompt, prefill=''):
  readline.set_startup_hook(lambda: readline.insert_text(prefill))
  try:
    return raw_input(prompt)
  finally:
    readline.set_startup_hook()

def generate_password():
  return check_output(["openssl", "rand", "-base64", "20"]).strip()

def update():
  oldencryptedfilename = "./files/vault.encrypted"
  encryptedfilename = "./group_vars/all/vault.yml"

  if not os.path.isfile(encryptedfilename) and os.path.isfile(oldencryptedfilename):
    print "Copying old vault location to new"
    shutil.copy(oldencryptedfilename, encryptedfilename)

def setup():
  encryptedfilename = "./group_vars/all/vault.yml"
  decryptedfilename = "./group_vars/vault.decrypted"
  configuration = {}
  newconfiguration = {}

  if os.path.isfile(encryptedfilename):
    print "Importing configuration from existing vault"
    call(["ansible-vault", "decrypt", encryptedfilename, "--output="+decryptedfilename])
    stream = open(decryptedfilename)
    configuration = yaml.load(stream)
    os.remove(decryptedfilename)

  newconfiguration["vault_domain"] = rlinput("Please enter your domain: ", configuration.get("vault_domain", None))
  newconfiguration["vault_first_name"] = rlinput("Please enter your first name: ", configuration.get("vault_first_name", None))
  newconfiguration["vault_last_name"] = rlinput("Please enter your last name: ", configuration.get("vault_last_name", None))
  newconfiguration["vault_username"] = rlinput("Please enter username (e.g: user if your desired email address is user@domain.com): ", configuration.get("vault_username", None))
  newconfiguration["vault_aws_access_key"] = rlinput("Please enter your AWS access key: ", configuration.get("vault_aws_access_key", None))
  newconfiguration["vault_aws_secret_key"] = rlinput("Please enter your AWS secret key: ", configuration.get("vault_aws_secret_key", None))
  while True:
    pass1 = getpass.getpass("Please set your password: ") 
    pass2 = getpass.getpass("Please re-enter password: ")
    if pass1 != pass2:
      print "Password's don't match.  Please try again."
    else:
      break

  newconfiguration["vault_password"] = pass1
  

  passwords = ["ldapadminpassword", "caldavduserpassword", "postfixuserpassword"]
  for x in passwords: 
    value = configuration.get("vault_"+x)
    if not value:
      print "Generating " + x + " ..."
      value = generate_password()

    newconfiguration["vault_"+x] = value 

  if not newconfiguration == configuration:
    print "Updating vault with new configuration"
    dir = os.path.dirname(decryptedfilename) 

    try:
      os.stat(dir)
    except:
      os.mkdir(dir)
 
    decrypted = open(decryptedfilename, "w")
    decrypted.truncate()
    decrypted.write(yaml.dump(newconfiguration, default_flow_style=False, explicit_start=True))
    decrypted.close()
    call(["ansible-vault", "encrypt", decryptedfilename, "--output", encryptedfilename])
    os.remove(decryptedfilename)
    print("Vault created in " + encryptedfilename)
  else:
    print("Configuration unchanged.")

def configure():
  call(["ansible-playbook", "-i", "inventory", "site.yml", "--tags", "configuration", "--ask-vault-pass"])

def usage():
  print "usage: ./oasis.py [--setup|--config|--both]"

def main():
  setupopt = False
  configopt = False
  
  args = sys.argv[1:]

  try:
    opts, args = getopt.getopt(args, "scbh", ["setup", "config", "both", "help"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts: 
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    if opt in ("-s", "--setup"):
      setupopt = True
    if opt in ("-c", "--config"):
      configopt = True
    if opt in ("-b", "--both"):
      configopt = True
      setupopt = True

  update()

  if setupopt:
    setup()
  if configopt:
    configure()


if __name__ == "__main__":
  main()
