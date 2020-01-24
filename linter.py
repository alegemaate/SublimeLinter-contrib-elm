#
# linter.py
# Elm Linter for SublimeLinter3, a code checking framework for Sublime Text 3
#
# Written by Allan Legemaate
# Github: @alegemaate
#
# License: MIT
#

"""This module exports the Elm plugin class."""

import json
import logging
import functools

from SublimeLinter.lint import Linter, util

LOGGER = logging.getLogger('SublimeLinter.plugin.elm')


class Elm(Linter):
    """Provides an interface to elm make linting."""

    cmd = 'elm make --report=json --output=/dev/null ${temp_file}'
    regex = (r'^@type=(?P<type>.*?)@@@'
             r'@line=(?P<line>.*?)@@@'
             r'@col=(?P<col>.*?)@@@'
             r'@message=(?P<message>[\s\S]*?)@@@$')

    multiline = True
    tempfile_suffix = 'elm'
    error_stream = util.STREAM_BOTH
    word_re = None
    defaults = {
        'selector': 'source.elm'
    }

    def run(self, cmd, code):
        """Run elm make command and parse output."""
        cmd_output = super().run(cmd, code)
        json_output = None

        # Parse json output, doesn't exist? We can assume clean output
        try:
            json_output = json.loads(cmd_output)
        except ValueError:
            return None

        # Reduce errors
        errors = json_output['errors']
        LOGGER.warning(functools.reduce(lambda a, b: a + "\n" + self.reduce_errors(b), errors, ""))
        return functools.reduce(lambda a, b: a + "\n" + self.reduce_errors(b), errors, "")

    def reduce_errors(self, json_errors):
        """Reduce array of errors to be sublime friendly."""
        problems = json_errors['problems']
        return functools.reduce(lambda a, b: a + "\n" + self.reduce_problems(b), problems, "")

    def reduce_problems(self, error):
        """Pad string so they will match regex."""
        region = error.get('subregion') or error.get('region')

        column = ''
        highlight = ''
        range_length = region['end']['column'] - region['start']['column']
        if range_length > 0:
            column = str(region['start']['column'])
            highlight = "x" * (region['end']['column'] - region['start']['column'])

        def pad_string(name, value):
            """Pad string so they will match regex."""
            return "@{a}={b}@@@".format(a=name, b=value)

        return "".join([
            pad_string("type", "error"),
            pad_string("line", str(region['start']['line'])),
            pad_string("col", column),
            pad_string("region", highlight),
            pad_string("message", self.reduce_message(error)),
        ])

    def reduce_message(self, json_error):
        """Reduce messages to a single message."""

        def resolve_message(message):
            """

            Resolve a message type to a string, as elm make returns objects
            for formatted strings and plain strings for unformatted ones
            
            """
            return message if isinstance(message, str) else message['string']

        message = functools.reduce(lambda a, b: a + resolve_message(b), json_error['message'], "")
        return "[{a}]\n{b}".format(a=json_error['title'], b=message)
