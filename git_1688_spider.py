# coding=utf-8

import requests
import execjs
import re
import time
import pprint


class Albb:
    def __init__(self):
        self.headers = {
            'authority': 'h5api.m.1688.com',
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': '*******',  # 换上自己的cookie
            'origin': 'https://ailing.1688.com',
            'referer': 'https://ailing.1688.com/',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': '*******',  # 换上User-Agent
        }

        self.token = re.findall('_m_h5_tk=(.*?)_', self.headers['cookie'], re.S)[0]  # token随着cookie变化，阿里的cookie保质期不长的。
        self.appKey = "12574478"
        self.time1 = str(int(time.time() * 1000))

    def execjs_run(self):  # 需要的参数我直接保存在初始化里了，所以调用execjs_run就不用传入参数了
        with open("albb.js", "r", encoding="utf-8") as f:
            js_content = f.read()
            context = execjs.compile(js_content)
            ret = context.call("h", self.e)

            return ret

    def get_star_url(self, star_url):
        '''
        1.设置了三种正则模式分别针对传递过来的url店铺首页，店铺全部商品页，商品详情页--->正则匹配获取店铺ID
        2.构造data和o.data中的memberId后面的数值
        :param star_url: 可以是浏览器打开的店铺下选择全部商品的url，也可以是浏览器打开的店铺首页的url,也可以是商品详情页(去掉后缀，否则弹验证码)
        :return: 构造data和o.data中的memberId后面的数值
        '''
        response = requests.get(star_url, headers=self.headers)
        try:
            ret = response.content.decode("gbk")  # 店铺首页需要gbk解码
        except UnicodeDecodeError:
            ret = response.content.decode()  # 店铺全部商品页可以utf-8解码，假如使用gbk解码就会报错UnicodeDecodeError
        # 正则匹配取出店铺ID
        ret_list = re.search("window.shopPageDataApi = .*?=(.*?)&|adminMemberId: \"(.*?)\"|cbu.*?b/-/(.*?)_s", ret, re.S)  # 获取店铺id--> memberId
        self.memberID = ret_list.group(1)  # 创建一个self.memberID来保存店铺iD
        if self.memberID == None:
            # 因为第一个正则匹配的是店铺全部商品页，如果第一个小括号没有内容为None，那么就取第二个
            self.memberID = ret_list.group(2)
            if self.memberID == None:  # 如果第二个还是没有就取第三个  (第二个是针对全部商品页 #第三个针对商品详情页)
                self.memberID = ret_list.group(3)
                print("从商品详情页获取到的ID--->", self.memberID)
                return self.memberID
            print("从全部商品页获取到的ID--->", self.memberID)
            return self.memberID
        print("从店铺首页获取到的ID--->", self.memberID)
        return self.memberID

    def run(self,star_url):

        # star_url = "https://shop9116362763633.1688.com/page/offerlist.htm?spm=a2615.7691456.wp_pc_common_topnav_38229151.0"
        # star_url = "https://shop12752d9581431.1688.com/page/index.html?spm=0.0.wp_pc_common_header_undefined.0"
        # star_url =  "https://detail.1688.com/offer/674373166227.html"
        self.get_star_url(star_url)   # 获取到了self.memberID 店铺ID

        self.data = {  # %s 替换为正则后提取的memberID
            'data': '{"dataType":"moduleData","argString":"{\\"memberId\\":\\"%s\\",\\"appName\\":\\"pcmodules\\",\\"resourceName\\":\\"wpOfferColumn\\",\\"type\\":\\"view\\",\\"version\\":\\"1.0.0\\",\\"appdata\\":{\\"sortType\\":\\"wangpu_score\\",\\"sellerRecommendFilter\\":false,\\"mixFilter\\":false,\\"tradenumFilter\\":false,\\"quantityBegin\\":null,\\"pageNum\\":1,\\"count\\":30}}"}' % self.memberID,
        }

        # self.o_data和self.data 都一样的。不过一个是字符串一个是字典。 然后pageNum要共同变化--->   \\"pageNum\\":1,\\
        self.o_data = "{\"dataType\":\"moduleData\",\"argString\":\"{\\\"memberId\\\":\\\"%s\\\",\\\"appName\\\":\\\"pcmodules\\\",\\\"resourceName\\\":\\\"wpOfferColumn\\\",\\\"type\\\":\\\"view\\\",\\\"version\\\":\\\"1.0.0\\\",\\\"appdata\\\":{\\\"sortType\\\":\\\"wangpu_score\\\",\\\"sellerRecommendFilter\\\":false,\\\"mixFilter\\\":false,\\\"tradenumFilter\\\":false,\\\"quantityBegin\\\":null,\\\"pageNum\\\":1,\\\"count\\\":30}}\"}" % self.memberID
        self.e = (self.token + '&' + str(self.time1) + '&' + self.appKey + '&' + self.o_data)  # 传入到js文件的参数

        # 通过excejs运行js文件中的函数得到sign值
        self.sign = self.execjs_run()  # 需要的参数我直接保存在初始化里了，所以调用execjs_run就不用传入参数了
        # 字符串以 f开头表示在字符串内支持大括号内的python 表达式
        url = f"https://h5api.m.1688.com/h5/mtop.1688.shop.data.get/1.0/?jsv=2.6.2&appKey=12574478&t={self.time1}&sign={str(self.sign)}&api=mtop.1688.shop.data.get&v=1.0&type=json&valueType=string&dataType=json&timeout=10000"

        self.params = {
            'jsv': '2.6.2',
            'appKey': '12574478',
            't': self.time1,
            'sign': str(self.sign),
            'api': 'mtop.1688.shop.data.get',
            'v': '1.0',
            'type': 'json',
            'valueType': 'string',
            'dataType': 'json',
            'timeout': '10000',
        }

        response = requests.post('https://h5api.m.1688.com/h5/mtop.1688.shop.data.get/1.0/', params=self.params,
                                 headers=self.headers, data=self.data)

        print("*"*50)
        pprint.pprint(response.content.decode())


if __name__ == '__main__':
    # 1. 输入店铺首页或者店铺全部商品页的url或者商品详情页
    print("可识别url为：1.店铺首页url 2.店铺全部商品页的url 3.商品详情页url")
    print("特别注意-->如果是商品详情页请去掉后缀，保留格式为：https://detail.1688.com/offer/**********.html")
    star_url = input("请输入url--->:")
    albb = Albb()
    albb.run(star_url)
