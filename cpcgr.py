from urllib import request
import requests
import json
from datetime import datetime
import logging
from pprint import pprint

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
        
        while still_good:
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
                    temp_dict = {tag_name: {'type': tag_info[0],
                                            'name': tag_info[1].replace('"', ''),
                                            'value': tag_value
                                            }
                                }
                else:
                    tag_key = tag_info[1].replace('"', '')
                    temp_dict = {tag_name: {tag_key: {'type': tag_info[0],
                                                    'value': tag_value
                                                    }
                                            }
                                }
                all_tag.update(temp_dict)
                                
            else:
                still_good = False

        return all_tag

    def parseSingleReview(self, review):
        game_info = self.extractRange(review, 'div', 'class="gamedetails"')
        game_info_dict = self.htmlToDict(game_info)
        
        publ = self.replaceSym(game_info_dict['p']['publisher']['value'], {'(': '', ')': ''})
        publ = publ.split(',')
        valid_output = {'ref': game_info_dict['a']['name'],
                        'name': game_info_dict['h1']['gametitle']['value']['a']['value'],
                        'publisher': publ[0],
                        'year': int(publ[1])
                        }
                
        return valid_output

    def parsePageReviews(self, data, path):
        review_data = self.extractRange(data, 'table', 'class="reviews"')
        review_split = self.replaceSym(review_data, {'</tr>': '', '</td>': ''})
        review_split = review_split.split('<tr>')[1:]
        
        all_reviews = []
        for review in review_split:
            all_reviews += [self.parseSingleReview(review)]
                
        return all_reviews
        
    def parsePage(self, path):
        logging.info('Parsing -> %s' % path)
        data = self.loadurl(path)
        index = self.readIndex(data)
        logging.info('      Found -> %i subpage(s)' % len(index))
        
        all_page_data = []
        for i in range(len(index)):
            path_page = path if i == 0 else path.replace('.html', '%i.html' % (i + 1))
            page_data = data if i == 0 else self.loadurl(path_page)
            all_page_data += [self.parsePageReviews(page_data, path_page)]
        
        return all_page_data        
        
    def parseAll(self):
        all_res = []
        for path in self.all_paths:
            all_res += [self.parsePage(path)]
            
        return all_res
        
        
    

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    
    reviews = ParseCPCGR()
    reviews_results = reviews.parseAll()
    
    path = 'http://cpcgamereviews.com/%s/index.html'
    
    all_paths = [path % chr(ord('a') + i) for i in range(26)]
   
    f = request.urlopen(all_paths[0])
    data = f.read().decode('utf-8')
    data_clean = data.replace('\n', '').replace('\t', '')
    
    # first extract all links
    def extractRange(txt, tag, tagval=None):
        taglng = '<%s' % tag + (' %s>' % tagval if tagval else '>')
        part = txt.split(taglng)
        if len(part) > 1:
            part = part[1]
            return part.split('</%s>' % tag)[0]
        else:
            return ''
    
    uu = extractRange(data_clean, 'table', 'class="page-index"')
    uu2 = extractRange(uu, 'tr').replace('/td', 'td').replace('<td>', '').split('<br />')[:-1]
    uu2
    xx = data.split('<table class="page-index"')
    
    print('done')
    
    # htmlContent = requests.get(all_paths[0], verify=False)
    # data = htmlContent.text
    # print("data",data)
    # jsonD = json.dumps(htmlContent.text)
    # jsonL = json.loads(jsonD)
    
    # ContentUrl = json.dumps({
    #     'url': str(all_paths[0]),
    #     'uid': str(1),
    #     'page_content': htmlContent.text,
    #     # 'date': datetime.now()
    #     })

    # print(ord('a'))
    # print(chr(ord('a')))