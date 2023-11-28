from bs4 import BeautifulSoup as BS

import telethon
from telethon.sync import TelegramClient

import pendulum
import regex as re
import requests
import json
import random
import numpy as np
import pandas as pd
import configparser
import time
import logging
from pathlib import Path


def get_headers(*, verbose=True):
    # use as: headers={'user-agent':UA_randomiser()["ua"]}

    tracker = random.random()*100
    score = f"UA score is {tracker}" # tracker for ratio chance
    logging.debug(score)
    if verbose:
        print(score)
    for UA in JUAs['data']:
        tracker-=UA['pct']
        if tracker <0:
            break
        logging.debug(f"UA {UA['ua']} skipped, with percent {round(UA['pct'], 3)}."
                      f" Tracker at {tracker}.")
    found = f"Found UA {UA['ua']}; {round(UA['pct'], 2)}%"
    logging.info(found)
    if verbose:
        print(found)
    return {"User-Agent":UA["ua"]}


# Page class

class DataMessage:
    # a telegram message
    
    def __init__(self, msg, proj_re):
        logging.debug(f"Attempting to parse message")
        if not isinstance(msg, telethon.types.Message):
            logging.debug(f"Not a Message, skipping.")
            return None

        self._merged = False
        self._parsed = False
        self._id = None
        
        self._analysis = dict() # dict of analysis data
        self._links = list() # msg links
        
        # regexes
        self.re = proj_re
        self.re['hashtags'] = re.compile(r'#[^#,.;\s\\\*\r\t\n]+')
        self.re['metadata'] = re.compile("^\$([a-zA-Z]{1,})\W(.*?)$", re.M)
        
        self._msg = msg
        self._text = msg.text
        self._msg_id = msg.id # message id
        self._chat_id = msg.chat.id # chat id

        try:
            self._media = msg.media.webpage.to_dict()
        except AttributeError:
            self._media = dict()

        # process analysis
        self._analyse()
        
        # get links
        self._get_links()
        
        
    def _set_id(self, *, force=False):
        logging.info("attempting to set self._id")
        if not self._r_link:
            raise ValueError("self._r_link does not exist.")
        elif self._id:
            raise ValueError("self._id already set.")
        else:
            self._id = self.re['id_re'].findall(self._r_link)[0] # get the id from the r_link
            
        
    def _analyse(self):
        msg_split = self._text.split("***", 1)
        msg_txt = self._analysis['text'] = msg_split[0]
        if len(msg_split)==2:
            self._analysis['comments'] = msg_split[1]
        else:
            self._analysis['comments'] = ""

        self._analysis['hashtags'] = self.re['hashtags'].findall(msg_txt)
        self._analysis['metadata'] = dict(self.re['metadata'].findall(msg_txt))
        self._analysis['observation time'] = pendulum.instance(self._msg.date).isoformat()
        
    # identify a reference link
    def _get_links(self):
        ref_link = self.re['link'].findall(self._text)
        print(f"ref link = {ref_link}")
        if not ref_link and 'display_url' in self._media:
            ref_link = self.re['link'].findall(self._media["display_url"])
            print(ref_link)

        if ref_link:
            # get the link string from the regex
            self._r_link = f"https://{ref_link[0]}" 
            self._set_id()
        else:
            print("no Ref_link")
            
        for link_re in self.re['backup']:
            if (found_link := link_re.findall(self._text)):
                val = f"https://{found_link[0]}"
                if val not in self._links:
                    self._links.append(val)
            
        
    @property
    def data(self):
        out_d = {self.id: 
                 {"analysis":self._analysis, 
                  "msg": {"msg_id": self._msg_id, 
                          "chat_id": self._chat_id}, 
                  "ref_link": self._r_link, 
                  "links": self._links}
                }
        return out_d
        
    
    @property
    def text(self):
        return self._text
    
    
    # R_LINK
    
    @property
    def r_link(self):
        return self._r_link
    
    
    def _set_r_link(self, val, *, force=False):
        if not isinstance(val, str):
            raise TypeError(f"_set_r_link requires a string. {type(val)} provided")
        if not force and self._r_link:
            raise ValueError(f"Reference r_link already assigned. "
                             f"Use self._set_r_link({val}, force=True) to force this change.")
        elif force and self._r_link:
            logging.warning(f"Replacing existing r_link, not recommended")
        if (found_link:= self.re.findall(val)):
            self._r_link = f"https://{found_link[0]}"
            logging.debug(f"Regex {link_regex} found {found_link[0]}")
        self._set_id()

    
    # C_LINK
    @property
    def c_link(self):
        """self.c_link is a 'clickable' link 
 - i.e. returns a functional link for the analysis, albeit not necessarily a referenceable one"""
        if self._r_link:
            return self._r_link
        else:
            for link in self._links:
                if link:
                    return link
    
    # ID
    @property
    def id(self):
        return self._id

    

