# Building the Documentation
* Ensure all requirements are met in the **requirements.txt** file.
* Using the command line/terminal, `cd` into **docs/**`.
* Perform `make clean`
* Perform `make html`
* With python3 installed, run `python -m http.server 5000` in the **docs/build/html/** directory.
* Go to `localhost:5000` to see the result.

# Seeing changes while editing
Simply use `make html` to update the textual changes and refresh the browser.

Note: To see changes for the toctree, the documents must be generated again. In this instance, one would do as follows:
* `ctrl + c` to stop the http server
* `make clean`
* `make html`
* `python -m http.server 5000` to start the server again

# PyCharm optional but recommended settings
* https://www.jetbrains.com/help/pycharm/documenting-source-code.html
* https://www.jetbrains.com/help/pycharm/restructured-text.html

# Note:
Since Sphinx docs is generating using python3, we are only covering the documentation for the python3 codebase.

# Read the Docs
Default settings will fail when deploying to Read the Docs. This is because the project's requirements are split up into multiple files.

Since we are only deploying documentation (currently) for python3+, I've made a `rtd-requirements.txt` at the root of this project's directory. Read the Docs settings has also been modified to install from the new requirements file. We needed to create this new file because Read the Docs only installs dependencies from **one** file, meanwhile, our dependencies for a python3 installation requires reading from both `requirements.txt` as well as `requirements-py35.txt`.