# openrepo_cli

The OpenRepo Command Line Interface (CLI) app provides an easy way to integrate OpenRepo with other applications such as Continuous Integration.  For example,
you could use the CLI app to automatically upload a package to a repo when a build completes, or create a new repo when a git repository is created.

## Usage

 - First download the OpenRepo CLI program from the Releases

        sudo wget https://github.com/xxxxxxxxxxxx -O /usr/local/bin/openrepo && sudo chmod +x /usr/local/bin/openrepo

 - Login to your OpenRepo server and navigate to the "User Info" page (/cfg/userinfo/)

 - Copy the CLI instructions which include your API key and server location.  For example:

        export OPENREPO_SERVER=http://repo.mydomain.com
        export OPENREPO_APIKEY=abcdef1234567890abcdef1234567890abcdef12
        openrepo list_repos

- The output should look similar to the following:

        user@computer:/home/user/openrepo/cli$ openrepo list_repos

        ┌──────────────────┬───────────┬───────────────┬─────────────────────────────┐
        │     repo_uid     │ repo_type │ package_count │         last_updated        │
        ├──────────────────┼───────────┼───────────────┼─────────────────────────────┤
        │ acmewidgets-dev  │    deb    │       7       │ 2022-12-01T02:38:48.595892Z │
        │ acmewidgets-prod │    deb    │       6       │ 2022-12-01T02:35:03.617695Z │
        │     qatools      │   files   │       78      │ 2022-12-01T03:43:56.944487Z │
        │   redhat-dist    │    rpm    │       5       │ 2022-12-01T03:44:10.276156Z │
        └──────────────────┴───────────┴───────────────┴─────────────────────────────┘

- Use the --help command to show repository options:


        user@computer:/home/user/openrepo/cli$ openrepo --help
        usage: openrepo [-h] [-k KEY] [-s SERVER] [--debug] [--json]
                        {list_packages,list_repos,list_signingkeys,package_copy,package_delete,package_detail,package_promote,repo_create,repo_delete,repo_details,upload} ...

        OpenRepo Command Line Interface

        positional arguments:
          {list_packages,list_repos,list_signingkeys,package_copy,package_delete,package_detail,package_promote,repo_create,repo_delete,repo_details,upload}
                                Available OpenRepo Operations
            list_packages       List packages in a repository
            list_repos          List all repositories
            list_signingkeys    List all signing keys
            package_copy        Copy a package from one repository to another
            package_delete      Delete a repository
            package_detail      Show detailed information about a package
            package_promote     Promote a package to the repo configured as "promote_to"
            repo_create         Create a new repository
            repo_delete         Delete new repository
            repo_details        Show detailed information about a particular repo
            upload              Upload package file to OpenRepo

        options:
          -h, --help            show this help message and exit
          -k KEY, --key KEY     API key
          -s SERVER, --server SERVER
                                OpenRepo Server
          --debug               Print debug info
          --json                Print output to JSON


        user@computer:/home/user/openrepo/cli$ openrepo package_copy --help
        usage: openrepo package_copy [-h] --src_repo_uid SRC_REPO_UID --src_package_uid SRC_PACKAGE_UID --dst_repo_uid DST_REPO_UID

        options:
          -h, --help            show this help message and exit
          --src_repo_uid SRC_REPO_UID
          --src_package_uid SRC_PACKAGE_UID
          --dst_repo_uid DST_REPO_UID


## Architecture

The OpenRepo CLI uses the OpenRepo REST API to communicate with the server.  The API key is sent in the Authorization header.  

The CLI program is written in Python.  For distribution, we create a standalone x86-64 binary using pyinstaller.

The server URL and API key can be provided either as CLI arguments or environment variables.  The CLI arg will take priority if provided.

The output can be either human-readable tables (default) or machine-readable JSON data.  To send JSON data, use the "--json" argument

the --debug argument logs detailed information about the request/response from the server.