class Page:
    # parses a telegram message into its constituent elements
    
    # things to add:
    # properties to return chat, id, chat obj.

    def __init__(self, _analysis, _proj):
        logging.debug(f"Attempting to parse message")
        if not isinstance(msg, telethon.types.Message):
            logging.debug(f"Not a Message, skipping.")
            return None
        
        self._id = None
        self._merged = False
        self._duplicates = dict()
        
        # set variables for later scraping
        self._soup_framework = _proj.soup_framework
        self._soup = None
        self._request = dict()
        self._request['status'] = list()

            

        
    def parse_link(self, *, force=False):
        if self._soup and not force:
            raise ValueError("Page already pulled for this link. "
                             "Use force=True to force a new pull.")
        val = dict()
        response = requests.get(self.c_link, headers=get_headers(verbose=False))
        self._request['status'].append((str(response.status_code), pendulum.now()))
        self._request['response']= str(response.ok)
        if not self._r_link:
            temp_link = self.response.url
            if (found:=self._re.findall(temp_link)):
                self._r_link = found[0]
                self._set_id()
        logging.info("page found, attempting to parse soup.")
        self._soup = BS(self.response.text)
        self._page = self._soup_framework(self._soup)
        self._page['removed'] = str(bool(response.ok))
        
    def _out_dict(self):
        out_d = dict()
        out_d['id'] = self._id
        out_d['link'] = self.c_link
        out_d['hashtags'] = self._analysis['hashtags']
        out_d['metadata'] = self._analysis['metadata']
        out_d['comments'] = self._analysis['comments']
        for k,v in self._page.items():
            _key = f"_{k}"
            out_d[_key] = v
        out_d['observation time'] = self._analysis['observation time']
        return out_d
        
    def _parse_soup(self):
        if self._soup:
            self._page = self._proj.soup_framework(self._soup, response)
        else:
            raise ValueError("Soup does not exist. ")
        
    def __str__(self):
        _str = "{"
        for k, v in self._data.items():
            _str = f"{_str}\n{k}: {v}, \n"
        _str = _str + "}"
        return _str


