from bs4 import BeautifulSoup
import pprint
import json

def table_from_HTML(input_html_file="bx_short.html"):
    table = {}
    headers = []
    soup = BeautifulSoup(open(input_html_file), "html.parser")

    for h in soup.find_all('thead'):
        for th in h.find_all('th'):
            for cell_value in th:
                headers.append(cell_value.string)
                break
    print headers

    for b in soup.find_all('tbody'):
        for tr in b.find_all('tr'):
            bx = 0
            for itd, td in enumerate(tr.find_all('td')):
                cell_value = td.get_text().strip()
                if itd == 0:
                    cell_value = int(cell_value)
                    bx = cell_value
                    table[bx] = {}  # table key is the bx number
                else:
                    cell_value = float(cell_value)
                table[bx][headers[itd]] = cell_value
    return table

if __name__ == '__main__':
    table = table_from_HTML(input_html_file='bx.html')
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(table)
    with open('bx_fill_4915_run_273162.json', 'w') as f:
        json.dump(table, f)
