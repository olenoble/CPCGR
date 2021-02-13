import logging
import pandas as pd
import numpy as np


class GenerateHTML:
    header = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n' \
             '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n\n' \
             '<html xmlns="http://www.w3.org/1999/xhtml" lang="en-UK">\n\n' \
             '<head>\n' \
             '<title>CPC Game Reviews - %s</title>\n' \
             '<meta http-equiv="Content-Language" content="en-UK" />\n' \
             '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />\n\n' \
             '<link rel=\"stylesheet\" type=\"text/css\" href=\"./css/style.css\" />\n' \
             '</head><body>\n\n' \
             '<p class="title"><a id="top"></a><h1>%s</h1></p><br /><br /><br /><br />\n' \
             '<p><table class="games-list" border="0" cellspacing="10" cellpadding="0" align="left">\n'
    closing = '\n\n\n</table></p></body></html>\n'

    group_ref = '\n\n\n<tr><td align="left" valign="top"><a name=%s></a><h2>%s</h2>\n' \
                '<p class="games-list-caption">%i game(s)</p></td>\n\n' \
                '%s\n' \
                '</tr>'
    column_ref = '<td align="left" valign="top"><font size="-1">\n' \
                 '<h3>%s</h3><br>\n' \
                 '%s' \
                 '</td>\n\n'
    entry_ref = '%s<br>\n'
    link_ref = '<a href="%s">%s</a><br>\n'

    def __init__(self, data, group=None, ref=None, title=None, column_list=None, link_col=None):
        self.group = group
        self.column_list = column_list
        self.link_col = link_col if hasattr(link_col, '__iter__') else [link_col]
        self.ref = ref
        self.title = title

        self.data = data

        self.output = self.header % (self.title, self.title)
        self.grouplist = np.sort(np.unique(review_data[group].values))

    def buildHTML(self):

        for group in self.grouplist:
            logging.info('Generating html for %s' % group)
            data_group = self.data[self.data[self.group] == group]
            group_count = len(data_group)
            ref_group = data_group[self.ref].values

            group_list_html = ''
            for i, col in enumerate(self.column_list):
                data_group_col = data_group[col[1]].values
                use_link = i in self.link_col
                row_ref = self.link_ref if use_link else self.entry_ref

                row_ref = row_ref * len(data_group_col)
                row_vals = [(ref_group[j], x) if use_link else [x] for j, x in enumerate(data_group_col)]
                row_vals = [item for subl in row_vals for item in subl]
                col_html = row_ref % tuple(row_vals)

                group_list_html += self.column_ref % (col[0], col_html)

            self.output += self.group_ref % (group, group, group_count, group_list_html)

        self.output += self.closing
        return self.output


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    review_data = pd.read_csv('review.csv')
    del review_data['Unnamed: 0']

    # By publisher
    html_publisher = GenerateHTML(review_data, group='publisher', ref='ref', title='Game By Publisher',
                                  column_list=[['Name', 'name'], ['Rating', 'score'], ['Year', 'year']],
                                  link_col=0)
    publish_file = html_publisher.buildHTML()

    with open('game_publisher.html', 'w') as f:
        f.write(publish_file)

    # By year
    html_year = GenerateHTML(review_data, group='year', ref='ref', title='Game By Year',
                             column_list=[['Name', 'name'], ['Publisher', 'publisher'], ['Rating', 'score']],
                             link_col=0)
    year_file = html_year.buildHTML()

    with open('game_year.html', 'w') as f:
        f.write(year_file)

    # By score
    html_score = GenerateHTML(review_data, group='score', ref='ref', title='Game By Rating',
                              column_list=[['Name', 'name'], ['Publisher', 'publisher'], ['Year', 'year']],
                              link_col=0)
    score_file = html_score.buildHTML()

    with open('game_score.html', 'w') as f:
        f.write(score_file)

    print('done')
