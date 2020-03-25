
SMB Lock manager for Qumulo Clusters 

Summary
-------------------------
This project will:

    * Require a Qumulo cluster running 3.0.3 _only_.

    * Provide a list of SMB file locks across an entire qumulo cluster by
        communicating with a single node. 
    
    * Close a specific SMB file lock by location id. There may be several
        per file/user.

It will NOT currently:

    * Support clusters before or after Qumulo core 3.0.3. The API is currently
      marked as beta, and will change in 3.0.4.

    * Close all locks held on a file or directory
    
    * Close all locks held by a username
    
    * Close the user session a lock is associate with. This means the original
        user may not be aware they have lost the lock, and you will fall back
        to using a social lock (tell your user!)


API User
--------------------------

The API user used to connect to the Qumulo cluster must be granted a minimum
of PRIVILEGE_SMB_FILE_HANDLE_READ, PRIVILEGE_SMB_FILE_HANDLE_WRITE, and 
PRIVILEGE_IDENTITY_READ. As a best practice, use an account with only this Role.

If you wish to use an admin account to create this role, do so like this:

$ qq auth_create_role -r SMB-lock-manager --description "Manage SMB file locks"
$ qq auth_modify_role -r SMB-lock-manager -G PRIVILEGE_SMB_FILE_HANDLE_READ
$ qq auth_modify_role -r SMB-lock-manager -G PRIVILEGE_SMB_FILE_HANDLE_WRITE
$ qq auth_modify_role -r SMB-lock-manager -G PRIVILEGE_IDENTITY_READ

As of 3.0.3, roles must be created using the CLI or API, and then can
privileges and membership may be managed by the WebUI. 


Authentication
--------------------------

There are three ways this script can authenticate with a cluster. They will be
tried in the following order:

1) Credential reuse from the qumulo_api cli. You can use 'qq login' to create
    a credential file. This provides interactive password entry, which is
    the most secure method.
2) Passed as parameters to the script itself using --host, --user, and
    --password.
3) Specified by the environmental variables API_HOSTNAME, API_USER, and
    API_PASSWORD. This would be most useful for non-interactive usage.


Python Virtual Environment
--------------------------

It's a good idea to use a virtual environment to run your scripts in. For a
quick start, try:

qumulo-smb-lock-manager$ virtualenv ~/qumulo_api
qumulo-smb-lock-manager$ source ~/qumulo_api/bin/activate
(qumulo_api) qumulo-smb-lock-manager$ pip install -r requirements.txt 
(qumulo_api) qumulo-smb-lock-manager$ qq --host your.cluster.company.com login -u lockadmin
(qumulo_api) qumulo-smb-lock-manager$ ./close_smb_locks.py --host your.cluster.company.com

To exit your virtual environment, you can run 'deactivate'.

If desired, you can replace the first line of close_smb_locks.py with the
path to this virtualenv python, eg.: #!/home/user/qumulo_api/bin/python

