import os
import re

from streamlink.plugin import HIGH_PRIORITY, Plugin, pluginmatcher
from streamlink.plugin.api import validate
from streamlink.stream import HLSStream

_post_schema = validate.Schema(
    {
        "cam": validate.Schema({
                    'streamName' : str
        }),
        "user": validate.Schema({
                    'user' : validate.Schema({
                                'status' : str,
                                'isLive' : bool,
                                'broadcastServer': str
                    })
        })    
    }
)

_url_re = re.compile(r"https?://(\w+\.)?stripchat\.com/(?P<username>[a-zA-Z0-9_-]+)")

@pluginmatcher(re.compile(r"https?://(\w+\.)?stripchat\.com/(?P<username>[a-zA-Z0-9_-]+)"))
@pluginmatcher(priority=HIGH_PRIORITY, pattern=re.compile("""
    https?://(?:
         sitenumberone
        |adifferentsite
        |somethingelse
    )
    /.+\.m3u8
""", re.VERBOSE))


class Stripchat(Plugin):
    @classmethod
    def can_handle_url(cls, url):
        return _url_re.match(url)

    def _get_streams(self):
        match = _url_re.match(self.url)
        username = match.group("username")
        api_call = "https://stripchat.com/api/front/v2/models/username/{0}/cam".format(username)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.url,
        }
        
        #self.logger.info("API Call: " + api_call)
        
        res = self.session.http.get(api_call, headers=headers)
        #self.logger.info("API Response: " + str(res.json()))
        data = self.session.http.json(res, schema=_post_schema)
        
        self.logger.info("Broadcast Server: " + data["user"]["user"]["broadcastServer"])

        server = "https://edge-hls.doppiocdn.com/hls/{1}/master/{1}.m3u8".format(data["user"]["user"]["broadcastServer"],data["cam"]["streamName"])

        server0 = "https://edge-hls.doppiocdn.com/hls/{1}/master/{1}.m3u8".format(data["user"]["user"]["broadcastServer"],data["cam"]["streamName"])

        self.logger.info("Stream status: {0}".format(data["user"]["user"]["status"]))
        self.logger.info("Stream live?: {0}".format(data["user"]["user"]["isLive"]))

        if (data["user"]["user"]["isLive"] is True and data["user"]["user"]["status"] == "public"):
            try:
                for s in HLSStream.parse_variant_playlist(self.session,server,headers={'Referer': self.url}).items():
                    self.logger.info("Playlist Item: " + str(s))
                    yield s
            except IOError as err:
                self.logger.info("This here is a exception. Hello fren :)")
                self.logger.info("The actual exception: " + str(err))
                stream = HLSStream(self.session, server0)
                yield "Auto", stream

__plugin__ = Stripchat
