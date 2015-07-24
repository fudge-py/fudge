#!/bin/sh

project_name="Fudge"

project_url="https://fudge.readthedocs.org/en/latest/"

# The location of your yuidoc install
yuidoc_home=~/src/yuidoc


# The location of the files to parse.  Parses subdirectories, but will fail if
# there are duplicate file names in these directories.  You can specify multiple
# source trees:
#     parser_in="%HOME/www/yui/src %HOME/www/event/src"

# this is sort of lame (avoid descending into tests directory):
rm -fr _tmp_src
mkdir _tmp_src
cp ./fudge/fudge.js _tmp_src/fudge.js
parser_in="./_tmp_src"

# The location to output the parser data.  This output is a file containing a 
# json string, and copies of the parsed files.
parser_out="./_build/docs"
mkdir -p $parser_out
rm -fr "${parser_out}/*"

# The directory to put the html file outputted by the generator
generator_out=$parser_out

# The location of the template files.  Any subdirectories here will be copied
# verbatim to the destination directory.
template=$yuidoc_home/template

# The version of your project to display within the documentation.
version=0.9.0

# The version of YUI the project is using.  This effects the output for
# YUI configuration attributes.  This should start with '2' or '3'.
yuiversion=2

##############################################################################
# add -s to the end of the line to show items marked private

if [ "$1" = "-h" -o "$1" = "--help" ]; then
    $yuidoc_home/bin/yuidoc.py --help
else
    $yuidoc_home/bin/yuidoc.py $parser_in \
        -p $parser_out \
        -o $generator_out \
        -t $template \
        -v $version \
        -Y $yuiversion \
        -m $project_name \
        -u $project_url
fi

rm -fr _tmp_src
