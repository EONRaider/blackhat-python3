# Python 3 "Black Hat Python" Source Code

## Description
Source code for the book "Black Hat Python" by Justin Seitz (No Starch Press). The code has been fully converted to Python 3 and reformatted to comply with PEP8 standards.

Although many optimizations could have been implemented in the source code
 presented
throughout the book, the code was left unaltered as much as possible so that
such implementations can be applied by the reader as he sees fit. The code as
it is needs some serious refactoring efforts ranging from docstrings to type
hinting and exception handling, not to mention enhancements like context
 managers, but these issues by themselves may come to benefit the reader if 
 he has the intention of implementing them. It also presents many bugs
 originating from indentation that have been corrected if fatal errors were 
 to be avoided during runtime.

## Usage
Simply make a new directory (DIR) for the project, create a new
 virtual environment or "venv" for it (recommended), clone this repository
  using *git clone* and install the requirements using *pip install*.

```
user@host:~$ mkdir DIR
user@host:~$ cd DIR
user@host:~/DIR$ python3 -m venv venv
user@host:~/DIR$ source venv/bin/activate
(venv) user@host:~/DIR$ git clone https://github.com/EONRaider/blackhat-python3
(venv) user@host:~/DIR$ pip install -r requirements.txt
```

## Notes
- Some listings presented on the book were missing from the author's code
 repository available from "no starch press" website and were
added to their respective chapters. A more accurate naming convention has
been applied to the files as necessary in order to relate them to the code
presented in the book.
- Minor bugs that generated warnings by the interpreter have been fixed
 throughout the code without altering its characteristics.
- Auxiliary files that were required to make the code work were added to their 
respective chapters.
- As a personal side-note, it could have been possible for the author
 to have written cleaner code without jeopardizing the quickness of
  implementation that is required for ethical hacking engagements. Why he
   opted for not doing so remains of unknown reason.

## Troubleshooting

Critical bug fixes that had to be made in order to properly implement the
 source code and avoid fatal errors:
- **chapter02/bh_sshserver.py** required the RSA key contained in "test_rsa.key
" file, now included in the corresponding directory.
- **chapter03/sniffer_ip_header_decode.py** had serious problems in the
 definition of IP packet sizes and portability between 32/64-bit systems due
  to problems in the implementation of structs. More about these issues on 
  [this thread on Stack Overflow.](https://stackoverflow.com/questions/29306747/python-sniffing-from-black-hat-python-book#29307402)