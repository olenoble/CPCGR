from urllib import request
import requests
import json
from datetime import datetime
import logging
from pprint import pprint
import pandas as pd


class ParseCPCGR:

    root_path = 'http://cpcgamereviews.com/%s/index.html'
    decode_ref = 'utf-8'
    map_sym = {'\n': '', '\t': ''}
    line_skip = '<br />'

    all_paths = []

    def __init__(self):
        # generate all paths
        logging.info('Generate all paths')
        self.all_paths = [self.root_path % chr(ord('a') + i) for i in range(26)]
        self.reviews = None

    def extractRange(self, data, tag, tagval=None):
        taglng = '<%s' % tag + (' %s>' % tagval if tagval else '>')
        part = data.split(taglng)        
        part = part if len(part) > 1 else ['', '']
        return part[1].split('</%s>' % tag)[0]

    @staticmethod
    def replaceSym(data, sym_map):
        for sym, rep in sym_map.items():
            data = data.replace(sym, rep)
        return data

    def loadurl(self, path, clean=True):
        with request.urlopen(path) as url:
            data = url.read().decode(self.decode_ref)

        return self.replaceSym(data, self.map_sym) if clean else data

    def readIndex(self, data):
        ind = self.extractRange(data, 'table', 'class="page-index"')
        ind = self.replaceSym(self.extractRange(ind, 'tr'), {'/td': 'td', '<td>': ''})
        return ind.split(self.line_skip)[:-1]

    def htmlToDict(self, txt):
        all_tag = {}
        still_good = True

        non_tag = []
        while still_good:
            check_non_tag = txt.split('<')
            if check_non_tag[0] != '':
                non_tag += [check_non_tag[0]]
                txt = '<' + '<'.join(check_non_tag[1:])

            txttag = txt.split('>')
            if len(txttag) > 1:
                txt = '>'.join(txttag[1:])
                tag_ref = txttag[0].replace('<', '')
                tag_name = tag_ref[:tag_ref.find(' ')]
                tag_info = tag_ref[tag_ref.find(' ') + 1:].split('=')

                if tag_name == 'img':
                    tag_value = ''
                else:
                    end_tag = txt.split('</%s>' % tag_name)
                    txt = ('</%s>' % tag_name).join(end_tag[1:])
                    tag_value = end_tag[0]
                    tag_value = self.htmlToDict(tag_value) if (tag_value.find('<') >= 0) else tag_value

                if tag_name == 'a':
                    temp_dict = {tag_info[0]: {'name': tag_info[1].replace('"', ''),
                                               'value': tag_value
                                               }
                                 }
                else:
                    tag_key = tag_info[1].replace('"', '')
                    temp_dict = {tag_key: {'type': tag_info[0],
                                           'value': tag_value
                                           }
                                 }

                all_tag.update(temp_dict)

            else:
                still_good = False

        all_tag['nontag'] = non_tag
        return all_tag

    def parseSingleReview(self, review, path):
        game_info = self.extractRange(review, 'div', 'class="gamedetails"')
        game_info_dict = self.htmlToDict(game_info)
        score = self.htmlToDict(self.extractRange(review, 'p', 'class="rating"'))
        score = score if score['nontag'] else self.htmlToDict(self.extractRange(review, 'p', 'class="rating no-line-break"'))

        publ = self.replaceSym(game_info_dict['publisher']['value'], {'(': '', ')': ''})
        publ = publ.split(',')
        publ = publ if len(publ) >= 2 else [publ, 'Unknown']
        valid_output = {'ref': '#'.join([path, game_info_dict['id']['name']]),
                        'name': game_info_dict['gametitle']['value']['href']['value'],
                        'publisher': publ[0],
                        'year': publ[1].replace(' ', ''),
                        'score': int(score['nontag'][0])
                        }

        return valid_output

    def parsePageReviews(self, data, path):
        review_data = self.extractRange(data, 'table', 'class="reviews"')
        review_split = self.replaceSym(review_data, {'</tr>': '', '</td>': ''})
        review_split = review_split.split('<tr>')[1:]

        all_reviews = []
        for review in review_split:
            all_reviews += [self.parseSingleReview(review, path)]

        return all_reviews

    def parsePage(self, path):
        data = self.loadurl(path)
        index = self.readIndex(data)
        logging.info('Checking %s' % path)
        logging.info('      Found -> %i subpage(s)' % len(index))

        all_page_data = []
        for i in range(len(index)):
            path_page = path if i == 0 else path.replace('.html', '%i.html' % (i + 1))
            logging.info('      Parsing -> %s' % path_page)
            page_data = data if i == 0 else self.loadurl(path_page)
            all_page_data += self.parsePageReviews(page_data, path_page)

        return all_page_data

    def parseAll(self):
        all_res = []
        for path in self.all_paths:
            all_res += self.parsePage(path)

        self.reviews = all_res
        res_tbl = pd.DataFrame(all_res)
        
        return res_tbl


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    
    reviews = ParseCPCGR()
    reviews_results = reviews.parseAll()
    
    reviews_results.to_csv('review.csv')