import time
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from urllib.parse import urljoin, urlencode 
from datetime import datetime
from collections import defaultdict
import itertools
from dateutil.relativedelta import relativedelta

from fhlb.config import SERVICE_ARGS, PHANTOM_JS_PATH
from fhlb.utils import mapt, partition

class Client():
	
	base_url = 'https://member.fhlbsf.com'
	reports_url = urljoin(base_url,'reports/')	

	def __init__(self,username,password):
		self.username = username
		self.password = password

		
		self.driver = self._login(
			self.base_url,
			self.username,
			self.password
		)
	
	def _login(self,login_url,username,password):
		'''
		Creates a webdriver and login to the site

		:param  login_url: base url for site
		:param  username: username for site
		:param  password: password for site
		
		:type  login_url: str
		:type  username: str
		:type  password: str

		:returns: logged in instance of webdriver
		:rtype: WebDriver
		'''
		self.driver = self._init_driver()
		self.driver.get(login_url)
		login_input = self.driver.find_element_by_id('user_username')
		password_input = self.driver.find_element_by_id('user_password')
		login_input.send_keys(username)
		password_input.send_keys(password)
		login_button = self.driver.find_element_by_name('commit')
		login_button.click()
		return self.driver
	
	def _init_driver(self):
		path = PHANTOM_JS_PATH or 'PhantomJS'
		service_args = None if not SERVICE_ARGS else SERVICE_ARGS
		driver = webdriver.PhantomJS(
			executable_path = path,
			service_args = service_args
		)
		return driver

	def advances(self,as_of_date):
		'''
		Get the outstanding FHLB advances as of a given date

		:param  as_of_date: date of the report in "YYYY-mm-dd" format
		:type  as_of_date: str

		:returns: [{'Trade Date':yyyy-mm-dd,'Funding Date': yyyy-mm-dd...}...]
		:rtype: list of dictionaries
		'''

		date = self._validate_date(as_of_date)
		advances_endpoint = 'advances?&start_date=' + date

		self.driver.get(
			urljoin(self.reports_url,advances_endpoint)
		)
		
		table = self._webdriver_get_xpath(15,"//*[@id='DataTables_Table_0']")
		
		doc = html.fromstring(table.get_attribute('innerHTML'))
		headers = doc.xpath("//tr[@role='row']//th//text()")
		tabledata = doc.xpath("//td[contains(@class,'report-cell')]//text()")
		
		data = mapt(self.format_text,[td.strip() for td in tabledata if td.strip()])
		data = [data[i*11:(i+1)*11] for i in range(int((len(data)/11)))]
		advances = [dict(zip(headers,d)) for d in data]
		return advances

	def sta_account(self,start_date,end_date):
		'''
		Shows the Settlement/Transaction Account for a range of dates, with
		history going back 6 months.

		:param  start_date: starting date of the report in "YYYY-mm-dd" format
		:param  end_date: ending date of the report in "YYYY-mm-dd" format
		
		:type  as_of_date: str
		:type  end_date: str

		:returns: {'date1':[{'Reference Number':ref#, 'Description':desc...}
		                    {'Reference Number':ref#, 'Description':desc...}]
				   'date2':[...]}
		:rtype: defaultdict
		'''
	
		sta_endpoint = 'settlement-transaction-account'
		
		bdate = self._validate_date(start_date)
		edate = self._validate_date(end_date)

		sta_url = urljoin(self.reports_url,sta_endpoint)
		
		self.driver.get(urljoin(
			sta_url,
			'?start_date={}&end_date={}'.format(bdate,edate)))
		
		table = self._webdriver_get_xpath(15,"//table[@class='report-table']")
		
		doc = html.fromstring(table.get_attribute('innerHTML'))
		td = doc.xpath('//tr//td')
		headers  = doc.xpath('//th//text()')
		headers  = [x.strip() for x in headers]
		sta_data = [x.getchildren()[0].text if x.getchildren() else x.text for x in td]
		sta_data = mapt(Client.format_text,sta_data)
		sta_data = itertools.groupby(
			partition(7,sta_data),
			lambda record: record[0]
		)

		res = defaultdict(list)
		for date, records_per_date in sta_data:
			for record in records_per_date:
				res[date].append(dict(zip(headers[1:],record[1:])))
		return res

	def _webdriver_get_xpath(self,wait_seconds,xpath):
		return WebDriverWait(self.driver, wait_seconds).until(
			EC.presence_of_element_located((By.XPATH,xpath))
		)

	def _validate_date(self,date):
		try:
			datetime.strptime(date,'%Y-%m-%d')
		except ValueError as e:
			raise e
		return date

	def is_monthend(self,date):
		date = datetime.strptime(date,'%Y-%m-%d')
		nextday = date + relativedelta(days=1)
		if date.month == 12:
			valid_month_end = nextday.month == 1
		else:
			valid_month_end = nextday.month == date.month + 1
		if not valid_month_end:
			raise AttributeError('{} is not a month-end!'.format(date))
	
	def current_rates(self):
		'''
		Reflects price indications as of 6:00 am PT on the current business day and STA
		rate as of the end of the prior business day.

		:returns: {'standard credit vrc':[{'Advance Maturity':'Overnight/Open',
		                                  {'Advance Rate (%)':2.57}}]
				   'standard credit frc': [{...}]}
		:rtype: dict
		'''
		
		current_rates_endpoint = 'current-price-indications'
		# dependent on table order in the website - if that changes, so should this
		tables = ['standard credit vrc',
				  'standard credit frc',
				  'standard adjustable rate credit',
				  'securities-backed credit vrc',
				  'securities-backed credit frc',
				  'securities-backed adjustable rate credit']
		
		self.driver.get(urljoin(self.reports_url,current_rates_endpoint))
		# wait for one of the tables to populate (they all do at the same time)
		self._webdriver_get_xpath(15,"//table[@id='DataTables_Table_1']/tbody")
		# then get outer div that wraps them (prior to waiting, all are empty)
		main_div = self._webdriver_get_xpath(15,
			"//div[@class='report report-price-indications " +
			"report-current-price-indications row']")
		
		div_html = html.fromstring(main_div.get_attribute('innerHTML'))
		
		rate_tables = {}
		for i, credit_type in enumerate(tables):
			table = div_html.xpath("//table[@id='DataTables_Table_{}']/tbody".format(i))
			text = table[0].xpath('.//td//text()') 
			records = [x.strip() for x in text if x.strip()]
			# dependent on table order in the website - if that changes, so should this
			if i in [0,1,3,4]:
				headers = ['Advance Maturity','Advance Rate (%)']
			elif i == 2:
				headers = [
					'Advance Maturity',
					'1 Month LIBOR',
					'3 Month LIBOR',
					'6 Month LIBOR',
					'Daily Prime'
				]
			else:
				headers = [
					'Advance Maturity',
					'1 Month LIBOR',
					'3 Month LIBOR',
					'6 Month LIBOR'
				]
			
			records = [dict(zip(headers,p)) 
				for p in partition(len(headers),mapt(self.format_text,records))]
			
			rate_tables[credit_type] = records
		
		sta_rates = div_html.xpath(".//table[@class='report-table sta-rate-table " +
			"report-table-vertical-headers']//td//text()")
		
		rate_tables['Settlement/Transaction Account (STA)'] = {sta_rates[0]:sta_rates[1]}
		
		return rate_tables
	
	def historical_rates(self,
						 start_date,
						 end_date,
						 collateral_type=None,
						 credit_type=None):
		'''
		Historical price indications as of 6:00 am PST on the date(s) referenced

		:param  start_date: starting date of the report in "YYYY-mm-dd" format
		:param  end_date: ending date of the report in "YYYY-mm-dd" format
		:param  collateral_type: one of: Standard Credit Program, 
			Securities-Backed Credit Program, or Settlemant/Transaction Acct. Rate
		:param  credit_type: one of: Fixed Rate Credit, Variable Rate Credit, or
			Adjustable Rate Credit, where Adjustable Rate Credit may be either
			1 Month Libor, 3 Month LIBOR, 6 Month LIBOR, or Daily Prime.  Note
			that Daily Prime is only applicable for the Standard Credit Program
			collateral_type.
		
		:type  as_of_date: str
		:type  end_date: str
		:type  collateral_type: str
		:type  credit_type: str

		:returns: {'date1': {'maturity1':rate1,'maturity2':rate2}
		           'date2': {...}
				  }
		:rtype: dict
		'''
		self._validate_date(start_date)
		self._validate_date(end_date)

		collateral_type = collateral_type.lower() if collateral_type else None
		credit_type     = credit_type.lower() if credit_type else None
		
		credit_types = ['frc','vrc','1m_libor','3m_libor',
						'6m_libor','daily_prime']
		
		valid_pairings = set(itertools.chain(
				itertools.product(['standard'],credit_types),
				itertools.product(['sbc'],credit_types[0:-1]),
				[('sta',None)]
			))

		if (collateral_type,credit_type) not in valid_pairings:
				raise AttributeError(
					"No matching entry for combination credit_type: {}".format(
						credit_type) + 
					" and collateral_type: {}".format(collateral_type)
				)

		historical_rates_endpoint = 'historical-price-indications'
		historical_rates_url      = urljoin(
			self.reports_url,
			historical_rates_endpoint
		)
		params = {
			'start_date'                       :start_date,
			'end_date'       				   :end_date,
			'historical_price_collateral_type' :collateral_type,
			'historical_price_credit_type'     :credit_type
		}
		params = urlencode(params)
		request_url = historical_rates_url + '?' + params
		self.driver.get(request_url)
		 # wait for data to load - sloppy but couldn't find a common xpath
		 # that all sub url's share.  Maybe try to find one again later
		 # but moving on for now
		time.sleep(10)
		# hopefully after 10 seconds the table referenced by the xpath 
		# below is populated
		table = self._webdriver_get_xpath(0,"//table[contains(@class,'report-table')]")
		table_html = html.fromstring(table.get_attribute('innerHTML'))
		data = table_html[0].xpath('//td//text()')
		headers = table_html[0].xpath('//th//text()')
		headers = [x.strip() for x in headers]
		records = [x.strip() for x in data if x.strip()]
		record_count = len(headers)
	
		if credit_type in ['frc','vrc'] or collateral_type == 'sta':
			return {p[0]:dict(zip(headers[1:],p[1:]))
				    for p in partition(record_count,
									   mapt(self.format_text,records))}
		elif 'libor' in credit_type:
			return {p[0]:dict(zip(headers[2:],p[1:]))
				    for p in partition(record_count-1,
							 	       mapt(self.format_text,records))}
		elif credit_type == 'daily_prime':
			mats, headers = headers[0:4], headers[4:]
			data = [mapt(self.format_text,p) for p in partition(9,records)]
			
			res = {}
			for d in data:
				date, *others = d
				bench_and_spread = partition(2,others)
				per_maturity = zip(mats,bench_and_spread)
				
				daily_obs = {}
				for mat,bns in per_maturity:
					daily_obs[mat] = {'benchmark':bns[0],'spread':bns[1]}
				res[date] = daily_obs
			return res

	def borrowing_capacity(self,as_of_date=None):
		'''
		Reflects borrowing capacity for the month-end `as_of_date`. 
		History is available going back back 12 months.

		Loan collateral reflects intraday processing of Mortgage Collateral Updates.
		Market value and all other data is as of prior business day close.

		:returns: TBD
		:rtype: dict of nested dicts
		'''
		today = datetime.now().strftime('%Y-%m-%d')
		if as_of_date is None:
			as_of_date = today
		else:
			self._validate_date(as_of_date)
			if as_of_date != today:
				self.is_monthend(as_of_date)

		borrowing_capacity_endpoint = 'borrowing-capacity'
		params = urlencode({'as_of_date':as_of_date})

		borrowing_capacity_url = urljoin(
			self.reports_url,
			borrowing_capacity_endpoint
		)
		
		self.driver.get(borrowing_capacity_url + '?' + params)
		
		tables = WebDriverWait(self.driver, 15).until(
			EC.presence_of_all_elements_located(
				(By.XPATH,"//table[contains(@class,'report-table report-sub-table')" 
				 + " or contains(@class,'report-table report-parent-table')]")
			)
		)
		
		tree = lambda: defaultdict(tree)
		res  = tree()
		
		for i,table in enumerate(tables):
			doc = html.fromstring(table.get_attribute('innerHTML'))
			headers = doc.xpath('.//th//text()')
			data   = doc.xpath('.//td//text()')
			if i == 0: # hack - first table missing 2nd to last value in footer
				data = data[:-1] + [None] + data[-1:]
			record_size = len(headers) or 2
			recs = partition(record_size,mapt(self.format_text,data))
			section = 'capacity' if i in [1,2,3,5] else 'collateral'
			credit_program = 'standard' if i in range(4) else 'securities_backed'
			for rec in recs:
				collateral_type, *info = rec
				if headers:
					entry = dict(zip(headers[1:],info))
				else:
					entry = info[0]
				res[credit_program][section][collateral_type] = entry
		return res
	
	def letters_of_credit(self):
		'''
		Reflects current status of letters of credit.

		:returns: [{'LC Number':2081-10, 'Beneficiary': 'inst name', ...}
				   {'LC Number':2081-10, 'Beneficiary': 'inst name', ...}...]
		:rtype: list of dicts
		'''
		
		loc_url = urljoin(self.base_url,'letters-of-credit/manage')
		self.driver.get(loc_url)
		table = self._webdriver_get_xpath(15,'//table')
		doc = html.fromstring(table.get_attribute('innerHTML'))
		data =  [self.format_text(d.strip()) 
				 for d in doc.xpath('//td//text()') if d != '\n']
		headers = doc.xpath('//th//text()')
		return [dict(zip(headers,rec)) for rec in partition(len(headers),data)]

	@staticmethod
	def format_text(text):
		"""format_texts numeric text to float, date text to consistent date
		format, and all else is left unchanged"""
		#matches number type, with optional preceding '$', format_text to float
		if text is None:
			return None
		elif re.match('(\$*\d+[\.,]*)+\d*\Z',text):
			return float(text.replace(',','').replace('$',''))
		# negative currency - strip parens and negate result
		elif text.startswith('('):
			return Client.format_text(text[1:-1]) * -1
		elif text == 'N/A':
			return None
		#matches date type with '/', format_text to consistent date format with '-'
		elif re.match('\d+[/]\d+[/]\d+',text):
			month, day, year = text.split('/')
			if len(year) == 2:
				year = '20' + year # i'll be dead before it matters
			return '-'.join([year,month,day])
		else:
			return text
# todo - reports that only go back 'n' months or have restrictions around month-end availability etc
# will not have the option to select incorrect dates on the site, but if you send a request with
# date query parameters outside those range, you'll just get zeroes back.  Guard against this.
