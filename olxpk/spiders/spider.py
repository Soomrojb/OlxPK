import scrapy, re
from bs4 import BeautifulSoup
#from scrapy.utils.response import open_in_browser

# variables
LoginURL = "https://www.olx.com.pk/i2/lahore/account/"
Sitemap = "https://www.olx.com.pk/sitemap/"
Credentials = ['', '']

class Olxpk(scrapy.Spider):
	name = "olxpk"
	allowed_domains = ['olx.com.pk']
	start_urls = [LoginURL]
	
	def parse(self, response):
		Soup = BeautifulSoup(response.body, "lxml")
		RawToken = Soup.find('script', text=re.compile('csrf_token_value'))
		Token = re.findall(r"csrf_token_value\s*\=\"([^\"]+)", RawToken.text, flags=0)[0]
		FormData = {
			'login[email]' : Credentials[0],
			'login[password]' : Credentials[1],
			'login[captcha]' : '',
			'csrf_token' : Token
		}
		yield scrapy.FormRequest.from_response(
			response,
			method="POST",
			formdata=FormData,
			callback=self.afterlogin
		)

	def afterlogin(self, response):
		yield scrapy.Request(Sitemap, dont_filter=True, callback=self.sitemappg)

	def sitemappg(self, response):
		Soup = BeautifulSoup(response.body, "lxml")
		for H3s in Soup.select('h3 > a[class*=link]'):
			CategoryUrl = H3s['href']
			CategoryName = H3s.text
			MetaData = {
				'Category Url' : re.sub('\n', '', CategoryUrl),
				'Category Name' : re.sub('\n', '', CategoryName)
			}
			yield scrapy.Request(CategoryUrl, dont_filter=True, meta=MetaData, callback=self.listingpg)
	
	def listingpg(self, response):
		Soup = BeautifulSoup(response.body, "lxml")
		for Post in Soup.select("td[class*='offer onclick']"):
			Title = Post.select("h3[class*=large] > a")[0].text
			PostUrl = Post.select("h3[class*=large] > a")[0]['href']
			try:
				Price = Post.select("div[class*=space] > p[class*=price] > strong")[0].text
			except:
				Price = "-"
			Date = Post.select("td[valign=bottom] > p")[0].text
			MetaData = {
				'Title' : re.sub('\n', '', Title),
				'PostUrl' : PostUrl,
				'Price' : re.sub('\n', '', Price),
				'Date' : Date,
				'Category Url' : response.meta['Category Url'],
				'Category Name' : response.meta['Category Name']
			}
			yield scrapy.Request(PostUrl, dont_filter=True, meta=MetaData, callback=self.recordpg)

	def recordpg(self, response):
		Soup = BeautifulSoup(response.body, "lxml")
		Address = Soup.select("span[class*=show-map-link] > strong[class*=c2b]")[0].text
		Views = Soup.select("div[class*=pdingtop] > strong")[0].text
		yield {
			'Title' : response.meta['Title'],
			'PostUrl' : response.meta['PostUrl'],
			'Price' : response.meta['Price'],
			'Date' : response.meta['Date'],
			'Category Url' : response.meta['Category Url'],
			'Category Name' : response.meta['Category Name'],
			'Address' : re.sub('\n', '', Address),
			'Views' : re.sub('\n', '', Views)
		}
			