class YachtMip:

    def __init__(self, chat, *, project_ini=None, proj_name=None, client_name=None):
        if project_ini:
            self.__project_ini = project_ini
        else:
            self.__project_ini = "YachtMip.ini"
        self._tool_status = dict()
        self._tool_status['initialised'] = False
        self._tool_status['chats'] = list()
        self._tool_status['version'] = None

        self._proj_status = dict()
        self._proj_status['ethics'] = list()
        self._proj_status['hashtags'] = list()
        self._proj_status['project name'] = proj_name
        
        # __last = time of the last scrape.
        # equiv to __scrape_history[-1]['time']
        self.__last = pendulum.now()

        self.__init_chat = chat
        #__delay = delay between individual scrapes
        self.__delay = None
        self._set_delay()
        
        #__period = a reference period for checking for volume
        # essentially this 
        self.__period = pendulum.duration(seconds=300)
        
        self.__scrape_history = []
        self.__vol  = 100
        
        self.__removed = list()

        # dict that will later be filled with dialogs for later looping over
        self._dialogs = dict()
        
        self._messages = list()
        self._api = dict()
        self._authors = dict()
        self.__get_config()
        if not client_name:
            client_name = 'CaptureClient'
        self.client = TelegramClient(client_name, self.api['id'], self.api['hash'])
        print(f"user {self.client.session.filename.split('.')[0]} created.")
        self.telethon_params = {"limit":None, "reverse":False,
                                "reply_to":None}
        
        # archive of pulled messages. Minimal research value.
        self._archive = dict()
        
        # checklist of processed messages, avoids double-entry of a message
        self._check = dict()
        
        # checklist of processed links, _tries_ to avoid double-entry of a page
        self._index = dict()

    #properties
    
    @property
    def project(self):
        out_d = dict()
        out_d['init file'] = self.__project_ini
        out_d += self._tool_status
        out_d += self._proj_status
        return out_d
    
    @property
    def archive(self):
        return self._archive
    
    @property
    def messages(self):
        return self._messages
    
    
    # *last*
    # the last scrape that was attempted
    
    @property
    def last(self):
        # the last scrape
        if self.__scrape_history:
            return self.__scrape_history[-1]
        else:
            return None

    # *delay*
    # the preferred delay between individual scrapes
    @property
    def delay(self):
        val = 0
        for x in range(0,5):
            val += random.randint(self.__delay[0], self.__delay[1])
        return val/500
        
    
    def _set_delay(self, *, _min=5, _max=10):
        # sets the delay in seconds
        self.__delay = (_min*100, _max*100)
        logging.info(f"Delay set to range between {_min/100} to {_max/100} seconds.")


    # ok
    #
    # checks if we are okay to continue scraping.
    @property
    def ok(self):
        # checks if we are okay to continue scraping
        if self.__vol == 0:
            # if no volume is set, stop.
            print("Volume is set to 0. No scrapes will proceed.")
            return False
        elif len(self.__scrape_history) == 0:
            # if no scrapes, go ahead
            return True
        if (pendulum.now() - self.__last) < self.__delay:
            return False
        elif (pendulum.now() - self.__last) > self.__delay:
            # if the delay has timed out, continue assessing.
            if len(self.__scrape_history)<self.__vol:
                # if the volume cap hasn't been reached
                return True
            elif (pendulum.now() - self.__scrape_history[-1*self.__vol]) > self.__period:
                # if the length has been reached, but enough time has passed
                return True
        print("eval concluding False with no clear outcome.")
        return False
    
    
    # history
    #
    # a list of recent scrapes
    @property
    def history(self):
        return self.__scrape_history
    
    @history.setter
    def history(self, val):
        if not isinstance(val, dict):
            raise TypeError
        self.__last = pendulum.now()
        new_scrape = {"time": self.__last, "link":val['link'],"id":val['id'],
                      "response":val['response'],"success": val['success']}
        self.__scrape_history.append(new_scrape)
        
    def print_history(self):
        if self.__scrape_history:
            temp_delay=0
            last_t = None
            for scrape in self.__scrape_history:
                if last_t:
                    temp_delay=(scrape['time']-last_t).in_seconds()
                else:
                    first = scrape['time']
                    hist_out = ("             time                |   Δ  |"
                                " resp  |success|  id\n")
                buffer  = (5-len(str(temp_delay)))*" "
                calc_delay = f"{buffer}{temp_delay}"
                hist_out +=(f"{scrape['time']} |{calc_delay} |  {scrape['response']}  |")
                if scrape['success']:
                    hist_out += " True  "
                else:
                    hist_out += " False "
                hist_out += f"| {scrape['id']}\n"
                last_t = scrape["time"]
            hist_out = (f"Starts at {first}\n"
                        f"Ends at {last_t} \n"
                        f"Total duration = {(last_t-first).in_seconds()}s\n{hist_out}")
            print(hist_out)
        else:
            print("No history")
    
    # period
    # a reference period for volume

    @property
    def period(self):
        return self.__period
    
    @period.setter
    def period(self, val):
        logging.info(f"Attemping to set self.__period to '{val}'.")
        try:
            dur = pendulum.duration(seconds=val)
            if dur >= pendulum.duration(seconds=0):
                self.__period=dur
                logging.info(f"self.__period set to '{self.__period}'.")
            elif val == 0:
                logging.error(f"attempt to set self.__period to '{val}', "
                              "but this was rejected.", 
                              exc_info=ZeroDivisionError)
                raise ZeroDivisionError
            else:
                logging.warning(f"attempt to set self.__period to '{val}', "
                                "but this was rejected.")
                print(f"Period set to {self.__period.in_seconds()} seconds.")
        except Exception as e:
            logging.exception(f"Setting self.__period to '{val}' failed. ")
            raise e


    # volume
    #
    # the number of scrapes in a reference period. 
    # refer to period variable for more detail
    
    @property
    def volume(self):
        return self.__vol

    @volume.setter
    def volume(self, val):
        logging.info(f"Attempting to set self.__vol to '{val}'.")
        try:
            if val > 0:
                logging.info(f"self.__vol set to '{int(val)}'")
                self.__vol = int(val)
            else:
                logging.info(f"'{val}' rejected as invalid.")
        except Exception as e:
            logging.exception(f"Setting self.__vol to '{val}' failed. ")
            raise e


    async def run_client(self):
        logging.info(f"Running self.run_client(self) with {self.client}.")
        await self.client.start()
        assert self.client.is_connected()
        try:
            assert await self.client.is_user_authorized()
        except AssertionError:
            logging.exception(f"self.client not authorized. Attempting login.")
            try:
                await self.client.send_code_request(self.api['phone'])
                print("check telegram on your phone for a verification code.")
                logging.info(f"TFA code requested.")
                login_code = input(" > ")
                logging.info(f"User provided input.")
                await self.client.sign_in(self.api['phone'], str(login_code))
                logging.info(f"Signin attempt sent.")
                assert await self.client.is_user_authorized()
                logging.info(f"User '{self.client.session.filename.split('.')[0]}'"
                             "authorised.")
                print(f"user {self.client.session.filename.split('.')[0]} authorised")
            except AssertionError as e:
                logging.exception("Process failed, unable to log in")
                print(f"Process failed with error {e}")
                raise e
            except Exception as e:
                logging.exception("Process failed during login, unable to log in")

                
    @property
    def status(self):
        return self._status_dict
        
    async def initialise(self):
        # runs, in sequence:
        # 1. self._grab_dialogs(full=True) - gets the chat object to pull messages from
        # 2. self._parse_messages() - pulls the messages
        try:
            await self.run_client()
            await self._grab_dialogs()
            self._set_dialogs(self.__init_chat)
            if self._dialogs:
                self._set_chats()
                print('Setting chats...')
            if self._tool_status['chats']:
                # runs next after a chat object has been found
                logging.info(f"{len(self._tool_status['chats'])} chat object(s) identified, "
                             "attempting to pull messages.")
                print('Parsing messages...')
                await self._parse_messages()
        finally:
            await self.close_connection()


    async def _pull_messages(self):
        # gets messages from Telegram, adds them to the message 
        await self.run_client()
        messages=list()
        count = 0
        for chat_obj in self._tool_status['chats']:
            async for message in self.client.iter_messages(chat_obj, 
                                                           **self.telethon_params):
                if isinstance(message, telethon.types.Message):
                    messages.append(message)
        print(f"{count} messages parsed.")
        return messages
    
            
    async def _parse_messages(self, *, reset=False):
        # gets messages from Telegram, adds them to the message 
        # archive if they are not already present
        await self.run_client()
        if reset:
            self._check=dict()
            self._messages = list()
        count = 0
        for chat_obj in self._tool_status['chats']:
            async for message in self.client.iter_messages(chat_obj, 
                                                           **self.telethon_params):
                if isinstance(message, telethon.types.Message):
                    if self._check_source(message):
                        try:
                            if (parsed:= DataMessage(message, self.re)):
                                self._messages.append(parsed)
                                count+=1
                            self._add_source(message)
                        except Exception as e:
                            raise e
        print(f"{count} messages parsed.")

            
    async def close_connection(self):
        # manually closes connection if necessary
        if self.client.is_connected():
            await self.client.disconnect()

        
    def _check_source(self, msg):
        # used to check whether a message has already been added to the archive
        # returns false 
        chat = str(msg.chat_id)
        id_ = str(msg.id)
        if chat in self._check:
            if id_ in self._check[chat]:
                return False
            else:
                return True
        else:
            return True

    def _add_source(self, msg):
        # used to check whether a message has already been added to the archive
        # returns false 
        chat = str(msg.chat_id)
        id_ = str(msg.id)
        if chat not in self._check:
            self._check[chat] = set()
        self._check[chat].add(id_)

        
    def print_dialogs(self):
        for k, v in self._dialogs.items():
            act_col = '\033[0mOFF'
            if v['active']:
                act_col = '\033[92m\033[1mON '
            print(f"{k}\t| {act_col} | {v['id']} | {v['name']}\033[0m")
        
    def _set_chats(self):
        logging.info("Starting self._set_chats")
        self._tool_status['chats'] = list()
        for key, value in self._dialogs.items():
            logging.debug(f"dialog {key} is set to {value['active']}")
            if value['active']:
                logging.info("Active value found.")
                self._tool_status['chats'].append(value['dialog'])
        
            
    @property
    def chats(self):
        return self._tool_status['chats']
        
    @property
    def dialogs(self):
        return self._dialogs
    
    @dialogs.setter
    def dialogs(self, val):
        self._set_dialogs(val)
    
    
    def _set_dialogs(self, val):
        # toggles specific dialogs on and off
        # if user is True then an interface is provided.
        if self._dialogs:
            logging.info(f"Attempting to toggle a self._dialogs object"
                         f" using reference '{val}'")
            try:
                val = int(val)
            except ValueError:
                pass
            try:
                #if it's a dialog, peer, or similar, we should be able to pull it via id
                val = int(val.id)
            except AttributeError:
                pass
            if isinstance(val, int):
                logging.info(f"Integer {val} found.")
                try:
                    logging.info(f"Trying to set by key.")
                    self._dialogs[val]['active'] = not self._dialogs[val]['active']
                    logging.info(f"Setting by key successful.")
                    report = (f"Valid integer found, object "
                              f"'{self._dialogs[val]['name']}' "
                              f"toggled to {self._dialogs[val]['active']}")
                    print(report)
                    logging.info(report)
                except KeyError:
                    logging.info(f"Setting by key failed. Trying to set by dialog.id")
                    found = False
                    for key, dialog in self._dialogs.items():
                        if int(dialog['id']) == val:
                            dialog['active'] = not dialog['active']
                            report = (f"Valid dialog id found, object "
                                      f"'{dialog['name']}' "
                                      f"toggled to {dialog['active']}")
                            print(report)
                            logging.info(report)
                            found = True
                    if not found:
                        logging.info(f"Value {val} not found in keys or dialog.id")
                        print(f"{val} does not appear in the dialog list. "
                              "Use self.print_dialogs() for a full list of "
                              "names and reference numbers")
            elif isinstance(val, str):
                logging.info(f"Trying to find.")
                found = False
                for key, dialog in self._dialogs.items():
                    logging.debug(f"logging key '{key}' - name '{dialog['name']}'")
                    if dialog['name'] == val:
                        dialog['active'] = not dialog['active']
                        report = (f"Valid name found, object '{dialog['name']}' "
                                  f"toggled to {dialog['active']}")
                        print(report)
                        logging.info(report)
                        found = True
                if not found:
                    print(f"{val} does not appear in the dialog list. "
                          "Use self.print_dialogs() for a full list of "
                          "names and reference numbers")
            else:
                report = (f"self.dialogs requires an int or str. "
                          f"Value {val} is a {type(val)}.")
                logging.error(report)
                raise TypeError(report)
            return self._dialogs
        else:
            return None
    
    
    @property
    def api(self):
        return self._api
    
    @property
    def authors(self):
        auths = list()
        for auth in self._authors.keys():
            try:
                auths.append(self._authors[auth]['fullname'])
            except KeyError:
                auths.append(auth)
        return auths
    
    def full_authors(self):
        return self._authors
    
    def __get_config(self):
        # pulls api codes via config parser
        #
        # Can be edited to include access other config files, but currently
        # this has been sanitised to limit excess information.

        config = configparser.ConfigParser()
        config.read(self.__project_ini)
        logging.info(f"Config file {self.__project_ini} loaded.")
        try:
            api = config['API']
        except KeyError as e:
            logging.exception(f"Config file {self.__project_ini} does not contain an 'API' section.")
            raise KeyError
        api_id = int(api['api_id'])
        api_hash = api['api_hash']
        admin_phone = api['admin_phone']
        api_dict = {"id": api_id, "hash":api_hash,"phone": admin_phone}
        logging.info(f"API keys id, hash, and phone successfully grabbed from {self.__project_ini}.")
        self._api = api_dict
        try:
            config_authors = config['AUTHORS']
            for author in config_authors:
                self._authors[author] = json.loads(config_authors[author])
        except KeyError as e:
            logging.exception(f"Config file {self.__project_ini} does not contain an 'AUTHORS' section.")
            pass
            

    async def _grab_dialogs(self):
        # resets self._dialogs then populates with a new list of dialog objects
        # uses a dict keyed to numbers in the event that an item gets deleted from a dict.
        logging.info(f"Getting client dialogs, resetting self._dialogs")
        self._dialogs = dict()
        assert await self.client.is_user_authorized()
        logging.info(f"Iterating dialogs")
        count = 0
        async for dialog in self.client.iter_dialogs():
            logging.debug(f"Dialog {dialog.id} parsed.")
            self._dialogs[count] = {"dialog": dialog, 
                                    "name": dialog.name,
                                    "id": dialog.id,
                                    "active": False}
            logging.debug(f"Incorporated into self._dialogs dict")
            count+=1
    

    def gen_archive(self, *, num=-1, force=False):
        print("Starting archive generation.")
        if not self._messages:
            raise ValueError("No messages have been parsed.")
        if not isinstance(num, int):
            raise TypeError(f"Num is not sent to an integer. Currently '{num}'")
        count=0
        for page in self._messages:
            if page.id in self._archive:
                self._archive[page.id]
            elif not page._soup:
                if num >0 and count>= num:
                    logging.info(f"Breaking parse of links due to count reaching max of {num}")
                    break
                delay_val = self.delay
                print(f'       running delay of {delay_val}\rmsg #{num}')
                time.sleep(delay_val)
                logging.debug("Pausing until self.ok == True")
                while not self.ok:
                    time.sleep(0.25)
                count+=1
                if page.c_link:
                    logging.debug(f"parsing link {page.c_link}")
                    page.parse_link()
                else:
                    logging.debug(f"page has no c_link, skipping {page.c_link}")



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


if __name__ == '__main__':
    datefmt='%Y/%m/%d %H:%M:%S'
    log_level = 0
    filename = Path(f'log {pendulum.now().format("YYYY.MM.DD HH:mm:ss")}.log')

    # Log level can be set to a numeric 
    # as per https://docs.python.org/3/library/logging.html#logging-levels

    logging.basicConfig(filename=filename, filemode='w', 
                        format=(f'%(asctime)s - %(levelname)s - %(processName)s: '
                                f'%(funcName)s:%(lineno)d'
                                f'\tʕ •ᴥ•ʔ %(message)s'), level=log_level, datefmt=datefmt)

    # runs a try-except block to make sure not to send a request if UAs exists
    try:
        logging.info("Attempting to load UA list.")
        JUAs = json.loads(UAs.text)
        logging.info("Success loading UAs locally.")
    except NameError:
        logging.info("Failed to load UA list. Getting UAs from useragents.me/api")
        print("UAs not captured... capturing.")
        UAs = requests.get("https://www.useragents.me/api")
        JUAs = json.loads(UAs.text)
        logging.info("Success loading UAs from useragents.me/api")