import requests
import dateutil
import json
import sys
import urllib
import urllib.parse
from urllib.parse import urlparse, parse_qs
import xbmc
import xbmcgui
import xbmcplugin
import datetime
import time
from dateutil import tz
from functools import reduce

try:
    import StorageServer
except:
   import storageserverdummy as StorageServer

class Kodi:
    def __init__(self):
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        self.args = parse_qs(sys.argv[2][1:])

    def build_url(self, query):
        return self.base_url + '?' + urllib.parse.urlencode(query)

class Authentication:
   
    def __init__(self, baseurl):
        if baseurl == None:
            raise Exception("baseurl is empty")

        self.__BaseUrl = baseurl
        self.Category = "personal_computer"
        self.Os_family = "http"
        self.Locale = "en-US"
        self.__Authenticated = False
        
        self.Remote_addr = None
        self.Uuid = None
        self.Token = None
        self.Country_code = None
        self.Authenticate()

    def Authenticate(self):
        url = self.__BaseUrl + "session?category=" + self.Category + "&os_family=" + self.Os_family + "&locale=" + self.Locale
        
        req = requests.request("GET", url)

        if req.status_code != 200:
            self.__Authenticated = False
            return False
        
        
        try:
            response = req.json()   
            self.Remote_addr = response['remote_addr']
            self.Uuid = response['uid']
            self.Token = response['token']
            self.Country_code = response['country_code']

            self.__Authenticated = True
        except:
            print("error occured decoding the json response.")
            self.__Authenticated = False
            return False


