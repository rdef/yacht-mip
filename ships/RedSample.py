#sample structure for a YachtMip Ship object

class RedShip(YachtMip):
    
    def __init__(self, chat=None, *, proj_ini=None, client_name=None):
        super().__init__(chat, client_name=client_name)
        
        self.timezone = pendulum.timezone('Australia/Melbourne')
        
        self.site_info = {"site": "xiaohongshu.com",
                     "info_pages": ["https://en.wikipedia.org/wiki/Xiaohongshu"]}
        
        self.re = dict()
        
        # the regex for grabbing a valid link
        self.re['link'] = re.compile("(xiaohongshu.com/(?:[a-zA-Z0-9_]*?/)*[a-zA-Z0-9]*)")
        # red uses a number of subdirectories for its links, including:
        #  - xiaohongshu.com/discovery/item/{id}
        #  - xiaohongshu.com/explore/{id}
        #  - xiaohongshu.com/search_result/{id}
        
        # backup regex for other link formats
        self.re['backup'] = [re.compile("(xhslink.com/[a-zA-Z0-9]*)")]
        
        # the regex for grabbing an id from a valid link
        self.re['id_re'] = re.compile("\/([a-zA-Z0-9]*?)(?:\?|\Z|\n)") 
    
    @classmethod
    def soup_framework(soup):
        entry = dict()
        try:
            entry["likes"] = soup.find("span", {'class':'like-wrapper'}).text
            entry["faves"] = soup.find("span", {'class':'collect-wrapper'}).text
            entry["comments"] = soup.find("span", {'class':'chat-wrapper'}).text
            entry["title"] = soup.find("title").text
            entry["author"] = soup.find("div", {'class':'author'}).text
            entry["description"] = (BS(str(soup.find("div", {'id':'detail-desc'}))
                                            .replace("<br/>", "\n")).text).split("@")[0].strip()
            date_loc = soup.find("span", {'class':'date'}).text
            entry["date"], entry["loc"] = date_loc.split(" ")
            entry['removed'] = "False"
        except AttributeError:
            entry["likes"] = ""
            entry["faves"] = ""
            entry["comments"] = ""
            entry["title"] = ""
            entry["author"] = ""
            entry["description"] = ""
            entry["date"] = ""
            entry["loc"] = ""
            entry['removed'] = "True"
        return entry