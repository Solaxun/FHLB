# FHLB - WIP
Ongoing work to implement an API interface to the Federal Home Loan Bank of San Francisco's website.

## Rationale
The Federal Home Loan Bank of San Francisco provides access via it's website to a plethora of member-bank data, however there is currently no programmatic interface to access this data.  Several reports are available in Excel/CSV format or PDF format, but this still requires logging into the webiste, pulling down the data, and parsing it before any work can be done.  This project is meant to wrap certain portions of the website in a programmer friendly API simlar to what it may look like as a REST API.

## Limitations
#### Limited Coverage of Available Data
For now, the main areas of focus will be a subset of the reporting tab within the FHLB website.  My primary focus will be on:
- Advances data
- Current and Historical Indicative Rates
- Settlement/Transaction Account Status
- Borrowing Capacity

There are of course, many more reports and further many more sections of the website outside of the reporting region which may not be covered initially by this project. I will probably expand the reporting section slowly but other areas may not be available initially, or indefinitely.
#### Fragility
Since there is no official API yet (although I have reason to believe it is on the roadmap), the data is pulled by scraping the webiste - similar to what mint.com or other financial aggregators have done in the past when there are no API's available.  The consequence is that if the site changes, it will break this program requiring an update.  Aggregators like mint.com have a team of people to keep their program in sync with providers, whereas for this project you have just me :)
#### Speed of Execution
In order to retrieve data from the FHLB website, I'm using selenium with a headless browser to simulate actual browser actions.  Unfortunately try as I may, I was unable to find the actual endpoints where the data lives, e.g. those endpoints hit internally by the FHLB when they receive a request and pass it along to their server.  

This means that everything you do is performed on one thread, syncrhonously, using one WebDriver. Given that each report takes several seconds to load on site itself, you are looking at roughly 10-15 seconds wait for each request you perform, possibly longer depending on how much historical data you pull.  That somewhat limits the utility of this project to more of a "batch-job" oriented approach, but in reality most of the data available isn't updating very frequently anyhow so that may be fine.  Nonetheless, be prepared for exection to take some time if you are pulling several different reports. In the future I would like to explore spinning up multiple webdrivers on different threads and trying to split the workload across those thread-specific drivers.  

## Examples
Now that the caveats are out of the way, lets walk through a few examples of pulling data for your institution.

##### Initialize the client with website username and password
```python
# username and password correspond to the websites login page
FHLB = Client(username,password)
```
##### Perform requests corresponding to reporting tab
```python
# request outstanding advances
FHLB.advances('2019-02-01')

# output
[{'Trade Date': '2011-05-30', 'Funding Date': '2011-06-01', 'Maturity Date': '2019-06-15', 'Advance Number': 192511.0, 'Advance Type': 'FRC', 'Current Par ($)': 100000.0, 'Interest Rate (%)': 1.23, 'Next Interest Payment Date': '2019-02-08', 'Accrued Interest ($)':   1835.15, 'Estimated Next Interest Payment ($)': 18591.81, 'Details': 'View'}, 
 {'Trade Date': '2012-08-17', 'Funding Date': '2012-08-18', 'Maturity Date': '2019-07-19', 'Advance Number': 381915.0, 'Advance Type':     'FRC', 'Current Par ($)': 150000000.0, 'Interest Rate (%)': 2.01, 'Next Interest Payment Date': '2019-02-28', 'Accrued Interest ($)':    8053.12, 'Estimated Next Interest Payment ($)': 6589.29, 'Details': 'View'} ...]
 
# get STA data
FHLB.sta_account('2019-02-01','2019-02-26')
 
# output
{'2019-02-26': [{'Reference Number': '  ', 'Description': 'Balance as of close of business', 'Rates (%)': 1.8, 'Debits ($)': None, 'Credits ($)': None, 'Balance ($)': 123458.18}, 
                {'Reference Number': 500123.0, 'Description': 'NEW ADVANCE 500123', 'Rates (%)': None, 'Debits ($)': None, 'Credits ($)': 175000000.0, 'Balance ($)': None}...]
'2019-02-25 : [...]...}

# get current indicative borrowing rates
FHLB.current_rates()

# output
{'standard credit vrc':              [{'Advance Maturity': 'Overnight/Open', 'Advance Rate (%)': 2.18}], 
 'standard credit frc':              [{'Advance Maturity': '1 Month', 'Advance Rate (%)': 2.19}, 
                                      {'Advance Maturity': '2 Months', 'Advance Rate (%)': 2.21}, 
			              {...}...], 
 'standard adjustable rate credit' : [{...}]}

# get historical indicative rates 
# output varies slightly for different collateral_type and credit_type combination
FHLB.historical_rates(
	'2019-02-01',
	'2019-02-26',
	collateral_type='standard',
	credit_type='frc'
)

# output
{'2019-02-01': {'1 mo': 2.57, '2 mo': 2.58, '3 mo': 2.58, '6 mo': 2.6, '1 yr': 2.61, '2 yr': 2.66, '3 yr': 2.68, '5 yr': 2.75, '7 yr': 2.99,'10 yr': 3.24, '15 yr': 3.48, '20 yr': 3.66, '30 yr': 3.86}, 
 '2019-02-04': {'1 mo': 2.57, '2 mo': 2.58, '3 mo': 2.58, '6 mo': 2.61, '1 yr': 2.64, '2 yr': 2.71, '3 yr': 2.74, '5 yr': 2.82, '7 yr': 3.07, '10 yr': 3.3, '15 yr': 3.55, '20 yr': 3.73, '30 yr': 3.89
 ...}
```
