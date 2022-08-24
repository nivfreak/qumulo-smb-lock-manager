#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""SMB file lock manager for Qumulo clusters"""
import argparse
import os
import sys
import argcomplete

import qumulo.lib.auth as qauth
import qumulo.lib.request as qrequest
import qumulo.rest.auth as qrestauth
import qumulo.rest.dns as qrestdns
import qumulo.rest.fs as qrestfs
import qumulo.rest.smb as qrestsmb

class QumuloConnections(object):
    """API Connection Object"""
    def __init__(self, args=None):

        self.port = args.port
        self.user = args.user
        self.passwd = args.passwd
        self.host = args.host

        self.credentials = qauth.get_credentials(\
            qauth.credential_store_filename())
        self.conninfo = qrequest.Connection(self.host, int(self.port),
            self.credentials)
        self.login()

    def login(self):
        """Login with either stored credentials, or username and password"""
        try:
            qrestauth.who_am_i(self.conninfo, self.credentials)
        except (qrequest.RequestError, ConnectionRefusedError):
            try:
                login_results, _ = qrestauth.login(\
                    self.conninfo, None, self.user, self.passwd)
                self.conninfo.credentials = qauth.Credentials.from_login_response(\
                    login_results)
            except (qrequest.RequestError, ConnectionRefusedError) as excpt:
                print("Error connecting to api at %s:%s\n%s" % (self.host,
                                                                self.port,
                                                                excpt))
                sys.exit(1)

    def get_file_handles(self):
        """Get all locked SMB file handles"""
        file_handles = {}
        for locks in qrestsmb.list_file_handles(self.conninfo, self.credentials,
                                                resolve_paths=True).__next__():
            if locks:
                file_handles.update(locks)

        file_handles = file_handles['file_handles']

        # Add a human readable identity
        for lock in file_handles:
                authid = lock['handle_info']['owner']
                username = self.resolve_identities(authid)
                lock['handle_info']['owner_name'] = username

        actionable_file_handles = []
        # XXX This may need to be handled differently at scale, one single API
        # request is likely better.
        for lock in file_handles:
            file = lock['handle_info']
            ip, hostname = self.get_lock_hosts(file['path'])
            # Exclude locks that don't have an associated ip address, these are
            #    typically shared(?) read locks on directories.
            if ip is None:
                next
            else:
                file['ip'] = ip
                file['hostname'] = hostname
                actionable_file_handles.append(file)
        return actionable_file_handles

    def close_location(self, location):
        """Close a single file handle by location id"""
        qrestsmb.close_smb_file(self.conninfo, self.credentials, location)


    def resolve_identities(self, owner):
        """Resolve the auth_id to a human readable name"""
        return qrestauth.find_identity(self.conninfo, self.credentials,
                                              auth_id=owner).data['name']


    def get_lock_hosts(self, path):
        """Enumerate a list of clients that have a lock on path"""
        fslocks = qrestfs.list_locks_by_file(self.conninfo, self.credentials,
                    protocol='smb', lock_type='share-mode', file_path=path)

        ips = []
        for fslock in fslocks.data['grants']:
            ips.append(fslock['owner_address'])

        dns = qrestdns.resolve_ips_to_names(self.conninfo, self.credentials, ips)

        all_hosts=list((sub['hostname'] for sub in dns.data if sub['result'] == 'OK'))

        # XXX We should probably handle multiple DNS names, but multiple IPs? Cheat for now...
        if len(ips) >= 1 and len(all_hosts) >= 1:
            return [ips[0], all_hosts[0]]
        else:
            return None, None

def print_fhs(file_handles):
    """Prints a list of file handles, but you can do better than this!"""
    # Print a header
    print("{:<2} {:<20} {:<20} {:<20} {:<30} {:<100}".format(\
            "#", "Location", "User", "IP", "Hostname", "Path"))

    # Display our enriched information on locked file handles
    for num, lock in enumerate(file_handles):
        print("{num:<2} {location:<20} {owner_name:<20} {ip:<20} {hostname:<30}"
              "{path:<100}".format(num=num, **lock))

def interactive_unlock():
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

    # Get user and file information for locked file handles
    file_handles = qapi.get_file_handles()

    # Try to print the file handles in some useful format
    print_fhs(file_handles)

    if not args.noninteractive:
        lock_to_destroy = int(input("What # do you want to close? "))

        # If a valid option was chosen, close the file handle lock.
        if lock_to_destroy < len(file_handles):
            location_to_destroy = file_handles[lock_to_destroy]['location']
            qapi.close_location(location_to_destroy)
        else:
            print("Invalid number")


# Main
if __name__ == '__main__':
    interactive_unlock()