class RedBull:
    baseResource = 'https://resources.redbull.tv/'

    def __init__(self, baseurl, token=None):
        self.__Baseurl = baseurl
        self.Token = token
        if token is None:
            auth = Authentication(baseurl)
            self.Token = auth.Token
        else:
            self.Token = token[0]

    def GetResource(self, id, type, size=300):
        url = self.baseResource + id + '/' + type + '/im:i:w_' + str(size) + ',q_70,f_jpg'
        xbmc.log(url)
        return url

    def GetData(self, url):
        xbmc.log(self.Token)
        xbmc.log(url)
        response = requests.request("GET", url, headers={"Authorization": self.Token})
        
        
        if response.status_code != 200:
            raise Exception("Error getting data, reponse code " + response.status_code)
        return response.json()

    def ProcessArt(self, id, resources):
        xbmc.log('ProcessArt(' + id + ', ' + json.dumps(resources) + ')')
        art = {}
        
        art['thumb'] = self.GetResource(id, resources[0])

        for resource in resources:
            if resource in {"rbtv_display_art_banner","rbtv_background_banner"}:
                art['banner'] = self.GetResource(id, resource)
            elif resource in {"rbtv_display_art_portrait", "rbtv_background_portrait"}:
                art['poster'] = self.GetResource(id, resource, 400)
            elif resource in {"rbtv_display_art_landscape","rbtv_background_landscape"}:
                art['landscape'] = self.GetResource(id, resource)
                art['fanart'] = self.GetResource(id, resource, 1080)
            elif resource in {"rbtv_display_art_square", "rbtv_background_square"}:
                art['icon'] = self.GetResource(id, resource, 100)
                
        xbmc.log(json.dumps(art))
        return art

    def GetTrailer(self, id, resources):
        xbmc.log('GetTrailers()')
        trailer = {}

        for resource in resources:
            if resource in {"short_preview_mp4_high"}:
                return self.GetResource(id, resource, 100)

    #base 
    def GetCollection(self, id, offset=0, limit=20):
        xbmc.log('GetCollection(' + id + ', ' + str(offset) + ', ' + str(limit) + ')')
        url = self.__Baseurl + 'collections/' + id + '?offset=' + str(offset) + '&limit=' + str(limit)

        collection = self.GetData(url)

        for item in collection['items']:
            long_description = ''
            setinfo = {}
            label = ''
            li = xbmcgui.ListItem()

            label = item['title']

            if item['long_description'] != '':
                long_description += item['long_description'] + '\n'

            if 'subheading' in item:
                setinfo['tagline'] = item['subheading']
            
            setinfo['tvshowtitle'] = collection['label']

            if 'resources' in item:
                setinfo['trailer'] = self.GetTrailer(item['id'], item['resources'])

            li.setLabel(label)

            if item['content_type'] == 'live_program' or 'stop':
                if 'status' in item:
                    if 'label' in item['status']:
                        long_description += 'Status: ' + item['status']['label'] + '\n\n'
                    if 'start_time' in item['status']:
                        xbmc.log(item['status']['start_time'])
                        utctime = None
                        try:
                            utctime = datetime.datetime.strptime(str(item['status']['start_time']), '%Y-%m-%dT%H:%M:%S.%fZ')
                        except TypeError:
                            utctime = datetime.datetime(*(time.strptime(item['status']['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ')[0:6]))
                        from_zone = tz.tzutc()
                        to_zone = tz.tzlocal()
                        utctime = utctime.replace(tzinfo=from_zone)
                        localtime = utctime.astimezone(to_zone)
                        long_description += 'Start time' + '\n'
                        long_description += '(UTC): ' + str(utctime.strftime('%Y-%m-%d %H:%M:%S')) + '\n'
                        long_description += '(Local): ' + str(localtime.strftime('%Y-%m-%d %H:%M:%S')) + '\n'
                        
                    long_description += '\n'
            
            
            setinfo['plot'] = long_description


            if 'resources' in item:
                li.setArt(self.ProcessArt(item['id'], item['resources']))
                #li.setThumbnailImage(self.GetResource(item['id'], item['resources'][0]))
            
            if 'playable' in item:
                li.setProperty('IsPlayable', str(item['playable']))

            if item['type'] == 'page':
                url = Kodi().build_url({
                    'mode': 'product',
                    'id': item['id'],
                    'token': self.Token
                    })

                li.setInfo('video',setinfo)
                xbmc.log(li.getArt('portrait'))


                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

            elif item['type'] == 'video':
                if 'duration' in item:
                    setinfo['duration'] = item['duration'] / 1000

                li.setInfo('video', setinfo)
                #li.setProperty('startoffset', str(10000))
                url = 'https://dms.redbull.tv/v3/' + item['id'] + '/' + self.Token + '/playlist.m3u8'
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)

        if collection['meta']['total'] > collection['meta']['offset'] + collection['meta']['limit']:
            li = xbmcgui.ListItem()
            li.setLabel('Next page')
            
            url = Kodi().build_url({
                'mode': 'collection',
                'id': id,
                'offset': offset + limit,
                'limit': limit,
                'token': self.Token
            })

            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

        return True

    def secondsToStr(self, t):
        rediv = lambda ll,b : list(divmod(ll[0],b)) + ll[1:]
        return "%d:%02d:%02d.%03d" % tuple(reduce(rediv,[[t*1000,],1000,60,60]))

    def GetProduct(self, id):
        xbmc.log('GetProducts(' + id + ')')
        url = self.__Baseurl + "products/" + id
        setInfo = {}
        productListItem = xbmcgui.ListItem()
        product =  self.GetData(url)

        if 'resources' in product:
            productListItem.setArt(self.ProcessArt(product['id'], product['resources']))
        
        if 'long_description' in product:
            setInfo['plot'] = product['long_description']

        setInfo['title'] = product['title']

        productListItem.setInfo('video', setInfo)

        if 'links' in product:
            for link in product['links']:
                if 'action' in link:
                    li = productListItem
                    li.setLabel(link['label'])

                    if 'resources' in link:
                        li.setArt(self.ProcessArt(collection['id'], collection['resources']))                    

                    if link['action'] == 'play':
                        li.setProperty('StartOffset', self.secondsToStr(60))
                        url = 'https://dms.redbull.tv/v3/' + link['id'] + '/' + self.Token + '/playlist.m3u8'
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)
                    
                    elif link['action'] == 'view':
                        url = Kodi().build_url({
                            'mode': 'product',
                            'id': link['id'],
                            'token': self.Token
                        })
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)


        for collection in product['collections']:
            li = productListItem
            li.setLabel(collection['label'])

            if 'resources' in collection:
                li.setArt(self.ProcessArt(collection['id'], collection['resources']))
            

            url = Kodi().build_url({
                'mode': 'collection',
                'id': collection['id'],
                'token': self.Token
                })

            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)