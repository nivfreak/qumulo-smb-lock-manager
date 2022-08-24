
SMB Lock manager for Qumulo Clusters 

Summary
-------------------------
This project will:

    * Require a Qumulo cluster running 3.0.4 or higher. Recently tested on 5.2.0.

    * Provide a list of SMB file locks across an entire qumulo cluster by
        communicating with a single node. 
    
    * Close a specific SMB file lock by location id. There may be several
        per file/user.

It will NOT currently:

    * Close all locks held on a file or directory
    
    * Close all locks held by a username
    
    * Close the user session a lock is associate with. This means the original
        user may not be aware they have lost the lock, and you will fall back
        to using a social lock (tell your user!)


API User
--------------------------

The API user used to connect to the Qumulo cluster must be granted a role with at least the following rights:
`PRIVILEGE_SMB_FILE_HANDLE_READ`, `PRIVILEGE_SMB_FILE_HANDLE_WRITE`, `PRIVILEGE_IDENTITY_READ`, `PRIVILEGE_ANALYTICS_READ`, `PRIVILEGE_ANALYTICS_READ`, and `PRIVILEGE_ANALYTICS_READ`.

As a best practice, use an account with only this Role.

If you wish to use an admin account to create this role from the CLI, do so like this:

```
$ qq auth_create_role -r SMB-lock-manager --description "Manage SMB file locks"
$ qq auth_modify_role -r SMB-lock-manager -G PRIVILEGE_SMB_FILE_HANDLE_READ PRIVILEGE_SMB_FILE_HANDLE_WRITE PRIVILEGE_IDENTITY_READ PRIVILEGE_ANALYTICS_READ PRIVILEGE_FS_LOCK_READ PRIVILEGE_DNS_USE
```

In recent version of Qumulo Core, these roles may be defined in the WebUI under the Role Managment section.

Authentication
--------------------------

There are three ways this script can authenticate with a cluster. They will be
tried in the following order:

1) Credential reuse from the qumulo_api cli. You can use 'qq login' to create
    a credential file. This provides interactive password entry, which is
    the most secure method.
2) Passed as parameters to the script itself using --host, --port, --user, and
    --password.
3) Specified by the environmental variables API_HOSTNAME, API_PORT, API_USER, and
    API_PASSWORD. This would be most useful for non-interactive usage.


Python Virtual Environment
--------------------------

It's a good idea to use a virtual environment to run your scripts in. For a
quick start, try:

```
qumulo-smb-lock-manager$ virtualenv ~/qumulo_api
qumulo-smb-lock-manager$ source ~/qumulo_api/bin/activate
(qumulo_api) qumulo-smb-lock-manager$ pip install -r requirements.txt 
(qumulo_api) qumulo-smb-lock-manager$ qq --host your.cluster.company.com login -u lockadmin
(qumulo_api) qumulo-smb-lock-manager$ ./smb_lock_manager.py --host your.cluster.company.com
```

To exit your virtual environment, you can run `deactivate`.

If desired, you can replace the first line of smb_lock_manager.py with the
path to this virtualenv python, eg.:
`#!/home/user/qumulo_api/bin/python`


Standalone Executable Package
--------------------------

Want something even simpler? If your system has python2, pip, and python3,
you can run `./build_binary.sh` to produce a standalone package you can
distribute.

