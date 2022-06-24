import re
import csv
import fitz
import pdfkit
from collections import Counter
from googletrans import Translator
# from pygoogletranslation import Translator


class pdf2word:

    # TODO: - is checked in clean why should do???
    STOP_CHARS = '!?$@&*~%|<>:"/=#+-%{}()[];\'.,'

    # empty init??
    def __init__(self):
        pass

    def read_srt(self, path: str) -> str:
        text = ""
        CLEANR = re.compile('<.*?>')
        try:
            with open(path, 'r') as f:
                for line in f:
                    if not line[0].isdigit():
                        text += " " + line.replace('\n', '')
                        text = text.lstrip()
        # TODO: oserror??
        except (OSError, UnicodeDecodeError, FileNotFoundError) as err:
            raise (err)
            # remove html tags
        text = re.sub(CLEANR, '', text)
        return text

    def read_txt(self, path: str) -> str:
        text = []
        try:
            with open(path, "r") as f:
                text = f.readlines()
        # TODO: seperate errors
        except (OSError, UnicodeDecodeError, FileNotFoundError) as err:
            raise (err)
        text = ''.join(text)
        return text

    def read_pdf(self, path: str, page_num: int = None) -> str:
        # TODO: list of specefic page
        text = ""
        try:
            with fitz.open(path) as doc:
                if page_num is None:
                    for page in doc:
                        text += page.get_text()
                else:
                    page = doc.loadPage(page_num)
                    text = page.getText('text')
        except (OSError, UnicodeDecodeError, FileNotFoundError) as err:
            raise (err)
        return text

    def clean_words(self, fulltext: str) -> dict:
        # TODO: set unicode range for all langs
        # TODO: set global var for path
        remove_words = self.read_txt('remove_words.txt')
        remove_words = remove_words.split()
        remove_male_names = self.read_txt('male_names_list.txt')
        remove_male_names = remove_male_names.split()
        remove_female_names = self.read_txt('female_names_list.txt')
        remove_female_names = remove_female_names.split()
        remove_sur_names = self.read_txt('surnames_list.txt')
        remove_sur_names = remove_sur_names.split()
        stop_words = remove_words + remove_male_names + \
            remove_female_names + remove_sur_names

        text = ''
        for char in fulltext:
            # isdigit???
            if char in self.STOP_CHARS or char.isdigit():
                text += ' '
            else:
                text += char
        # split(' ')??
        pieces = text.split()
        '''
        for c in STOP_CHARS:
            # replace space? or none?
            text = text.replace(c, ' ')
        '''
        words = {}
        not_word_count = 0
        not_added_count = 0
        blacklist_words = 0
        duplicates_count = 0
        for piece in pieces:
            piece = piece.lower()
            is_word = True
            for char in piece:
                # english ascii code
                if 96 < ord(char) < 123:
                    continue
                elif ord(char) == 45:
                    continue
                elif ord(char) == 39:
                    continue
                is_word = False
                break
            if not is_word:
                not_word_count += 1
                continue
            if piece.endswith('\'ve') or \
                    piece.endswith('\'ll') or \
                    piece.endswith('n\'t') or \
                    piece.endswith('\'re') or \
                    piece.endswith('in\''):
                piece = piece[:-3]
            elif piece.endswith('\''):
                piece = piece[:-1]
            elif piece.startswith('\''):
                piece = piece[1:]
            if len(piece) < 3:
                not_added_count += 1
                continue
            if piece + 'ing' in words:
                words.pop(piece + 'ing')
            if piece.endswith('ing') and piece[:-3] in words:
                not_added_count += 1
                continue
            if piece + 's' in words:
                words.pop(piece + 's')
            elif piece.endswith('s') and piece[:-1] in words:
                not_added_count += 1
                continue
            if piece[0] == '-' or piece[-1] == '-':
                not_added_count += 1
                continue
            if piece not in stop_words:
                # avalesh(code) bayad inja biad?
                if piece not in words:
                    words[piece] = 1
                else:
                    words[piece] += 1
                    duplicates_count += 1
            else:
                blacklist_words += 1
            # TODO: elifs is true??
        words_list = [{k: v} for k, v in words.items()]
        # TODO: change some var names...
        result = (
            words_list,
            not_added_count,
            blacklist_words,
            not_word_count,
            duplicates_count
        )
        return result
        # return res, not_added_count, blacklist_words, not_word_count, duplicates_count

    # change var names...
    def translate_words(self, res: dict) -> dict:
        # print(len(res))
        # print(res)

        # TODO: use async
        # TODO: langs ask from user
        from_lang = 'en'
        to_lang = 'fa'
        translator = Translator()
        limit = 5000
        str_chunk = []
        # choose better name
        word = ''
        count_words = 0
        for i in res:
            key = list(i)[0]
            if len(key) + len(word) < limit:
                word += f'{key}\n'
                count_words += 1
            else:
                str_chunk.append(word)
                word = ''
                word += f'{key}\n'

        if str_chunk == []:
            str_chunk.append(word)

        print(len(str_chunk))
        # bug size res and tmp and ans
        # print(len(res))
        # for api limit
        trans_res = []
        # TODO: better algorithm and dicts and list...
        for i in str_chunk:
            r = translator.translate(i, src=from_lang, dest=to_lang)
            tmp = i
            tmp = tmp.split('\n')
            ans = r.text.split('\n')
            tmp = [j for j in tmp if j != '']
            to_list = [
                {
                    tmp[i]: ans[i]
                } for i in range(len(tmp))
            ]
            for i in to_list:
                trans_res.append(i)

        print(len(trans_res), count_words, len(res))
        data = []
        for d in trans_res:
            key = list(d)[0]
            value = list(d.values())[0]
            for d in res:
                if key in d:
                    data.append(
                        {'word': key, 'translate': value, 'count': d[key]}
                    )

        return data

    def dic_to_html(self,
                    data: list,
                    words_len: int,
                    not_added_count: int,
                    blacklist_words: int,
                    not_word_count: int,
                    duplicates_count: int
                    ) -> str:
        html = ''.join(f'<th lang="en">{x}</th>' for x in data[0].keys())
        for d in data:
            row = ''
            for x in d.values():
                # english words
                if x != list(d.values())[1]:
                    row += f'<td lang="en">{x}</td>'
                else:
                    row += f'<td lang="fa">{x}</td>'
            html += f'<tr>{row}</tr>'
        # TODO: use charts and statistics
        style = (
            '<style>'
            ':lang(en) {'
            '   font-family: Ubuntu, sans-serif;'
            '}'
            ':lang(fa) {'
            '   font-family: Vazirmatn, sans-serif;'
            '}'
            'table {'
            '   border-collapse: collapse;'
            '}'
            'th, td {'
            '   text-align: center;'
            '   vertical-align: middle;'
            '   font-family: Vazirmatn, sans-serif;'
            '   font-size: 20px;'
            '   font-style: normal;'
            '   padding: 10px;'
            '   border: 1px solid;'
            '   border-color: #96D4D4;'
            '}'
            'th {'
            '   color:#216dff;'
            '   background-color:#00ffe729;'
            '}'
            '</style>'
        )
        # #00ffe729
        # #216dff
        words_log = (
            '<table>'
            '<tr>'
            '<th lang="en">words length</th>'
            '<th lang="en">not added words</th>'
            '<th lang="en">blacklist words</th>'
            '<th lang="en">not count words</th>'
            '<th lang="en">duplicate word</th>'
            '</t>'
            '<tr>'
            f'<td lang="en">{words_len}</td>'
            f'<td lang="en">{not_added_count}</td>'
            f'<td lang="en">{blacklist_words}</td>'
            f'<td lang="en">{not_word_count}</td>'
            f'<td lang="en">{duplicates_count}</td>'
            '</tr>'
            '</table>'
        )
        banner = '<h1>WordsGolchin</h1>'
        return f'<!DOCTYPE html><head><meta charset="UTF-8">{style}</head><body><center>{banner}{words_log}<br><br><table>{html}</table></center></body>'

    def dic_to_csv(self,
                   data: list,
                   words_len: int,
                   not_added_count: int,
                   blacklist_words: int,
                   not_word_count: int,
                   duplicates_count: int,
                   filename: str
                   ) -> str:
        keys = data[0].keys()
        # TODO: add statistics words_len and.....
        csv_name = f'{filename}.csv'
        with open(csv_name, "w", encoding='utf8', newline='') as file:
            dict_writer = csv.DictWriter(file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        # TODO: can user stringio instead of string...

    def export_pdf(self, html: str, file_name: str) -> str:
        html_name = f'{file_name}.html'
        with open(html_name, "w") as file:
            file.write(html)
        pdf_name = f'{file_name}.pdf'
        pdfkit.from_file(html_name, pdf_name)


# TODO: do better main
def main(ext: str = 'pdf'):
    p2w = pdf2word()
    fname = 'my.pdf'
    if ext == 'srt':
        fulltext = p2w.read_srt(fname)
        words_list, not_added_count, blacklist_words, not_word_count, duplicates_count = p2w.clean_words(
            fulltext)
    elif ext == 'pdf':
        # fulltext = p2w.read_pdf(fname, 707)
        fulltext = p2w.read_pdf(fname)
        print(fulltext)
        words_list, not_added_count, blacklist_words, not_word_count, duplicates_count = p2w.clean_words(
            fulltext)
    else:
        fulltext = p2w.read_txt(fname)
        words_list, not_added_count, blacklist_words, not_word_count, duplicates_count = p2w.clean_words(
            fulltext)

    d = p2w.translate_words(words_list)
    # sort dicts by most frequent words to least
    d = sorted(d, key=lambda d: d['count'], reverse=True)
    '''
    # if export csv
    p2w.dic_to_csv(
        d, len(d), not_added_count, blacklist_words, not_word_count, duplicates_count, "out.csv")
    '''
    html = p2w.dic_to_html(
        d, len(d), not_added_count, blacklist_words, not_word_count, duplicates_count)
    p2w.export_pdf(html, 't')


main()
