#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""SMB file lock manager for Qumulo clusters"""
import argparse
import os
from socket import error as socket_error
import sys
import argcomplete


import qumulo.lib.auth as qauth
import qumulo.lib.request as qrequest
import qumulo.rest.auth as qrestauth
import qumulo.rest.fs as qfs
import qumulo.rest.smb as qsmb

class QumuloConnections(object):
    """API Connection Object"""
    def __init__(self, args=None):

        self.port = args.port
        self.user = args.user
        self.passwd = args.passwd
        self.host = args.host

        self.conninfo = qrequest.Connection(self.host, int(self.port))
        #self.credentials = None
        self.credentials = qauth.get_credentials(\
            qauth.credential_store_filename())
        self.login()

    def login(self):
        """Login with either stored credentials, or username and password"""
        try:
            qrestauth.who_am_i(self.conninfo, self.credentials)
        except (qrequest.RequestError, socket_error):
            try:
                login_results, _ = qrestauth.login(\
                    self.conninfo, None, self.user, self.passwd)

                self.credentials = qauth.Credentials.from_login_response(\
                    login_results)
            except (qrequest.RequestError, socket_error), excpt:
                print "Error connecting to api at %s:%s\n%s" % (self.host,
                                                                self.port,
                                                                excpt)
                sys.exit(1)

    def get_file_handles(self):
        """Get all locked SMB file handles"""
        file_handles = {}
        for lock in qsmb.list_file_handles(self.conninfo,
                                           self.credentials).next():
            if lock:
                file_handles.update(lock)
        return file_handles

    def close_location(self, location):
        """Close a single file handle by location id"""
        qsmb.close_smb_file(self.conninfo, self.credentials, location)

    def file_handle_info(self, file_handle):
        """Lookup a full set of file handle information"""
        # get the lock location for the file handle
        location = file_handle.values()[1]['location']
        # Store the access masks eg. MS_ACCESS_FILE_READ_ATTRIBUTES,
        # MS_ACCESS_FILE_WRITE_ATTRIBUTES, MS_ACCESS_SYNCHRONIZE
        access_mask = file_handle.values()[1]['access_mask']
        # Get the auth_id for the lock owner, this is the internal qumulo
        # identiy stored on disk
        owner_auth_id = file_handle.values()[1]['owner']
        # Resolve the auth_id to a human readable name
        owner_entry = qrestauth.find_identity(self.conninfo, self.credentials,
                                              auth_id=owner_auth_id).data
        # Parse the file_id from the lock location field
        file_id = location.split('.')[1]
        # Look up file information for the file_id
        file_entry = qfs.resolve_paths(self.conninfo, self.credentials,
                                       [file_id]).data[0]
        file_entry['owner_name'] = owner_entry['name']
        file_entry['location'] = location
        file_entry['access_mask'] = access_mask
        return file_entry

def print_fhs(file_handles):
    """Prints a list of file handles, but you can do better than this!"""
    # Print a header
    print "{:<2} {:<20} {:<20} {:<100}\n{:>120}".format(\
        "#", "Location", "User", "Path", "Access Mask")

    # Display our enriched information on locked file handles
    for num, lock in enumerate(file_handles):
        print("{num:<2} {location:<20} {owner_name:<20} {path:<100}\n"
              "{access_mask:>120}\n").format(num=num, **lock)

def main():
    """Main"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "--ip", dest="host", required=False,
                        default=os.environ.get('API_HOSTNAME', "localhost"),
                        help="Specify a hostname or ip to reach the API")
    parser.add_argument("-P", "--port", type=int, dest="port", default=8000,
                        required=False,
                        help="Specify API port on cluster; defaults to 8000")
    parser.add_argument("-u", "--user", dest="user", required=False,
                        default=os.environ.get('API_USER', "admin"),
                        help="Specify user name for login; defaults to admin")
    parser.add_argument("-p", "--pass", dest="passwd", required=False,
                        default=os.environ.get('API_PASSWORD', "Admin123"),
                        help="Specify password for login; defaults to Admin123")
    parser.add_argument("-l", "--location", default=False, required=False,
                        dest="location",
                        help="File handle location id to close, eg. 4.676543750958.39903",)
    parser.add_argument("-n", "--non-interactive", default=False,
                        dest="noninteractive", action='store_true',
                        help="Simply print a list of locked file handles.")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    qapi = QumuloConnections(args)

    # If specified, close a file handle by location id
    if args.location:
        qapi.close_location(args.location)
        sys.exit(0)

    # Retreive all locked SMB file handles
    open_smb_files = qapi.get_file_handles()

    # Lookup user and file information for locked file handles
    file_handles = [qapi.file_handle_info(i)
                    for i in open_smb_files['file_handles']]

    # Try to print the file handles in some useful format
    print_fhs(file_handles)

    if not args.noninteractive:
        lock_to_destroy = input("What # do you want to close? ")

        # If a valid option was chosen, close the file handle lock.
        if lock_to_destroy < len(file_handles):
            location_to_destroy = file_handles[lock_to_destroy]['location']
            # Use until smb.close_smb_file is in your qumulo_api package
            qapi.close_location(location_to_destroy)
        else:
            print "Invalid number"


# Main
if __name__ == '__main__':
    main()
