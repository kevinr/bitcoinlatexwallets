#!/usr/bin/env python

import sys, re, optparse, subprocess, itertools

from mako.template import Template


# based off http://stackoverflow.com/questions/2541616/how-to-escape-strip-special-characters-in-the-latex-document/5422751#5422751
latex_substitutions = {
    "#": "\\#",
    "$": "\\$",
    "%": "\\%",
    "&": "\\&",
    "~": "\\~{}",
    "_": "\\_",
    "^": "\\^{}",
    "\\":"\\textbackslash ",
    "{": "\\{",
    "}": "\\}",
}
latex_re = re.compile("([\^\%~\\\\#\$%&_\{\}])")

def sanitize_latex(s):
    global latex_substitutions, latex_re
    return latex_re.sub(lambda m: latex_substitutions[m.group(1)], s)


def main():
    usage = "Usage: %prog [-n|--number=NUMBER] [-o|--output=FILE]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-n', '--number', 
        help='number of wallets to generate, default 8', 
        default=8,
        metavar='NUMBER')
    parser.add_option('-o', '--output',
        help='file to which to output generated TeX, default STDOUT',
        metavar='FILE')

#    if len(sys.argv) < 2:
#        parser.print_help()
#        sys.exit(1)

    (options, args) = parser.parse_args()

    if not options.output:
        output = sys.stdout
    else:
        output = open(options.output, 'w')

    # another place to force UTF-8
    output.write(render(options.number).encode('utf-8'))

    sys.exit(0)


def render(number, **kwargs):
    """Returns LaTeX document as string."""
    
    address_re = re.compile('^Address: (\w+)$')
    privkey_re = re.compile('^Privkey: (\w+)$')

    vanitygen = subprocess.Popen(("./vanitygen", "-k", ""), bufsize=256, stdout=subprocess.PIPE)

    waiting_for_new_key = True
    keys = []
    for raw_l in vanitygen.stdout:
        if waiting_for_new_key and len(keys) >= number:
            break

        l = unicode(raw_l, 'utf-8')
        if waiting_for_new_key:
            m = address_re.match(l)
            if m:
                waiting_for_new_key = False
                keys.append({'address': m.group(1)})
                continue
        else:

            m = privkey_re.match(l)
            if m:
                keys[-1]['privkey'] = m.group(1)
                waiting_for_new_key = True
                continue

    vanitygen.terminate()

    with open('bitcoin-cards.tex', 'r') as template_f:
        template = template_f.read()

    compiled_template = Template(template)
    return compiled_template.render_unicode(keys = keys)


if __name__ == '__main__': main()
