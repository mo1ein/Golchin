#! /usr/bin/env python3

from sys import argv
from os.path import (isdir, sep, split)
from os import (mkdir, getcwd)
from glob import glob
from codecs import open as codecs_open

from io import StringIO

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter


class PDF2Word:
    MARKS = '!"#$%&()*+,./'
    PDF2WORD_DIR = 'pdf2word'
    BLACKLIST_FILES = [
        'pdf2wordblacklist.txt',
        '/home/pouriya/.config/pdf2wordblacklist.txt'
    ]

    def __init__(
        self,
        paths,
        blacklist_words=[],
        repeat_count=50,
        exclude_repeated=False
    ):
        self.paths = paths
        self.repeat_count = repeat_count
        self.exclude_repeated = exclude_repeated
        self.blacklist_words = blacklist_words
        for filename in self.BLACKLIST_FILES:
            self._may_read_blacklist(filename)
        print_info(
            'have {} word(s) in blacklist files'.format(
                len(self.blacklist_words)
            )
        )

    def _may_read_blacklist(self, filename):
        data = None
        try:
            data = self._read_blacklist_file(filename)
        except FileNotFoundError:
            pass
        except Exception as reason:
            print_error(
                'could not read blackist file {!r}, {}'.format(
                    filename,
                    reason
                )
            )
        if data is not None:
            for part in data.splitlines():
                part = part.lower()
                if part not in self.blacklist_words:
                    self.blacklist_words.append(part)

    def _sort(self, items_dict):
        items = []
        for word, repeat in items_dict.items():
            items.append((word, repeat))

        items.sort(key=lambda tup: tup[1])
        items.reverse()
        last_repeat = 0
        buff = []
        words = []
        for word, repeat in items:
            item = (word, repeat)
            if repeat < last_repeat:
                buff.sort(key=lambda tup: tup[0])
                buff.append(('', 0))
                [words.append(x) for x in buff]
                buff = []
            buff.append(item)
            last_repeat = repeat
        buff.sort(key=lambda tup: tup[0])
        [words.append(x) for x in buff]
        return words

    def _read_blacklist_file(self, filename):
        data = None
        for encoding in ['utf-8', 'iso-8859-15']:
            try:
                fd = open(filename, encoding=encoding)
                data = fd.read()
                fd.close()
            except UnicodeDecodeError:
                pass
        return data

    def _read_file(self, filename):
        data = None
        try:
            fd = open(filename, 'rb')
        except UnicodeDecodeError:
            return data
        outfd = StringIO()
        rsrcmgr = PDFResourceManager()  # caching=True)
        imagewriter = None
        laparams = LAParams()
        laparams.all_texts = True
        device = TextConverter(
            rsrcmgr,
            outfd,
            laparams=laparams,
            imagewriter=imagewriter
        )
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        buff = ''
        try:
            for page in PDFPage.get_pages(
                fd,
                set(),
                caching=True,
                check_extractable=True
            ):
                try:
                    interpreter.process_page(page)
                except Exception as reason:
                    print_error(
                        'could interpret content from {!r}, {}'.format(
                            filename, reason
                        )
                    )
        except Exception as reason:
            print_error(
                'could interpret any content from {!r}, {}'.format(
                    filename, reason
                )
            )
            return data
        fd.close()
        data = outfd.getvalue()
        # print(data)
        return data

    def _find_words(self, fulltext):
        text = ''
        for char in fulltext:
            if char in self.MARKS:
                text += ' '
            else:
                text += char
        parts = text.split(' ')

        words = {}
        words_list = []
        word_count = 0
        duplicates_count = 0
        not_added_count = 0
        blacklist_words = 0
        not_word_count = 0
        for part in parts:
            part = part.lower()
            is_word = True
            for char in part:
                char_int = ord(char)
                if (96 < char_int < 123):
                    continue
                elif char_int == 45:
                    continue
                elif char_int == 39:
                    continue
                is_word = False
                break
            if not is_word:
                not_word_count += 1
                continue
            if part.endswith('\'s') or part.endswith('\'d'):
                part = part[:-2]
            elif part.endswith('\'ve') or \
                    part.endswith('\'ll') or \
                    part.endswith('n\'t') or \
                    part.endswith('\'re') or \
                    part.endswith('in\''):
                part = part[:-3]
            elif part.endswith('\''):
                part = part[:-1]
            elif part.startswith('\''):
                part = part[1:]
            if len(part) < 3:
                not_added_count += 1
                continue
            if part + 'ing' in words_list:
                words_list.remove(part + 'ing')
                words.pop(part + 'ing')
            if part.endswith('ing') and part[:-3] in words_list:
                not_added_count += 1
                continue
            if part + 's' in words_list:
                words_list.remove(part + 's')
                words.pop(part + 's')
            elif part.endswith('s') and part[:-1] in words_list:
                not_added_count += 1
                continue
            if part[0] == '-' or part[-1] == '-':
                not_added_count += 1
                continue
            if part not in self.blacklist_words:
                if part not in words_list:
                    words[part] = 1
                    words_list.append(part)
                    word_count += 1
                else:
                    words[part] += 1
                    duplicates_count += 1
            else:
                blacklist_words += 1

        result = (
            self._sort(words),
            word_count,
            duplicates_count,
            not_added_count,
            blacklist_words,
            not_word_count
        )
        return result

    def _write_pdf2word_file(self, filename, words, count):
        fd = open(
            self.PDF2WORD_DIR + sep + filename.replace('.pdf', '.txt'),
            'w'
        )
        fd.write('Word count: {}\n\n'.format(count))
        word_number = 1
        write_repeat = True
        print_repeated = False
        print_list = []
        for word, repeat in words:
            if self.repeat_count != 0 and repeat > self.repeat_count:
                if not print_repeated:
                    print_repeated = True
                print_list.append(word)
            if word != '':
                if write_repeat:
                    fd.write(str(repeat) + ':\n')
                    write_repeat = False
                fd.write('{:^8} {}'.format(word_number, word))
                word_number += 1
            else:
                write_repeat = True
                word_number = 1
            fd.write('\n')
        if print_list:
            print_info(
                '{} word(s) repeated more than {} times:'.format(
                    len(print_list),
                    self.repeat_count
                ),
                ' '
            )
            print_list.sort()
            [print(x, end=',') for x in print_list]
            print()
        fd.close()
        self._write_html_file(filename, words, count)

    def _write_html_file(self, filename, words, count):
        fd = open(
            self.PDF2WORD_DIR + sep + filename.replace('.pdf', '.html'),
            'w'
        )
        fd.write('''<!DOCTYPE html>
<html>
 <head>
  <title>PDF2Word: {}</title>
 </head>
 <body>'''.format(count))
        word_number = 1
        write_repeat = True
        for word, repeat in words:
            if word != '':
                if write_repeat:
                    fd.write(
                        '  <h5 id="{}" style="text-align:center;font-f'
                        'amily:courier;"><a style="color:black;" href='
                        '"#{}">Repeated {} times</a></h5>\n   <ul styl'
                        'e="text-align:center;list-style-type:none;">\n'
                        .format(repeat, repeat, repeat)
                    )
                    write_repeat = False
                fd.write(
                    '    <li><a href="https://translate.google.com/#vi'
                    'ew=home&op=translate&sl=en&tl=fa&text={}" target='
                    '"_blank" style="color:#678e8b;">{}</a></li>\n'
                    .format(word, word[0].upper() + word[1:])
                )
                word_number += 1
            else:
                write_repeat = True
                word_number = 1
                fd.write('   </ul>\n')
        # if print_repeated:
            # print()
        fd.write('  </ul>\n <body>\n</html>')
        fd.close()

    def _log_statistics(self, words_data, context=None):
        if context is None:
            context = 'Total'
        else:
            context = '{!r}'.format(context)
        (
            words,
            word_count,
            duplicates_count,
            not_added_count,
            blacklist_words,
            not_word_count
        ) = words_data
        print_info(
            '{} statistics: Saved => {}, Duplicate: {}, '
            'Dropped: {}, Blacklist: {}, Anything el'
            'se: {}'.format(
                context,
                word_count,
                duplicates_count,
                not_added_count,
                blacklist_words,
                not_word_count
            )
        )

    def main(self):
        all_words = {}
        all_not_word_count = 0
        all_word_count = 0
        all_duplicates_count = 0
        all_not_added_count = 0
        all_blacklist_words = 0
        for path in self.paths:
            print_info('searching in {!r}'.format(path))
            subs = glob(path + sep + '*.pdf')
            if subs:
                print_info(
                    'detected {} file(s) in {!r}'.format(len(subs), path)
                )
                if not isdir(self.PDF2WORD_DIR):
                    mkdir(self.PDF2WORD_DIR)
            for sub in subs:
                print_info('working on {!r}'.format(sub))
                data = self._read_file(sub)
                if data is None:
                    print_error(
                        'could not read file {!r}'.format(sub)
                    )
                    continue
                words_data = self._find_words(data)
                (
                    words,
                    word_count,
                    duplicates_count,
                    not_added_count,
                    blacklist_words,
                    not_word_count
                ) = words_data
                if not words:
                    print_error(
                        'could not found any word in {!r}'.format(sub)
                    )
                    continue
                new_word_count = 0
                for word, repeat in words:
                    if word not in all_words.keys():
                        all_words[word] = repeat
                        new_word_count += 1
                    else:
                        all_words[word] += repeat
                all_word_count += new_word_count
                all_duplicates_count += duplicates_count
                all_not_added_count += not_added_count
                all_blacklist_words += blacklist_words
                all_not_word_count += not_word_count
                self._write_pdf2word_file(
                    split(sub)[1],
                    words,
                    word_count
                )
                self._log_statistics(words_data, split(sub)[1])
            if all_word_count > 0:
                self._write_pdf2word_file(
                    'pdf2word_total.txt',
                    self._sort(all_words),
                    all_word_count
                )
                self._log_statistics(
                    (
                        all_words,
                        all_word_count,
                        all_duplicates_count,
                        all_not_added_count,
                        all_blacklist_words,
                        all_not_word_count
                    )
                )


def print_info(text, end='\n'):
    print('\033[1;33m' + '*INFO*' + '\033[0m ' + text, end=end)


def print_error(text):
    print('\033[1;31m' + '*ERROR*' + '\033[0m ' + text)


def print_warning(text):
    print('\033[1;31m' + '*WARNING*' + '\033[0m ' + text)


if __name__ == '__main__':
    paths = []
    repeat_count = 0
    exclude_repeated = False
    for arg in argv[1:]:
        if arg == '-x':
            exclude_repeated = True
            continue
        elif isdir(arg):
            if arg not in paths:
                paths.append(arg)
        elif arg.isdigit():
            print_info('set repeat count to {}'.format(arg))
            repeat_count = int(arg)
        else:
            print_warning('invalid path {!r}'.format(arg))
    if paths == []:
        paths = [getcwd()]
    try:
        PDF2Word(paths, [], repeat_count, exclude_repeated).main()
    except KeyboardInterrupt:
        print()
