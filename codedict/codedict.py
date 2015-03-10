""" 
Let's you compile and access your own personal dictionary 
for programming via the command line with ease.

Usage:
  codedict -d LANGUAGE [USAGE] [-e --cut --hline]
  codedict -a 
  codedict -f LANGUAGE PATH-TO-FILE  
  codedict -c LANGUAGE USAGE
  codedict --editor EDITOR
  codedict LANGUAGE --suffix SUFFIX
  codedict --version  
  codedict (-h | --help)

Options:

  -d          Displays content from codedict.
  -a          Adds content to codedict.
  -c          Display and add code (examples).
  -f          Load content from file into codedict.
  
  -e          Displays every value.

  --editor    Sets your editor to the specified value. This has to be an executable.
  --suffix    Sets the specified suffix for the language. This is convenient for
              syntax highlighting inside editors.  
  --cut       Cutting search phrase from the output's usage. 
  --hline     Prints a horizontal line between each row of the output table. 

  --help      Show this screen.  
  --version   Show version.

"""

#relative import
from docopt import docopt 
import processor 

if __name__ == '__main__':

    COMMAND_LINE_ARGS = docopt(__doc__, version="codedict v 0.4")

    try:
        processor.start_process(COMMAND_LINE_ARGS)
    except KeyboardInterrupt:
        print "\nAborted!"
