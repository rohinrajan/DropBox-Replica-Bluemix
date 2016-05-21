import os
import json
import keystoneclient.v3 as keystoneclient
import swiftclient.client as swiftclient
import urllib3
import gnupg
import sys
import os
import time
import logging
import mimetypes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
try:
  from SimpleHTTPServer import SimpleHTTPRequestHandler as Handler
  from SocketServer import TCPServer as Server
except ImportError:
  from http.server import SimpleHTTPRequestHandler as Handler
  from http.server import HTTPServer as Server

encryptfilename = 'Sample1encrypt'
decryptfilename = 'decryptfile'
Passphrase = 'CloudComputing'
project_id = '9c7ea377c9bf4a169c1314c94089f107'
user_id = '95e540fdc54c4615a792b346db5f9a05'
region_name = 'dallas'
password = 'lDO(MIW^A4PX3F&f'
auth_url = 'https://identity.open.softlayer.com' + '/v3'
user = 'admin_fb607fac-61f1-4616-82bc-727d5cfb674d_ee7059e5fe24'
container_name= 'cont1'

# Get a Swift client connection object
conn = swiftclient.Connection(
              user = user,
              key=password,
              authurl=auth_url,
              auth_version='3',
              os_options={"project_id": project_id,
                           "user_id": user_id,
                           "region_name": region_name})

#Class Implemented to check to see if new files are present in uploads folder
class FileCreateEventHandler(FileSystemEventHandler):
    def __init__(self, observer):
        self.observer = observer

    def on_created(self, event):
        if not event.is_directory:
            uploadFile(event.src_path)

#function to start watchdog to check to see if new files are present or not
def startSync():
    path = os.getcwd() + '\\Uploads'
    observer = Observer()
    event_handler = FileCreateEventHandler(observer)
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
  
  
# method to upload a file based on filename
def uploadFile(filename):
      print "Uploading filename=" + filename
      print('Connecting to BlueMix..................')
      print "Connecting to Object Storage in Bluemix"
      print "Creating a new container with container name=" +container_name 
      # create a new container
      conn.put_container(container_name)
      print "Container " + container_name + " created successfully"
      # Openening the file in order to encrypt the file
      file = open(filename,'rb',buffering=-1)      
      print "Opened Successfully"
      print "Will now start encrypting the file"
      gpg = gnupg.GPG(gnupghome= os.path.join("E:","python","Gnupg","gnupg"))
      print "Generating a Key"
      input_data = gpg.gen_key_input(key_type="RSA", key_length=1024,passphrase=Passphrase)
      key = gpg.gen_key(input_data)
      print "Generated a Key successfully"
      print "Encrypting a file...... Please wait"
      fencryptfilename = encryptfilename + get_file_extension(filename)
      status = gpg.encrypt_file(file,None,passphrase=Passphrase, symmetric='AES256', output=fencryptfilename)
      print "Successfull in Encryption with filename:" +fencryptfilename
      print status.ok
      print status.status
      print status.stderr
      file.close()
      afile = open(fencryptfilename, 'rb')
      content = afile.read()
      fcontent_type = get_content_type(filename)
      print "Uploading file to object storage"
      # Put the file into storage
      filename = os.path.basename(filename)
      conn.put_object(container_name,filename,contents=content,content_type=fcontent_type)
      print "Successfully Uploaded with filename=" + filename 
      afile.close()
      # deleting the local copy of the file
      os.remove(fencryptfilename)
      # call startup again
      startup()

               
# method to download and decrypt the file
def download_file():
  print "Decrypting the file"
  filename = raw_input("Enter the filename:")
  obj = conn.get_object(container_name, filename)
  fdecryptfilename = decryptfilename + get_file_extension(filename)
  with open(fdecryptfilename, 'wb') as my_example:
        my_example.write(obj[1])
        
  print "Downloaded successfully"
  print "The file is located in "+ os.getcwd() + '\\' + filename
  
  with open(fdecryptfilename,'rb') as my_obj:
       content = my_obj.read()

  print "Will now start decrypting the file"
  gpg = gnupg.GPG(gnupghome= os.path.join("E:","python","Gnupg","gnupg"))
  status = gpg.decrypt(content,passphrase=Passphrase,output=filename)
  print "Decrypted file downloaded Successfully with filename " + filename
  print status.ok
  # remove the decrypted file
  os.remove(fdecryptfilename)
  # call startup again
  startup()

# get the file extension type based on filename
def get_file_extension(filename):
    return '.' + filename.rsplit('.', 1)[1]

# get the content type of the file which
def get_content_type(filename):
    mimetypes.init(filename)
    extension = get_file_extension(filename)
    return mimetypes.types_map[extension]
    

# startup call method 
def startup():
  print "1. Upload files from uploads folder"
  print "2. Download files to uploads folder"
  print "Any thing else to Exit"
  choice = raw_input("Enter your choice:")
  if choice == '1':
    print "Starting to look for files in Uploads folder"
    startSync()
  elif choice == '2':
    download_file()
  else:
    print "Bye"
    return

if __name__ == '__main__':
    startup()

